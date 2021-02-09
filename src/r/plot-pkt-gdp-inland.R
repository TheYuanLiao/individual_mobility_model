# Title     : Visualize the multi-region results
# Objective : PKT vs GDP/capita
# Created by: Yuan Liao
# Created on: 2020-10-18

library(dplyr)
library(ggplot2)
library(ggrepel)
library(ggpubr)

# Domestic trips
df_dom <- read.csv('results/multi-region_stats_rid_6.csv', encoding = "UTF-8")

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

g1 <- ggplot(df_dom, aes(x = gdp_capita, y = pkt_inland_yr_capita)) +
  labs(x='GDP (kUSD/capita/yr), nominal',
       y='Domestic PKT (1000 km/capita/yr)') +
  geom_label_repel(aes(label = region_name,  color = country),
                   alpha = 0.75, size = 2.5, label.size = NA) +
  geom_point(aes(color = country), size=3) +
  scale_color_manual(values = cols, name = 'Country') +
  geom_smooth(method = "lm", formula = y ~ log(x),
              se = TRUE, color='gray', size = 0.05, alpha = 0.05)

# # International trips
# df_ab <- read.csv('results/multi-region_stats_rid_2.csv', encoding = "UTF-8")
# df_ab <- df_ab %>%
#   mutate(outland = (pkt_yr_capita - pkt_inland_yr_capita) * 1000)
#
# g2 <- ggplot(df_ab, aes(x = gdp_capita, y = outland)) +
#   labs(x='GDP (kUSD/capita/yr), nominal',
#        y='International PKT (1000 km/capita/yr)') +
#   geom_label_repel(aes(label = region_name,  color = country),
#                    alpha = 0.75, size = 2.5, label.size = NA) +
#   geom_point(aes(color = country), size=3) +
#   scale_color_manual(values = cols, name = 'Country') +
#   geom_smooth(method=lm, aes(x = gdp_capita, y = outland), color = 'gray', size = 0.05, alpha = 0.05) +
#   # Add correlation coefficient
#   stat_cor(method = "pearson", color='gray')
#
# w <- 3 * 2
# h <- 3
# G <- ggarrange(g1, g2,
#                ncol = 2, nrow = 1,
#                common.legend = TRUE, legend="top")
ggsave(filename = "figures/multi-region-pkt-vs-gdp-inland.png", plot=g1,
       width = 9, height = 7, unit = "in", dpi = 300)