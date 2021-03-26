# Title     : Visualise the trip distance distributions across regions
# Objective : Show the trip distance distribution and the fitted power law
# Created by: Yuan Liao
# Created on: 2021-02-16

library(ggplot2)
library(glue)
library(ggpubr)
library(scales)
library(latex2exp)
library(randomcoloR)

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
df_e <- read.csv('results/multi-region_trips_rid_6_pcdf.csv')
df_m <- read.csv('results/multi-region_trips_rid_6_pcdf_model.csv')
df_para <- read.csv('results/multi-region_trips_rid_6_paras.csv')
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

region_list1 <- c('netherlands', 'sweden', 'austria','australia',
                 'saudiarabia',  'egypt', 'moscow', 'stpertersburg',
                 'saopaulo',  'rio', 'barcelona', 'madrid',
                 'cebu', 'manila', 'jakarta', 'surabaya',
                 'capetown', 'johannesburg', 'nairobi', 'lagos'
                 )
glist <- lapply(region_list1, rgplot)
G1 <- ggarrange(plotlist = glist, nrow = 5, ncol = 4)

g1 <- rgplot('guadalajara')
g2 <- rgplot('kualalumpur')

my_colors <- unname(distinctColorPalette(22))

type <- 'cdf'
df <- df_e[df_e$type==type,]
g3 <- ggplot(df) +
    geom_line(aes(x = d, y = y, color=region_name), size=0.3, alpha=0.7) +
    theme_minimal() +
    labs(x='d (km)', y='P(d)', title = 'All the regions') +
    scale_color_manual(name = "Region", values = my_colors) +
    scale_x_log10(limits = c(0.1, 10^4),
                  breaks = trans_breaks("log10", function(x) 10^x),
                  labels = trans_format("log10", scales::math_format(10^.x))) +
    scale_y_log10(limits = c(10^(-4), 1.1),
                  breaks = trans_breaks("log10", function(x) 10^x),
                  labels = trans_format("log10", scales::math_format(10^.x))) +
    annotation_logticks()
#    theme(legend.position = c(0.3, 0.3))

G2 <- ggarrange(g1, g2, g3, nrow = 1, ncol = 3, widths = c(1, 1, 2))

G <- ggarrange(G1, G2, nrow = 2, ncol = 1, heights = c(5, 1))

ggsave(filename = glue("figures/trip_distance.png"), plot=G,
     width = 16, height = 20, unit = "in", dpi = 300)

######################################
type <- 'cdf'

rgplot <- function(region){
  df2plot_e <- read.csv(glue('dbs/{region}/visits/visits_{runid}_trips_dom.csv'))
  d0 <- df_para[df_para$region==region, 'median']
  df2plot_e <- df2plot_e[df2plot_e$distance > 0.1, ]
  g <- ggplot(df2plot_e, aes(x = distance)) +
     stat_ecdf(geom = "step") +
#    geom_line(size=0.3, show.legend = F) +
#    geom_line(data=df2plot_m, aes(x = d, y = y), color='steelblue', size=0.5, show.legend = F) +
    theme_minimal() +
    labs(x='d (km)', y='CDF', title = region_names[region]) +
    geom_vline(xintercept = d0, linetype ='dotted', color="steelblue", size=0.8) +
    annotate(geom = 'text', x = d0 + 25, y = 0.25,
             label = sprintf('Median trip distance=%.2f', d0)) +
    scale_x_log10(limits = c(0.1, 10^4),
                  breaks = trans_breaks("log10", function(x) 10^x),
                  labels = trans_format("log10", scales::math_format(10^.x))) +
    scale_y_continuous(limits = c(NA, 1)) +
    annotation_logticks(sides = "b")
  return(g)
}
    # scale_y_continuous(limits = c(10^(-4), 1.1),
    #                    breaks = c(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
    #                    labels = c(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)) +
glist <- lapply(region_list, rgplot)
G3 <- ggarrange(plotlist = glist, nrow = 6, ncol = 4)

ggsave(filename = glue("figures/trip_distance_CDF.png"), plot=G3,
     width = 16, height = 20, unit = "in", dpi = 300)