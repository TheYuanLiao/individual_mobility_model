# Title     : Distance difference between Haversine distance and network distance
# Objective : Based on simulation
# Created by: Yuan Liao
# Created on: 2021-07-20

library(ggplot2)
library(dplyr)
library(viridis)
library(ggpubr)
library(scales)
library(ggsci)
options(scipen=10000)

# Load distances
df.total <- read.csv('../dbs/distance_error_simulation.csv')

# Load region names and areas
region_list <- c('../dbs/guadalajara', 'kualalumpur', 'surabaya', 'barcelona', 'madrid',
                 'nairobi', 'stpertersburg', 'johannesburg', 'capetown', 'cebu'
                 )
region_names <- c('Guadalajara, Mexico', 'Kuala Lumpur, Malaysia', 'Surabaya, Indonesia',
                  'Barcelona, Spain', 'Madrid, Spain',  'Nairobi, Kenya',
                  'Saint Petersburg, Russia', 'Johannesburg, South Africa',
                  'Cape Town, South Africa', 'Cebu, Philippines')
# Area ranges between 272.3 -- 4878.7

df.total$region_n <- factor(df.total$region, levels=region_list, labels=region_names)
df.region.distance <- df.total %>%
  group_by(region_n)  %>%
  summarise(d_min=min(distance),
            d_max=max(distance))

df.total$gp <- cut(df.total$distance, breaks = unlist(lapply(seq(-1, 3, 4/30), function(x){10^(x)})))

df_stats <- df.total %>%
  group_by(region_n, gp)  %>%
  summarise(distance = median(distance),
            center_diff = median(diff),
            lower_diff = quantile(diff, 0.25),
            upper_diff = quantile(diff, 0.75))


g <- ggplot(data = df_stats) +
  theme_minimal() +
  # Distances by groups
  geom_ribbon(aes(x=distance, ymin=lower_diff, ymax=upper_diff, fill=region_n), alpha=0.1, size=0.5) +
  geom_line(aes(x=distance, y=center_diff, color=region_n), size = 0.5) +
  scale_color_igv(name = 'Urban area')  +
  scale_fill_igv(name = 'Urban area') +
  labs(x = "Trip distance (Euclidean, km)", y = 'Distance ratio') +
  scale_x_log10(limits = c(0.1, 300),
                breaks = trans_breaks("log10", function(x) 10^x),
                labels = trans_format("log10", scales::math_format(10^.x))) +
  scale_y_log10(limits = c(1, 10), breaks = c(1, 2, 5, 10), labels = c(1, 2, 5, 10)) +
  theme(legend.position = c(0.8, 0.6), legend.key.height= unit(0.3, 'cm'))

h <- 3
w <- 6
ggsave(filename = "figures/distance_error_simulation.png", plot=g,
       width = w, height = h, unit = "in", dpi = 300)