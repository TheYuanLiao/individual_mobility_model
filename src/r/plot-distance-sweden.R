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

region <- 'sweden'
scale <- c('national', 'west', 'east')
result <- fromJSON(file = glue("results/{region}-v.json"))
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

# national
# model
df <- read.csv(paste0(rs_path, region, '-', result$national$runid, '/distance-metrics-national.csv'))
df <- df %>%
  mutate(model = cumsum(model_sum),
         gt = cumsum(sampers_sum)) %>%
  filter(model > 0 & gt > 0)

df$d <- sapply(df$distance, dist_upper)

# model-validated
dfv <- read.csv(paste0(rs_path, region, '-', result$national$runid, '-v', '/distance-metrics-national.csv'))
dfv <- dfv %>%
  mutate(model = cumsum(model_sum),
         gt = cumsum(sampers_sum)) %>%
  filter(model > 0 & gt > 0)

dfv$d <- sapply(dfv$distance, dist_upper)

# parameter
p <- result$national$p
gamma <- result$national$gamma
beta <- result$national$beta

# line names and optimal parameters
m.cali1 <- paste0("Model calibrated: KL divergence = ", signif(result$national$kl, digits=3))
m.vali1 <- paste0("Model validated: KL divergence = ", signif(result$national$`kl-v`$national, digits=3))
para <- TeX(sprintf("$\\rho = %.2f,{ }\\beta = %.3f,{ }\\gamma = %.2f$", p, beta, gamma))

# plot
g1 <- plt(title = 'Sweden - National (>= 100 km)', para = para,
          df=df, dfv=dfv, model_cali=m.cali1, model_vali=m.vali1)

# west
# model
df <- read.csv(paste0(rs_path, region, '-', result$west$runid, '/distance-metrics-west.csv'))
df <- df %>%
  mutate(model = cumsum(model_sum),
         gt = cumsum(sampers_sum)) %>%
  filter(model > 0 & gt > 0)

df$d <- sapply(df$distance, dist_upper)

# model-validated
dfv <- read.csv(paste0(rs_path, region, '-', result$west$runid, '-v', '/distance-metrics-west.csv'))
dfv <- dfv %>%
  mutate(model = cumsum(model_sum),
         gt = cumsum(sampers_sum)) %>%
  filter(model > 0 & gt > 0)

dfv$d <- sapply(dfv$distance, dist_upper)

# parameter
p <- result$west$p
gamma <- result$west$gamma
beta <- result$west$beta

# line names and optimal parameters
m.cali2 <- paste0("Model calibrated: KL divergence = ", signif(result$west$kl, digits=3))
m.vali2 <- paste0("Model validated: KL divergence = ", signif(result$west$`kl-v`$west, digits=3))
para <- TeX(sprintf("$\\rho = %.2f,{ }\\beta = %.3f,{ }\\gamma = %.2f$", p, beta, gamma))

# Plot
g2 <- plt(title = 'Sweden - West', para = para,
          df=df, dfv=dfv, model_cali=m.cali2, model_vali=m.vali2)

# east
# model
df <- read.csv(paste0(rs_path, region, '-', result$east$runid, '/distance-metrics-east.csv'))
df <- df %>%
  mutate(model = cumsum(model_sum),
         gt = cumsum(sampers_sum)) %>%
  filter(model > 0 & gt > 0)

df$d <- sapply(df$distance, dist_upper)

# model-validated
dfv <- read.csv(paste0(rs_path, region, '-', result$east$runid, '-v', '/distance-metrics-east.csv'))
dfv <- dfv %>%
  mutate(model = cumsum(model_sum),
         gt = cumsum(sampers_sum)) %>%
  filter(model > 0 & gt > 0)

dfv$d <- sapply(dfv$distance, dist_upper)

# parameter
p <- result$east$p
gamma <- result$east$gamma
beta <- result$east$beta

# line names and optimal parameters
m.cali3 <- paste0("Model calibrated: KL divergence = ", signif(result$east$kl, digits=3))
m.vali3 <- paste0("Model validated: KL divergence = ", signif(result$east$`kl-v`$east, digits=3))
para <- TeX(sprintf("$\\rho = %.2f,{ }\\beta = %.3f,{ }\\gamma = %.2f$", p, beta, gamma))

# Plot
g3 <- plt(title = 'Sweden - East', para = para,
          df=df, dfv=dfv, model_cali=m.cali3, model_vali=m.vali3)

# save plot
w <- 12
h <- 4
G <- ggarrange(g1, g2, g3,
               ncol = 3, nrow = 1)
ggsave(filename = glue("figures/{region}-distance.png"), plot=G,
       width = w, height = h, unit = "in", dpi = 300)