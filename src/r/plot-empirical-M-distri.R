# Title     : Visualise the distribution of visits per day
# Objective : Bar plot of visits per individual per visits from Swedish National travel survey (travel-survey-se)
# Created by: Yuan Liao
# Created on: 2021-07-13

library(ggplot2)
library(ggpubr)

x <- c(2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 27)
y <- c(3110, 11266, 4395, 4878, 2102, 1401, 691, 403, 206, 131, 71, 31, 28, 20, 11, 7, 2, 3, 2, 1, 1)

g <- ggplot() +
  geom_bar(aes(x=as.factor(x), y=y), stat="identity") +
  scale_x_discrete(breaks = x) +
  labs(x='No. of visits per day', y='Frequency') +
  theme_minimal()

ggsave(filename = "figures/M_day_empirical.png", plot=g,
     width = 5, height = 3, unit = "in", dpi = 300)