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

df2plot <- df[df$source=='Travel survey',]
g1 <- ggplot(df2plot) +
  geom_line(aes(x = seq, y = count, group=source), color=colors[1], size=0.5) +
  geom_smooth(aes(x = seq, y = count), alpha=0.2, color=NA, fill=colors[1]) +
  labs(y='Reported locations (%)', x='', title = 'Travel survey') +
  scale_x_continuous(labels = c('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'),
                     breaks = df2plot[seq(12,nrow(df2plot),23), 'seq'],) +
  theme_minimal()

df2plot <- df[df$source=='Geotagged tweets',]
g2 <- ggplot(df2plot) +
  geom_line(aes(x = seq, y = count, group=source), color=colors[2], size=0.5) +
  geom_smooth(aes(x = seq, y = count), alpha=0.2, color=NA, fill=colors[2]) +
  labs(y='', x='', title = 'Geotagged tweets') +
  scale_x_continuous(labels = c('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'),
                     breaks = df2plot[seq(12,nrow(df2plot),23), 'seq'],) +
  theme_minimal()

G <- ggarrange(g1, g2, nrow = 1, ncol = 2)
ggsave(filename = "figures/dis_pres_behaviour_bias.png", plot=G,
     width = 9, height = 4, unit = "in", dpi = 300)