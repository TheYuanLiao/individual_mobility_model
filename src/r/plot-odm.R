# Title     : ODM visualization
# Objective : Ground truth vs Model output
# Created by: Yuan Liao
# Created on: 2021-02-01

library(ggplot2)
library(dplyr)
library(viridis)
library(ggpubr)

region <- 'saopaulo' # netherlands, saopaulo
df <- read.csv(paste0('dbs/', region, '/odms.csv')) # calibration_odm.csv, validation_odm.csv
df <- df[(df$gt != 0)|(df$model_c != 0)|(df$model_v != 0), ]

# Plot No. of trips by ozone x dzone
g1 <- ggplot(df, aes(x=gt)) +
  theme_minimal() +
  geom_point(aes(y=model_c, color='Model calibrated'), size=0.2, alpha=0.3) +
  geom_point(aes(y=model_v, color='Model validated'), size=0.2, alpha=0.3) +
  geom_abline(intercept = 0, slope = 1, size=0.3, color='gray45') +
  scale_x_continuous(trans='log10', limits = c(NA, 0.01)) +
  scale_y_continuous(trans='log10', limits = c(NA, 0.01)) +
  scale_color_manual(name = "",
                     values = c('#3c40c6','#05c46b')) +
  labs(x = " ", y = '') +
  theme(legend.position = c(0.3, 0.9),
        plot.margin = margin(1,0.5,0,0, "cm"))

region <- 'netherlands' # netherlands, saopaulo
df <- read.csv(paste0('dbs/', region, '/odms.csv')) # calibration_odm.csv, validation_odm.csv
df <- df[(df$gt != 0)|(df$model_c != 0)|(df$model_v != 0), ]

# Plot No. of trips by ozone x dzone
g2 <- ggplot(df, aes(x=gt)) +
  theme_minimal() +
  geom_point(aes(y=model_c, color='Model calibrated'), size=0.2, alpha=0.3) +
  geom_point(aes(y=model_v, color='Model validated'), size=0.2, alpha=0.3) +
  geom_abline(intercept = 0, slope = 1, size=0.3, color='gray45') +
  scale_x_continuous(trans='log10', limits = c(NA, 0.01)) +
  scale_y_continuous(trans='log10', limits = c(NA, 0.01)) +
  scale_color_manual(name = "",
                     values = c('#3c40c6','#05c46b')) +
  labs(x = "Trip frequency rate (ground truth)", y = '') +
  theme(legend.position = c(0.3, 0.9),
        plot.margin = margin(1,0,0,0, "cm"))

region <- 'sweden' # netherlands, saopaulo
df <- read.csv(paste0('dbs/', region, '/odms.csv')) # calibration_odm.csv, validation_odm.csv
df <- df[(df$gt != 0)|(df$model_c != 0)|(df$model_v != 0), ]

# Plot No. of trips by ozone x dzone
g3 <- ggplot(df, aes(x=gt)) +
  theme_minimal() +
  geom_point(aes(y=model_c, color='Model calibrated'), size=0.2, alpha=0.3) +
  geom_point(aes(y=model_v, color='Model validated'), size=0.2, alpha=0.3) +
  geom_abline(intercept = 0, slope = 1, size=0.3, color='gray45') +
  scale_x_continuous(trans='log10') +
  scale_y_continuous(trans='log10') +
  scale_color_manual(name = "",
                     values = c('#3c40c6','#05c46b')) +
  labs(x='', y = "Trip frequency rate (model)") +
  theme(legend.position = c(0.3, 0.9),
        plot.margin = margin(1,0,0,0, "cm"))

h <- 3
w <- h * 3
G <- ggarrange(g3, g2, g1,
               ncol = 3, nrow = 1, labels = c('(a)', '(b)', '(c)'))
ggsave(filename = "figures/od_pairs.png", plot=G,
       width = w, height = h, unit = "in", dpi = 300)