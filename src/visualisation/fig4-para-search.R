# Title     : The results of parameters search
# Objective : Take the search records and visualise them
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

title_region <- c('Sweden', 'the Netherlands', 'São Paulo, Brazil') # 'Sweden - West', 'Sweden - East',
names(title_region) <- c('sweden', 'netherlands', 'saopaulo') # 'sweden-west', 'sweden-east',

plt.region <- function(region){    # Load grid search records
    lst <- readLines(glue('results/para-search-r1/parasearch-n_{region}.txt')) %>% lapply(fromJSON)
    df <- bind_rows(lst)
    df <- df[(df$kl != 999) & (df$kl > 0),]
    para.op <- df[df$kl == min(df$kl), c('p', 'beta', 'gamma', 'kl')]
    # parameter
    p <- para.op$p
    gamma <- para.op$gamma
    beta <- para.op$beta
    kl <- para.op$kl

    # line names and optimal parameters
    title <- TeX(sprintf("KL divergence = %.3f, $\\rho = %.2f,{ }\\beta = %.2f,{ }\\gamma = %.2f$",
                            signif(kl, digits=3), p, beta, gamma))

    # showing data points on the same color scale
    g1 <- levelplot(kl ~ beta * p, df, xlab = TeX("$\\beta$"), ylab = TeX("$\\rho$"),
                    main = paste0(title_region[region], '    '),
                    pretty = TRUE,
                    par.settings = list(axis.line = list(col = "gray"),
                                        strip.background = list(col = 'transparent'),
                                        strip.border = list(col = 'transparent')),
                    panel = panel.levelplot.points, cex = 1.2,
                    col.regions = viridis(100)
    ) + layer_(panel.2dsmoother(..., n = 200))

    # showing data points on the same color scale
    g2 <- levelplot(kl ~ beta * gamma, df, xlab = TeX("$\\beta$"), ylab = TeX("$\\gamma$"),
                    main = title,
                    pretty = TRUE,
                    par.settings = list(axis.line = list(col = "gray"),
                                        strip.background = list(col = 'transparent'),
                                        strip.border = list(col = 'transparent')),
                    panel = panel.levelplot.points, cex = 1.2,
                    col.regions = viridis(100)
    ) + layer_(panel.2dsmoother(..., n = 200))

    # showing data points on the same color scale
    g3 <- levelplot(kl ~ p * gamma, df, xlab = TeX("$\\rho$"), ylab = TeX("$\\gamma$"),
                    main = "      ",
                    pretty = TRUE,
                    par.settings = list(axis.line = list(col = "gray"),
                                        strip.background = list(col = 'transparent'),
                                        strip.border = list(col = 'transparent')),
                    panel = panel.levelplot.points, cex = 1.2,
                    col.regions = viridis(100)
    ) + layer_(panel.2dsmoother(..., n = 200))

    G <- ggarrange(g1, g2, g3, ncol = 3, nrow = 1)
    return(G)
}

G1 <- plt.region('sweden')
G2 <- plt.region('netherlands')
G3 <- plt.region('saopaulo')
G <- ggarrange(G1, G2, G3, ncol = 1, nrow = 3, labels = c("(a)", "(b)", "(c)"))

w <- 2.5 * 3
h <- 2.5 * 3
ggsave(filename = "figures/para-search.png", plot=G,
           width = w*1.2, height = h*1.2, unit = "in", dpi = 300)