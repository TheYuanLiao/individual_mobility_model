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
  geom_violin(aes(x = country, y = share_active*100, fill=country), color=NA, show.legend = FALSE) +
  geom_boxplot(aes(x = country, y = share_active*100), width=0.1, lwd=0.4, outlier.size = 0.3) +
  scale_fill_igv() +
  geom_hline(yintercept=median(df$share_active*100), linetype="dashed", color = "gray45") +
  labs(y='Share of active day that has at least one location (%)', x='Country',
       title=sprintf('Median share of active day \n =%.1f%%', median(df$share_active)*100)) +
  coord_flip() +
  theme_minimal()

g2 <- ggplot(df) +
  geom_violin(aes(x = country, y = geo_freq, fill=country), color=NA, show.legend = FALSE) +
  geom_boxplot(aes(x = country, y = geo_freq), width=0.1, lwd=0.4, outlier.size = 0.3) +
  scale_fill_igv() +
  geom_hline(yintercept=median(df$geo_freq), linetype="dashed", color = "gray45") +
  labs(x='',
       y='# of geotagged tweets per active day',
       title=sprintf('Median # of geotagged tweets / active day \n =%.1f', median(df$geo_freq))) +
  scale_y_continuous(trans='log10', breaks = c(1, 10, 100)) +
  scale_x_discrete(labels = NULL) +
  coord_flip() +
  theme_minimal()

G <- ggarrange(g1, g2, nrow = 1, ncol = 2, widths = c(1, 0.8))
ggsave(filename = "figures/dis_pres_sparsity.png", plot=G,
     width = 9, height = 4, unit = "in", dpi = 300)