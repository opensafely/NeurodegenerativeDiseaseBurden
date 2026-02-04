from ehrql import create_dataset
from ehrql.tables.tpp import (patients)
from codelists import *
from generate_variables import generate_variables

dataset = create_dataset()

dataset.configure_dummy_data(population_size=10000)

start_date = "2022-01-01"
end_date = "2022-12-31"

dataset.define_population(patients.exists_for_patient())

dataset = generate_variables(dataset,start_date,end_date)