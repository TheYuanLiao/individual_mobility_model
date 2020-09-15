# Title     : Grid search results
# Objective : Take the grid search record and visualise it
# Created by: Yuan Liao
# Created on: 2020-09-08

library(dplyr)
library(ggplot2)
library(glue)
library(data.table)
library(RColorBrewer)
library(latex2exp)
library(ggpubr)
library(jsonlite)
library(viridisLite)
library(latticeExtra)

title_region <- c('Sweden - West', 'Sweden - National', 'Sweden - East', 'The Netherlands', 'São Paulo, Brazil')
names(title_region) <- c('sweden-west', 'sweden-national', 'sweden-east', 'netherlands', 'saopaulo')
region <- 'sweden-west'
title <- title_region[region]

# Load grid search records
lst <- readLines(glue('results/gridsearch-n_{region}.txt')) %>% lapply(fromJSON)
df <- bind_rows(lst)

# Plot the matrix of gamma x beta ~ p
myPalette <- colorRampPalette(rev(brewer.pal(11, "Spectral")))
sc <- scale_colour_gradientn(colours = myPalette(100), limits=c(0, 1), name = 'KL divergence')

# showing data points on the same color scale
g1 <- levelplot(kl ~ beta * p, df, xlab = TeX("$\\beta$"), ylab = TeX("$\\rho$"),
                pretty = TRUE,
                par.settings = list(axis.line = list(col = "gray"),
                                    strip.background = list(col = 'transparent'),
                                    strip.border = list(col = 'transparent')),
                panel = panel.levelplot.points, cex = 1.2,
                col.regions = viridis(100)
) + layer_(panel.2dsmoother(..., n = 200))

# showing data points on the same color scale
g2 <- levelplot(kl ~ beta * gamma, df, xlab = TeX("$\\beta$"), ylab = TeX("$\\gamma$"), main = title,
                pretty = TRUE,
                par.settings = list(axis.line = list(col = "gray"),
                                    strip.background = list(col = 'transparent'),
                                    strip.border = list(col = 'transparent')),
                panel = panel.levelplot.points, cex = 1.2,
                col.regions = viridis(100)
) + layer_(panel.2dsmoother(..., n = 200))

# showing data points on the same color scale
g3 <- levelplot(kl ~ p * gamma, df, xlab = TeX("$\\rho$"), ylab = TeX("$\\gamma$"),
                pretty = TRUE,
                par.settings = list(axis.line = list(col = "gray"),
                                    strip.background = list(col = 'transparent'),
                                    strip.border = list(col = 'transparent')),
                panel = panel.levelplot.points, cex = 1.2,
                col.regions = viridis(100)
) + layer_(panel.2dsmoother(..., n = 200))


w <- 3 * 3
h <- 3
G <- ggarrange(g1, g2, g3,
               ncol = 3, nrow = 1)
ggsave(filename = glue("figures/{region}-grid-search.png"), plot=G,
       width = w*1.5, height = h*1.5, unit = "in", dpi = 300)