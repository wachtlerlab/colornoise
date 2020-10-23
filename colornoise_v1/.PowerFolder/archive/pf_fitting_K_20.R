#install.packages('readxl')
#install.packages('quickpsy')
#install.packages('dplyr')

#install.packages('circular')
library(readxl)
library(quickpsy)
library(dplyr)
library(openxlsx)
library(ggpubr)
library(circular)



# import and merge data
fit_pf <- function (subject, all_files, plot=TRUE){
  if (missing(all_files)) {
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

  color2plot <- (x <- structure(rep(circular.colors(n=length(data)/2, m=pi/4, M=2*pi+pi/4), each=2),
                                names=names(data)))

  for (label in names(data)){
    df <- dplyr::select(data[[label]], All.Intensities, All.Responses)  # extract data for fitting
    df_grp <- merge(dplyr::count(df, All.Intensities),  # the total number of trials for each intensity
                   df %>% group_by(All.Intensities) %>% summarise(All.Responses = sum(All.Responses)),  # group by intensity and count the number of correct trials
                   all.x = TRUE)
    fit_list[[label]] <- quickpsy(df_grp, x=All.Intensities, k=All.Responses, n=n, guess=0.5)

    gg_list[[label]] <-  ggplot(fit_list[[label]]$curves, aes(x, y)) + geom_line()
    gg_list[[label]] <-  ggplot() +
      geom_line(fit_list[[label]]$curves, mapping = aes(x, y), color=color2plot[[label]]) +
      geom_point(fit_list[[label]]$averages, mapping = aes(All.Intensities, prob), color=color2plot[[label]]) +
      geom_vline(xintercept = fit_list[[label]]$thresholds$thre, linetype='dashed') +
      geom_hline(yintercept = fit_list[[label]]$thresholds$prob, linetype='dashed') +
      ylim(0.5, 1.0) +
      xlim(0, 6)

  }

  title_list <- list()
  for (i in seq_along(fit_list)){
    title_list[i]<- paste(names(fit_list)[i], round(fit_list[[i]]$thresholds$thre, digits = 2), sep = ':')
  }

  if (plot){
    ggarrange(plotlist=gg_list, widths = c(4,4), labels = title_list)
  }
}

#fit_pf("fschrader", plot=TRUE)
#fit_pf("fschrader", all_files =c('data/fschrader/20200730T1039L-L.xlsx',
#                                 'data/fschrader/20200730T1122L-L.xlsx'), plot=TRUE)
#fit_pf("pilot", all_files = c('data/pilot/20200730T1610L-L.xlsx',
#       'data/pilot/20200730T1630L-L.xlsx'), plot = TRUE)