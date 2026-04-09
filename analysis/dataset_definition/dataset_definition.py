from ehrql import create_dataset, get_parameter, minimum_of, maximum_of, case, when
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
from datetime import date

# Create dataset
dataset = create_dataset()

# Configure dummy data
dataset.configure_dummy_data(population_size=10000)

# Specify start, end and mid dates
start_date = get_parameter(name="start_date")
end_date = get_parameter(name="end_date")
death_date = minimum_of(patients.date_of_death, ons_deaths.date)
pat_end_date = minimum_of(end_date, death_date, practice_registrations.for_patient_on(start_date).end_date) 

d1 = date.fromisoformat(start_date)
d2 = date.fromisoformat(end_date)
# Identify mid-dates 
d1 = date.fromisoformat(start_date)
d2 = date.fromisoformat(end_date)

## If full calendar year, use 30/06
if d1.month == 1 and d1.day == 1 and d2.month == 12 and d2.day == 31 and d1.year == d2.year:
    mid_date = f"{d1.year}-06-30"
    mid_date_prev = f"{d1.year}-07-01"
## If full calendar month, use 15/MM
elif (
    d1.day == 1 and
    d1.year == d2.year and
    d1.month == d2.month and
    d2.day == calendar.monthrange(d1.year, d1.month)[1]
):
    mid_date = f"{d1.year}-{d1.month:02d}-15"
    mid_date_prev = f"{d1.year}-{d1.month:02d}-16"
## Otherwise split interval in half
else:
    midpoint = d1 + (d2 - d1) / 2
    mid_date = midpoint.isoformat()
    mid_date_prev = (midpoint + timedelta(days=1)).isoformat()
# Covariates 

## Age
dataset.cov_num_age = patients.age_on(start_date)

## Sex
dataset.cov_cat_sex = patients.sex

## Region
dataset.cov_cat_region = practice_registrations.for_patient_on(start_date).practice_nuts1_region_name

## IMD and MSOA
patient_address = addresses.for_patient_on(start_date)
dataset.cov_cat_imd = patient_address.imd_decile
dataset.cov_cat_msoa = patient_address.msoa_code

## Ethnicity
dataset.cov_cat_ethnicity = get_latest_ethnicity(
    start_date, ethnicity_codelist, grouping=16
)

## Cambridge Multimorbidity Score (CMS)
dataset.cov_num_cms = get_cms_on_date(start_date, death_date)

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
    prevalent_mid = []

    if "snomed" in codes:
        ## Primary care
        ### First record in year
        incident.append(
            first_matching_tpp_between(codes["snomed"], start_date, end_date, death_date)
        )
        ### Identify prevalent cases

        prevalent_start.append(
            prevalent_tpp(codes["snomed"], start_date, death_date)
        )

        prevalent_mid.append(
            prevalent_tpp(codes["snomed"], mid_date_prev, death_date)
        )

    if "icd" in codes:
        ## Secondary care
        ### First record in year
        incident.append(
            first_matching_apc_between(codes["icd"], start_date, end_date, death_date, only_prim_diagnoses=False)
        )
        ### Identify prevalent cases

        prevalent_start.append(
            prevalent_apc(codes["icd"], start_date, death_date)
        )

        prevalent_mid.append(
            prevalent_apc(codes["icd"], mid_date_prev, death_date)
        )         
        
        ## Death
        ### First record in year
        incident.append(
            first_matching_death_between(codes["icd"], start_date, end_date, death_date)
        )

    # Prevalance at start date
    if len(prevalent_start) == 1:
        tmp_pnumer_bin_start = prevalent_start[0]
    elif len(prevalent_start) > 1:
        tmp_pnumer_bin_start = maximum_of(*prevalent_start)
    
    # Prevalence at mid date
    if len(prevalent_mid) == 1:
        tmp_pnumer_bin_mid = prevalent_mid[0]
    elif len(prevalent_mid) > 1:
        tmp_pnumer_bin_mid = maximum_of(*prevalent_mid)

    # Prevalence numerator
    setattr(dataset,
            f"pnumer_bin_{name}",
            case(
                when((tmp_pnumer_bin_mid==1) & 
                     ((death_date>=mid_date) | (death_date.is_null())) & 
                     (practice_registrations.exists_for_patient_on(mid_date))
                    ).then(1),
                otherwise=0
                )
            )
       
    # Incidence numerator
    if len(incident) == 1:
        tmp_incident_date = incident[0]
    elif len(incident) > 1:
        tmp_incident_date  = minimum_of(*incident)

    setattr(
        dataset,
        f"inumer_bin_{name}",
        case(
            when(tmp_pnumer_bin_start == 1).then(0),
            when(practice_registrations.exists_for_patient_on(tmp_incident_date)).then(1),
            otherwise=0,
        )
    )

    # Incidence denominator
    tmp_idenom_num = minimum_of(pat_end_date, tmp_incident_date)
    setattr(
        dataset,
        f"idenom_num_{name}",
        maximum_of(0,(tmp_idenom_num - start_date).days)
    )

    # Case fatality numerator
    setattr(
        dataset,
        f"fnumer_bin_1y_{name}",
        case(when((getattr(dataset,f"inumer_bin_{name}")==1) & 
                  ((death_date - tmp_incident_date).years <=1) &
                  (practice_registrations.exists_for_patient_on(death_date))
                ).then(1),
             otherwise=0
            )
        )
    
    setattr(
        dataset,
        f"fnumer_bin_5y_{name}",
        case(when((getattr(dataset,f"inumer_bin_{name}")==1) & 
                  ((death_date - tmp_incident_date).years <=5) &
                  (practice_registrations.exists_for_patient_on(death_date))
                ).then(1),
             otherwise=0
            )
        )
            
# Prevalence denominator - population at mid date
dataset.pdenom_bin_mid = case(when(((death_date>=mid_date) | (death_date.is_null())) &
                                   (practice_registrations.exists_for_patient_on(mid_date))
                                  ).then(1), 
                              otherwise=0           
                            )

# Define population
population = ((death_date>=start_date)|(death_date.is_null())) & (practice_registrations.exists_for_patient_on(start_date)) & (dataset.cov_num_age <= 110) & (dataset.cov_num_age >= 18)
dataset.define_population(population)