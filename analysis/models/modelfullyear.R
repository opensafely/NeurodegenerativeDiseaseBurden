library(data.table)

# Define output folder 
print("Define output folder")

fs::dir_create(here::here("output/models/"))

# Specify arguments 
print('Specify arguments')

args <- commandArgs(trailingOnly = TRUE)

if (length(args) == 0) {
  yrange <- 2020:2023
} else {
  cargs <- unlist(strsplit(args[[1]], "_"))
  yrange <- seq(as.integer(cargs[1]), as.integer(cargs[2]))
}

# Read dataset
print('Read dataset')
df <- data.table()
for (i in yrange){
  dataset_name <- paste0(i,"0101_",i,"1231")
  df <- rbind(df, fread(file = paste0(
  "output/calculations/results-byallg-", dataset_name, ".csv"),
  colClasses = list(factor = c("year", "age", "sex", "region", "imd", "ethnicity", "cms"))
  )
  )
}

# Set cov ref level
df[,c("year", "age", "sex", "region", "imd", "ethnicity", "cms") := .(
  relevel(year, ref = "2020"),
  relevel(age, ref = "40-49"), 
  relevel(sex, ref = "male"), 
  relevel(region, ref = "London"), 
  relevel(imd, ref = "9-10 (least deprived)"), 
  relevel(ethnicity, ref = "White British"),
  relevel(cms, ref = "Q1")
  )]

# Add offset term
df[, logdenom := log(denom)]  

# Remove zeros
df <- df[!(numer==0 | denom==0)]

# Function to fit model and extract coefficients
fitfullmodel <- function(df, outcome, metric){
  data = df[disease == outcome & metric == metric]
  tryCatch({
      fit <- glm(numer ~ 
      #year + 
      age + sex + region + imd + ethnicity + cms, 
        offset = logdenom, data = data, family = quasipoisson(link = "log")
        )
      coefs <- summary(fit)$coefficients
      dt <- as.data.table(coefs, keep.rownames = "term")
      setnames(dt, c("Estimate", "Std. Error", "t value", "Pr(>|t|)"),
                    c("estimate", "std_error", "statistic", "p_value"))
      dt[, c("disease", "metric", "error") := .(outcome, metric, NA_character_)]
      setcolorder(dt, c("disease", "metric", "term", "estimate", "std_error", "statistic", "p_value", "error"))
      dt
    }, error = function(e) {
      data.table(
        disease = outcome,
        metric = metric,
        term = NA_character_,
        estimate = NA_real_,
        std_error = NA_real_,
        statistic = NA_real_,
        p_value = NA_real_,
        error = e$message
      )
    }) 
}

# Fit models for all outcomes and metrics
outcomes <- c("osd", "ud",  "ad",  "cjd", "pd",  "ftd", "mnd", "psp", "vd",  "hd",  "msa", "cbd",
              "pca", "dlb")

metrics <- c("prevalence", "incidence", "fatality_1y", "fatality_5y")

modelresults <- rbindlist(lapply(outcomes, function(outcome) {
  rbindlist(lapply(metrics, function(metric) {
    fitfullmodel(df = df, outcome = outcome, metric = metric)
  }))
}))

# Save results
fwrite(modelresults, file = paste0("output/models/modelfull_year",args[[1]], ".csv"))