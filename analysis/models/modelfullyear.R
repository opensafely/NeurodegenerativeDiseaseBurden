library(data.table)
library(ggplot2)
library(viridisLite)
library(patchwork)

# Define output folder 
print("Define output folder")

fs::dir_create(here::here("output/models/"))
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
  yend <- 2023
}

# Read dataset
print('Read dataset')
df <- data.table()
for (i in ystart:yend){
  dataset_name <- paste0(i,"0101_",i,"1231")
  df <- rbind(df, fread(file = paste0(
  "output/calculations/results-byallg-", dataset_name, ".csv"))
  )
}

# Add label for empty subgoup
df[, c("sex", "region") := .(
  fifelse(!is.na(sex) & sex != "", sex, "unknown"),
  fifelse(!is.na(region) & region != "", region, "unknown")
  )
]

# Set cov ref level
df[,c("year", "age", "sex", "region", "imd", "ethnicity", "cms") := .(
  relevel(as.factor(year), ref = as.character(max(year))),
  relevel(as.factor(age), ref = "40-49"), 
  relevel(as.factor(sex), ref = "male"), 
  relevel(as.factor(region), ref = "London"), 
  relevel(as.factor(imd), ref = "9-10 (least deprived)"), 
  relevel(as.factor(ethnicity), ref = "White British"),
  relevel(as.factor(cms), ref = "Q1")
  )]

# Add offset term
df[, logdenom := log(denom)]  

# Remove zeros
df <- df[!(numer==0 | denom==0)]

# Function to fit model and extract coefficients and predictions
fitfullmodel <- function(df, out_arg, metric_arg){
  data = df[disease == out_arg & metric == metric_arg]
  
  tryCatch({
      #fit model
      fit <- glm(numer ~
      year + age + sex + region + imd + ethnicity + cms, 
        offset = logdenom, data = data, family = quasipoisson(link = "log")
        )
      #get model coef
      coefs <- summary(fit)$coefficients
      dt <- as.data.table(coefs, keep.rownames = "term")
      setnames(dt, c("Estimate", "Std. Error", "t value", "Pr(>|t|)"),
                    c("estimate", "std_error", "statistic", "p_value"))
      
      #get response for different cov comb
      vars <- c("year", "age", "sex", "region", "imd", "ethnicity", "cms")

      # get levels actually retained in model frame
      mf <- model.frame(fit)

      # ref level of each factor
      ref <- lapply(mf[vars], function(x) {
        levels(x)[1] 
      })
      ref <- as.data.frame(ref)

      # generate predictions
      pred_dt <- do.call(
        rbind,
        lapply(vars, function(v) {
          x <- mf[[v]]
          levs <- levels(x)
          do.call(
            rbind,
            lapply(levs, function(z) {
              tmp <- ref
              tmp[[v]] <- z
              tmp[['logdenom']] <- 0
              data.frame(category = v, term = paste0(v, z), pred = predict(fit, newdata = tmp, type = "response"))
            })
          )
        })
      )
      rownames(pred_dt) <- NULL
      
      #combine results
      dt2 <- merge(dt, pred_dt, by = "term", all = TRUE)
      dt2[, c("disease", "metric", "error") := .(out_arg, metric_arg, NA_character_)]
      setcolorder(dt2, c("disease", "metric", "category", "term", "estimate", "std_error", "statistic", "p_value", "pred", "error"))
      dt2
    },
    #get error message if model fails 
    error = function(e) {
      data.table(
        disease = out_arg,
        metric = metric_arg,
        category = NA_character_,
        term = NA_character_,
        estimate = NA_real_,
        std_error = NA_real_,
        statistic = NA_real_,
        p_value = NA_real_,
        pred = NA_real_,
        error = e$message
      )
    }) 
}

# Fit models for all outcomes and metrics
outcomes <- c("osd", "ud",  "ad",  "cjd", "pd",  "ftd", "mnd", "psp", "vd",  "hd",  "msa", "cbd",
              "pca", "dlb")

metrics <- c("prevalence", "incidence", "fatality_1y", "fatality_5y")

modelresults <- rbindlist(lapply(outcomes, function(o) {
  rbindlist(lapply(metrics, function(m) {
    fitfullmodel(df = df, out_arg = o, metric_arg = m)
  }))
}))

modelresults[, c("irr", "lcl", "hcl") := .(exp(estimate), exp(estimate - 1.96 *std_error), exp(estimate + 1.96 *std_error))]

# Save results
fwrite(modelresults, file = paste0("output/models/tbl_modelfull_year_", ystart, "_", yend, ".csv"))

# Extract prediction results for age, sex, cms, deprivation
print("Extract preds for age sex cms deprivation")

results <- modelresults[!is.na(term) & !term %in% c("(Intercept)", "sexunknown", "imdunknown") & !grepl('^(year|ethnicity|region).*', term)]

lvls <- c("age18-39", "age40-49", "age50-59", "age60-69", "age70-79", "age80-89", "age90-99", "age100-110", 
  "sexfemale", "sexmale", "sexintersex", "imd9-10 (least deprived)", "imd7-8", "imd5-6", "imd3-4", 
  "imd1-2 (most deprived)", "cmsQ1", "cmsQ2", "cmsQ3", "cmsQ4")

results[,group := paste0(disease,metric,category)]

results[, lab := factor(term, levels = lvls,labels = sub('^(age|cms|imd|sex)', '', lvls))]

results[metric %in% c('prevalence', 'fatality_1y', 'fatality_5y'), pred := pred * 100]

# Generate plots for preds and relative estimates for age, sex, imd and cms
# set color for each disease
colpal <- setNames(
  viridisLite::turbo(length(outcomes)),
  outcomes[order(substr(outcomes,1,1))]
)

#Plot for preds
print("Generate plot for preds")
makesubplot <- function(data, label){
ggplot(data,
       aes(
         x = lab,
         y = pred,
         colour = disease,
         group = group
       )
) +
  geom_line(linewidth = .8, show.legend=TRUE) +
  geom_point(size = 1, show.legend=FALSE) +
  scale_color_manual(
    values = colpal,
    drop = FALSE,
    limits = names(colpal)
    ) +
  labs(
    x = NULL,
    y = label,
    colour = "Disease"
  ) +
  theme_bw() +
  theme(
    axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1),
    panel.border = element_blank(),
    axis.line.y = element_line(),
    panel.grid.major = element_blank()
    
  ) +
  annotate(
    "segment",
    x = 0, xend = 8,
    y = 0, yend = 0,
    linewidth = 1
  ) +
  annotate(
    "segment",
    x = 9, xend = 11,
    y = 0, yend = 0,
    linewidth = 1
  )+
  annotate(
    "segment",
    x = 12, xend = 16,
    y = 0, yend = 0,
    linewidth = 1
  )+
  annotate(
    "segment",
    x = 17, xend = 20,
    y = 0, yend = 0,
    linewidth = 1
  ) +
  scale_y_continuous(expand = expansion(mult = c(0,0.02)))
}


#Generate subplots

p1 <-  makesubplot(results[metric=='prevalence'],'Percentage (%)')
p2 <-  makesubplot(results[metric=='incidence'],'Events per 100,000 person-years')
p3 <-  makesubplot(results[metric=='fatality_1y'],'Fatality percentage (%)')

g_pred <- (p1 | p2| p3) +
  plot_layout(guides = 'collect')

ggsave(g_pred, filename = paste0("output/figs/fig_preds_modelfull_year_", ystart, "_", yend, ".png"), width = 16, units = "in")

# Forest plot for relative estiamtes
print("Generate forest plot for relative estimates")
results2 = results[metric!='fatality_5y']
results2[,lab:= factor(lab, levels = rev(levels(lab)))]
results2[,metric := factor(metric,levels = c('prevalence', 'incidence', 'fatality_1y'))]
g_forest <- ggplot(results2, aes(
  x = irr,
  y = lab,
  color = disease
)) +
  geom_vline(xintercept = 1, linetype = "dashed") +
  geom_point(position = position_dodge(width = 0.5), show.legend = FALSE) +
  geom_errorbar(
    aes(xmin = lcl, xmax = hcl),
    position = position_dodge(width = 0.5),
    orientation = 'y',
    show.legend = TRUE
  ) +
  scale_color_manual(
    values = colpal,
    drop = FALSE,
    limits = names(colpal)
    ) +
  labs(x = NULL, y = NULL, color = 'Disease') +
  facet_wrap(~metric, labeller = as_labeller(
    c(prevalence = 'Prevalence', incidence = 'Incidence', fatality_1y = 'Fatality')
  )) +
  scale_x_log10() +
  theme_bw()
ggsave(g_forest, filename = paste0("output/figs/fig_forest_modelfull_year_", ystart, "_", yend, ".png"), width = 10, units = "in")

# Heatmap for ethnicity
print("Curate modelling results for ethnicity")
results3 <- modelresults[category == "ethnicity" & metric!='fatality_5y' &term!="ethnicityMissing"]
results3[,group := paste0(disease,metric)]
results3 <- results3[results3[term=="ethnicityWhite British",unique(group)],on="group"]
results3 <- results3[term!="ethnicityWhite British"]
results3 <- results3[!is.na(estimate)&!is.na(p_value)]
results3[, "lab" := sub("^ethnicity", "", term)]
lvls <- c(         
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
lvls <- lvls[order(substr(lvls,1,1))]
results3[, "lab" := factor(lab ,levels = lvls)]

print("Function to gen heatmap for ethnicity")
makeplot2 <- function(data) {
  gen_plot <- function(data, title){
    brks <- exp(seq(min(data$estimate, na.rm = TRUE), max(data$estimate, na.rm = TRUE), length.out = 5))
    brks2 <- seq(min(data$p_value, na.rm = TRUE), max(data$p_value, na.rm = TRUE), length.out =3)
    brks2 <- sort(unique(c(
      brks2,
      0.05
    )))
    ggplot(data, aes(disease, lab)) +
      geom_tile(aes(fill = estimate), colour = "white") +
      geom_point(aes(size = p_value), shape = 21, fill = "black") +
      scale_fill_gradient2(
        low = "#2166AC",
        mid = "white",
        high = "#B2182B",
        midpoint = 0,
        breaks = log(brks),
        labels = signif(brks, 2),
        name = "Ratio relative to\nWhite British"
      ) +
      scale_size_continuous(
        range = c(1, 7), 
        name = "P value", 
        trans = "reverse",
        breaks = brks2,
        labels = signif(brks2, 2)
      ) +
      coord_equal() +
      labs(title = title) +
      theme_minimal() +
      theme(
        legend.position = "top",
        legend.box = "vertical",
        panel.grid = element_blank(),
        axis.title = element_blank()
      ) +
      guides(
        fill = guide_colourbar(order = 1),
        size = guide_legend(order = 2)
    ) 
  }
  data <- copy(data)
  p1 <- gen_plot(data[metric=="prevalence"], "Prevalence")
  p2 <- gen_plot(data[metric == "incidence"], "Incidence")
  p3 <- gen_plot(data[metric == "fatality_1y"], "1-year fatality")
  g_heat <- (p1 | p2 | p3) 
  ggsave(g_heat, filename = paste0("output/figs/fig_heat_ethnicity_", ystart, "_", yend, ".png"), width=16, units="in")
}

print("Generate heat maps for ethnicity")
makeplot2(results3)

