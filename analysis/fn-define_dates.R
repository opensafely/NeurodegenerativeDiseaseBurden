define_dates <- function(start_year = 2020, end_year = 2023) {
  # Yearly ranges
  year_start <- as.Date(sprintf("%d-01-01", start_year:end_year))
  year_end <- as.Date(sprintf("%d-12-31", start_year:end_year))

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

  # Make data frame
  dates <- data.frame(
    start_date = c(year_start, month_start),
    end_date = c(year_end, month_end)
  )

  # Format as YYYYMMDD
  dates$start_date <- format(dates$start_date, "%Y%m%d")
  dates$end_date <- format(dates$end_date, "%Y%m%d")

  return(dates)
}
