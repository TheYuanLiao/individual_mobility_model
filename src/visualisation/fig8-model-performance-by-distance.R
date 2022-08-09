# Title     : Model performance by distance
# Objective : Trip frequency rate of model, benchmark, vs. ground-truth data by distance
# Created by: Yuan Liao
# Created on: 2022-07-24

library(dplyr)
library(ggplot2)
library(rjson)
library(glue)
library(ggpubr)
library(latex2exp)
library(scales)
options(scipen=10000)

title_region <- c('Sweden', 'The Netherlands', 'São Paulo, Brazil')
names(title_region) <- c('sweden', 'netherlands', 'saopaulo')

rs_path <- 'results/para-search-r1/'

dist_upper <- function(x) {
  x_s <- unlist(strsplit(x, ","))
  return( as.numeric(substr(x_s[2], 2, nchar(x_s[2]) - 1)))
}
cols <- c('#ffa801', '#3c40c6', 'steelblue', '#05c46b')

plot.freq.distance <- function(region, type) {
  # load model results
  df <- read.csv(paste0(rs_path, region, '_', type, '_distances.csv'))
  df <- df %>%
    filter(model_sum > 0 & groundtruth_sum > 0) %>%
    mutate(model = model_sum - groundtruth_sum,
           benchmark = benchmark_sum - groundtruth_sum)
  df$d <- sapply(df$distance, dist_upper)

  g1 <- ggplot(data = df, aes(x=d)) +
#    geom_segment(aes(xend=d, y=model_sum, yend=groundtruth_sum), color="grey", size=0.2) +
    geom_point(aes(y=groundtruth_sum, color='Ground truth'), size=0.7, alpha=0.7 ) +
    geom_line(aes(y=groundtruth_sum, color='Ground truth'), alpha=0.5, size=0.5) +
    geom_point(aes(y=model_sum, color=paste('Model-', type)), size=0.7, alpha=0.7 ) +
    geom_point(aes(y=benchmark_sum, color='Benchmark'), size=0.3, alpha=0.5 ) +
    scale_color_manual(name='Source',
                       breaks=c('Model- calibration', 'Model- validation', 'Ground truth', 'Benchmark'),
                       values=c('Model- calibration'=cols[2],
                                'Model- validation'=cols[3],
                                'Ground truth'=cols[1],
                                'Benchmark'=cols[4])) +
    scale_y_log10(limits = c(min(df[, 'groundtruth_sum']), 1),
                  breaks = trans_breaks("log10", function(x) 10^x),
                  labels = trans_format("log10", scales::math_format(10^.x))) +
    scale_x_log10(limits = c(min(df[, 'd']), max(df[, 'd'])),
                  breaks = trans_breaks("log10", function(x) 10^x),
                  labels = trans_format("log10", scales::math_format(10^.x))) +
    theme_minimal() +
    theme(
      plot.title = element_text(size=9),
      legend.position = c(0.3, 0.2),
      panel.border = element_blank(),
    ) +
    xlab("Distance (km)") +
    ylab("Trip frequency rate") +
    theme(plot.margin = margin(1,0.5,0,0, "cm"))

  g2 <- ggplot(data = df, aes(x=d)) +
    geom_point(aes(y=model, color=paste('Model-', type)), size=0.7, alpha=0.7 ) +
    geom_point(aes(y=benchmark, color='Benchmark'), size=0.3, alpha=0.5 ) +
    scale_color_manual(name='Source',
                       breaks=c('Model- calibration', 'Model- validation', 'Benchmark'),
                       values=c('Model- calibration'=cols[2],
                                'Model- validation'=cols[3],
                                'Benchmark'=cols[4])) +
    scale_x_log10(limits = c(min(df[, 'd']), max(df[, 'd'])),
                  breaks = trans_breaks("log10", function(x) 10^x),
                  labels = trans_format("log10", scales::math_format(10^.x))) +
    theme_minimal() +
    theme(
      plot.title = element_text(size=9),
      legend.position = c(0.3, 0.2),
      panel.border = element_blank(),
    ) +
    xlab("Distance (km)") +
    ylab("Trip frequency rate differnce") +
    theme(plot.margin = margin(1,0.5,0,0, "cm"))
  return(g1)
}

type <- 'calibration'
region <- 'sweden'
g_se.c <- plot.freq.distance(region, type)

region <- 'netherlands'
g_nt.c <- plot.freq.distance(region, type)

region <- 'saopaulo'
g_sp.c <- plot.freq.distance(region, type)

type <- 'validation'
region <- 'sweden'
g_se.v <- plot.freq.distance(region, type)

region <- 'netherlands'
g_nt.v <- plot.freq.distance(region, type)

region <- 'saopaulo'
g_sp.v <- plot.freq.distance(region, type)

# save plot
h <- 3.3 * 3
w <- 3 * 2
G <- ggarrange(g_se.c, g_se.v, g_nt.c, g_nt.v, g_sp.c, g_sp.v,
               ncol = 2, nrow = 3, labels = c('(a)', '(b)', '(c)', '(d)', '(e)', '(f)'))
ggsave(filename = glue("figures/model_perf_distance.png"), plot=G,
       width = w, height = h, unit = "in", dpi = 300)

