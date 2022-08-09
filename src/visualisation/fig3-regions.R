# Title     : Visualize the regions
# Objective : Visualize the regions
# Created by: Yuan Liao
# Created on: 2020-09-09

# packages required
library(sf)
library(ggplot2)
library(ggmap)
library(classInt)
library(dplyr)
library(ggpubr)
library(ggsn)
library(ggspatial)
library(gridExtra)

region_files <- c("dbs/sweden/survey_deso/DeSO/DeSO_2018_v2.shp",
                  'dbs/netherlands/mobility_data/CBS_PC4_2017_v1.shp',
                  "dbs/sweden/sampers/national/region.shp",
                  "dbs/sweden/sampers/west/region.shp",
                  "dbs/sweden/sampers/east/region.shp",
                  'dbs/saopaulo/zones/zones.shp')
names(region_files) <- c('sweden', 'netherlands', 'sweden-national', 'sweden-west', 'sweden-east', 'saopaulo')

region <- 'sweden'
# Read shapefiles: zones
# zones <- st_transform(st_read(region_files[region]), "+proj=longlat +datum=WGS84")
zones <- st_transform(st_read(region_files[region]))

# Plot
g1 <- ggplot() +
  geom_sf(data = zones, fill=NA, color='gray45', size=0.01) +
  theme_void() +
  annotation_scale(location = 'br')

region <- 'netherlands'
# Read shapefiles: zones
# zones <- st_transform(st_read(region_files[region]), "+proj=longlat +datum=WGS84")
zones <- st_transform(st_read(region_files[region]))

# Plot
g2 <- ggplot() +
  geom_sf(data = zones, fill=NA, color='gray45', size=0.01) +
  theme_void() +
  annotation_scale(location = 'br')

region <- 'saopaulo'
# Read shapefiles: zones
# zones <- st_transform(st_read(region_files[region]), "+proj=longlat +datum=WGS84")
zones <- st_transform(st_read(region_files[region]))

# Plot
g3 <- ggplot() +
  geom_sf(data = zones, fill=NA, color='gray45', size=0.01) +
  theme_void() +
  annotation_scale(location = 'br')

G2 <- ggarrange(g2, g3,
               labels = c("(b)", "(c)"),
               ncol = 1, nrow = 2)
G <- ggarrange(g1, G2, widths = c(1, 1.3),
               labels = c("(a)", ""),
               ncol = 2, nrow = 1)

ggsave(filename = paste0("figures/gt-zones.png"), plot=G,
       width = 5, height = 5, unit = "in", dpi = 1000)
