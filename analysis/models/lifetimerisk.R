library(data.table)
library(survival)
library(ggplot2)
library(viridis)

# Define output folder 
print("Define output folder")

fs::dir_create(here::here("output/models/"))
fs::dir_create(here::here("output/figs/"))

# Specify arguments 
print('Specify arguments')

args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0) {
  dataset_name <- '20200101_20231231'
} else {
  dataset_name <- args[[1]]
}

# Read dataset-lifetime
print('Read dataset')

df <- fread(paste0("output/dataset_definition/dataset-lifetime-", dataset_name, ".csv.gz"))

# Categorize covs ----
print('Categorize covs')

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

## Define function to calculate lifetime risk 
get_lifetimerisk <- function(df, outcome, bygroup=NA) {
  if (is.na(bygroup)) {
    tmp <- df[get(paste0("prev_bin_",outcome))==0,.(entryage,survage = get(paste0("survage_",outcome)),event = get(paste0("event_",outcome)))]
    tmp[, c("survage", "event") := .((survage +1), factor(event, levels = c("censored", "neuro", "death")))]
    fit <- survfit(Surv(time = entryage, time2 = survage, event =  event)~1, data = tmp, time0 = TRUE)
    out <- data.table(
      outcome = outcome,  
      cat = "all",
      group = "all",
      time  = fit$time,
      prob  = fit$pstate[, "neuro"],
      lower = fit$lower[, "neuro"],
      upper = fit$upper[, "neuro"]
      
    )
    out
  } else {
    tmp <- df[get(paste0("prev_bin_",outcome))==0,.(entryage,survage = get(paste0("survage_",outcome)),event = get(paste0("event_",outcome)),group = get(paste0("cov_cat_",bygroup)))]
    tmp[, c("survage", "event") := .((survage +1), factor(event, levels = c("censored", "neuro", "death")))]
    groups <- tmp[,unique(group)]
    out <- lapply(groups, function(g) {
        tmpg <- tmp[group == g, ]
        fit <- survfit(Surv(time = entryage, time2 = survage, event =  event)~1, data = tmpg, time0 = TRUE)
        data.table(
          outcome = outcome,
          cat = bygroup,
          group = g,
          time  = fit$time,
          prob  = fit$pstate[, "neuro"],
          lower = fit$lower[, "neuro"],
          upper = fit$upper[, "neuro"]
        )
    })
    rbindlist(out)
  }
  
}  

# Fit model for all outcomes and subgroups ----
outcomes <- c("osd", "ud",  "ad",  "cjd", "pd",  "ftd", "mnd", "psp", "vd",  "hd",  "msa", "cbd",
              "pca", "dlb")

print('Fit model for whole pop')

liferisk_all <- rbindlist(lapply(outcomes, get_lifetimerisk, df = df))

print('Fit model for subgroups')

bygroups <- c("sex", "region", "imd", "ethnicity", "cms")
liferisk_subgroup <- rbindlist(lapply(bygroups, function(x) {rbindlist(lapply(outcomes, get_lifetimerisk, df = df, bygroup = x))}))

liferisks <- rbind(liferisk_all, liferisk_subgroup)

print('Return results')
fwrite(liferisks, paste0("output/models/lifetimerisk_", dataset_name, ".csv"))

print('Plot lifetime risk for whole population')
g_life = ggplot(liferisks[cat == "all"],
  aes(x = time, y = prob, group = outcome, color = outcome, fill = outcome)) + 
  geom_line() + 
  geom_ribbon(aes(ymin = lower, ymax = upper), color=NA, alpha = 0.2, show.legend = FALSE) + 
  scale_color_viridis_d(option = "turbo") +
  labs(x = "Age", y = "Lifetime risk", color = "Disease") +
  theme_bw() +
  theme(legend.position = "right")
ggsave(g_life, filename = paste0("output/figs/fig_lifetimerisk_all_", dataset_name, ".png"))
