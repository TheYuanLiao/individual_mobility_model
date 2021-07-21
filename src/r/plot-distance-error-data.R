# Title     : Distance difference between Haversine distance and network distance
# Objective : Based on travel survey
# Created by: Yuan Liao
# Created on: 2021-07-19

library(ggplot2)
library(dplyr)
library(viridis)
library(ggpubr)
library(scales)
options(scipen=10000)

# Load distances
df.total <- read.csv('dbs/distance_error_data.csv')
df.total <- df.total[df.total$distance_network >= df.total$distance, ]
df.total$diff <- df.total$distance_network/df.total$distance

# Sweden
df <- df.total[df.total$region=='sweden', ]
df$dg <- cut(df$distance, breaks = unlist(lapply(seq(-1, 4, 5/30), function(x){10^(x)})))

df_stats <- df %>%
  group_by(dg)  %>%
  summarise(distance = median(distance),
            center = median(distance_network),
            lower = quantile(distance_network, 0.25),
            upper = quantile(distance_network, 0.75),
            center_diff = median(diff),
            lower_diff = quantile(diff, 0.25),
            upper_diff = quantile(diff, 0.75))

g1 <- ggplot(data = df) +
  theme_minimal() +
  # Raw data
  geom_bin2d(aes(x=distance, y=distance_network), alpha=0.2) +
  scale_fill_gradient(name = 'No. of trips', low = "steelblue", high = 'coral') +

  # Distances by groups
  geom_linerange(data = df_stats, aes(x=distance, ymin=lower, ymax=upper), color='steelblue', size=0.5) +
  geom_point(data = df_stats, aes(x=distance, y=center), color='steelblue', shape = 21, fill = "white", size = 2) +

  geom_abline(intercept = 0, slope = 1, size=0.3, color='gray45') +
  labs(x = "Trip distance (Euclidean, km)", y = 'Reported travel distance (km)') +
  scale_x_log10(limits = c(0.1, 1500),
                breaks = trans_breaks("log10", function(x) 10^x),
                labels = trans_format("log10", scales::math_format(10^.x))) +
  scale_y_log10(limits = c(0.1, 1500),
                breaks = trans_breaks("log10", function(x) 10^x),
                labels = trans_format("log10", scales::math_format(10^.x))) +
  theme(legend.position = 'top', legend.key.height= unit(0.3, 'cm'),
        plot.margin = margin(1,0.5,0,0, "cm"))

g2 <- ggplot(data = df) +
  theme_minimal() +
  # Raw data
  geom_bin2d(aes(x=distance, y=diff), alpha=0.2) +
  scale_fill_gradient(name = 'No. of trips', low = "steelblue", high = 'coral') +

  # Distances by groups
  geom_linerange(data = df_stats, aes(x=distance, ymin=lower_diff, ymax=upper_diff), color='steelblue', size=0.5) +
  geom_point(data = df_stats, aes(x=distance, y=center_diff), color='steelblue', shape = 21, fill = "white", size = 2) +

  geom_hline(yintercept=median(df$diff), size=0.3, color='black') +
  annotate("text", x = 100, y = 5, label = sprintf('Median ratio = %.1f', median(df$diff))) +
  labs(x = "Trip distance (Euclidean, km)", y = 'Distance ratio') +
  scale_x_log10(limits = c(0.1, 1500),
                breaks = trans_breaks("log10", function(x) 10^x),
                labels = trans_format("log10", scales::math_format(10^.x))) +
  scale_y_log10(limits = c(1, 100), breaks = c(1, 10, 100), labels = c(1, 10, 100)) +
  theme(legend.position = 'top', legend.key.height= unit(0.3, 'cm'),
        plot.margin = margin(1,0.5,0,0, "cm"))


# the Netherlands
df <- df.total[df.total$region=='netherlands', ]
df$dg <- cut(df$distance, breaks = unlist(lapply(seq(-1, 3, 4/30), function(x){10^(x)})))

df_stats <- df %>%
  group_by(dg)  %>%
  summarise(distance = median(distance),
            center = median(distance_network),
            lower = quantile(distance_network, 0.25),
            upper = quantile(distance_network, 0.75),
            center_diff = median(diff),
            lower_diff = quantile(diff, 0.25),
            upper_diff = quantile(diff, 0.75))

g3 <- ggplot(data = df) +
  theme_minimal() +
  # Raw data
  geom_bin2d(aes(x=distance, y=distance_network), alpha=0.2) +
  scale_fill_gradient(name = 'No. of trips', low = "steelblue", high = 'coral') +

  # Distances by groups
  geom_linerange(data = df_stats, aes(x=distance, ymin=lower, ymax=upper), color='steelblue', size=0.5) +
  geom_point(data = df_stats, aes(x=distance, y=center), color='steelblue', shape = 21, fill = "white", size = 2) +

  geom_abline(intercept = 0, slope = 1, size=0.3, color='gray45') +
  labs(x = "Trip distance (Euclidean, km)", y = 'Reported travel distance (km)') +
  scale_x_log10(limits = c(0.1, 1500),
                breaks = trans_breaks("log10", function(x) 10^x),
                labels = trans_format("log10", scales::math_format(10^.x))) +
  scale_y_log10(limits = c(0.1, 1500),
                breaks = trans_breaks("log10", function(x) 10^x),
                labels = trans_format("log10", scales::math_format(10^.x))) +
  theme(legend.position = 'top', legend.key.height= unit(0.3, 'cm'),
        plot.margin = margin(1,0.5,0,0, "cm"))

g4 <- ggplot(data = df) +
  theme_minimal() +
  # Raw data
  geom_bin2d(aes(x=distance, y=diff), alpha=0.2) +
  scale_fill_gradient(name = 'No. of trips', low = "steelblue", high = 'coral') +

  # Distances by groups
  geom_linerange(data = df_stats, aes(x=distance, ymin=lower_diff, ymax=upper_diff), color='steelblue', size=0.5) +
  geom_point(data = df_stats, aes(x=distance, y=center_diff), color='steelblue', shape = 21, fill = "white", size = 2) +

  geom_hline(yintercept=median(df$diff), size=0.3, color='black') +
  annotate("text", x = 100, y = 5, label = sprintf('Median ratio = %.1f', median(df$diff))) +
  labs(x = "Trip distance (Euclidean, km)", y = 'Distance ratio') +
  scale_x_log10(limits = c(0.1, 1500),
                breaks = trans_breaks("log10", function(x) 10^x),
                labels = trans_format("log10", scales::math_format(10^.x))) +
  scale_y_log10(limits = c(1, 100), breaks = c(1, 10, 100), labels = c(1, 10, 100)) +
  theme(legend.position = 'top', legend.key.height= unit(0.3, 'cm'),
        plot.margin = margin(1,0.5,0,0, "cm"))

h <- 3.3 * 2
w <- 3 * 2
G <- ggarrange(g1, g2, g3, g4,
               ncol = 2, nrow = 2, labels = c('(a)', '(b)', '(c)', '(d)'))
ggsave(filename = "figures/distance_error_data.png", plot=G,
       width = w, height = h, unit = "in", dpi = 300)