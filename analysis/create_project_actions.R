# Load libraries ----

library(tidyverse)
library(yaml)
library(here)
library(glue)
library(readr)
library(dplyr)

# Define time frame

ystart <- 2020
yend <- 2023

# Source functions ----

source("analysis/fn-define_dates.R")

# Specify defaults ----

defaults_list <- list(
  version = "4.0"
)

# Create generic action function ----

action <- function(
  name,
  run,
  dummy_data_file = NULL,
  arguments = NULL,
  needs = NULL,
  highly_sensitive = NULL,
  moderately_sensitive = NULL
) {
  outputs <- list(
    moderately_sensitive = moderately_sensitive,
    highly_sensitive = highly_sensitive
  )
  outputs[sapply(outputs, is.null)] <- NULL

  actions <- list(
    run = paste(c(run, arguments), collapse = " "),
    dummy_data_file = dummy_data_file,
    needs = needs,
    outputs = outputs
  )
  actions[sapply(actions, is.null)] <- NULL

  action_list <- list(name = actions)
  names(action_list) <- name

  action_list
}

# Create generic comment function ----

comment <- function(...) {
  list_comments <- list(...)
  comments <- map(list_comments, ~ paste0("## ", ., " ##"))
  comments
}

# Create function to convert comment "actions" in a yaml string into proper comments ----

convert_comment_actions <- function(yaml.txt) {
  yaml.txt %>%
    str_replace_all("\\\n(\\s*)\\'\\'\\:(\\s*)\\'", "\n\\1") %>%
    #str_replace_all("\\\n(\\s*)\\'", "\n\\1") %>%
    str_replace_all("([^\\'])\\\n(\\s*)\\#\\#", "\\1\n\n\\2\\#\\#") %>%
    str_replace_all("\\#\\#\\'\\\n", "\n")
}

# Create function to generate study population ----

generate_dataset <- function(start_date, end_date, dataset_name) {
  splice(
    comment(glue("Generate dataset-{dataset_name}")),
    action(
      name = glue("generate_dataset-{dataset_name}"),
      run = glue(
        "ehrql:v1 generate-dataset analysis/dataset_definition/dataset_definition.py --output output/dataset_definition/dataset-{dataset_name}.csv.gz -- --start_date {start_date} --end_date {end_date}"
      ),
      highly_sensitive = list(
        dataset = glue(
          "output/dataset_definition/dataset-{dataset_name}.csv.gz"
        )
      )
    )
  )
}

# Create function to perform calculations ----

perform_calculations <- function(dataset_name) {
  splice(
    comment(glue("Perform calculations for dataset-{dataset_name}")),
    action(
      name = glue("calculations-{dataset_name}"),
      run = glue(
        "r:v2 analysis/calculations/calculation.R"
      ),
      arguments = list(glue("{dataset_name}")),
      needs = list(glue("generate_dataset-{dataset_name}")),
      moderately_sensitive = list(
        results = glue(
          "output/calculations/results-{dataset_name}.csv"
        ),
        results_byallg = glue(
          "output/calculations/results-byallg-{dataset_name}.csv"
        )
      )
    )
  )
}

# Create function to fit models ----

fit_models <- function(start_year=ystart, end_year=yend) {
  splice(
    comment("Fit models using yearly calculation results"),
    action(
      name = "model-full-year",
      run = glue(
        "r:v2 analysis/models/modelfullyear.R"
      ),
      arguments = list(paste0(start_year, "_", end_year)),
      needs = lapply(start_year:end_year, function(i) glue("calculations-{i}0101_{i}1231")),
      moderately_sensitive = list(
        modelresults = glue(
          "output/models/modelfull_year{start_year}_{end_year}.csv"
        )
      )
    )
  )
}

# Create function to plot monthly results ----

plot_results <- function(start_year=ystart, end_year=yend) {
  dates_month <- define_dates(start_year, end_year, year = FALSE)
  splice(
    comment("Plot monthly results"),
    action(
      name = "plot-month",
      run = glue(
        "r:v2 analysis/plots/plotmonth.R"
      ),
      arguments = list(paste0(start_year, "_", end_year)),
      needs = lapply(dates_month$dataset_name, function(i) glue("calculations-{i}")),
      moderately_sensitive = list(
        g_round = glue(
          "output/figs/fig_round_month_{start_year}_{end_year}.png"
        ),
        g_raw = glue(
          "output/figs/fig_raw_month_{start_year}_{end_year}.png"
        ),
        rounded_month = glue(
          "output/figs/tbl_round_month_{start_year}_{end_year}.csv"
        )
      )
    )
  )
}

# Create function to convert comment "actions" in a yaml string into proper comments ----

convert_comment_actions <- function(yaml.txt) {
  yaml.txt %>%
    str_replace_all("\\\n(\\s*)\\'\\'\\:(\\s*)\\'", "\n\\1") %>%
    #str_replace_all("\\\n(\\s*)\\'", "\n\\1") %>%
    str_replace_all("([^\\'])\\\n(\\s*)\\#\\#", "\\1\n\n\\2\\#\\#") %>%
    str_replace_all("\\#\\#\\'\\\n", "\n")
}


# Define dates ----

dates <- define_dates(start_year = ystart, end_year = yend)

# Make actions list ----

actions_list <- splice(
  ## Post YAML disclaimer ----

  comment(
    "# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #",
    "DO NOT EDIT project.yaml DIRECTLY",
    "This file is created by create_project_actions.R",
    "Edit and run create_project_actions.R to update the project.yaml",
    "# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #"
  ),

  ## Generate datasets ----

  splice(
    unlist(
      lapply(
        1:nrow(dates),
        function(x) {
          generate_dataset(
            start_date = dates[x, ]$start_date,
            end_date = dates[x, ]$end_date,
            dataset_name = dates[x, ]$dataset_name
          )
        }
      ),
      recursive = FALSE
    )
  ),

  ## Perform calculations ----

  splice(
    unlist(
      lapply(
        1:nrow(dates),
        function(x) {
          perform_calculations(
            dataset_name = dates[x, ]$dataset_name
          )
        }
      ),
      recursive = FALSE
    )
  ),

  ## Fit models ----
  splice(
    fit_models()
  ),

  ## Plot results ----
  splice(
    plot_results()
   )
)

# Combine actions into project list ----

project_list <- splice(
  defaults_list,
  list(actions = actions_list)
)

# Convert list to yaml, reformat, and output a .yaml file ----

as.yaml(project_list, indent = 2) %>%
  # convert comment actions to comments
  convert_comment_actions() %>%
  # add one blank line before level 1 and level 2 keys
  str_replace_all("\\\n(\\w)", "\n\n\\1") %>%
  str_replace_all("\\\n\\s\\s(\\w)", "\n\n  \\1") %>%
  writeLines("project.yaml")

# Return number of actions ----

count_run_elements <- function(x) {
  if (!is.list(x)) {
    return(0)
  }

  # Check if any names of this list are "run"
  current_count <- sum(names(x) == "run", na.rm = TRUE)

  # Recursively check all elements in the list
  return(current_count + sum(sapply(x, count_run_elements)))
}

print(paste0(
  "YAML created with ",
  count_run_elements(actions_list),
  " actions."
))
