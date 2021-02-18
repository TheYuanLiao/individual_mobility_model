# Title     : Characterising trip distance for global regions
# Objective : Fit the trip distance data to Weibull distribution
# Created by: Yuan Liao
# Created on: 2021-02-10

library(fitdistrplus)
library(ggplot2)
library(poweRlaw)
library(glue)
library(robustbase)

# 1. Load PDF
runid <- 6
df <- read.csv(glue('results/multi-region_trips_rid_6_pdf.csv'))
region_list <- c('../dbs/netherlands', 'sweden', 'austria', 'australia',
                 'saudiarabia', 'egypt', 'moscow', 'stpertersburg',
                 'saopaulo', 'rio', 'barcelona', 'madrid',
                 'cebu', 'manila', 'jakarta', 'surabaya',
                 'capetown', 'johannesburg', 'nairobi', 'lagos',
                 'guadalajara', 'kualalumpur'
                 )
region <- '../dbs/saopaulo'
df.m <- df[df$region == region, ]

## 1.1 Truncated powerlaw 1
tpl.m <- nlrob(p_d ~ (d + d0) ^ (-beta) * exp(-d / K), data = df.m,
               start = list(d0=1, beta=1.5, K=1.5))
summary(tpl.m)

## 1.2 Powerlaw
nlsfit <- nls(y ~ alpha * x ^ (-beta), d.m, start=list(alpha=1, beta=0.15))
summary(nlsfit)

## 1.3 Expotional
nlsfit <- nls(y ~ alpha * exp(-x / K), d.m, start=list(alpha=1.5, K=0.15))
summary(nlsfit)

d.m$predy <- predict(nlsfit)

ggplot(d.m, aes(x = x, y = y)) +
#  geom_line(aes(x = x, y = predy), size = 0.3, color='red') +
  geom_point(size=0.3) +
  theme_minimal() +
  scale_x_continuous(trans='log10') +
  scale_y_continuous(trans='log10')

## 1.4 Try two-phase fit
cut <- 15
d.m.1 <- d.m[d.m$x <= cut,]
nlsfit.1 <- nls(y ~ alpha * exp(-x / K), d.m.1, start=list(alpha=2, K=0.15))
summary(nlsfit.1)
d.m.1$predy <- predict(nlsfit.1)

d.m.2 <- d.m[d.m$x >= cut,]
nlsfit.2 <- nls(y ~ alpha * x ^ (-beta), d.m.2, start=list(alpha=2, beta=0.15))
summary(nlsfit.2)
d.m.2$predy <- predict(nlsfit.2)

ggplot(d.m, aes(x = x, y = y)) +
#  geom_line(data=d.m.1, aes(x = x, y = predy), size = 1, color='red') +
#  geom_line(data=d.m.2, aes(x = x, y = predy), size = 1, color='orange') +
  geom_point(size=0.3) +
  theme_minimal() +
  scale_x_continuous(trans='log10') +
  scale_y_continuous(trans='log10')


# ECDF
p  <- ggplot(df, aes(x=distance)) + stat_ecdf(step=TRUE)
pg <- ggplot_build(p)$data[[1]]
ggplot(pg, aes(x = x, y = 1-y )) +
  geom_point(size=0.3) +
  theme_minimal() +
  scale_x_continuous(trans='log10') +
  scale_y_continuous(trans='log10')


ggplot(data=df) +
  theme_minimal() +
  labs(x='Trip distance (km), d', y='P(d)') +
  #stat_ecdf(geom = "step", aes(x=distance)) +
  # geom_histogram(bins = sqrt(nrow(df)), aes(x=distance, y = ..density..)) +
  geom_density(aes(x=distance)) +
  scale_x_continuous(trans='log10') +
  scale_y_continuous(trans='log10')
  # stat_function(fun = dlnorm, args = list(meanlog = fl$estimate['meanlog'],
  #                                         sdlog = fl$estimate['sdlog']),
  #               colour = "red") +
  # stat_function(fun = dgamma, args = list(shape = fg$estimate['shape'],
  #                                        rate = fg$estimate['rate']),
  #               colour = "blue") +
  # stat_function(fun = dweibull, args = list(shape = fw$estimate['shape'],
  #                                           scale = fw$estimate['scale']),
  #               colour = "green")

descdist(df$distance, discrete=FALSE)

fw <- fitdist(df$distance, "weibull")
fg <- fitdist(df$distance, "gamma")
fl <- fitdist(df$distance, "lnorm")

