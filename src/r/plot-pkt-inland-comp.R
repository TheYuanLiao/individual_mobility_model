# Title     : Visualize the multi-region results
# Objective : PKT vs PKT from the other data source (iTEM)
# Created by: Yuan Liao
# Created on: 2020-10-03

library(dplyr)
library(ggplot2)
library(ggrepel)
library(ggpubr)

df <- read.csv('results/multi-region_stats_rid_3.csv', encoding = "UTF-8")

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
df2 <- filter(df, !is.na(pkt_inland_yr_capita_gt))
cols2 <- cols[df2$country]

g <- ggplot(df2, aes(x = pkt_inland_yr_capita, y = pkt_inland_yr_capita_gt)) +
  labs(y='Inland PKT by iTEM (million km/capita/yr)',
       x='Inland PKT (million km/capita/yr)') +
  geom_label_repel(aes(label = region_name,  color = country),
                   alpha = 0.75, size = 2.5, label.size = NA) +
  geom_point(aes(color = country), size=3) +
  scale_color_manual(values = cols2, name = 'Country')

g