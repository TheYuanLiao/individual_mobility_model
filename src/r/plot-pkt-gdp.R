# Title     : Visualize the multi-region results
# Objective : PKT vs GDP/capita
# Created by: Yuan Liao
# Created on: 2020-09-28

library(dplyr)
library(ggplot2)
library(ggrepel)
library(ggpubr)

theme_set(
  theme_minimal() +
    theme(legend.position = "top",
          aspect.ratio=1)
  )

gg_color_hue <- function(n) {
  hues <- seq(15, 375, length = n + 1)
  hcl(h = hues, l = 65, c = 100)[1:n]
}

cols <- gg_color_hue(14)

df <- read.csv('results/multi-region_stats.csv')

g1 <- ggplot(df, aes(x = gdp_capita, y = pkt_yr_capita)) +
  labs(x='GDP (kUSD/capita/yr), nominal',
       y='Total PKT (million km/capita/yr), inland + outland') +
  geom_label_repel(aes(label = region_name,  color = country),
                   alpha = 0.75, size = 2.5, label.size = NA) +
  geom_point(aes(color = country), size=3) +
  scale_color_manual(values = cols, name = 'Country')

df2 <- filter(df, !is.na(pkt_yr_capita_gt))

g2 <- ggplot(df2, aes(x = pkt_yr_capita, y = pkt_yr_capita_gt)) +
  labs(y='Inland PKT by iTEM (million km/capita/yr)',
       x='Total PKT (million km/capita/yr), inland + outland') +
  geom_label_repel(aes(label = region_name,  color = country),
                   alpha = 0.75, size = 2.5, label.size = NA) +
  geom_point(aes(color = country), size=3) +
  scale_color_manual(values = cols, name = 'Country')

w <- 3 * 2
h <- 3
G <- ggarrange(g1, g2,
               ncol = 2, nrow = 1)
ggsave(filename = "figures/multi-region-pkt.png", plot=G,
       width = w*2, height = h*2, unit = "in", dpi = 300)