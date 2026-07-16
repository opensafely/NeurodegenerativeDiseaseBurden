library(data.table)
library(ggplot2)
library(patchwork)
library(viridisLite)

# Define output folder 
print("Define output folder")

fs::dir_create(here::here("output/figs/"))

# Source date function
source("analysis/fn-define_dates.R")

# Specify arguments 
print('Specify arguments')

args <- commandArgs(trailingOnly = TRUE)

if (length(args) == 1) {
  cargs <- unlist(strsplit(args[[1]], "_"))
  ystart <- as.integer(cargs[1])
  yend <- as.integer(cargs[2])
} else {
  ystart <- 2020
  yend <- 2023
}
dates <- define_dates(ystart, yend, year = FALSE)

# Read dataset
print('Read dataset')

df <- data.table()
for (i in dates$dataset_name){
  tmp <- fread(file = paste0(
  "output/calculations/results-", i, ".csv"))
  tmp <- tmp[bygroup == "all" & category == "all"]
  tmp[, "date" := as.IDate(substr(i, 1, 8), format = "%Y%m%d")]
  df <- rbind(df, tmp)
}

# Round results
print('Round results')
roundmid_any <- function(x, to=6){
  # like round_any, but centers on (integer) midpoint of the rounding points
  ceiling(x/to)*to - (floor(to/2)*(x!=0))
}
df[metric %in% c("prevalence", "fatality_1y", "fatality_5y"), 
  c("numer_midpoint6", "denom_midpoint6") := .(roundmid_any(numer), roundmid_any(denom))]
df[metric == "incidence", c("numer_midpoint6", "denom_midpoint6") := .(roundmid_any(numer), denom)]
df[metric %in% c("prevalence", "fatality_1y", "fatality_5y"), "result_midpoint6_derived" := numer_midpoint6 / denom_midpoint6 *100]
df[metric == "incidence", "result_midpoint6_derived" := numer_midpoint6 / denom_midpoint6]

# Save rounded results
fwrite(df[,.(metric, disease, date, numer_midpoint6, denom_midpoint6, result_midpoint6_derived, result)], 
       paste0("output/figs/tbl_raw_month_", ystart, "_", yend, ".csv"))
fwrite(df[,.(metric, disease, date, numer_midpoint6, denom_midpoint6, result_midpoint6_derived)], 
       paste0("output/figs/tbl_round_month_", ystart, "_", yend, ".csv"))
       
# Function to generate plots
ds <- c("osd", "ud",  "ad",  "cjd", "pd",  "ftd", "mnd", "psp", "vd",  "hd",  "msa", "cbd",
        "pca", "dlb", "dementia")
colpal <- setNames(
  viridisLite::turbo(length(ds)),
  ds[order(substr(ds,1,1))]
)

make_plot <- function(data, rounded = TRUE, ylab, ylog = TRUE) { 
  if (rounded) {
    setnames(data, "result_midpoint6_derived", "result_to_plot")
  } else {
    setnames(data, "result", "result_to_plot")
  }
  ggplot(data, aes(x = date, y = result_to_plot, group = disease, color = disease)) +
    geom_line(linewidth = .8, show.legend = TRUE) +
    scale_x_date(
      breaks = seq(min(data$date), max(data$date), by = "12 months"),
      date_labels = "%Y"
    ) +
    scale_color_manual(
      values = colpal,
      drop = FALSE,
      limits = names(colpal)
    ) +
    labs(x = "Year", y = ylab, color = "Disease") +
    theme_bw() +
    if (ylog) scale_y_log10() 
}


# Use rounded results
print('Generate plot for rounded monthly results')
p1 <- make_plot(df[df$metric == "prevalence"], TRUE, "Prevalence(%)", TRUE)
p2 <- make_plot(df[df$metric == "incidence"], TRUE, "Incidence(per 100,000 person-years)", TRUE)
p3 <- make_plot(df[df$metric == "fatality_1y" & !disease %in% c("cbd", "cjd")], TRUE, "1-year fatality(%)", FALSE)
# p4 <- make_plot(df[df$metric == "fatality_5y" & !disease %in% c("cbd", "cjd")], TRUE, "5-year fatality(%)", FALSE)

g_round <- (p1 | p2 | p3) +
     plot_layout(guides = "collect")

# Save plot
ggsave(g_round, filename = paste0("output/figs/fig_round_month_", ystart, "_", yend, ".png"), width = 12, units = "in")

rm(list=c("p1", "p2", "p3", "g_round"))

# Use rounded results
print('Generate plot for raw monthly results')
p1 <- make_plot(df[df$metric == "prevalence"], FALSE, "Prevalence(%)", TRUE) 
p2 <- make_plot(df[df$metric == "incidence"], FALSE, "Incidence(per 100,000 person-years)", TRUE)
p3 <- make_plot(df[df$metric == "fatality_1y"], FALSE, "1-Year fatality(%)", FALSE)
# p4 <- make_plot(df[df$metric == "fatality_5y"], FALSE, "5-Year fatality(%)", FALSE)

g_raw <- (p1 | p2 | p3) +
     plot_layout(guides = "collect")

# Save plot
ggsave(g_raw, filename = paste0("output/figs/fig_raw_month_", ystart, "_", yend, ".png"), width = 12, units = "in")

