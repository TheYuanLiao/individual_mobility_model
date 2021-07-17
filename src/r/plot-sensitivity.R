# Title     : Visualise the sensitivity of model parameters
# Objective : The performance gain when use the other two regions' parameters and the average
# Created by: Yuan Liao
# Created on: 2021-07-17

library(ggplot2)
library(dplyr)
library(viridis)
library(ggpubr)

df <- read.csv('results/para-search-r1/sensitivity_summary.csv')
df$region <- factor(df$region, levels=c('sweden', 'netherlands', 'saopaulo'),
                    labels=c('Sweden', 'the Netherlands', 'São Paulo'))
df$region2cross <- factor(df$region2cross, levels=c('sweden', 'netherlands', 'saopaulo', 'average'),
                          labels=c('Sweden', 'the Netherlands', 'São Paulo', 'Average'))

# Plot the matrix
min_g_c <- min(df[(df$type == 'calibration') & (df$gain > 0), 'gain'])
min_g_v <- min(df[(df$type == 'validation') & (df$gain > 0), 'gain'])
min_g <- min(c(min_g_c, min_g_v))


g1 <- ggplot(df[df$type == 'calibration', ], aes(x=region2cross, y=region)) +
  geom_tile(aes(fill = gain), colour = "white") +
  scale_fill_viridis(name = 'Performance gain (%)', limits = c(min_g, 100)) +
  geom_text(aes(label = round(gain, 1)), color='white') +
  theme_minimal() +
  theme(legend.position = "bottom", legend.key.width = unit(0.5, "cm"),
        panel.grid = element_blank()) +
  theme(axis.text.x = element_text(angle = 30, vjust=0.7),
        plot.margin = margin(1,0,0,0, "cm")) +
  labs(x='Model parameters', y='Applying region') +
  coord_equal() +
  scale_y_discrete(limits=rev)


g2 <- ggplot(df[df$type == 'validation', ], aes(x=region2cross, y=region)) +
  geom_tile(aes(fill = gain), colour = "white") +
  scale_fill_viridis(name = 'Performance gain (%)', limits = c(min_g, 100)) +
  geom_text(aes(label = round(gain, 1)), color='white') +
  theme_minimal() +
  theme(legend.position = "bottom", legend.key.width = unit(0.5, "cm"),
        panel.grid = element_blank()) +
  theme(axis.text.x = element_text(angle = 30, vjust=0.7),
        plot.margin = margin(1,0,0,0, "cm")) +
  coord_equal() +
  scale_y_discrete(limits=rev) +
  labs(x='Model parameters', y='Applying region')

# save plots
h <- 3
w <- 3 * 2
G <- ggarrange(g1, g2,
               ncol = 2, nrow = 1, labels = c('(a)', '(b)'), common.legend = T, legend="bottom")
ggsave(filename = "figures/sensitivity.png", plot=G,
       width = w, height = h, unit = "in", dpi = 300)