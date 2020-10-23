#install.packages('readxl')
#install.packages('quickpsy')
#install.packages('dplyr')
library(ggplot2)
library(readxl)
library(quickpsy)
library(dplyr)
library(openxlsx)
library(ggpubr)
library(data.table)

fit_pf <- function (subject, sel_par, sel_ses, rm_ses, plot=TRUE){
#' Fit and plot PF.
#'
#' @param sel_par string as 'pattern1|parttern2|pattern3'
#' @param sel_ses string as 'pattern1|parttern2|pattern3'
#' @return fitting output for each hue

  sub_path <- paste0("data/", subject)
  xrl_df <- fread(paste0(sub_path,'/', subject, '.xrl'), sep=',', header = FALSE, strip.white = TRUE)
  all_xrl <- xrl_df %>% filter(grepl('xlsx', V4))

  # Check if data selection is required
  if (!missing(sel_par)) {
    all_xrl<- all_xrl %>% filter(grepl(sel_par, V2))
  }

  if (!missing(sel_ses)) {
    all_xrl <- all_xrl %>% filter(grepl(sel_ses, V4))
  }

  if (!missing(rm_ses)) {
    all_xrl <- all_xrl %>% filter(!grepl(rm_ses, V4))
  }

  # Read and append xlsx files
  all_files <- all_xrl$V4
  df_list <- list()
  for (i in seq_along(all_files)){
    all_labels <- openxlsx::getSheetNames(all_files[i])
    df_list[[i]]<- lapply(all_labels, read.xlsx, xlsxFile=all_files[i])  # read multiple sheets
    names(df_list[[i]]) <- all_labels
  }

  # Merge session data and pool data based on conditions
  data <- do.call(Map, c(f = rbind, df_list))
  data <- data[order(names(data))]

  # Rearrange data to combine plus and minus sides
  rearr_data <- list()

  for (i in seq(1, length(data),2)){
    idx <- ceiling(i/2)
    name <- paste0('hue_', idx)

    df_1 <- data[[i]]
    if(endsWith(names(data[i]), 'm')){
      df_1$All.Responses <- 1 - df_1$All.Responses
    }

    df_2 <- data[[i+1]]
    if(endsWith(names(data[i+1]), 'm')){
      df_2$All.Responses <- 1 - df_2$All.Responses
    }

    rearr_data[[name]] <- rbind(df_1, df_2)
  }

  # Fit PF by quickpsy and plot PF if plot==TRUE
  fit_list <- list()
  gg_list <- list()

  for (label in names(rearr_data)){
    df <- dplyr::select(rearr_data[[label]], All.Intensities, All.Responses)  # extract data for fitting
    df$All.Intensities <-round(df$All.Intensities, 1)
    fit_list[[label]] <- quickpsy(df, x= All.Intensities, k=All.Responses, guess=0, lapses=0.01,
                                  fun = cum_normal_fun, B = 100)

    gg_list[[label]] <-  ggplot(fit_list[[label]]$curves, aes(x, y)) + geom_line()
    gg_list[[label]] <-  ggplot() +
      geom_line(fit_list[[label]]$curves, mapping = aes(x, y)) +
      geom_point(fit_list[[label]]$averages, mapping = aes(All.Intensities, prob), color='grey') +
      geom_vline(xintercept = fit_list[[label]]$thresholds$thre, linetype='dashed') +
      geom_hline(yintercept = fit_list[[label]]$thresholds$prob, linetype='dashed') +
      ylim(0, 1.0) +
      xlim(-15, 15)
  }

  if (plot) {
    title_list <- list()
    for (i in seq_along(fit_list)) {
      title_list[i] <- names(fit_list)[i]
    }
    p <- ggarrange(plotlist = gg_list, ncol = 4, nrow = 2, labels = title_list, font.label = list(size = 8, color = 'black'))
    print(p)
  }

  return(fit_list)
}


param_plot <- function (fit_list){
#' Plot estimated paramters after PF fitting.
#'
#' @param fit_list a list of fitting output of function fit_pf
  param_df <- data.frame()

  for (label in names(fit_list)){
    fit <- fit_list[[label]]
    param <- fit[['par']]
    param$label <- label
    #if(param$parn == 'p1') {param$parn <- 'mean'}
    #if(param$parn == 'p2') {param$parn <- 'std'}
    param_df <- rbind(param_df, param)
  }
  angles <-  rep(seq(0+22.5, 360, 360/length(fit_list)), each=2)
  param_df$angle <- angles
  p <- ggplot(param_df, aes(x=angle, y=par, group=parn, color=parn)) +
    geom_pointrange(aes(ymin=parinf, ymax=parsup)) +
    geom_line()
  #p + scale_fill_discrete(name="params",
  #                       labels=c("mean", "std"))
  print(p)
}

### example
#fit_ysu <- fit_pf("ysu", sel_par = 'cn2x8_HH_ysu_scaledN_a.yaml', rm_ses = '20201012', plot = FALSE)
#param_plot(fit_ysu)