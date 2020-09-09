# Title     : Grid search results
# Objective : Take the grid search record and visualise it - Netherlands
# Created by: Yuan Liao
# Created on: 2020-09-08

library(dplyr)
library(ggplot2)
library(glue)
library(data.table)
library(RColorBrewer)
library(latex2exp)
library(ggpubr)

region <- 'netherlands'
# Load grid search records
df1 <- data.table(read.csv(glue('results/{region}-grid-search-1.csv')))
df2 <- data.table(read.csv(glue('results/{region}-grid-search-2.csv')))
df <- rbindlist(list(df1, df2))
df <- unique(df, by = "runid")
df <- df[df$gamma < 1,]
# Plot the matrix of gamma x beta ~ p
myPalette <- colorRampPalette(rev(brewer.pal(11, "Spectral")))
sc <- scale_colour_gradientn(colours = myPalette(100), limits=c(0, 0.03), name = 'KL divergence')

# national
g1 <- ggplot(df, aes(x=beta, y=gamma, color=national)) +
  geom_point(size=3) +
    facet_grid(.~p, labeller = label_parsed) +
  sc +
  labs(title = 'The Netherlands', subtitle = TeX("$\\rho$"),
       x = TeX("$\\beta$"), y = TeX("$\\gamma$")) +
  theme_minimal()

w <- 5
h <- 1.5 * 1
ggsave(filename = glue("figures/{region}-grid-search.png"), plot=g1,
       width = w*1.5, height = h*1.5, unit = "in", dpi = 300)