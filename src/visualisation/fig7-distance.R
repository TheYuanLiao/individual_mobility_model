# Title     : Distance distribution visualization
# Objective : Model-calibrated & -validated vs ground truth and benchmark
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
df <- df[4:6,]

rs_path <- 'results/para-search-r1/'

dist_upper <- function(x) {
  x_s <- unlist(strsplit(x, ","))
  return( as.numeric(substr(x_s[2], 2, nchar(x_s[2]) - 1)))
}


plt <- function(title, para, df, dfv, model_c, benchmark_c, model_v, benchmark_v, x_lab, y_lab) {
  GT <- "Ground truth \n"
  ctype <- c('#ffa801', '#3c40c6', '#05c46b', '#3c40c6', '#05c46b')
  names(ctype) <- c(GT, model_c, benchmark_c, model_v, benchmark_v)
  ltype <- c('solid', 'solid', 'solid', 'dashed', 'dashed')
  names(ltype) <- c(GT, model_c, benchmark_c, model_v, benchmark_v)
  g <- ggplot() + theme_minimal() +
    geom_line(data = df, aes(x=d, y = gt, color=GT, linetype=GT), size=0.6) +
    geom_line(data = df, aes(x=d, y = model, color=model_c, linetype=model_c), size=0.3) +
    geom_line(data = df, aes(x=d, y = benchmark, color=benchmark_c, linetype=benchmark_c), size=0.3) +
    geom_line(data = dfv, aes(x=d, y = model, color=model_v, linetype=model_v), size=0.3) +
    geom_line(data = dfv, aes(x=d, y = benchmark, color=benchmark_v, linetype=benchmark_v), size=0.3) +
    geom_point(data = df, aes(x=d, y=0.41), shape=108, size=0.5) +
    scale_x_log10() +
    scale_color_manual(name = "", values = ctype,
                       breaks=c(GT, model_c, benchmark_c, model_v, benchmark_v)) +
    scale_linetype_manual(name = "", values = ltype,
                          breaks=c(GT, model_c, benchmark_c, model_v, benchmark_v)) +
    labs(title = title, subtitle = para,
         x = x_lab, y = y_lab) +
    scale_y_continuous(limits = c(0.4, NA)) +
    theme(legend.position = c(0.55, 0.4),
          plot.margin = margin(0,0,0,0, "cm"))
  return(g)
}

reg_plt <- function(region, title_region, result, rs_path, df, x_lab, y_lab) {
  result <- df[df$region == region, c('p', 'gamma', 'beta', 'kl', 'kl-baseline', 'kl-v', "kl-v-baseline")]

  # model-calibration
  df <- read.csv(paste0(rs_path, region, '_calibration_distances.csv'))
  df <- df %>%
    mutate(model = cumsum(model_sum),
           gt = cumsum(groundtruth_sum),
           benchmark = cumsum(benchmark_sum)) %>%
    filter(model > 0 & gt > 0)

  df$d <- sapply(df$distance, dist_upper)

  # model-validation
  dfv <- read.csv(paste0(rs_path, region, '_validation_distances.csv'))
  dfv <- dfv %>%
    mutate(model = cumsum(model_sum),
           gt = cumsum(groundtruth_sum),
           benchmark = cumsum(benchmark_sum)) %>%
    filter(model > 0 & gt > 0)

  dfv$d <- sapply(dfv$distance, dist_upper)

  # parameter
  p <- result$p
  gamma <- result$gamma
  beta <- result$beta

  # line names and optimal parameters
  m.cali1 <- paste0("Model (C) = ", signif(result$kl, digits=3), "\n")
  m.vali1 <- paste0("Model (V) = ", signif(result$`kl-v`, digits=3), "\n")
  b.cali1 <- paste0("Benchmark (C) = ", signif(result$`kl-baseline`, digits=3), "\n")
  b.vali1 <- paste0("Benchmark (V) = ", signif(result$`kl-v-baseline`, digits=3))
  para <- TeX(sprintf("$\\rho = %.2f,{ }\\beta = %.2f,{ }\\gamma = %.2f$", p, beta, gamma))

  # plot calibration
  g <- plt(title = '', para = '', #title = title_region[region], para = para
            df=df, dfv=dfv, model_c=m.cali1, benchmark_c=b.cali1,
            model_v=m.vali1, benchmark_v=b.vali1,
           x_lab = x_lab, y_lab = y_lab)

  return(g)
}

region <- 'sweden'
g_se <- reg_plt(region, title_region, result, rs_path, df, '', 'Cumulative share of trips')

region <- 'netherlands'
g_nt <- reg_plt(region, title_region, result, rs_path, df, "Distance (log, km)", '')

region <- 'saopaulo'
g_sp <- reg_plt(region, title_region, result, rs_path, df, '', '')


# save plot
h <- 4
w <- 4 * 3
G <- ggarrange(g_se, g_nt, g_sp,
               ncol = 3, nrow = 1, labels = c('(a)', '(b)', '(c)'))
ggsave(filename = glue("figures/distance.png"), plot=G,
       width = w, height = h, unit = "in", dpi = 300)