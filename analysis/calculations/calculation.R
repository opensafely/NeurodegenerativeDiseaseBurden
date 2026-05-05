# Load libraries
print('Load libraries')
library(data.table)

# Define output folder ----
print("Define output folder")

fs::dir_create(here::here("output/calculations/"))

# Specify arguments ----
print('Specify arguments')

args <- commandArgs(trailingOnly = TRUE)

if (length(args) == 0) {
  dataset_name <- "20200101_20201231"
} else {
  dataset_name <- args[[1]]
}

# Read dataset ----
print('Read dataset')

df <- fread(paste0(
  "output/dataset_definition/dataset-",
  dataset_name,
  ".csv.gz"
))

# Categorize covs ----
print('Categorize covs')

df[,
  cov_cat_age := cut(
    cov_num_age,
    breaks = c(17, 39, 49, 59, 69, 79, 89, 99, 110),
    labels = c(
      "18-39",
      "40-49",
      "50-59",
      "60-69",
      "70-79",
      "80-89",
      "90-99",
      "100-110"
    )
  )
]
df[,
  cov_cat_cms := cut(
    cov_num_cms,
    breaks = quantile(cov_num_cms, probs = seq(0, 1, 0.25), na.rm = TRUE),
    labels = c("Q1", "Q2", "Q3", "Q4"),
    include.lowest = TRUE
  )
]
df[,
  cov_cat_imd := factor(
    cov_cat_imd,
    levels = c(
      "1 (most deprived)",
      "10 (least deprived)",
      "2",
      "3",
      "4",
      "5",
      "6",
      "7",
      "8",
      "9",
      "unknown"
    ),
    labels = c(
      "1-2 (most deprived)",
      "9-10 (least deprived)",
      "1-2 (most deprived)",
      "3-4",
      "3-4",
      "5-6",
      "5-6",
      "7-8",
      "7-8",
      "9-10 (least deprived)",
      "unknown"
    )
  )
]

# Get column names ----
print('Get column names')

cols = grep("(p|i|f)numer", colnames(df), value = TRUE)

# Define function to calculate inci, prev, fatality in the whole population or by subgroups of age, sex, region, imd, ethnicity, cms ----
print('Define function to calculate inci, prev, fatality')

cal_metric = function(df, col, bygroup = NA) {
  tmp = unlist(strsplit(col, "_", fixed = TRUE))
  outcome = tmp[length(tmp)]
  if (is.na(bygroup)) {
    if (grepl("^pnumer", col)) {
      num = df[, sum(get(col))]
      denom = df[, sum(pdenom_bin_mid)]
      tmpt = data.table(
        metric = "prevalence",
        disease = outcome,
        numer = num,
        denom = denom,
        result = num / denom * 100
      )
    } else if (grepl("^fnumer", col)) {
      futime = tmp[3]
      num = df[, sum(get(col))]
      denom = df[, sum(get(paste0("inumer_bin_", outcome)))]
      tmpt = data.table(
        metric = paste0("fatality_", futime),
        disease = outcome,
        numer = num,
        denom = denom,
        result = num / denom * 100
      )
    } else {
      num = df[, sum(get(col))]
      denom = df[, sum(get(paste0("idenom_num_", outcome))) / 365 / 100000]
      tmpt = data.table(
        metric = "incidence",
        disease = outcome,
        numer = num,
        denom = denom,
        result = num / denom
      )
    }
    tmpt[, c("bygroup", "category") := .("all", "all")]
    setcolorder(
      tmpt,
      c("metric", "disease", "bygroup", "category", "numer", "denom", "result")
    )
  } else {
    if (grepl("^pnumer", col)) {
      num = df[,
        .(numer = sum(get(col))),
        by = .(category = get(paste0("cov_cat_", bygroup)))
      ]
      denom = df[,
        .(denom = sum(pdenom_bin_mid)),
        by = .(category = get(paste0("cov_cat_", bygroup)))
      ]
      tmpt = merge(num, denom, by = "category", all = TRUE)
      tmpt[,
        c("metric", "disease", "result", "bygroup") := .(
          "prevalence",
          outcome,
          numer / denom * 100,
          bygroup
        )
      ]
    } else if (grepl("^fnumer", col)) {
      futime = tmp[3]
      num = df[,
        .(numer = sum(get(col))),
        by = .(category = get(paste0("cov_cat_", bygroup)))
      ]
      denom = df[,
        .(denom = sum(get(paste0("inumer_bin_", outcome)))),
        by = .(category = get(paste0("cov_cat_", bygroup)))
      ]
      tmpt = merge(num, denom, by = "category", all = TRUE)
      tmpt[,
        c("metric", "disease", "result", "bygroup") := .(
          paste0("fatality_", futime),
          outcome,
          numer / denom * 100,
          bygroup
        )
      ]
    } else {
      num = df[,
        .(numer = sum(get(col))),
        by = .(category = get(paste0("cov_cat_", bygroup)))
      ]
      denom = df[,
        .(denom = sum(get(paste0("idenom_num_", outcome))) / 365 / 100000),
        by = .(category = get(paste0("cov_cat_", bygroup)))
      ]
      tmpt = merge(num, denom, by = "category", all = TRUE)
      tmpt[,
        c("metric", "disease", "result", "bygroup") := .(
          "incidence",
          outcome,
          numer / denom,
          bygroup
        )
      ]
    }
    setcolorder(
      tmpt,
      c("metric", "disease", "bygroup", "category", "numer", "denom", "result")
    )
  }
  return(tmpt)
}

# function to calculate metrics by all subgroups
cal_metric_byallg = function(df, col) {
  tmp = unlist(strsplit(col, "_", fixed = TRUE))
  outcome = tmp[length(tmp)]
  if (grepl("^pnumer", col)) {
      num = df[,
        .(numer = sum(get(col))),
        by = .(age = cov_cat_age, sex = cov_cat_sex, 
        region = cov_cat_region, imd = cov_cat_imd, 
        ethnicity = cov_cat_ethnicity, cms = cov_cat_cms)
      ]
      denom = df[,
        .(denom = sum(pdenom_bin_mid)),
        by = .(age = cov_cat_age, sex = cov_cat_sex, 
        region = cov_cat_region, imd = cov_cat_imd, 
        ethnicity = cov_cat_ethnicity, cms = cov_cat_cms)
      ]
      tmpt = merge(num, denom, by = c("age", "sex", "region", "imd",
       "ethnicity", "cms"), all = TRUE)
      tmpt[,
        c("metric", "disease", "result") := .(
          "prevalence",
          outcome,
          numer / denom * 100          
        )
      ]
    } else if (grepl("^fnumer", col)) {
      futime = tmp[3]
      num = df[,
        .(numer = sum(get(col))),
        by = .(age = cov_cat_age, sex = cov_cat_sex, 
        region = cov_cat_region, imd = cov_cat_imd, 
        ethnicity = cov_cat_ethnicity, cms = cov_cat_cms)
      ]
      denom = df[,
        .(denom = sum(get(paste0("inumer_bin_", outcome)))),
        by = .(age = cov_cat_age, sex = cov_cat_sex, 
        region = cov_cat_region, imd = cov_cat_imd, 
        ethnicity = cov_cat_ethnicity, cms = cov_cat_cms)
      ]
      tmpt = merge(num, denom, by = c("age", "sex", "region", "imd",
       "ethnicity", "cms"), all = TRUE)
      tmpt[,
        c("metric", "disease", "result") := .(
          paste0("fatality_", futime),
          outcome,
          numer / denom * 100
        )
      ]
    } else {
      num = df[,
        .(numer = sum(get(col))),
        by = .(age = cov_cat_age, sex = cov_cat_sex, 
        region = cov_cat_region, imd = cov_cat_imd, 
        ethnicity = cov_cat_ethnicity, cms = cov_cat_cms)
      ]
      denom = df[,
        .(denom = sum(get(paste0("idenom_num_", outcome))) / 365 / 100000),
        by = .(age = cov_cat_age, sex = cov_cat_sex, 
        region = cov_cat_region, imd = cov_cat_imd, 
        ethnicity = cov_cat_ethnicity, cms = cov_cat_cms)
      ]
      tmpt = merge(num, denom, by = c("age", "sex", "region", "imd",
       "ethnicity", "cms"), all = TRUE)
      tmpt[,
        c("metric", "disease", "result") := .(
          "incidence",
          outcome,
          numer / denom
        )
      ]
    }
    tmpt[,"year" := as.integer(substr(dataset_name,1,4))]
    tmpt[,"month" := ifelse(as.integer(substr(dataset_name,5,6))
      ==as.integer(substr(dataset_name,14,15)), 
      as.integer(substr(dataset_name,5,6)),
      NA_integer_)]
    setcolorder(
      tmpt,
      c("metric", "disease", "year", "month", "age", "sex", "region", "imd",
       "ethnicity", "cms", "numer", "denom", "result")
    )
}

# Calculate metrics for whole population ----
print('Calculate metrics for whole population')

results = rbindlist(lapply(cols, cal_metric, df = df))

# Calculate metrics for subgroups ----
print('Calculate metrics for subgroups')

for (i in c("age", "sex", "region", "imd", "ethnicity", "cms")) {
  tmp2 = rbindlist(lapply(cols, cal_metric, df = df, bygroup = i))
  results = rbindlist(list(a = results, b = tmp2))
}

# Return results ----
print('Return results')

write.csv(results, paste0("output/calculations/results-", dataset_name, ".csv"), row.names = FALSE)

# Calculate metrics by all subgroups
print('Calculate metrics by all subgroups')

results_byallg = rbindlist(lapply(cols, cal_metric_byallg, df = df))

print('Return results')

write.csv(results_byallg, paste0("output/calculations/results-byallg-", dataset_name, ".csv"), row.names = FALSE)
