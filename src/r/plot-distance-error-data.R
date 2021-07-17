# Title     : Visualise the distance error between Euclidean distance and network distance
# Objective : Data-based results from Sweden and the Netherlands
# Created by: Yuan Liao
# Created on: 2021-07-17

library(dplyr)
library(ggplot2)
library(rjson)
library(glue)
library(ggpubr)
library(latex2exp)

title_region <- c('Sweden', 'The Netherlands')
names(title_region) <- c('sweden', 'netherlands')

lst <- readLines('results/summary.txt') %>% lapply(fromJSON)
df <- bind_rows(lst)
df <- df[4:6,]

rs_path <- 'results/para-search-r1/'

dist_upper <- function(x) {
  x_s <- unlist(strsplit(x, ","))
  return( as.numeric(substr(x_s[2], 2, nchar(x_s[2]) - 1)))
}


plt <- function(df, gt_true, x_lab, y_lab) {
  GT <- "Euclidean distance \n"
  ctype <- c('#ffa801', '#ffa801')
  names(ctype) <- c(GT, gt_true)
  ltype <- c('solid', 'dashed')
  names(ltype) <- c(GT, gt_true)
  g <- ggplot() + theme_minimal() +
    geom_line(data = df, aes(x=d, y = gt, color=GT, linetype=GT), size=0.6) +
    geom_line(data = df, aes(x=d, y = gt_t, color=gt_true, linetype=gt_true), size=0.3) +
    geom_point(data = df, aes(x=d, y=0.41), shape=108, size=0.5) +
    scale_x_log10() +
    scale_color_manual(name = "", values = ctype,
                       breaks=c(GT, gt_true)) +
    scale_linetype_manual(name = "", values = ltype,
                          breaks=c(GT, gt_true)) +
    labs(x = x_lab, y = y_lab) +
    scale_y_continuous(limits = c(0.4, NA)) +
    theme(legend.position = c(0.55, 0.4),
          plot.margin = margin(1,0,0,0, "cm"))
  return(g)
}

reg_plt <- function(region, title_region, result, rs_path, df, x_lab, y_lab) {
  result <- df[df$region == region, 'kl-deviation']

  # model-calibration
  df <- read.csv(paste0(rs_path, region, '_calibration_distances.csv'))
  df <- df %>%
    mutate(gt_t = cumsum(groundtruth_true_sum),
           gt = cumsum(groundtruth_sum)) %>%
    filter(gt_t > 0 & gt > 0)

  df$d <- sapply(df$distance, dist_upper)


  # line names and optimal parameters
  gt_true <- paste0("True distance = ", signif(result$`kl-deviation`, digits=3))

  # plot calibration
  g <- plt(df=df, gt_true = gt_true, x_lab = x_lab, y_lab = y_lab)

  return(g)
}

region <- 'sweden'
g_se <- reg_plt(region, title_region, result, rs_path, df, 'Distance (log, km)', 'Cumulative share of trips')

region <- 'netherlands'
g_nt <- reg_plt(region, title_region, result, rs_path, df, "Distance (log, km)", '')


# save plots
h <- 3
w <- 3 * 2
G <- ggarrange(g_se, g_nt,
               ncol = 2, nrow = 1, labels = c('(a)', '(b)'))
ggsave(filename = glue("figures/distance_error_data.png"), plot=G,
       width = w, height = h, unit = "in", dpi = 300)