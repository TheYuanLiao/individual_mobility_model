# Title     : ODM visualization
# Objective : Ground truth vs Model output and Benchmark
# Created by: Yuan Liao
# Created on: 2021-07-16

library(ggplot2)
library(dplyr)
library(viridis)
library(ggpubr)


## Sweden g1 - g2
region <- 'sweden' # netherlands, saopaulo
df <- read.csv(paste0('dbs/', region, '/odms.csv')) # calibration_odm.csv, validation_odm.csv
df <- df[(df$gt != 0) & (df$model_c != 0) & (df$benchmark_c != 0), ]
print(paste('Min gt', min(df[df$gt != 0, 'gt'])))
print(paste('Max gt', max(df$gt)))
df$gt_cat <- cut(df$gt, breaks = unlist(lapply(seq(8, 2, -(8-2)/30), function(x){10^(-x)})))


df_stats <- df %>%
  group_by(gt_cat)  %>%
  summarise(gt = median(gt),
            center = median(model_c),
            lower = quantile(model_c, 0.25),
            upper = quantile(model_c, 0.75),
            center_b = median(benchmark_c),
            lower_b = quantile(benchmark_c, 0.25),
            upper_b = quantile(benchmark_c, 0.75))

# Plot No. of trips by ozone x dzone
g1 <- ggplot() +
  theme_minimal() +
  # Model vs GT
  geom_bin2d(data = df, aes(x=gt, y=model_c), alpha=0.2) +
  scale_fill_gradient(name = 'No. of OD pairs', low = "#3c40c6", high = 'coral') +
  # Model
  geom_linerange(data = df_stats, aes(x=gt, ymin=lower, ymax=upper), color='#3c40c6', size=0.5) +
  geom_point(data = df_stats, aes(x=gt, y=center), color='#3c40c6', shape = 21, fill = "white", size = 2) +

  geom_abline(intercept = 0, slope = 1, size=0.3, color='gray45') +
  scale_x_continuous(trans='log10', limits = c(min(df[df$gt != 0, 'gt']), 0.01)) +
  scale_y_continuous(trans='log10', limits = c(min(df[df$gt != 0, 'gt']), 0.01)) +
  labs(x = "Ground truth", y = 'Model') +
  theme(legend.position = 'top',
        plot.margin = margin(1,0.5,0,0, "cm"))

g2 <- ggplot() +
  theme_minimal() +
  # Benchmark vs GT
  geom_bin2d(data = df, aes(x=gt, y=benchmark_c), alpha=0.2) +
  scale_fill_gradient(name = 'No. of OD pairs', low = "#05c46b", high = 'coral') +

  # Benchmark
  geom_linerange(data = df_stats[df_stats$center_b > 0, ], aes(x=gt + 1e-10, ymin=lower_b, ymax=upper_b), color='#05c46b', size=0.5) +
  geom_point(data = df_stats, aes(x=gt + 1e-10, y=center_b), color='#05c46b', shape = 21, fill = "white", size = 2) +

  geom_abline(intercept = 0, slope = 1, size=0.3, color='gray45') +
  scale_x_continuous(trans='log10', limits = c(min(df[df$gt != 0, 'gt']), 0.01)) +
  scale_y_continuous(trans='log10', limits = c(min(df[df$gt != 0, 'gt']), 0.01)) +
  labs(x = "Ground truth", y = 'Benchmark') +
  theme(legend.position = 'top',
        plot.margin = margin(1,0.5,0,0, "cm"))


## Netherlands g3 - g4
region <- 'netherlands' # netherlands, saopaulo
df <- read.csv(paste0('dbs/', region, '/odms.csv')) # calibration_odm.csv, validation_odm.csv
df <- df[(df$gt != 0) & (df$model_c != 0) & (df$benchmark_c != 0), ]
print(paste('Min gt', min(df[df$gt != 0, 'gt'])))
print(paste('Max gt', max(df$gt)))
df$gt_cat <- cut(df$gt, breaks = unlist(lapply(seq(7, 3, -(7-3)/30), function(x){10^(-x)})))


df_stats <- df %>%
  group_by(gt_cat)  %>%
  summarise(gt = median(gt),
            center = median(model_c),
            lower = quantile(model_c, 0.25),
            upper = quantile(model_c, 0.75),
            center_b = median(benchmark_c),
            lower_b = quantile(benchmark_c, 0.25),
            upper_b = quantile(benchmark_c, 0.75))

# Plot No. of trips by ozone x dzone
g3 <- ggplot() +
  theme_minimal() +
  # Model vs GT
  geom_bin2d(data = df, aes(x=gt, y=model_c), alpha=0.2) +
  scale_fill_gradient(name = 'No. of OD pairs', low = "#3c40c6", high = 'coral') +
  # Model
  geom_linerange(data = df_stats, aes(x=gt, ymin=lower, ymax=upper), color='#3c40c6', size=0.5) +
  geom_point(data = df_stats, aes(x=gt, y=center), color='#3c40c6', shape = 21, fill = "white", size = 2) +

  geom_abline(intercept = 0, slope = 1, size=0.3, color='gray45') +
  scale_x_continuous(trans='log10', limits = c(min(df[df$gt != 0, 'gt']), 0.01)) +
  scale_y_continuous(trans='log10', limits = c(min(df[df$gt != 0, 'gt']), 0.01)) +
  labs(x = "Ground truth", y = 'Model') +
  theme(legend.position = 'top',
        plot.margin = margin(1,0.5,0,0, "cm"))

g4 <- ggplot() +
  theme_minimal() +
  # Benchmark vs GT
  geom_bin2d(data = df, aes(x=gt, y=benchmark_c), alpha=0.2) +
  scale_fill_gradient(name = 'No. of OD pairs', low = "#05c46b", high = 'coral') +

  # Benchmark
  geom_linerange(data = df_stats[df_stats$center_b > 0, ], aes(x=gt + 1e-10, ymin=lower_b, ymax=upper_b), color='#05c46b', size=0.5) +
  geom_point(data = df_stats, aes(x=gt + 1e-10, y=center_b), color='#05c46b', shape = 21, fill = "white", size = 2) +

  geom_abline(intercept = 0, slope = 1, size=0.3, color='gray45') +
  scale_x_continuous(trans='log10', limits = c(min(df[df$gt != 0, 'gt']), 0.01)) +
  scale_y_continuous(trans='log10', limits = c(min(df[df$gt != 0, 'gt']), 0.01)) +
  labs(x = "Ground truth", y = 'Benchmark') +
  theme(legend.position = 'top',
        plot.margin = margin(1,0.5,0,0, "cm"))

## Sao Paulo g5 - g6
region <- 'saopaulo' # netherlands, saopaulo
df <- read.csv(paste0('dbs/', region, '/odms.csv')) # calibration_odm.csv, validation_odm.csv
df <- df[(df$gt != 0) & (df$model_c != 0) & (df$benchmark_c != 0), ]
print(paste('Min gt', min(df[df$gt != 0, 'gt'])))
print(paste('Max gt', max(df$gt)))
df$gt_cat <- cut(df$gt, breaks = unlist(lapply(seq(9, 2, -(9-2)/30), function(x){10^(-x)})))


df_stats <- df %>%
  group_by(gt_cat)  %>%
  summarise(gt = median(gt),
            center = median(model_c),
            lower = quantile(model_c, 0.25),
            upper = quantile(model_c, 0.75),
            center_b = median(benchmark_c),
            lower_b = quantile(benchmark_c, 0.25),
            upper_b = quantile(benchmark_c, 0.75))

# Plot No. of trips by ozone x dzone
g5 <- ggplot() +
  theme_minimal() +
  # Model vs GT
  geom_bin2d(data = df, aes(x=gt, y=model_c), alpha=0.2) +
  scale_fill_gradient(name = 'No. of OD pairs', low = "#3c40c6", high = 'coral') +
  # Model
  geom_linerange(data = df_stats, aes(x=gt, ymin=lower, ymax=upper), color='#3c40c6', size=0.5) +
  geom_point(data = df_stats, aes(x=gt, y=center), color='#3c40c6', shape = 21, fill = "white", size = 2) +

  geom_abline(intercept = 0, slope = 1, size=0.3, color='gray45') +
  scale_x_continuous(trans='log10', limits = c(min(df[df$gt != 0, 'gt']), 0.01)) +
  scale_y_continuous(trans='log10', limits = c(min(df[df$gt != 0, 'gt']), 0.01)) +
  labs(x = "Ground truth", y = 'Model') +
  theme(legend.position = 'top',
        plot.margin = margin(1,0.5,0,0, "cm"))


g6 <- ggplot() +
  theme_minimal() +
  # Model vs GT
  geom_bin2d(data = df, aes(x=gt, y=benchmark_c), alpha=0.2) +
  scale_fill_gradient(name = 'No. of OD pairs', low = "#05c46b", high = "coral") +

  # Benchmark
  geom_linerange(data = df_stats[df_stats$center_b > 0, ], aes(x=gt + 1e-10, ymin=lower_b, ymax=upper_b), color='#05c46b', size=0.5) +
  geom_point(data = df_stats, aes(x=gt + 1e-10, y=center_b), color='#05c46b', shape = 21, fill = "white", size = 2) +

  geom_abline(intercept = 0, slope = 1, size=0.3, color='gray45') +
  scale_x_continuous(trans='log10', limits = c(min(df[df$gt != 0, 'gt']), 0.01)) +
  scale_y_continuous(trans='log10', limits = c(min(df[df$gt != 0, 'gt']), 0.01)) +
  labs(x = "Ground truth", y = 'Benchmark') +
  theme(legend.position = 'top',
        plot.margin = margin(1,0.5,0,0, "cm"))

h <- 3.3 * 3
w <- 3 * 2
G <- ggarrange(g1, g2, g3, g4, g5, g6,
               ncol = 2, nrow = 3, labels = c('(a)', '(b)', '(c)', '(d)', '(e)', '(f)'))
ggsave(filename = "figures/od_pairs_validation.png", plot=G,
       width = w, height = h, unit = "in", dpi = 300)