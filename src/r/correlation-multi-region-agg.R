# Title     : Explore the regional heterogeneity
# Objective : ks, r2, city, median, gdp_capita, para1, para2, area
# Created by: Yuan Liao
# Created on: 2021-02-19

library(ggplot2)
library(glue)
library(ggpubr)
library(PerformanceAnalytics)
library(corrplot)

df <- read.csv('results/multi-region_rid_6.csv')
df <- df[df$region != 'manila',]
df$geonum_user <- df$num_geotweets / df$num_users
df2exp <- df[, c('ks', 'r2', 'city', 'median', 'gdp_capita', 'para1', 'para2', 'area', 'pop',
                 'num_users', 'num_geotweets', 'geonum_user')]
chart.Correlation(df2exp, histogram=TRUE, pch=19, method = "spearman")