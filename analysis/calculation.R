library(argparse)
library(data.table)

parser <- ArgumentParser()

# Add arguments
parser$add_argument("--start_date", required = TRUE)
parser$add_argument("--end_date", required = TRUE)

# Parse arguments
args <- parser$parse_args()
start_date = gsub("-", "", args$start_date)
end_date = gsub("-", "", args$end_date)

# Read dataset
df = fread(paste0("output/dataset_definition/dataset-", start_date, "_", end_date, ".csv.gz"))

# Categorize covs
df[, cov_cat_age := cut(cov_num_age, breaks = c(17, 39, 49, 59, 69, 79, 89, 99, 110),
  labels = c("18-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90-99", "100-110"))]
df[, cov_cat_cms := cut(cov_num_cms, breaks = quantile(cov_num_cms, probs = seq(0, 1, 0.25),
  na.rm = TRUE), labels = c("Q1", "Q2", "Q3", "Q4"), include.lowest = TRUE)]
df[, cov_cat_imd := factor(cov_cat_imd, labels = c(
  "1-2 (most deprived)", "9-10 (least deprived)", "1-2 (most deprived)",
  "3-4", "3-4", "5-6", "5-6", "7-8", "7-8", "9-10 (least deprived)",
  "unknown"))]

# Get column names
cols = grep("(p|i|f)numer", colnames(df), value = TRUE)

# Define function to calculate inci, prev, fatality in the whole population or
# by subgroups of age, sex, region, imd, ethnicity, cms
cal_metric = function(df, col, bygroup = NA)
{tmp = unlist(strsplit(col, "_", fixed = TRUE))
 outcome = tmp[length(tmp)]
 if (is.na(bygroup))
  {if (grepl("^pnumer", col))
    {num = df[, sum(get(col))]
     denom = df[, sum(pdenom_bin_mid)]
     tmpt = data.table(metric = "prevalence", disease = outcome, numer = num, denom = denom, result = num / denom * 100)
    } else if (grepl("^fnumer", col))
        {futime = tmp[3]
         num = df[, sum(get(col))]
         denom = df[, sum(get(paste0("inumer_bin_", outcome)))]
         tmpt = data.table(metric = paste0("fatality_", futime), disease = outcome, numer = num, denom = denom, result = num / denom * 100)
        } else {num = df[, sum(get(col))]
                denom = df[, sum(get(paste0("idenom_num_", outcome))) / 365 / 100000]
                tmpt = data.table(metric = "incidence", disease = outcome, numer = num, denom = denom, result = num / denom)
               }
   tmpt[, c("bygroup", "category") := .("all", "all")]
   setcolorder(tmpt, c("metric", "disease", "bygroup", "category", "numer", "denom", "result"))
  } else
      {if (grepl("^pnumer", col))
        {num = df[, .(numer = sum(get(col))), by = .(category = get(paste0("cov_cat_", bygroup)))]
         denom = df[, .(denom = sum(pdenom_bin_mid)), by = .(category = get(paste0("cov_cat_", bygroup)))]
         tmpt = merge(num, denom, by = "category", all = TRUE)
         tmpt[, c("metric", "disease", "result", "bygroup") := .("prevalence", outcome, numer / denom * 100, bygroup)]
        } else if (grepl("^fnumer", col))
            {futime = tmp[3]
             num = df[, .(numer = sum(get(col))), by = .(category = get(paste0("cov_cat_", bygroup)))]
             denom = df[, .(denom = sum(get(paste0("inumer_bin_", outcome)))), by = .(category = get(paste0("cov_cat_", bygroup)))]
             tmpt = merge(num, denom, by = "category", all = TRUE)
             tmpt[, c("metric", "disease", "result", "bygroup") := .(paste0("fatality_", futime), outcome, numer / denom * 100, bygroup)]
            } else
                {num = df[, .(numer = sum(get(col))), by = .(category = get(paste0("cov_cat_", bygroup)))]
                 denom = df[, .(denom = sum(get(paste0("idenom_num_", outcome))) / 365 / 100000), by = .(category = get(paste0("cov_cat_", bygroup)))]
                 tmpt = merge(num, denom, by = "category", all = TRUE)
                 tmpt[, c("metric", "disease", "result", "bygroup") := .("incidence", outcome, numer / denom, bygroup)]
                }
       setcolorder(tmpt, c("metric", "disease", "bygroup", "category", "numer", "denom", "result"))
      }
 return(tmpt)
}

# Calculate metrics for whole population
results = rbindlist(lapply(cols, cal_metric, df = df))

# Calculate metrics for subgroups
for (i in c("age", "sex", "region", "imd", "ethnicity", "cms"))
  {tmp2 = rbindlist(lapply(cols, cal_metric, df = df, bygroup = i))
  results = rbindlist(list(a = results, b = tmp2))
  }

# Return results
results
