# Title     : Visualise the distribution of visits per day and selection of D
# Objective : Bar plot of visits per individual per visits from Swedish National travel survey (travel-survey-se)
# and KL vs selection of D_day
# Created by: Yuan Liao
# Created on: 2021-11-04

library(dplyr)
library(ggplot2)
library(glue)
library(ggpubr)
options(scipen=10000)

# Get the results
df <- read.csv('results/parameter_D_KL_relationship.csv')
df <- df %>%
  mutate(region=recode(region, "sweden"="Sweden",
                       "netherlands"="The Netherlands",
                       "saopaulo"="São Paulo, Brazil"))
names(df)[names(df) == 'region'] <- 'Region'

g1 <- ggplot(df, aes(x=days, y=kl, shape=Region)) + theme_minimal() +
  geom_line(color='gray65', size = 0.3) +
  geom_point(color='gray45', size = 1.5) +
  theme(legend.position = c(0.7, 0.7)) +
  labs(y = 'KL divergence', x="D (day)")

x <- c(2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 27)
y <- c(3110, 11266, 4395, 4878, 2102, 1401, 691, 403, 206, 131, 71, 31, 28, 20, 11, 7, 2, 3, 2, 1, 1)

g2 <- ggplot() +
  geom_bar(aes(x=as.factor(x), y=y), stat="identity") +
  scale_x_discrete(breaks = x) +
  labs(x='No. of visits per day', y='Frequency') +
  theme_minimal()

G <- ggarrange(g2, g1, ncol = 2, nrow = 1, labels = c('(a)', '(b)'), widths = c(1.6, 1))
ggsave(filename = "figures/M_day_D.png", plot=G,
     width = 6.5, height = 3.3, unit = "in", dpi = 300)