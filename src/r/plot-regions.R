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
  geom_sf(data = zones, fill = "cornsilk2", color='bisque4', size = 0.01) +
  theme_void() +
  blank() +
  north(zones, location = "topleft") +
  annotation_scale()

region <- 'netherlands'
# Read shapefiles: zones
# zones <- st_transform(st_read(region_files[region]), "+proj=longlat +datum=WGS84")
zones <- st_transform(st_read(region_files[region]))

# Plot
g2 <- ggplot() +
  geom_sf(data = zones, fill = "cornsilk2", color='bisque4', size = 0.01) +
  theme_void() +
  blank() +
  north(zones, location = "topleft") +
  annotation_scale()

region <- 'saopaulo'
# Read shapefiles: zones
# zones <- st_transform(st_read(region_files[region]), "+proj=longlat +datum=WGS84")
zones <- st_transform(st_read(region_files[region]))

# Plot
g3 <- ggplot() +
  geom_sf(data = zones, fill = "cornsilk2", color='bisque4', size = 0.01) +
  theme_void() +
  blank() +
  north(zones, location = "topleft") +
  annotation_scale()

G <- ggarrange(g1, g2, g3,
               labels = c("Sweden", "The Netherlands", "São Paulo, Brazil"),
               ncol = 3, nrow = 1)

ggsave(filename = paste0("figures/gt-zones.png"), plot=G,
       width = 10, height = 4, unit = "in", dpi = 300)

#
# region <- 'sweden-national'
# # Read shapefiles: zones
# zones <- st_transform(st_read(region_files[region]), "+proj=longlat +datum=WGS84")
#
# # Plot
# g1 <- ggplot(data = zones) +
#   geom_sf() +
#   theme_void() +
#   blank() +
#   north(zones, location = "topleft") +
#   scalebar(zones, dist = 100, dist_unit = "km",
#            transform = TRUE, model = "WGS84")
#
# region <- 'sweden-west'
# # Read shapefiles: zones
# zones <- st_transform(st_read(region_files[region]), "+proj=longlat +datum=WGS84")
#
# # Plot
# g2 <- ggplot(data = zones) +
#   geom_sf() +
#   theme_void() +
#   blank() +
#   north(zones, location = "topleft") +
#   scalebar(zones, dist = 100, dist_unit = "km",
#            transform = TRUE, model = "WGS84")
#
# region <- 'sweden-east'
# # Read shapefiles: zones
# zones <- st_transform(st_read(region_files[region]), "+proj=longlat +datum=WGS84")
#
# # Plot
# g3 <- ggplot(data = zones) +
#   geom_sf() +
#   theme_void() +
#   blank() +
#   north(zones, location = "topleft") +
#   scalebar(zones, dist = 100, dist_unit = "km",
#            transform = TRUE, model = "WGS84")
#
# G <- ggarrange(g1, g2, g3,
#                labels = c("Sweden - National", "Sweden - West", "Sweden - East"),
#                ncol = 3, nrow = 1)
#
# ggsave(filename = paste0("figures/sweden-zones.png"), plot=G,
#        width = 12, height = 7, unit = "in", dpi = 300)
