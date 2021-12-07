# Title     : Visualise the trip distance distributions across selected regions
# Objective : For the dissertation
# Created by: Yuan Liao
# Created on: 2021-05-09

library(ggplot2)
library(glue)
library(ggpubr)
library(scales)
library(latex2exp)
library(randomcoloR)
library(ggsci)

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
df_e <- read.csv('results/multi-region_trips_rid_7_pcdf.csv')
df_m <- read.csv('results/multi-region_trips_rid_7_pcdf_model.csv')
df_para <- read.csv('results/multi-region_trips_rid_7_paras.csv')
df_e$region_name <- unlist(lapply(df_e$region, function(x){return(region_names[x])}))
df_m$region_name <- unlist(lapply(df_m$region, function(x){return(region_names[x])}))

type <- 'pdf'

rgplot <- function(region){
  df2plot_e <- df_e[(df_e$region==region) & (df_e$type==type),]
  df2plot_m <- df_m[(df_m$region==region) & (df_m$type==type),]
  d0 <- df_para[df_para$region==region, 'median']
  g <- ggplot(df2plot_e, aes(x = d, y = y)) +
    geom_point(size=0.3, show.legend = F) +
    geom_line(data=df2plot_m, aes(x = d, y = y), color='steelblue', size=0.5, show.legend = F) +
    theme_minimal() +
    labs(x='d (km)', y='p(d)', title = region_names[region]) +
    geom_vline(xintercept = d0, linetype ='dotted', color="steelblue", size=0.8) +
    annotate(geom = 'text', x = d0 + 25, y = 10^(-8.5),
             label = sprintf('Median trip distance=%.1f', d0)) +
    scale_x_log10(limits = c(0.1, 10^4),
                  breaks = trans_breaks("log10", function(x) 10^x),
                  labels = trans_format("log10", scales::math_format(10^.x))) +
    scale_y_log10(limits = c(10^(-10), 1),
                  breaks = trans_breaks("log10", function(x) 10^x),
                  labels = trans_format("log10", scales::math_format(10^.x))) +
    annotation_logticks()
  return(g)
}

region_list1 <- c('australia', 'nairobi')
glist <- lapply(region_list1, rgplot)
G1 <- ggarrange(plotlist = glist, nrow = 1, ncol = 2)

my_colors <- pal_igv('default')(22)

type <- 'pdf'
df <- df_e[df_e$type==type,]
g3 <- ggplot(df) +
    geom_point(aes(x = d, y = y, color=region_name), size=0.3, alpha=0.3, show.legend = F) +
    theme_minimal() +
    labs(x='d (km)', y='p(d)', title = '') +
    scale_color_manual(name = "Region", values = my_colors) +
    scale_x_log10(limits = c(0.1, 10^4),
                  breaks = trans_breaks("log10", function(x) 10^x),
                  labels = trans_format("log10", scales::math_format(10^.x))) +
    scale_y_log10(limits = c(10^(-10), 1),
                  breaks = trans_breaks("log10", function(x) 10^x),
                  labels = trans_format("log10", scales::math_format(10^.x))) +
    annotation_logticks()

G <- ggarrange(G1, g3, nrow = 2, ncol = 1, heights = c(1, 1), labels = c('(a)', '(b)'))

ggsave(filename = glue("figures/trip_distance.png"), plot=G,
     width = 6, height = 6, unit = "in", dpi = 300)