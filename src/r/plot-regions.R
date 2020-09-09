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

region_files <- c('dbs/netherlands/mobility_data/CBS_PC4_2017_v1.shp',
                  "dbs/sampers/national/region.shp",
                  "dbs/sampers/west/region.shp",
                  "dbs/sampers/east/region.shp",
                  'dbs/saopaulo/zones/zones.shp')
names(region_files) <- c('netherlands', 'sweden-national', 'sweden-west', 'sweden-east', 'saopaulo')

region <- 'netherlands'
# Read shapefiles: zones
zones <- st_transform(st_read(region_files[region]), "+proj=longlat +datum=WGS84")

# Plot
g1 <- ggplot(data = zones) +
  geom_sf() +
  theme_void() +
  blank() +
  north(zones, location = "topleft") +
  scalebar(zones, dist = 30, dist_unit = "km",
           transform = TRUE, model = "WGS84")

region <- 'saopaulo'
# Read shapefiles: zones
zones <- st_transform(st_read(region_files[region]), "+proj=longlat +datum=WGS84")

# Plot
g2 <- ggplot(data = zones) +
  geom_sf() +
  theme_void() +
  blank() +
  north(zones, location = "topleft") +
  scalebar(zones, dist = 30, dist_unit = "km",
           transform = TRUE, model = "WGS84")

G <- ggarrange(g1, g2,
               labels = c("The Netherlands", "São Paulo, Brazil"),
               ncol = 2, nrow = 1)

ggsave(filename = paste0("figures/saopaulo-netherlands-zones.png"), plot=G,
       width = 14, height = 7, unit = "in", dpi = 300)


region <- 'sweden-national'
# Read shapefiles: zones
zones <- st_transform(st_read(region_files[region]), "+proj=longlat +datum=WGS84")

# Plot
g1 <- ggplot(data = zones) +
  geom_sf() +
  theme_void() +
  blank() +
  north(zones, location = "topleft") +
  scalebar(zones, dist = 100, dist_unit = "km",
           transform = TRUE, model = "WGS84")

region <- 'sweden-west'
# Read shapefiles: zones
zones <- st_transform(st_read(region_files[region]), "+proj=longlat +datum=WGS84")

# Plot
g2 <- ggplot(data = zones) +
  geom_sf() +
  theme_void() +
  blank() +
  north(zones, location = "topleft") +
  scalebar(zones, dist = 100, dist_unit = "km",
           transform = TRUE, model = "WGS84")

region <- 'sweden-east'
# Read shapefiles: zones
zones <- st_transform(st_read(region_files[region]), "+proj=longlat +datum=WGS84")

# Plot
g3 <- ggplot(data = zones) +
  geom_sf() +
  theme_void() +
  blank() +
  north(zones, location = "topleft") +
  scalebar(zones, dist = 100, dist_unit = "km",
           transform = TRUE, model = "WGS84")

G <- ggarrange(g1, g2, g3,
               labels = c("Sweden - National", "Sweden - West", "Sweden - East"),
               ncol = 3, nrow = 1)

ggsave(filename = paste0("figures/sweden-zones.png"), plot=G,
       width = 12, height = 7, unit = "in", dpi = 300)
