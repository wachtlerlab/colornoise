library(readxl)
library(quickpsy)
library(dplyr)

# import and merge data
setwd("PhD-projects/colornoise")
all_files <- list.files(path="data/test10bit", pattern = "*.xlsx", full.names = T)
df_lists <- list() 


for (i in 1:length(all_files)){
  all_labels <- openxlsx::getSheetNames(all_files[i])
  df_lists[[i]]<- lapply(all_labels,openxlsx::read.xlsx,xlsxFile=all_files[i])
  names(df_lists[[i]]) <- all_labels
}
data <- do.call(Map, c(f = rbind, df_lists))
data <- data[order(names(data))]

# extract data for fitting
for (dt in data){
  df <- select(dt, All.Intensities, All.Responses)
  fit <- quickpsy(df, All.Intensities, All.Responses, guess = 0.5)
  fit %>% plot()
}

# df_group = aggregate(data = df1,All.Responses ~ All.Intensities, FUN=paste)
# TODO: structure the data to what quickpsy asks