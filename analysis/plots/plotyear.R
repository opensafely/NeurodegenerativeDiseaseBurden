library(data.table)
library(ggplot2)
library(viridis)

# Define output folder 
print("Define output folder")

fs::dir_create(here::here("output/figs/"))

# Specify arguments 
print('Specify arguments')

args <- commandArgs(trailingOnly = TRUE)

if (length(args) == 1) {
  cargs <- unlist(strsplit(args[[1]], "_"))
  ystart <- as.integer(cargs[1])
  yend <- as.integer(cargs[2])
  } else {
  ystart <- 2020
  yend <- 2023}

# Read data
print("Read annual results")

df <- data.table()
for (i in ystart:yend){
  dataset_name <- paste0(i,"0101_",i,"1231")
  tmp <- fread(file = paste0(
  "output/calculations/results-", dataset_name, ".csv")
  )
  tmp[, "year" := as.integer(substr(dataset_name,1,4))]
  tmp[, "month" := ifelse(
        as.integer(substr(dataset_name,5,6)) == as.integer(substr(dataset_name,14,15)), 
        as.integer(substr(dataset_name,5,6)),
        NA_integer_)]
  tmp[category == "", category := "unknown"]
  df <- rbind(df, tmp[metric == "incidence" & bygroup == "all"])
}

# Round counts
print("Round counts")

roundmid_any <- function(x, to=6){
  # like round_any, but centers on (integer) midpoint of the rounding points
  ceiling(x/to)*to - (floor(to/2)*(x!=0))
}
df[, c("numer_midpoint6", "denom_midpoint6") := .(roundmid_any(numer), denom)]
df[, "result_midpoint6_derived" := numer_midpoint6 / denom_midpoint6]

fwrite(df, paste0("output/figs/tbl_round_year_", ystart, "_", yend, ".csv"))

# Bar plots for dementia
outcomes <- c("ad", "ud", "vd", "ftd", "dlb", "advdmixed", "osdmixed")
df <- df[disease %in% outcomes]
df[, prop := round(numer_midpoint6/sum(numer_midpoint6)*100,1), by = year]
g_bar <- ggplot(df, aes(
  x = factor(year),
  y = prop,
  fill = disease
)) +
  geom_col() +
  labs(x = "Year", y = "Pencentage", fill = "Disease") +
  scale_fill_viridis_d(option = "viridis") +
  scale_y_continuous(
    expand = expansion(mult = c(0, 0.05))
  ) +
  theme_bw() 

ggsave(g_bar, filename = paste0("output/figs/fig_round_year_bar_", ystart, "_", yend, ".png"))