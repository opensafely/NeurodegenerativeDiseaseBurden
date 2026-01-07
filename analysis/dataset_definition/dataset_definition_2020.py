from ehrql import create_dataset
from ehrql.tables.tpp import patients, ons_deaths,practice_registrations,clinical_events,addresses
from codelists import *

dataset = create_dataset()
index_date = "2020-01-01"

dataset.sex = patients.sex
dataset.date_of_birth = patients.date_of_birth
dataset.date_of_death = ons_deaths.date

prac_reg = practice_registrations.for_patient_on(index_date)
dataset.prac_stp =  prac_reg.practice_stp
dataset.prac_region = prac_reg.practice_nuts1_region_name

dataset.ethnic_group = (
    clinical_events.where(clinical_events.snomedct_code.is_in(ethnicity_codelist))
    .where(clinical_events.date.is_before(index_date))
    .sort_by(clinical_events.date)
    .last_for_patient()
    .snomedct_code.to_category(ethnicity_codelist)
)

patient_address = addresses.for_patient_on(index_date)
dataset.imd_decile = patient_address.imd_decile
dataset.msoa_code = patient_address.msoa_code

qa_1 = clinical_events.where(
        clinical_events.snomedct_code.is_in(pregnancy_snomed)
)
qa_2 = clinical_events.where(
        clinical_events.snomedct_code.is_in(prostate_snomed)
)

dataset.define_population((patients.date_of_birth.year < 2020)
                          &((ons_deaths.date.year >= 2020)|(ons_deaths.date.is_null()))
                          &(prac_reg.practice_nuts1_region_name.is_not_null())
                          &(patient_address.imd_decile.is_not_null()) 
                          &~((qa_1.exists_for_patient())&(patients.sex=='male'))
                          &~((qa_2.exists_for_patient())&(patients.sex=='female'))
                          )

multimorbid_codelists = {
    "alcohol": alcohol_codelist,
    "anxiety": anxiety_codelist,
    "af":af_codelist, 
    "cancer":cancer_codelist , 
    "ckd":ckd_codelist, 
    "tissue":tissue_codelist, 
    "copd":copd_codelist, 
    "chd":chd_codelist, 
    "dementia":dementia_codelist, 
    "diabetes":diabetes_codelist, 
    "epilepsy":epilepsy_codelist, 
    "hearloss":hearloss_codelist, 
    "hf":hf_codelist, 
    "bowel":bowel_codelist, 
    "psychosis":psychosis_codelist, 
    "stroke":stroke_codelist, 
    "athma":athma_codelist, 
    "hypertension":hypertension_codelist, 
    "constipation":constipation_codelist, 
    "pain":pain_codelist   

}

multimorbid_weights = {
    "alcohol": 0.65,
    "anxiety": 0.5,
    "af":1.34, 
    "cancer":1.53 , 
    "ckd":0.53, 
    "tissue":0.43, 
    "copd":1.46, 
    "chd":0.49, 
    "dementia":2.5, 
    "diabetes":0.75, 
    "epilepsy":0.92, 
    "hearloss":0.09, 
    "hf":1.18, 
    "bowel":0.21, 
    "psychosis":0.64, 
    "stroke":0.8, 
    "athma":0.19, 
    "hypertension":0.08, 
    "constipation":1.12, 
    "pain":0.92   

}

multi_cols = []
for name, codelist in multimorbid_codelists.items():
    score = (clinical_events.where(clinical_events.snomedct_code.is_in(codelist))
                                    .where(clinical_events.date.is_before(index_date))
                                    .exists_for_patient().as_int()*multimorbid_weights[name]    
                      )
    dataset.add_column(f"multimorbid_{name}", score)
    multi_cols += [f"multimorbid_{name}"]
    
    
dataset.cambridge_index = dataset[multi_cols].sum(axis=1)

