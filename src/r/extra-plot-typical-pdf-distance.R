# Title     : Illustrate the typical trip distance distributions
# Objective : Weibull, Gamma, lognormal, truncated power law, power law, and exponential
# Created by: Yuan Liao
# Created on: 2021-02-23

library(ggplot2)
library(ggpubr)
library(scales)
library(ggsci)

d <- seq(0, 10000, 0.1)

# Weibull
k <- 1.5
ld <- 3
y.weibull <- k/ld*(k/ld)^(k-1)*exp(-(d/ld)^k)

# Gamma
beta <- 3
alpha <- 6
y.gamma <- beta^alpha*d^(alpha-1)*exp(-beta*d)/gamma(alpha)

# lognormal
miu <- 1.5
sigma <- 1.7
y.lognormal <- 1/(d*sigma*(2*pi)^0.5)*exp(-(log(d) - miu)^2/(2*sigma^2))

# truncated power law
beta <- 1.75
K <- 300
d0 <- 1.5
y.tpower <- (d + d0) ^ (-beta) * exp(-d / K)

# power law
beta <- 1.75
y.power <- (d + d0) ^ (-beta)

# exponential
ld <- 0.1
y.exp <- ld*exp(-ld*d)

dfc <- function(y, n){
  df <- data.frame(d)
  names(df) <- 'd'
  df$pdf <- y
  df$Distribution <- n
  return(df)
}

df <- rbind(dfc(y.weibull, 'Weibull'), dfc(y.gamma, 'Gamma'), dfc(y.lognormal, 'Lognormal'),
            dfc(y.tpower, 'Truncated power law'), dfc(y.power, 'Power law'), dfc(y.exp, 'Exponential'))
df <- df[(df$d > 0) & (df$pdf > 0), ]

g <- ggplot(df, aes(x = d, y = pdf, group=Distribution)) +
  geom_line(aes(color=Distribution)) +
  scale_color_igv()  +
  theme_minimal() +
  labs(x='d (km)', y='p(d)') +
  scale_x_log10(limits = c(0.1, 10^4),
                breaks = trans_breaks("log10", function(x) 10^x),
                labels = trans_format("log10", scales::math_format(10^.x))) +
  scale_y_log10(limits = c(10^(-10), 1),
                breaks = trans_breaks("log10", function(x) 10^x),
                labels = trans_format("log10", scales::math_format(10^.x))) +
  annotation_logticks() +
  theme(legend.position = c(0.2, 0.35))

ggsave(filename = "figures/trip_distance_pdf_theoretical.png", plot=g,
     width = 7, height = 4, unit = "in", dpi = 300)