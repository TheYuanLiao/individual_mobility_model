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

rs_path <- 'results/para-search/'

dist_upper <- function(x) {
  x_s <- unlist(strsplit(x, ","))
  return( as.numeric(substr(x_s[2], 2, nchar(x_s[2]) - 1)))
}


plt <- function(title, para, df, dfv, model_cali, model_vali, x_lab, y_lab) {
  g <- ggplot() + theme_minimal() +
    geom_line(data = df, aes(x=d, y = gt, color="Ground truth \n"), size=0.3) +
    geom_line(data = df, aes(x=d, y = model, color=model_cali), size=0.3) +
    geom_line(data = dfv, aes(x=d, y = model, color=model_vali), size=0.3) +
    geom_point(data = df, aes(x=d, y=0.01), shape=108, size=0.5) +
    scale_x_log10() +
    scale_color_manual(name = "",
                       values = c('#ffa801','#3c40c6','#05c46b')) +
    labs(title = title, subtitle = para,
         x = x_lab, y = y_lab) +
    theme(legend.position = c(0.55, 0.4),
          plot.margin = margin(0,0,0,0, "cm"))
  return(g)
}

reg_plt <- function(region, title_region, result, rs_path, df, x_lab, y_lab) {
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
  m.cali1 <- paste0("Model calibration \n KL divergence = ", signif(result$kl, digits=3), "\n")
  m.vali1 <- paste0("Model validation \n KL divergence = ", signif(result$`kl-v`, digits=3))
  para <- TeX(sprintf("$\\rho = %.2f,{ }\\beta = %.2f,{ }\\gamma = %.2f$", p, beta, gamma))

  # plot
  g1 <- plt(title = '', para = '', #title = title_region[region], para = para
            df=df, dfv=dfv, model_cali=m.cali1, model_vali=m.vali1,
            x_lab = x_lab, y_lab = y_lab)
  return(g1)
}

# region <- 'sweden-west'
# g1 <- reg_plt(region, title_region, result, rs_path, df)
# region <- 'sweden-east'
# g2 <- reg_plt(region, title_region, result, rs_path, df)

region <- 'sweden'
g1 <- reg_plt(region, title_region, result, rs_path, df, '', 'Cumulative share of trips')
region <- 'netherlands'
g2 <- reg_plt(region, title_region, result, rs_path, df, "Distance (log, km)", '')
region <- 'saopaulo'
g3 <- reg_plt(region, title_region, result, rs_path, df, '', '')

# save plot
w <- 2.5 * 3
h <- 2.5
G <- ggarrange(g1, g2, g3,
               ncol = 3, nrow = 1, labels = c('(a)', '(b)', '(c)'))
ggsave(filename = glue("figures/distance.png"), plot=G,
       width = w, height = h, unit = "in", dpi = 300)