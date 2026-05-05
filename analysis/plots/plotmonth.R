library(data.table)
library(ggplot2)
library(patchwork)
library(viridis)

# Define output folder 
print("Define output folder")

fs::dir_create(here::here("output/figs/"))

# Source date function
source("analysis/fn-define_dates.R")

# Specify arguments 
print('Specify arguments')

args <- commandArgs(trailingOnly = TRUE)

if (length(args) == 0) {
  ystart <- 2020
  yend <- 2023
} else {
  cargs <- unlist(strsplit(args[[1]], "_"))
  ystart <- as.integer(cargs[1])
  yend <- as.integer(cargs[2])
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

# Generate plots
print('Generate plot for monthly results')

make_plot <- function(data, ylab) {
  ggplot(data, aes(x = date, y = result, group = disease, color = disease)) +
    geom_line() +
    scale_x_date(
      breaks = seq(min(data$date), max(data$date), by = "12 months"),
      date_labels = "%Y"
    ) +
    scale_color_viridis_d(option = "turbo") +
    labs(x = "Year", y = ylab, color = "Disease") +
    theme_bw()
}

p1 <- make_plot(df[df$metric == "prevalence"], "Prevalence(%)")
p2 <- make_plot(df[df$metric == "incidence"], "Incidence(per 100,000 person-years)")
p3 <- make_plot(df[df$metric == "fatality_1y"], "1-Year fatality(%)")
p4 <- make_plot(df[df$metric == "fatality_5y"], "5-Year fatality(%)")

g <- (p1 | p2) / (p3 | p4) +
     plot_layout(guides = "collect") & 
     theme(legend.position = "right")

# Save plot
ggsave(g, filename = paste0("output/figs/fig_month_", ystart, "_", yend, ".png"))

