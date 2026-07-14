library(data.table)
library(ggplot2)
library(patchwork)
library(viridisLite)

# Define output folder 
print("Define output folder")

fs::dir_create(here::here("output/models/"))
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
  period <- as.IDate(substr(i, 1, 8), format = "%Y%m%d")
  if (period < as.IDate("2020-12-01"))
    tmp[, "tp" := "COVID-19, no vaccination"]
  if (period >= as.IDate("2020-12-01") & period < as.IDate("2022-04-01"))
    tmp[, "tp" := "Beginning of vaccination programme"]
  if (period >= as.IDate("2022-04-01"))
    tmp[, "tp" := "After COVID-19 restrictions"]
  df <- rbind(df, tmp)
}

# Set time period category
df[, "tp" := factor(tp, levels = c("COVID-19, no vaccination", 
    "Beginning of vaccination programme",
    "After COVID-19 restrictions"))]

# Add offset term
df[, logdenom := log(denom)]  

# Remove zeros
df <- df[!(numer==0 | denom==0)]

# Function to fit model for covid periods
fitcovid <- function(df, out_arg, metric_arg){
  data = df[disease == out_arg & metric == metric_arg]
  tryCatch({
      #fit model
      fit <- glm(numer ~ tp, 
        offset = logdenom, data = data, family = quasipoisson(link = "log")
        )
      #get model coef
      coefs <- summary(fit)$coefficients
      dt <- as.data.table(coefs, keep.rownames = "term")
      setnames(dt, c("Estimate", "Std. Error", "t value", "Pr(>|t|)"),
                    c("estimate", "std_error", "statistic", "p_value"))
      dt[, c("irr", "lcl", "hcl") := .(exp(estimate), exp(estimate - 1.96 *std_error), exp(estimate + 1.96 *std_error))]
      dt[, c("percent", "lp", "hp") := .((irr-1)*100, (lcl-1)*100, (hcl-1)*100)]
      dt[, "term" := sub("^tp", "", term)]
      baseline <- data[, .(avg = mean(result, na.rm=TRUE)), by=.(term = tp)]
      base <- baseline[term=="COVID-19, no vaccination", avg]
      dt2 <- merge(dt, baseline, by = "term", all = TRUE)
      dt2[, "pred1" := base]
      dt2[term!="COVID-19, no vaccination", "pred1" := base * irr]
      base2 <- ifelse(metric_arg != "incidence", dt[term=="(Intercept)", exp(estimate)*100], dt[term=="(Intercept)", exp(estimate)])
      dt2[, "pred2" := base2]
      dt2[term!="COVID-19, no vaccination", "pred2" := base2 * irr]
      dt2[, c("disease", "metric", "error") := .(out_arg, metric_arg, NA_character_)]
      setcolorder(dt2, c("disease", "metric", "term", "estimate", "std_error", "statistic", 
        "p_value", "irr", "lcl", "hcl", "percent", "lp", "hp", "avg", "pred1", "pred2", "error"))

      },
    #get error message if model fails 
    error = function(e) {
      data.table(
        disease = out_arg,
        metric = metric_arg,
        term = NA_character_,
        estimate = NA_real_,
        std_error = NA_real_,
        statistic = NA_real_,
        p_value = NA_real_,
        irr = NA_real_,
        lcl = NA_real_,
        hcl = NA_real_,
        percent = NA_real_,
        lp = NA_real_,
        hp = NA_real_,
        avg = NA_real_,
        pred1 = NA_real_,
        pred2 = NA_real_,
        error = e$message
      )
    }) 
}

# Fit models for all outcomes and metrics
ds <- c("osd", "ud",  "ad",  "cjd", "pd",  "ftd", "mnd", "psp", "vd",  "hd",  "msa", "cbd",
        "pca", "dlb", "dementia")

metrics <- c("prevalence", "incidence", "fatality_1y", "fatality_5y")

modelresults <- rbindlist(lapply(ds, function(o) {
  rbindlist(lapply(metrics, function(m) {
    fitcovid(df = df, out_arg = o, metric_arg = m)
  }))
}))

fwrite(modelresults, file = paste0("output/models/tbl_modelcovid_month_", ystart, "_", yend, ".csv"))

# Remove na results and convert term to factor
results <- modelresults[!is.na(term) & term!="(Intercept)"]
results[, "term" := factor(term, levels=c("COVID-19, no vaccination", 
        "Beginning of vaccination programme",
        "After COVID-19 restrictions"))
        ]

# Function to generate plots
colpal <- setNames(
  viridisLite::turbo(length(ds)),
  ds[order(substr(ds,1,1))]
)

make_plot <- function(data, use = "avg") { 
  gen_plot <- function(data, ylab, ylog = FALSE){
  ggplot(data, aes(x = term, y = pred, group = disease, color = disease)) +
    geom_line(linewidth = .8, show.legend = TRUE) +
    geom_vline(xintercept = c(1.5, 2.5), linetype = "dashed", color = "grey") + 
    annotate(
      "text",
      x = c(1, 2, 3),
      y = Inf,
      label = c("COVID-19,\nno vaccination", 
        "Beginning of\nvaccination programme",
        "After COVID-19\nrestrictions"),
      vjust = 1.5,
      size = 2
    ) +
    scale_x_discrete(expand = expansion(mult=0.2)) +
    scale_color_manual(
      values = colpal,
      drop = FALSE,
      limits = names(colpal)
    ) +
    labs(x = NULL, y = ylab, color = "Disease") +
    theme_bw() +
    theme(
        axis.text.x = element_blank()
        ) +
    if (ylog) scale_y_log10()
  } 
  data <- copy(data)
  setnames(data, use, "pred")
  p1 <- gen_plot(data[data$metric == "prevalence"], "Prevalence(%)") 
  p2 <- gen_plot(data[data$metric == "incidence"], "Incidence(per 100,000 person-years)")
  p3 <- gen_plot(data[data$metric == "fatality_1y" & !disease %in% c("cbd", "cjd")], "1-year fatality(%)")
  g_covid <- (p1 | p2 | p3) +
     plot_layout(guides = "collect")
  ggsave(g_covid, filename = paste0("output/figs/fig_modelcovid_", use, "_", ystart, "_", yend, ".png"), width=12, units="in")
}


# p4 <- make_plot(df[df$metric == "fatality_5y" & !disease %in% c("cbd", "cjd")], TRUE, "5-year fatality(%)", FALSE)


print('Generate plot for average results for covid periods')
make_plot(results, "avg")

print('Generate plot for model results with avg baseline')
make_plot(results, "pred1")

print('Generate plot for model results with fit intercept')
make_plot(results, "pred2")

