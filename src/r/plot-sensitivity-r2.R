# Title     : Visualise the sensitivity of model parameters
# Objective : The performance gain ratio when use the other two regions' parameters and the average
# Created by: Yuan Liao
# Created on: 2021-10-27

library(ggplot2)
library(dplyr)
library(viridis)
library(ggpubr)

df <- read.csv('results/para-search-r1/sensitivity_summary.csv')
df$region <- factor(df$region, levels=c('sweden', 'netherlands', 'saopaulo'),
                    labels=c('SE', 'NL', 'SP'))
df$region2cross <- factor(df$region2cross, levels=c('sweden', 'netherlands', 'saopaulo', 'average'),
                          labels=c('SE', 'NL', 'SP', 'AVG'))

# Plot the matrix
min_g <- min(df[df$gain_ratio > 0, 'gain_ratio'])
max_g <- max(df[, 'gain_ratio'])

g1 <- ggplot(df[df$type == 'calibration', ], aes(x=region2cross, y=region)) +
  geom_tile(colour = "gray", fill = "white") +
  geom_text(aes(label = signif(gain_ratio, 3), color = gain_ratio)) +
  scale_color_gradient(name='Relative performance (%)',
                       limits = c(min_g, max_g),
                       na.value = "darkred") +
  theme_minimal() +
  theme(legend.position = "bottom", legend.key.width = unit(0.5, "cm"),
        panel.grid = element_blank()) +
  theme(plot.margin = margin(1,0,0,0, "cm")) + # axis.text.x = element_text(angle = 30, vjust=0.7),
  labs(x='Model parameters', y='Applying region') +
  coord_equal() +
  scale_y_discrete(limits=rev)


g2 <- ggplot(df[df$type == 'validation', ], aes(x=region2cross, y=region)) +
  geom_tile(colour = "gray", fill = "white") +
  geom_text(aes(label = signif(gain_ratio, 3), color = gain_ratio)) +
  scale_color_gradient(name='Relative performance (%)',
                       limits = c(min_g, max_g),
                       na.value = "darkred") +
  theme_minimal() +
  theme(legend.position = "bottom", legend.key.width = unit(0.5, "cm"),
        panel.grid = element_blank()) +
  theme(plot.margin = margin(1,0,0,0, "cm")) + # axis.text.x = element_text(angle = 30, vjust=0.7),
  labs(x='Model parameters', y='Applying region') +
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