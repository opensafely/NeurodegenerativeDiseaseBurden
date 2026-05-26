from ehrql import create_dataset, get_parameter, minimum_of, maximum_of, case, when, years
from ehrql.tables.tpp import (
    patients,
    ons_deaths,
    practice_registrations,
    addresses,
)
from codelists import *
from variable_helper_functions import (
    get_cms_on_date,
    get_latest_ethnicity,
    first_matching_tpp_between,
    first_matching_apc_between,
    first_matching_death_between,
    prevalent_tpp,
    prevalent_apc,
)

# Create dataset
dataset = create_dataset()

# Configure dummy data
dataset.configure_dummy_data(population_size=5000)

# Specify start, end and index date
start_date = get_parameter(name="start_date")
index_date = maximum_of(patients.date_of_birth + years(65), start_date)
end_date = get_parameter(name="end_date")
death_date = minimum_of(patients.date_of_death, ons_deaths.date)
pat_end_date = minimum_of(end_date, death_date, practice_registrations.for_patient_on(index_date).end_date) 

## Entry age
dataset.entryage = case(
    when(index_date <= start_date).then(patients.age_on(start_date)),
    when((index_date > start_date)
         & (index_date <= pat_end_date)).then(65)
)

## Sex
dataset.cov_cat_sex = patients.sex

## Region
dataset.cov_cat_region = practice_registrations.for_patient_on(index_date).practice_nuts1_region_name

## IMD and MSOA
patient_address = addresses.for_patient_on(index_date)
dataset.cov_cat_imd = patient_address.imd_decile
dataset.cov_cat_msoa = patient_address.msoa_code

## Ethnicity
dataset.cov_cat_ethnicity = get_latest_ethnicity(
    index_date, ethnicity_codelist, grouping=16
)

## Cambridge Multimorbidity Score (CMS)
dataset.cov_num_cms = get_cms_on_date(index_date, death_date, return_components=False)


# Outcomes
olists = {
    "osd": {"snomed": specified_dementia_snomed, "icd": specified_dementia_icd},
    "ud": {"snomed": unspecified_dementia_snomed, "icd": unspecified_dementia_icd},
    "ad": {"snomed": alzheimers_snomed, "icd": alzheimers_icd},
    "cjd": {"snomed": cjd_snomed, "icd": cjd_icd},
    "pd": {"snomed": parkinsons_snomed, "icd": parkinsons_icd},
    "ftd": {"snomed": frontotemporal_snomed, "icd": frontotemporal_icd},
    "mnd": {"snomed": motor_snomed, "icd": motor_icd},
    "psp": {"snomed": palsy_snomed, "icd": palsy_icd},
    "vd": {"snomed": vascular_snomed, "icd": vascular_icd},
    "hd": {"snomed": huntingtons_snomed, "icd": huntingtons_icd},
    "msa": {"snomed": multiatrophy_snomed, "icd": multiatrophy_icd},
    "cbd": {"snomed": corticobasal_snomed},
    "pca": {"snomed": postcortical_snomed},
    "dlb": {"snomed": lewybody_snomed},
}

for name, codes in olists.items():

    incident = []
    prevalent_start = []

    if "snomed" in codes:
        ## Primary care
        ### First record in year
        incident.append(
            first_matching_tpp_between(codes["snomed"], index_date, end_date, death_date)
        )
        ### Identify prevalent cases
        prevalent_start.append(
            prevalent_tpp(codes["snomed"], index_date, death_date)
        )


    if "icd" in codes:
        ## Secondary care
        ### First record in year
        incident.append(
            first_matching_apc_between(codes["icd"], index_date, end_date, death_date, only_prim_diagnoses=False)
        )
        ### Identify prevalent cases
        prevalent_start.append(
            prevalent_apc(codes["icd"], index_date, death_date)
        )

        ## Death
        ### First record in year
        incident.append(
            first_matching_death_between(codes["icd"], index_date, end_date, death_date)
        )

    # Prevalance at start 
    if len(prevalent_start) == 1:
        tmp_pnumer_bin_start = prevalent_start[0]
    elif len(prevalent_start) > 1:
        tmp_pnumer_bin_start = maximum_of(*prevalent_start)

    setattr(
        dataset,
        f"prev_bin_{name}",
        tmp_pnumer_bin_start
    )
    
    # Event: censored, neuro, death
    if len(incident) == 1:
        tmp_incident_date = incident[0]
    elif len(incident) > 1:
        tmp_incident_date  = minimum_of(*incident)

    setattr(
        dataset,
        f"event_{name}",
        case(
            when(practice_registrations.exists_for_patient_on(tmp_incident_date)).then("neuro"),
            when(practice_registrations.exists_for_patient_on(death_date)).then("death"),
            otherwise="censored",
        )
    )

    # Survage
    tmp_idenom_num = minimum_of(pat_end_date, tmp_incident_date)
    setattr(
        dataset,
        f"survage_{name}",
        patients.age_on(tmp_idenom_num)
    )

# Define population
population = (
    ((death_date >= index_date)|(death_date.is_null()))
    & (practice_registrations.exists_for_patient_on(index_date)) 
    & (dataset.entryage <= 110) & (dataset.entryage >=65)
    )
dataset.define_population(population)