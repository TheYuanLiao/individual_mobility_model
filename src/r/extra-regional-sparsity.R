# Title     : Sparsity issue across multiple regions
# Objective : Visualise the sparsity of regional statistics
# Created by: Yuan Liao
# Created on: 2021-05-14

library(dplyr)
library(ggplot2)
library(ggsci)
library(ggpubr)

df <- read.csv('dbs/regional_stats.csv')
df <- df %>%
  filter(df$share_active <= 1)

g1 <- ggplot(df) +
  # geom_violin(aes(x = country, y = share_active*100, fill=country), color=NA, show.legend = FALSE) +
  # geom_boxplot(aes(x = country, y = share_active*100), width=0.1, lwd=0.4, outlier.size = 0.3) +
  # scale_fill_igv() +
  geom_histogram(aes(x=share_active*100)) +
  geom_vline(xintercept=median(df$share_active*100), linetype="dashed", color = "orange") +
  labs(x='Share of active day that has at least one location (%)', y='# of Twitter users',
       title=sprintf('Median share of active day \n =%.1f%%', median(df$share_active)*100)) +
  theme_minimal()

g2 <- ggplot(df) +
  # geom_violin(aes(x = country, y = geo_freq, fill=country), color=NA, show.legend = FALSE) +
  # geom_boxplot(aes(x = country, y = geo_freq), width=0.1, lwd=0.4, outlier.size = 0.3) +
  # scale_fill_igv() +
  geom_histogram(aes(x=geo_freq)) +
  geom_vline(xintercept=median(df$geo_freq), linetype="dashed", color = "orange") +
  labs(y='# of Twitter users',
       x='# of geotagged tweets per active day',
       title=sprintf('Median # of geotagged tweets / active day \n =%.1f', median(df$geo_freq))) +
  scale_x_continuous(trans='log10', breaks = c(1, 10, 100)) +
  theme_minimal()

# G <- ggarrange(g1, g2, nrow = 1, ncol = 2, widths = c(1, 0.8))
ggsave(filename = "figures/dis_pres_sparsity_1.png", plot=g1,
     width = 5, height = 4, unit = "in", dpi = 300)

ggsave(filename = "figures/dis_pres_sparsity_2.png", plot=g2,
     width = 5, height = 4, unit = "in", dpi = 300)