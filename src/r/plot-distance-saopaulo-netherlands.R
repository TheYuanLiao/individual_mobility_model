# Title     : Distance distribution visualization
# Objective : Model-calibrated & -validated vs ground truth - The netherlands and Sao Paulo
# Created by: Yuan Liao
# Created on: 2020-09-09

library(dplyr)
library(ggplot2)
library(rjson)
library(glue)
library(ggpubr)
library(latex2exp)

rs_path <- 'results/'

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

# netherlands
region1 <- 'netherlands'
scale <- c('national')
result <- fromJSON(file = glue("results/{region1}-v.json"))
# model
df <- read.csv(paste0(rs_path, region1, '-', result$national$runid, '/distance-metrics.csv'))
df <- df %>%
  mutate(model = cumsum(model_sum),
         gt = cumsum(groundtruth_sum)) %>%
  filter(model > 0 & gt > 0)

df$d <- sapply(df$distance, dist_upper)

# model-validated
dfv <- read.csv(paste0(rs_path, region1, '-', result$national$runid, '-v', '/distance-metrics.csv'))
dfv <- dfv %>%
  mutate(model = cumsum(model_sum),
         gt = cumsum(groundtruth_sum)) %>%
  filter(model > 0 & gt > 0)

dfv$d <- sapply(dfv$distance, dist_upper)

# parameter
p <- result$national$p
gamma <- result$national$gamma
beta <- result$national$beta

# line names and optimal parameters
m.cali1 <- paste0("Model calibrated: KL divergence = ", signif(result$national$kl, digits=3))
m.vali1 <- paste0("Model validated: KL divergence = ", signif(result$national$`kl-v`, digits=3))
para <- TeX(sprintf("$\\rho = %.2f,{ }\\beta = %.3f,{ }\\gamma = %.2f$", p, beta, gamma))

# plot
g1 <- plt(title = 'The Netherlands', para = para,
          df=df, dfv=dfv, model_cali=m.cali1, model_vali=m.vali1)

# Sao Paulo
region2 <- 'saopaulo'
scale <- c('national')
result <- fromJSON(file = glue("results/{region2}-v.json"))
# model
df <- read.csv(paste0(rs_path, region2, '-', result$national$runid, '/distance-metrics.csv'))
df <- df %>%
  mutate(model = cumsum(model_sum),
         gt = cumsum(groundtruth_sum)) %>%
  filter(model > 0 & gt > 0)

df$d <- sapply(df$distance, dist_upper)

# model-validated
dfv <- read.csv(paste0(rs_path, region2, '-', result$national$runid, '-v', '/distance-metrics.csv'))
dfv <- dfv %>%
  mutate(model = cumsum(model_sum),
         gt = cumsum(groundtruth_sum)) %>%
  filter(model > 0 & gt > 0)

dfv$d <- sapply(dfv$distance, dist_upper)

# parameter
p <- result$national$p
gamma <- result$national$gamma
beta <- result$national$beta

# line names and optimal parameters
m.cali2 <- paste0("Model calibrated: KL divergence = ", signif(result$national$kl, digits=3))
m.vali2 <- paste0("Model validated: KL divergence = ", signif(result$national$`kl-v`, digits=3))
para <- TeX(sprintf("$\\rho = %.2f,{ }\\beta = %.3f,{ }\\gamma = %.2f$", p, beta, gamma))

# plot
g2 <- plt(title = 'São Paulo, Brazil', para = para,
          df=df, dfv=dfv, model_cali=m.cali2, model_vali=m.vali2)

# save plot
w <- 8
h <- 4
G <- ggarrange(g1, g2,
               ncol = 2, nrow = 1)
ggsave(filename = glue("figures/{region}-distance.png"), plot=G,
       width = w, height = h, unit = "in", dpi = 300)