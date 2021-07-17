# Title     : Temporal profiles of geotagged tweets vs. destinations in travel survey
# Objective : Sweden case
# Created by: Yuan Liao
# Created on: 2021-05-15

library(dplyr)
library(ggplot2)
library(ggsci)
library(ggpubr)

df <- read.csv('dbs/sweden/temporal_tw_vs_survey.csv')
colors <- pal_igv('default')(2)
df$weekday <- factor(df$weekday, labels=c('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'))

df2plot <- df[df$source=='Travel survey',]
g1 <- ggplot(df2plot) +
  geom_line(aes(x = hour, y = count, group=source), color=colors[1], size=0.5) +
  labs(y='Share of visited locations (%)', x='Hour', title = 'Travel survey') +
  geom_vline(xintercept = 12, color = "orange", size=0.3) +
  geom_vline(xintercept = c(0, 23), color = "gray60") +
  scale_x_continuous(labels = c('0', '8', '12', '16'),
                     breaks = c(0, 8, 12, 16)) +
  facet_grid(.~ weekday) +
  theme_minimal()

df2plot <- df[df$source=='Geotagged tweets',]
df2plot_contrast <- df[df$source=='Travel survey',]
g2 <- ggplot() +
  geom_ribbon(data=df2plot_contrast,
            aes(x = hour, ymax = count, group=source), ymin=0, fill=colors[1], alpha=0.1, color=NA) +
  geom_line(data=df2plot, aes(x = hour, y = count, group=source), color=colors[2], size=0.5) +
  labs(y='', x='Hour', title = 'Geotagged tweets') +
  geom_vline(xintercept = 12, color = "orange", size=0.3) +
  geom_vline(xintercept = c(0, 23), color = "gray60") +
  scale_x_continuous(labels = c('0', '8', '12', '16'),
                     breaks = c(0, 8, 12, 16)) +
  facet_grid(.~ weekday) +
  theme_minimal()

G <- ggarrange(g1, g2, nrow = 1, ncol = 2)
ggsave(filename = "figures/dis_pres_behaviour_bias.png", plot=G,
     width = 15, height = 4, unit = "in", dpi = 300)