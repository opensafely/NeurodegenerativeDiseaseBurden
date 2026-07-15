library(data.table)
library(ggplot2)
library(viridisLite)
library(patchwork)
library(cowplot)

# Define output folder 
print("Define output folder")

fs::dir_create(here::here("output/coh/"))
fs::dir_create(here::here("output/figs/"))

# Specify arguments 
print('Specify arguments')

args <- commandArgs(trailingOnly = TRUE)

if (length(args) == 1) {
  dataset_name <- args
} else {
  dataset_name <- "20200101_20231231"
}

#characteristics
print("calcualte cohort characteristics")
df <- fread(paste0("output/dataset_definition/dataset-lifetime-", dataset_name, "_age18.csv.gz"))

# Categorize covs ----
print('Categorize covs')
df[,
  "cov_cat_age" := cut(
    entryage,
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

df[, "cov_cat_sex" := factor(cov_cat_sex, levels = c("female", "male", "intersex", "unknown"))]

df[,
  "cov_cat_cms" := cut(
    cov_num_cms,
    breaks = quantile(cov_num_cms, probs = seq(0, 1, 0.25), na.rm = TRUE),
    labels = c("Q1", "Q2", "Q3", "Q4"),
    include.lowest = TRUE
  )
]
df[,
  "cov_cat_imd" := factor(
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

for (i in c("age", "sex", "ethnicity", "imd", "region", "cms")) {
  df[get(paste0("cov_cat_", i)) == "", paste0("cov_cat_", i):= "unknown"]
}

#function to get summary stats for diff outcomes
print("function to get summary stats")
roundmid_any <- function(x, to=6){
  # like round_any, but centers on (integer) midpoint of the rounding points
  ceiling(x/to)*to - (floor(to/2)*(x!=0))
}
get_summary <- function(df, outcome = NA){
  if (is.na(outcome)){
    dat <- copy(df)
  } else {
    dat <- df[get(paste0("prev_bin_",outcome))==0 & get(paste0("event_",outcome))=="neuro"]
  }
  coh <- dat[, .(category = "total", group = "total", n = .N, percent=100)]
  coh[, "n" := roundmid_any(n)]
  for (i in c("age", "sex", "ethnicity", "imd", "region", "cms")) {
    tmp <- dat[,.(category = i, n=.N), by=.(group = get(paste0("cov_cat_",i)))]
    tmp[, "n" := roundmid_any(n)]
    totn <- tmp[, sum(n)]
    tmp[, "percent" := round(n/totn*100,1)]
    coh <- rbind(coh, tmp)
    if (i == "cms") {
      tmp2<- data.table(category=i, 
                        group="median (Q1, Q3)", 
                        n= sprintf(
                        "%.1f (%.1f, %.1f)",
                        dat[, median(cov_num_cms, na.rm = TRUE)],
                        dat[, quantile(cov_num_cms, 0.25, na.rm = TRUE)],
                        dat[, quantile(cov_num_cms, 0.75, na.rm = TRUE)]
                      ),
                      percent = NA_real_
      )
      coh <- rbind(coh, tmp2)
    } 
  } 
  coh[, "disease" := outcome]
  } 

print("get summary stats for whole pop and specific diseases")
coh <- rbindlist(lapply(c(NA, "dementia", "pd", "mnd", "anyneuro"), get_summary, df=df))
fwrite(coh, paste0("output/coh/tbl_round_coh_subgroup_",dataset_name, ".csv"))

#calculate diag source

# function to get percentage record in each data source
print("function to calculate diag source")

get_source <- function(df, outcome, bygroup = NA){
  if (bygroup %in% c("age", "sex", "ethnicity", "imd", "region", "cms")){
    totn <- df[get(paste0("prev_bin_", outcome))==0 & get(paste0("event_", outcome))=="neuro", .N, by=.(group=get(paste0("cov_cat_", bygroup)))]
    n_prim <- df[get(paste0("prev_bin_", outcome))==0 & get(paste0("event_", outcome))=="neuro" & get(paste0("event_",outcome, "_source_primary"))==1, .(n=.N), by=.(group=get(paste0("cov_cat_", bygroup)))]
    n_second <- df[get(paste0("prev_bin_", outcome))==0 & get(paste0("event_", outcome))=="neuro" & get(paste0("event_",outcome, "_source_secondary"))==1, .(n=.N), by=.(group=get(paste0("cov_cat_", bygroup)))]
    n_death <- df[get(paste0("prev_bin_", outcome))==0 & get(paste0("event_", outcome))=="neuro" & get(paste0("event_",outcome, "_source_death"))==1, .(n=.N), by=.(group=get(paste0("cov_cat_", bygroup)))]
    totn[, "N" := roundmid_any(N)]
    n_prim[, "n" := roundmid_any(n)]
    n_second[, "n" := roundmid_any(n)]
    n_death[, "n" := roundmid_any(n)]
    tmp1 <- n_prim[totn, .(disease=outcome, category=bygroup, group, source="primary", percent=round(n/N*100,1)),on="group"]
    tmp2 <- n_second[totn, .(disease=outcome, category=bygroup, group, source="secondary", percent=round(n/N*100,1)),on="group"]
    tmp3 <- n_death[totn, .(disease=outcome, category=bygroup, group, source="death", percent=round(n/N*100,1)),on="group"]
    tmp <- rbind(tmp1, tmp2, tmp3)
    } else{
      totn <- df[get(paste0("prev_bin_", outcome))==0 & get(paste0("event_", outcome))=="neuro", .N]
      n_prim <- df[get(paste0("prev_bin_", outcome))==0 & get(paste0("event_", outcome))=="neuro" & get(paste0("event_",outcome, "_source_primary"))==1, .N]
      n_second <- df[get(paste0("prev_bin_", outcome))==0 & get(paste0("event_", outcome))=="neuro" & get(paste0("event_",outcome, "_source_secondary"))==1, .N]
      n_death <- df[get(paste0("prev_bin_", outcome))==0 & get(paste0("event_", outcome))=="neuro" & get(paste0("event_",outcome, "_source_death"))==1, .N]
      totn <- roundmid_any(totn)
      n_prim <- roundmid_any(n_prim)
      n_second <- roundmid_any(n_second)
      n_death <- roundmid_any(n_death)
      tmp <- data.table(disease=outcome, category="all", group="all", source=c("primary", "secondary", "death"), percent=c(round(n_prim/totn*100,1), round(n_second/totn*100,1), round(n_death/totn*100,1)))
    }
}

print("calculate diag source percentage for all outcome and subgroups")
ds <- c("osd", "ud",  "ad",  "cjd", "pd",  "ftd", "mnd", "psp", "vd",  "hd",  "msa", "cbd",
              "pca", "dlb", "dementia")

cats <- c(NA, "age", "sex", "ethnicity", "imd", "cms")
diag_source<- rbindlist(lapply(ds, function(x) rbindlist(lapply(cats, get_source, df=df, outcome=x), use.names = TRUE)),use.names = TRUE)
fwrite(diag_source, paste0("output/coh/tbl_round_diag_source_",dataset_name, ".csv"))

print("function to plot diag source by disease and subgroup")
makeplot <- function(data, bygroup=NA){
  gen_plot <- function(data, title="Whole pop") {
    ggplot(data, aes(
      x = factor(disease),
      y = percent,
      fill = factor(source, levels=c("primary", "secondary", "death"))
    )) +
    geom_col(position = position_dodge(width = 0.8),
        width = 0.7,
        show.legend = TRUE) +
    labs(x = "Disesae", y = "Pencent", fill = "Data source", title = title) +
    scale_fill_manual(
      values = setNames(viridisLite::viridis(3),
        c("primary", "secondary", "death")
        ),
      drop = FALSE,
      limits = c("primary", "secondary", "death")
      ) +
    scale_y_continuous(
      expand = expansion(mult = c(0, 0.05))
      ) +
    theme_bw() +
    theme(axis.title = element_blank(),
    )
  }
  
  if (is.na(bygroup)) {
    gen_plot(data[group=="all"]) + theme(axis.title = element_text(size=10))
    } else {
        if (bygroup == "sex") 
          groups = c("female", "male", "intersex")
        if (bygroup == "age")
          groups = c(
          "18-39",
          "40-49",
          "50-59",
          "60-69",
          "70-79",
          "80-89",
          "90-99",
          "100-110"
        )
        if (bygroup == "cms")
          groups = c("Q1", "Q2", "Q3", "Q4")
        if (bygroup == "imd")
          groups = c(
          "1-2 (most deprived)",
          "3-4",
          "5-6",
          "7-8",
          "9-10 (least deprived)"
          )
        if (bygroup == "ethnicity")
          groups = c(
          "White British", 
          "White Irish",
          "Other White",
          "White and Caribbean",
          "White and African",
          "White and Asian",
          "Other Mixed",
          "Indian",
          "Pakistani",
          "Bangladeshi",
          "Other Asian",
          "Caribbean",
          "African",
          "Other Black",
          "Chinese",
          "All other ethnic groups"
          )
        ps <- lapply(groups, function(g) gen_plot(data[group==g], g))
        g_source <- wrap_plots(ps, rows=length(groups)%/%2+1) +
                plot_layout(guides = "collect") 
        g_source <- ggdraw() +
          theme(
            plot.background = element_rect(fill = "white", colour = NA)
          ) +
          draw_plot(g_source,
            x = 0.08,
            y = 0.08,
            width = 0.92,
            height = 0.88) +
          draw_label("Disease", x = 0.5, y = 0.05) +
          draw_label("Percent (%)",
                    x = 0.05,
                    y = 0.5,
                    angle = 90)
            }
}
print("plot diag source for whole pop")
g_source_all <- makeplot(diag_source)
ggsave(g_source_all, filename = paste0("output/figs/fig_bar_diagsource_all_", dataset_name, ".png"), width=16, units="in")

print("plot diag source by sex")
g_source_sex <- makeplot(diag_source, bygroup="sex")     
ggsave(g_source_sex, filename = paste0("output/figs/fig_bar_diagsource_sex_", dataset_name, ".png"), width=20, units="in")

print("plot diag source by age")
g_source_sex <- makeplot(diag_source, bygroup="age")     
ggsave(g_source_sex, filename = paste0("output/figs/fig_bar_diagsource_age_", dataset_name, ".png"), width=20, units="in")

print("plot diag source by ethnicity")
g_source_eth <- makeplot(diag_source, bygroup="ethnicity")     
ggsave(g_source_eth, filename = paste0("output/figs/fig_bar_diagsource_ethnicity_", dataset_name, ".png"), width=20, units="in")

print("plot diag source by comorbidity")
g_source_cms <- makeplot(diag_source, bygroup="cms")     
ggsave(g_source_cms, filename = paste0("output/figs/fig_bar_diagsource_cms_", dataset_name, ".png"), width=20, units="in")

print("plot diag source by deprivation")
g_source_imd <- makeplot(diag_source, bygroup="imd")     
ggsave(g_source_imd, filename = paste0("output/figs/fig_bar_diagsource_imd_", dataset_name, ".png"), width=20, units="in")

#diag age boxplot
print("generate boxplot for median and iqr of diag age")
get_diagage <- function(df, outcome, bygroup = NA){
  if (bygroup %in% c("age", "sex", "ethnicity", "imd", "region", "cms")){
    tmp <- df[get(paste0("prev_bin_", outcome))==0 & get(paste0("event_", outcome))=="neuro", .(age=get(paste0("survage_", outcome))
              ),
              by=.(group=get(paste0("cov_cat_", bygroup)))]
    tmp[, c("disease", "category") := .(outcome, bygroup)]
    } else{
      tmp <- df[get(paste0("prev_bin_", outcome))==0 & get(paste0("event_", outcome))=="neuro", .(age=get(paste0("survage_", outcome))
                )
                ]
      tmp[, c("disease", "category", "group") := .(outcome, "all", "all")]
    }
}
diag_age<- rbindlist(lapply(ds, function(x) rbindlist(lapply(cats, get_diagage, df=df, outcome=x), use.names = TRUE)),use.names = TRUE)

print("function to plot diag age")
makeplot2 <- function(data, bygroup=NA){
  gen_plot <- function(data, title="Whole pop") {
    ggplot(data, aes(
      x = factor(disease),
      y = age
    )) +
      geom_boxplot(outlier.shape = NA) +
      labs(x = "Disesae", y = "Age", title = title) +
      theme_bw() +
      theme(axis.title = element_blank(),
      )
  }
  if (is.na(bygroup)) {
    gen_plot(data[group=="all"]) + theme(axis.title = element_text(size=10))
    } else {
        if (bygroup == "sex") 
          groups = c("female", "male", "intersex")
        if (bygroup == "age")
          groups = c(
          "18-39",
          "40-49",
          "50-59",
          "60-69",
          "70-79",
          "80-89",
          "90-99",
          "100-110"
        )
        if (bygroup == "cms")
          groups = c("Q1", "Q2", "Q3", "Q4")
        if (bygroup == "imd")
          groups = c(
          "1-2 (most deprived)",
          "3-4",
          "5-6",
          "7-8",
          "9-10 (least deprived)"
          )
        if (bygroup == "ethnicity")
          groups = c(
          "White British", 
          "White Irish",
          "Other White",
          "White and Caribbean",
          "White and African",
          "White and Asian",
          "Other Mixed",
          "Indian",
          "Pakistani",
          "Bangladeshi",
          "Other Asian",
          "Caribbean",
          "African",
          "Other Black",
          "Chinese",
          "All other ethnic groups"
          )
        ps <- lapply(groups, function(g) gen_plot(data[group==g], g))
        g_source <- wrap_plots(ps, rows=length(groups)%/%2+1) 
        g_source <- ggdraw() +
          theme(
            plot.background = element_rect(fill = "white", colour = NA)
          ) +
          draw_plot(g_source,
            x = 0.08,
            y = 0.08,
            width = 0.92,
            height = 0.88) +
          draw_label("Disease", x = 0.5, y = 0.05) +
          draw_label("Age",
                    x = 0.05,
                    y = 0.5,
                    angle = 90)
            }
}

print("plot diag age for whole pop")
g_diagage_all <- makeplot2(diag_age)
ggsave(g_diagage_all, filename = paste0("output/figs/fig_box_diagage_all_", dataset_name, ".png"), width=16, units="in")

print("plot diag age by sex")
g_diagage_sex <- makeplot2(diag_age, bygroup="sex")     
ggsave(g_diagage_sex, filename = paste0("output/figs/fig_box_diagage_sex_", dataset_name, ".png"), width=20, units="in")

