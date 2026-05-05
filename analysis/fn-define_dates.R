define_dates <- function(start_year = 2020, end_year = 2023, year =  TRUE) {
  # Monthly ranges
  month_start <- seq.Date(
    from = as.Date(sprintf("%d-01-01", start_year)),
    to = as.Date(sprintf("%d-12-01", end_year)),
    by = "month"
  )

  month_end <- seq.Date(
    from = as.Date(sprintf("%d-02-01", start_year)),
    to = as.Date(sprintf("%d-01-01", end_year + 1)),
    by = "month"
  ) -
    1

  if (year) {
    # Yearly ranges
    year_start <- as.Date(sprintf("%d-01-01", start_year:end_year))
    year_end <- as.Date(sprintf("%d-12-31", start_year:end_year))

    # Make data frame
    dates <- data.frame(
    start_date = c(year_start, month_start),
    end_date = c(year_end, month_end)
  )
  } else {
    dates <- data.frame(
    start_date = month_start,
    end_date = month_end
  )
  }

  # Add dataset name
  dates$dataset_name <- paste0(
    format(dates$start_date, "%Y%m%d"),
    "_",
    format(dates$end_date, "%Y%m%d")
  )

  return(dates)
}
