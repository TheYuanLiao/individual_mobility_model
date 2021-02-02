# Title     : Distance distribution visualization
# Objective : Model-calibrated & -validated vs ground truth - Sweden
# Created by: Yuan Liao
# Created on: 2020-09-08

library(dplyr)
library(ggplot2)
library(rjson)
library(glue)
library(ggpubr)
library(latex2exp)

title_region <- c('Sweden', 'Sweden - West', 'Sweden - East', 'The Netherlands', 'São Paulo, Brazil')
names(title_region) <- c('sweden', 'sweden-west', 'sweden-east', 'netherlands', 'saopaulo')

lst <- readLines('results/summary.txt') %>% lapply(fromJSON)
df <- bind_rows(lst)

rs_path <- 'results/grid-search/'

dist_upper <- function(x) {
  x_s <- unlist(strsplit(x, ","))
  return( as.numeric(substr(x_s[2], 2, nchar(x_s[2]) - 1)))
}


plt <- function(title, para, df, dfv, model_cali, model_vali) {
  g <- ggplot() + theme_minimal() +
    geom_line(data = df, aes(x=d, y = gt, color="Ground truth"), size=0.8) +
    geom_line(data = df, aes(x=d, y = model, color=model_cali), size=0.8) +
    geom_line(data = dfv, aes(x=d, y = model, color=model_vali), size=0.8) +
    geom_point(data = df, aes(x=d, y=0.01), shape=108) +
    scale_x_log10() +
    scale_color_manual(name = "",
                       values = c('#ffa801','#3c40c6','#05c46b')) +
    labs(title = title, subtitle = para,
         x = "Distance (log, km)", y = "Cumulative share of trips") +
    theme(legend.position = c(0.55, 0.3))
  return(g)
}

reg_plt <- function(region, title_region, result, rs_path, df) {
  result <- df[df$region == region, c('p', 'gamma', 'beta', 'kl', 'kl-v')]

  # model
  df <- read.csv(paste0(rs_path, region, '_calibration_distances.csv'))
  df <- df %>%
    mutate(model = cumsum(model_sum),
           gt = cumsum(groundtruth_sum)) %>%
    filter(model > 0 & gt > 0)

  df$d <- sapply(df$distance, dist_upper)

  # model-validated
  dfv <- read.csv(paste0(rs_path, region, '_validation_distances.csv'))
  dfv <- dfv %>%
    mutate(model = cumsum(model_sum),
           gt = cumsum(groundtruth_sum)) %>%
    filter(model > 0 & gt > 0)

  dfv$d <- sapply(dfv$distance, dist_upper)

  # parameter
  p <- result$p
  gamma <- result$gamma
  beta <- result$beta

  # line names and optimal parameters
  m.cali1 <- paste0("Model calibrated: KL divergence = ", signif(result$kl, digits=3))
  m.vali1 <- paste0("Model validated: KL divergence = ", signif(result$`kl-v`, digits=3))
  para <- TeX(sprintf("$\\rho = %.2f,{ }\\beta = %.2f,{ }\\gamma = %.2f$", p, beta, gamma))

  # plot
  g1 <- plt(title = title_region[region], para = para,
            df=df, dfv=dfv, model_cali=m.cali1, model_vali=m.vali1)
  return(g1)
}

# region <- 'sweden-west'
# g1 <- reg_plt(region, title_region, result, rs_path, df)
# region <- 'sweden-east'
# g2 <- reg_plt(region, title_region, result, rs_path, df)

region <- 'sweden'
g1 <- reg_plt(region, title_region, result, rs_path, df)
region <- 'netherlands'
g2 <- reg_plt(region, title_region, result, rs_path, df)
region <- 'saopaulo'
g3 <- reg_plt(region, title_region, result, rs_path, df)

# save plot
w <- 9
h <- 3
G <- ggarrange(g1, g2, g3,
               ncol = 3, nrow = 1)
ggsave(filename = glue("figures/distance.png"), plot=G,
       width = w, height = h, unit = "in", dpi = 300)