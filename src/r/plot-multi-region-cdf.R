# Title     : Visualise the trip distance distributions across regions
# Objective : CDF
# Created by: Yuan Liao
# Created on: 2021-02-19

library(ggplot2)
library(glue)
library(ggpubr)
library(scales)

region_list <- c('netherlands', 'sweden', 'austria','australia',
                 'saudiarabia',  'egypt', 'moscow', 'stpertersburg',
                 'saopaulo',  'rio', 'barcelona', 'madrid',
                 'cebu', 'manila', 'jakarta', 'surabaya',
                 'capetown', 'johannesburg', 'nairobi', 'lagos',
                 'guadalajara', 'kualalumpur'
                 )

region_names <- c('The Netherlands', 'Sweden', 'Austria','Australia',
                 'Saudi Arabia',  'Egypt', 'Moscow, Russia', 'St Pertersburg, Russia',
                 'Sao Paulo, Brazil',  'Rio, Brazil', 'Barcelona, Spain', 'Madrid, Spain',
                 'Cebu, Philippines', 'Manila, Philippines', 'Jakarta, Indonesia', 'Surabaya, Indonesia',
                 'Cape Town, South Africa', 'Johannesburg, South Africa', 'Nairobi, Kenya', 'Lagos, Nigeria',
                  'Guadalajara, Mexico', 'Kuala Lumpur, Malaysia'
                 )
names(region_names) <- region_list
runid <- 6
df <- read.csv(glue('dbs/visits_{runid}_trips_dom.csv'))

rgplot <- function(region){
  df2plot <- df[df$region==region,]
  d0 <- median(df2plot$distance)
  percentile <- ecdf(df2plot$distance)
  g <- ggplot() +
    geom_line(aes(x=seq(1, 1000, 0.1), y=percentile(seq(1, 1000, 0.1))), size=0.7) +
    theme_minimal() +
    labs(x='d (km)', y='CDF', title = region_names[region]) +
    geom_vline(xintercept = d0, linetype ='dotted', color="steelblue", size=0.8) +
    annotate(geom = 'text', x = d0 + 25, y = 0.25,
             label = sprintf('Median trip distance=%.2f', d0)) +
    scale_x_log10(limits = c(1, 10^3),
                  breaks = trans_breaks("log10", function(x) 10^x),
                  labels = trans_format("log10", scales::math_format(10^.x))) +
    scale_y_continuous(limits = c(percentile(1), 1)) +
    annotation_logticks(sides = "b")
  return(g)
}
glist <- lapply(region_list, rgplot)
G <- ggarrange(plotlist = glist, nrow = 6, ncol = 4)

ggsave(filename = "figures/trip_distance_CDF.png", plot=G,
     width = 16, height = 20, unit = "in", dpi = 300)