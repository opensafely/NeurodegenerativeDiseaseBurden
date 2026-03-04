from ehrql import create_dataset, get_parameter, minimum_of, maximum_of, case, when
from ehrql.tables.tpp import (
    patients,
    ons_deaths,
    practice_registrations,
    clinical_events,
    addresses,
    apcs,
)
from codelists import *
from variable_helper_functions import (
    get_latest_ethnicity,
    first_matching_tpp_between,
    first_matching_apc_between,
    first_matching_death_between
)

# Create dataset
dataset = create_dataset()

# Configure dummy data
dataset.configure_dummy_data(population_size=10000)

# Specify start and end dates
start_date = get_parameter(name="start_date")
end_date = get_parameter(name="end_date")
pat_end_date = minimum_of(end_date, patients.date_of_death, ons_deaths.date, practice_registrations.for_patient_on(start_date).end_date) 

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

## Camrbidge Multimorbidity Score (CMS)
cms = clinical_events.exists_for_patient().as_int().as_float() * 0

for codelist, weight in [
   (alcohol_codelist, 0.65),
   (anxiety_codelist, 0.05),
   (af_codelist, 1.34),
   (cancer_codelist, 1.53),
   (ckd_codelist, 0.53),
   (tissue_codelist, 0.43),
   (copd_codelist, 1.46),
   (chd_codelist, 0.49),
   (dementia_codelist, 2.50),
   (diabetes_codelist, 0.75),
   (epilepsy_codelist, 0.92),
   (hearloss_codelist, 0.09),
   (hf_codelist, 1.18),
   (bowel_codelist, 0.21),
   (psychosis_codelist, 0.64),
   (stroke_codelist, 0.80),
   (athma_codelist, 0.19),
   (hypertension_codelist, 0.08),
   (constipation_codelist, 1.12),
   (pain_codelist, 0.92),
]:
    cms += (
        clinical_events.where(
            clinical_events.snomedct_code.is_in(codelist)
        ).where(
            clinical_events.date.is_before(start_date)
        ).exists_for_patient().as_int().as_float()
        * weight
    )

dataset.cov_num_cms = cms

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
    prevalent = []

    if "snomed" in codes:
        ## Primary care
        ### First record in year
        incident.append(
            first_matching_tpp_between(codes["snomed"], start_date, end_date)
        )
        ### Identify prevalent cases
        prevalent.append(
            clinical_events
            .where(clinical_events.snomedct_code.is_in(codes["snomed"]))
            .where(clinical_events.date.is_before(start_date))
            .exists_for_patient()
            .as_int()
        )

    if "icd" in codes:
        ## Secondary care
        ### First record in year
        incident.append(
            first_matching_apc_between(codes["icd"], start_date, end_date, only_prim_diagnoses=False)
        )
        ### Identify prevalent cases
        prevalent.append(
            apcs
            .where(apcs.primary_diagnosis.is_in(codes["icd"]))
            .where(apcs.admission_date.is_before(start_date))
            .exists_for_patient()
            .as_int()
        )
        
        ## Death
        ### First record in year
        incident.append(
            first_matching_death_between(codes["icd"], start_date, end_date)
        )

    # Prevalance numerator
    if len(prevalent) == 1:
        tmp_pnumer_bin = prevalent[0]
    elif len(prevalent) > 1:
        tmp_pnumer_bin = maximum_of(*prevalent)

    setattr(
            dataset,
            f"pnumer_bin_{name}",
            tmp_pnumer_bin
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
            when(getattr(dataset, f"pnumer_bin_{name}") == 1).then(0),
            otherwise=tmp_incident_date.is_not_null().as_int(),
        )
    )

    # Incidence denominator
    tmp_idenom_num = minimum_of(pat_end_date, tmp_incident_date)
    setattr(
        dataset,
        f"idenom_num_{name}",
        maximum_of(0,(tmp_idenom_num - start_date).days)
    )
            
# Prevalence denominator
dataset.pdenom_num = maximum_of(0,(pat_end_date - start_date).days)

# Define population
population = patients.is_alive_on(start_date) & (practice_registrations.for_patient_on(start_date).exists_for_patient()) & (dataset.cov_num_age <= 110) & (dataset.cov_num_age >= 18)
dataset.define_population(population)