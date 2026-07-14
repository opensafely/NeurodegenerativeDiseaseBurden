library(data.table)
library(survival)
library(ggplot2)
library(viridisLite)
library(patchwork)
library(cowplot)

# Define output folder 
print("Define output folder")

fs::dir_create(here::here("output/models/"))
fs::dir_create(here::here("output/figs/"))

# Specify arguments 
print('Specify arguments')

args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 2) {
  dataset_name <- args[[1]]
  start_age <- args[[2]]
} else {
  dataset_name <- '20200101_20231231'
  start_age <- 65
}

# Read dataset-lifetime
print('Read dataset')

df <- fread(paste0("output/dataset_definition/dataset-lifetime-", dataset_name, "_age", start_age,".csv.gz"))

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
get_lifetimerisk <- function(df, outcome, bygroup=NA, dementia_compete = FALSE) {
  if (is.na(bygroup)) {
    if (!dementia_compete) {
      tmp <- df[get(paste0("prev_bin_",outcome))==0,.(entryage,survage = get(paste0("survage_",outcome)),event = get(paste0("event_",outcome)))]
      tmp[, c("survage", "event") := .((survage + .5), factor(event, levels = c("censored", "neuro", "death")))]
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
      out[is.na(lower), c("lower") := 0]
      out[is.na(upper), c("upper") := 0]
      out
    } else {
      if (outcome %in% c("ad", "vd", "osd", "ud")) {
        tmp <- df[get(paste0("prev_bin_",outcome))==0,.(entryage,survage = survage_dementia_compete,event = event_dementia_compete)]
        tmp[, c("survage", "event") := .((survage + .5), factor(event, levels = c("censored", "ad", "vd", "osd", "ud", "death")))]
        fit <- survfit(Surv(time = entryage, time2 = survage, event =  event)~1, data = tmp, time0 = TRUE)
        out <- data.table(
          outcome = outcome,  
          cat = "all",
          group = "all",
          time  = fit$time,
          prob  = fit$pstate[, outcome],
          lower = fit$lower[, outcome],
          upper = fit$upper[, outcome]
        )
        out[is.na(lower), c("lower") := 0]
        out[is.na(upper), c("upper") := 0]
        out
      }
    }
  } else {
    if (!dementia_compete) {
      tmp <- df[get(paste0("prev_bin_",outcome))==0,.(entryage,survage = get(paste0("survage_",outcome)),event = get(paste0("event_",outcome)),group = get(paste0("cov_cat_",bygroup)))]
      tmp[, c("survage", "event") := .((survage + .5), factor(event, levels = c("censored", "neuro", "death")))]
      groups <- tmp[,unique(group)]
      out <- lapply(groups, function(g) {
          tmpg <- tmp[group == g, ]
          fit <- survfit(Surv(time = entryage, time2 = survage, event =  event)~1, data = tmpg, time0 = TRUE)
          outg <- data.table(
            outcome = outcome,
            cat = bygroup,
            group = g,
            time  = fit$time,
            prob  = fit$pstate[, "neuro"],
            lower = fit$lower[, "neuro"],
            upper = fit$upper[, "neuro"]
          )
          outg[is.na(lower), c("lower") := 0]
          outg[is.na(upper), c("upper") := 0]
          outg
    
        })
      rbindlist(out)
    } else {
      if (outcome %in% c("ad", "vd", "osd", "ud")){
        tmp <- df[get(paste0("prev_bin_",outcome))==0,.(entryage, survage = survage_dementia_compete, event = event_dementia_compete,group = get(paste0("cov_cat_",bygroup)))]
        tmp[, c("survage", "event") := .((survage + .5), factor(event, levels = c("censored", "ad", "vd", "osd", "ud", "death")))]
        groups <- tmp[,unique(group)]
        out <- lapply(groups, function(g) {
            tmpg <- tmp[group == g, ]
            fit <- survfit(Surv(time = entryage, time2 = survage, event =  event)~1, data = tmpg, time0 = TRUE)
            outg <- data.table(
              outcome = outcome,
              cat = bygroup,
              group = g,
              time  = fit$time,
              prob  = fit$pstate[, outcome],
              lower = fit$lower[, outcome],
              upper = fit$upper[, outcome]
            )
            outg[is.na(lower), c("lower") := 0]
            outg[is.na(upper), c("upper") := 0]
            outg
      
          })
        rbindlist(out)
        }
      }  
  }
}  

# function to generate lifetime risk plot
makeplot <- function(data, title, ylog = FALSE) {
 ggplot(data,
  aes(x = time, y = prob*100, group = outcome, color = outcome, fill = outcome)) + 
  geom_line(linewidth = 0.5) +
  geom_ribbon(aes(ymin = lower*100, ymax = upper*100), color=NA, alpha = 0.2, show.legend = FALSE) + 
  xlim(as.integer(start_age), 100) +
  scale_color_manual(
      values = colpal,
      drop = FALSE
    ) +
  labs(x = "Age", y = "Cumulative risk (%)", color = "Disease", title = title) +
  theme_bw() +
  theme(legend.position = "None",
        axis.title = element_blank()) +
  if (ylog) scale_y_log10()   
}

# set color for each disease
ds <- c("osd", "ud",  "ad",  "cjd", "pd",  "ftd", "mnd", "psp", "vd",  "hd",  "msa", "cbd",
              "pca", "dlb", "dementia")

colpal <- setNames(
  viridisLite::turbo(length(ds)),
  ds[order(substr(ds,1,1))]

)

print('Lifetime risk for dementia subtypes')
dement = c("osd", "ud", "ad", "vd")
dem_censor <- rbindlist(lapply(c(dement,"dementia"), get_lifetimerisk, df = df))
fwrite(dem_censor, paste0("output/models/tbl_liferisk_all_demcensor_", dataset_name, "_age", start_age, ".csv"))
dem_comp <- rbind(rbindlist(lapply(c(dement), get_lifetimerisk, df = df, dementia_compete=TRUE)),get_lifetimerisk(df=df, outcome="dementia"))
fwrite(dem_comp, paste0("output/models/tbl_liferisk_all_demcomp_", dataset_name, "_age", start_age, ".csv"))

# g_dem_censor <- makeplot(dem_censor, "Whole pop dementia subtypes censored") + theme(legend.position = "right")
# g_dem_compete <- makeplot(dem_comp, "Whole pop dementia subtypes competing adjusted")
# g_dem_all <- (g_dem_censor|g_dem_compete) +
#               plot_layout(guides = 'collect')

# g_life_all_dem <- ggdraw() +
#   theme(
#     plot.background = element_rect(fill = "white", colour = NA)
#   ) +
#   draw_plot(g_dem_all,
#     x = 0.08,
#     y = 0.08,
#     width = 0.92,
#     height = 0.88) +
#   draw_label("Age", x = 0.5, y = 0.05) +
#   draw_label("Cumulative risk (%)",
#              x = 0.05,
#              y = 0.5,
#              angle = 90)
# ggsave(g_life_all_dem, filename = paste0("output/figs/fig_liferisk_all_dem_", dataset_name, "_age", start_age, ".png"),width=12,units='in')
g_dem_censor <- makeplot(dem_censor, "Whole pop dementia subtypes censored") + theme(legend.position = "right", axis.title = element_text(size=10))
ggsave(g_dem_censor, filename = paste0("output/figs/fig_liferisk_all_demcensor_", dataset_name, "_age", start_age, ".png"))
g1_dem_comp <- makeplot(dem_comp, "Whole pop dementia subtypes competing adjusted") +theme(legend.position = "right")
g2_dem_comp <- makeplot(dem_comp, "", TRUE)
g_dem_comp <- (g1_dem_comp|g2_dem_comp) +
              plot_layout(guides = 'collect')

g_dem_comp <- ggdraw() +
  theme(
    plot.background = element_rect(fill = "white", colour = NA)
  ) +
  draw_plot(g_dem_comp,
    x = 0.08,
    y = 0.08,
    width = 0.92,
    height = 0.88) +
  draw_label("Age", x = 0.5, y = 0.05) +
  draw_label("Cumulative risk (%)",
             x = 0.05,
             y = 0.5,
             angle = 90)
ggsave(g_dem_comp, filename = paste0("output/figs/fig_liferisk_all_demcomp_", dataset_name, "_age", start_age, ".png"),width=12,units='in')

print('Lifetime risk for other outcomes')
# Other outcomes ----
outcomes <- c("cjd", "pd",  "ftd", "mnd", "psp", "hd",  "msa", "cbd",
              "pca", "dlb")
liferiskall <- rbindlist(lapply(outcomes, get_lifetimerisk, df = df))
fwrite(liferiskall, paste0("output/models/tbl_liferisk_all_", dataset_name, "_age", start_age, ".csv"))

g_life_all <- makeplot(liferiskall, "Whole pop", TRUE) + theme(legend.position = "right")
# g_life_all <- (g_life_all_linear|g_life_all_log) +
#               plot_layout(guides = 'collect')

# g_life_all <- ggdraw() +
#   theme(
#     plot.background = element_rect(fill = "white", colour = NA)
#   ) +
#   draw_plot(g_life_all,
#     x = 0.08,
#     y = 0.08,
#     width = 0.92,
#     height = 0.88) +
#   draw_label("Age", x = 0.5, y = 0.05) +
#   draw_label("Cumulative risk (%)",
#              x = 0.05,
#              y = 0.5,
#              angle = 90)
ggsave(g_life_all, filename = paste0("output/figs/fig_liferisk_all_", dataset_name, "_age", start_age, ".png"))

print('Lifetime risk by sex')
liferisksex <- rbindlist(lapply(outcomes, get_lifetimerisk, df = df, bygroup = "sex"))
fwrite(liferisksex, paste0("output/models/tbl_liferisk_sex_", dataset_name, "_age", start_age, ".csv"))

# p1_linear <- makeplot(liferisksex[group=='female'], "Female")
p1_log <- makeplot(liferisksex[group=='female'], "Female", TRUE) + theme(legend.position = "right")
# p2_linear <- makeplot(liferisksex[group=='male'], "Male")
p2_log <- makeplot(liferisksex[group=='male'], "Male", TRUE)
g_life_sex <- (p1_log|p2_log)+
          plot_layout(guides = "collect")
g_life_sex <- ggdraw() +
  theme(
    plot.background = element_rect(fill = "white", colour = NA)
  ) +
  draw_plot(g_life_sex,
    x = 0.08,
    y = 0.08,
    width = 0.92,
    height = 0.88) +
  draw_label("Age", x = 0.5, y = 0.05) +
  draw_label("Cumulative risk (%)",
             x = 0.05,
             y = 0.5,
             angle = 90)
ggsave(g_life_sex, filename = paste0("output/figs/fig_liferisk_sex_", dataset_name, "_age", start_age, ".png"),width=12,units='in')

print('Lifetime risk by deprivation')
liferiskimd <- rbindlist(lapply(outcomes, get_lifetimerisk, df = df, bygroup = "imd"))
fwrite(liferiskimd, paste0("output/models/tbl_liferisk_imd_", dataset_name, "_age", start_age, ".csv"))

# p1_linear <- makeplot(liferiskimd[group=='9-10 (least deprived)'], "9-10 (least deprived)") 
p1_log <- makeplot(liferiskimd[group=='9-10 (least deprived)'], "9-10 (least deprived)", TRUE)
# p2_linear <- makeplot(liferiskimd[group=='7-8'], "7-8")
p2_log <- makeplot(liferiskimd[group=='7-8'], "7-8", TRUE)
# p3_linear <- makeplot(liferiskimd[group=='5-6'], "5-6")
p3_log <- makeplot(liferiskimd[group=='5-6'], "5-6", TRUE) + theme(legend.position = "right")
# p4_linear <- makeplot(liferiskimd[group=='3-4'], "3-4")
p4_log <- makeplot(liferiskimd[group=='3-4'], "3-4", TRUE)
# p5_linear <- makeplot(liferiskimd[group=='1-2 (most deprived)'], "1-2 (most deprived)")
p5_log <- makeplot(liferiskimd[group=='1-2 (most deprived)'], "1-2 (most deprived)", TRUE) 
g_life_imd <- (p1_log|p2_log|p3_log)/ (p4_log|p5_log)+
          plot_layout(guides = "collect") 
g_life_imd <- ggdraw() +
  theme(
    plot.background = element_rect(fill = "white", colour = NA)
  ) +
  draw_plot(g_life_imd,
    x = 0.08,
    y = 0.08,
    width = 0.92,
    height = 0.88) +
  draw_label("Age", x = 0.5, y = 0.05) +
  draw_label("Cumulative risk (%)",
             x = 0.05,
             y = 0.5,
             angle = 90)                   
ggsave(g_life_imd, filename = paste0("output/figs/fig_liferisk_imd_", dataset_name, "_age", start_age, ".png"),width=16,units='in')

print('Lifetime risk by ethnicity')
liferisketh <- rbindlist(lapply(outcomes, get_lifetimerisk, df = df, bygroup = "ethnicity"))
fwrite(liferisketh, paste0("output/models/tbl_liferisk_ethnicity_", dataset_name, "_age", start_age, ".csv"))

eths <-  df[cov_cat_ethnicity!='Missing',unique(cov_cat_ethnicity)]
p_eths <- lapply(eths, function(eth) {if (eth != 'White British') makeplot(liferisketh[group==eth], eth, TRUE) else makeplot(liferisketh[group==eth], eth, TRUE)+theme(legend.position = "right")}) 
g_life_eth <- wrap_plots(p_eths, cols=4) +
                plot_layout(guides = "collect") 
g_life_eth <- ggdraw() +
  theme(
    plot.background = element_rect(fill = "white", colour = NA)
  ) +
  draw_plot(g_life_eth,
    x = 0.08,
    y = 0.08,
    width = 0.92,
    height = 0.88) +
  draw_label("Age", x = 0.5, y = 0.05) +
  draw_label("Cumulative risk (%)",
             x = 0.05,
             y = 0.5,
             angle = 90)       
ggsave(g_life_eth, filename = paste0("output/figs/fig_liferisk_ethnicity_", dataset_name, "_age", start_age, ".png"),height=16, width=16, units='in')
