# Title     : Visualise the sparse traces (benchmark model) and model output
# Objective : An example individual in Sao Paulo
# Created by: Yuan Liao
# Created on: 2021-07-21

# Libraries
library(circlize)
library(dplyr)
library(ggsci)

# Load data
# Synthesised output
df <- read.csv('results/input-output-example/odm.csv')
names(df) <- c('from', 'to', 'value')
df <- df %>%
  filter(value!=0) %>%
  filter(from != to)

# Benchmark model
df.b <- read.csv('results/input-output-example/odm_benchmark.csv')
names(df.b) <- c('from', 'to', 'value')
df.b <- df.b %>%
  filter(value!=0) %>%
  filter(from != to)

# Unique zones
zones <- unique(c(df$from, df$to, df.b$from, df.b$to))
mycolors <- rand_color(length(zones), luminosity = "bright")
# Define colors
colors.benchmark <- mycolors[unique(c(df.b$from, df.b$to))]
colors.model <- mycolors[unique(c(df$from, df$to))]

# Plot
png("figures/chord_input_output.png", width = 1800, height = 900)
par(mfrow = c(1, 2))
# Benchmark
chordDiagram(df.b, annotationTrack = "grid", grid.col = colors.benchmark, transparency = 0.3)
title("(a)", cex.main = 5, adj  = 0, line = -5)
# Model
chordDiagram(df, annotationTrack = "grid", grid.col = colors.model, transparency = 0.3)
title("(b)", cex.main = 5, adj  = 0, line = -5)
dev.off()

# Restart circular layout parameters
circos.clear()