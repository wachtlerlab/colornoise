#install.packages('readxl')
#install.packages('quickpsy')
#install.packages('dplyr')

library(readxl)
library(quickpsy)
library(dplyr)
library(openxlsx)
library(reticulate)
library(ggpubr)

# TDDO: add python complie module and color codes for plotting
#source('colorpalette_plus.py')

#color4plot <- function (num){
#    colorcodes = ColorPicker().circolors(numStim=num)
#    return [x / 255 for x in colorcodes]
#}


# import and merge data
fit_pf <- function (subject, all_files=FALSE, plot=TRUE){
  if (!all_files) {
    all_files <- list.files(path= paste0("data/", subject), pattern = "*.xlsx", full.names = T)
  }

  df_list <- list()
  for (i in seq_along(all_files)){
    all_labels <- openxlsx::getSheetNames(all_files[i])
    df_list[[i]]<- lapply(all_labels, read.xlsx, xlsxFile=all_files[i])  # read multiple sheets
    names(df_list[[i]]) <- all_labels
  }
  data <- do.call(Map, c(f = rbind, df_list))
  data <- data[order(names(data))]

  fit_list <- list()
  gg_list <- list()
  for (label in names(data)){
    df <- dplyr::select(data[[label]], All.Intensities, All.Responses)  # extract data for fitting
    df_grp <- merge(dplyr::count(df, All.Intensities),  # the total number of trials for each intensity
                   df %>% group_by(All.Intensities) %>% summarise(All.Responses = sum(All.Responses)),  # group by intensity and count the number of correct trials
                   all.x = TRUE)
    fit_list[[label]] <- quickpsy(df_grp, x=All.Intensities, k=All.Responses, n=n, guess=0.5)

    gg_list[[label]] <-  ggplot(fit_list[[label]]$curves, aes(x, y)) + geom_line()
    gg_list[[label]] <-  ggplot() +
      geom_line(fit_list[[label]]$curves, mapping = aes(x, y)) +
      geom_point(fit_list[[label]]$averages, mapping = aes(All.Intensities, prob)) +
      geom_vline(xintercept = fit_list[[label]]$thresholds$thre, linetype='dashed') +
      geom_hline(yintercept = fit_list[[label]]$thresholds$prob, linetype='dashed')

    #gg_list[[label]] <- ggline(fit_list[[label]]$curves, "x", "y")
  }
  if (plot){
    ggarrange(plotlist=gg_list, widths = c(4,4), labels = names(gg_list))
  }
}

fit_pf("pilot", all_files=FALSE, plot=TRUE)