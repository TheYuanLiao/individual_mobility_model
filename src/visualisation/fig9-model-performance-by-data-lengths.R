# Title     : Impact of data length
# Objective : Relationship between model performance and data lengths
# Created by: Yuan Liao
# Created on: 2022-07-28

library(dplyr)
library(ggplot2)
library(glue)
library(ggpubr)
library(latex2exp)
options(scipen=10000)

# Get the results
df.n <- read.csv('results/N_KL_relationship.csv', encoding = "latin1")
df.n <- df.n %>%
  mutate(region=recode(region, "sweden"="Sweden",
                       "netherlands"="The Netherlands",
                       "saopaulo"="São Paulo, Brazil")) %>%
  filter(nmax != 100000)
names(df.n)[names(df.n) == 'region'] <- 'Region'

df.nind <- read.csv('results/Nindi_KL_relationship.csv')
df.nind <- df.nind %>%
  mutate(region=recode(region, "sweden"="Sweden",
                       "netherlands"="The Netherlands",
                       "saopaulo"="São Paulo, Brazil"))
names(df.nind)[names(df.nind) == 'region'] <- 'Region'

g1 <- ggplot(df.n, aes(x=nmax, y=kl, shape=Region)) + theme_minimal() +
  geom_line(color='gray65', size = 0.3) +
  geom_point(color='gray45', size = 1.5) +
  theme(legend.position = c(0.7, 0.7)) +
  labs(y = 'KL divergence', x="Maximum no. of geolocations per individual")

g2 <- ggplot(df.nind, aes(x=n_total/1000, y=kl, shape=Region)) + theme_minimal() +
  geom_line(color='gray65', size = 0.3) +
  geom_point(color='gray45', size = 1.5) +
  theme(legend.position = c(0.7, 0.7)) +
  labs(y = 'KL divergence', x=TeX("No. of geolocations ($10^3$)"))

G <- ggarrange(g2, g1, ncol = 2, nrow = 1, labels = c('(a)', '(b)'), widths = c(1, 1), common.legend = T, legend = 'bottom')
ggsave(filename = "figures/data_length_impact.png", plot=G,
     width = 6.5, height = 3.3, unit = "in", dpi = 300)
