# Title     : Visualise the sparse traces and model output
# Objective : An example individual in Sao Paulo
# Created by: Yuan Liao
# Created on: 2021-02-02

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
library(raster)
library(stplanr)
library(tmap)

region_files <- c("dbs/sweden/survey_deso/DeSO/DeSO_2018_v2.shp",
                  'dbs/netherlands/mobility_data/CBS_PC4_2017_v1.shp',
                  "dbs/sweden/sampers/national/region.shp",
                  "dbs/sweden/sampers/west/region.shp",
                  "dbs/sweden/sampers/east/region.shp",
                  'dbs/saopaulo/zones/zones.shp')
names(region_files) <- c('sweden', 'netherlands', 'sweden-national', 'sweden-west', 'sweden-east', 'saopaulo')
region <- 'saopaulo'
# Read shapefiles: zones
zones <- st_transform(st_read(region_files[region]), "+proj=longlat +datum=WGS84")
e <- extent(zones)
p <- as(e, 'list')

# Sparse input
geotweets <- read.csv('results/input-output-example/tweets.csv')

# Synthesised output
df <- read.csv('results/input-output-example/odm.csv')
names(df) <- c('ozone', 'dzone', 'trip')
df_a <- df %>%
    filter(ozone != dzone) %>%
    mutate(trip = trip / sum(trip) * 100) %>%
    filter(trip > 0)
lines <- od2line(flow = df_a, zones = zones)
lines <- arrange(lines, trip)

# Bounding box of the zoom-in view
bb_idf <- st_sf(st_as_sfc(st_bbox(c(xmin = min(geotweets$longitude), xmax = max(geotweets$longitude) - 0.5,
                                    ymin = min(geotweets$latitude) + 0.01, ymax = max(geotweets$latitude) - 0.01),
                                  crs = st_crs(4326))))

# Input sparse traces
g1 <- ggplot() +
  geom_sf(data = zones, fill = "cornsilk2", color='white', size = 0.3) +
  theme_void() +
  blank() + # labs(title = "Sparse traces") +
  geom_point(data=geotweets, aes(longitude, latitude),
             inherit.aes = TRUE, alpha = 0.3, size = 0.8, color='darkblue') +
  coord_sf(xlim = c(min(geotweets$longitude), max(geotweets$longitude) - 0.5),
           ylim = c(min(geotweets$latitude) + 0.01, max(geotweets$latitude) - 0.01), expand = FALSE)

# draw the ODMs
g2 <- tm_shape(zones) +
    tm_fill(col="cornsilk2") +
    tm_borders("white", alpha=1, lwd = 0.3) +
    tm_shape(lines) +
    tm_lines(
        palette = "plasma",
        trans = "log10", style="cont", # lwd = "trip",
        scale = 9,
        lwd = 0.1,
        title.lwd = 0.5,
        alpha = 0.3,
        col = "trip",
        title = "Trip share (%)",
        legend.lwd.show = FALSE,
        legend.col.show = FALSE
    ) +
    tm_shape(bb_idf) +
    tm_borders("black", alpha=1, lwd = 1.5) +
    tm_layout(
        title = '', # 'Synthesised traces (individual ODM)',
        frame = FALSE,
        legend.bg.alpha = 0.5,
        legend.bg.color = "white"
    )


g3 <- tm_shape(zones, bbox=tmaptools::bb(matrix(c(min(geotweets$longitude),
                                                  min(geotweets$latitude) + 0.01,
                                                  max(geotweets$longitude) - 0.5,
                                                  max(geotweets$latitude) - 0.01),
                                                2,2))) +
    tm_fill(col="cornsilk2") +
    tm_borders("white", alpha=1, lwd = 0.3) +
    tm_shape(lines, bbox=tmaptools::bb(matrix(c(min(geotweets$longitude),
                                                  min(geotweets$latitude) + 0.01,
                                                  max(geotweets$longitude) - 0.5,
                                                  max(geotweets$latitude) - 0.01),
                                                2,2))) +
    tm_lines(
        palette = "plasma",
        trans = "log10", style="cont", # lwd = "trip",
        scale = 9,
        lwd = "trip",
        title.lwd = 0.5,
        alpha = 0.3,
        col = "trip",
        title = "Trip share (%)",
        legend.lwd.show = FALSE
    ) +
    tm_layout(
        title = '', # 'Synthesised traces (individual ODM)',
        frame = FALSE,
        legend.bg.alpha = 0.5,
        legend.bg.color = "white"
    )

h <- 3
w <- h
tmap_save(tm=g2, filename = "figures/input-output_3.png",
          width = w, height = h, unit = "in", dpi = 300)
tmap_save(tm=g3, filename = "figures/input-output_2.png",
          width = w, height = h, unit = "in", dpi = 300)
ggsave(filename = "figures/input-output_1.png", plot=g1,
       width = w, height = h, unit = "in", dpi = 300)