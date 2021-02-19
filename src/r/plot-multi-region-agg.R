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
df$geonum_user <- df$num_geotweets / df$num_users
df2exp <- df[, c('ks', 'r2', 'city', 'median', 'gdp_capita', 'para1', 'para2', 'area', 'pop',
                 'num_users', 'num_geotweets', 'geonum_user')]
chart.Correlation(df2exp, histogram=TRUE, pch=19)

lm <- lm(ks ~ city, data=df)
summary(lm)

lm1 <- lm(r2 ~ city + gdp_capita + area, data=df)
summary(lm1)

lm2 <- lm(median ~ area, data=df)
summary(lm2)

lm3 <- lm(para1 ~ num_users + num_geotweets + geonum_user, data=df)
summary(lm3)
