# Title     : Visualize the multi-region results
# Objective : PKT
# Created by: Yuan Liao
# Created on: 2020-10-03

library(dplyr)
library(ggplot2)
library(ggrepel)
library(ggpubr)

df <- read.csv('results/multi-region_stats.csv', encoding = "UTF-8")
df1 <- df[, c('region_name', 'country', 'pkt_inland_yr_capita')]
names(df1) <- c('region_name', 'country', 'pkt')
df1$pkt_yr_capita <- df$pkt_yr_capita
df1$pkt_type <- 'Inland'

df2 <- df[, c('region_name', 'country', 'pkt_yr_capita')]
names(df2) <- c('region_name', 'country', 'pkt')
df2$pkt_yr_capita <- df$pkt_yr_capita
df2$pkt_type <- 'Total'

df <- rbind(df1, df2)

theme_set(
  theme_minimal() +
    theme(legend.position = "top",
          aspect.ratio=1)
  )

gg_color_hue <- function(n) {
  hues <- seq(15, 375, length = n + 1) # 15, 375
  hcl(h = hues, l = 65, c = 100)[1:n] # 65
}

cols <- gg_color_hue(16)
names(cols) <- unique(df$country)

g <- ggplot(data=df, aes(x=reorder(region_name, pkt_yr_capita), y=pkt)) +
  labs(x='Region',
       y='PKT (million km/capita/yr)') +
  geom_line(aes(group = region_name), color='gray', size=0.8) +
  geom_point(aes(color = country), size=2) +
  scale_color_manual(values = cols, name = 'Country') +
  coord_flip()

ggsave(filename = "figures/multi-region-pkt.png", plot=g,
       width = 14, height = 5, unit = "in", dpi = 300)