# Title     : Browsing and cleaning project folders
# Objective : This script is exploring the scr folder and the scripts under it to clean up for further working process.
# Created by: Yuan Liao
# Created on: 2020-08-06
# Notes: Put this directly in the repo folder to explore different folders and the scripts in them.

library(data.table)
library(dplyr)

# Folder contains source code
srcpy_folder <- "src/py/"

# Get files
file_list <- data.table(file = list.files(srcpy_folder, full.names = TRUE))

# Divide files catch their extensions
file_list$format <- sapply(strsplit(file_list$file, "\\."), function(x){unlist(x)[2]})

# Order by their file format
file_list <- file_list[order(file_list$format)]

# Output to a table for manually going through
# write.csv(file_list, "code_files_cleaning.csv", row.names = F)

# Try to read a notebook
pkgs <- function(file) {
  f <- readLines(file, warn=FALSE)
  f_pks <- unlist(strsplit(f[grep("\"import ", f)], split = "\"import "))
  f_pks <- f_pks[grep(",", f_pks)]
  f_pks <- substr(f_pks,1, nchar(f_pks)-4)
  return(f_pks)
}
file_list_ipynb <- filter(file_list, grepl(".ipynb", file, fixed = TRUE))
pkgs_used <- data.frame(pkg=unique(unlist(lapply(file_list_ipynb$file, pkgs))))