from datetime import datetime
from ehrql import create_dataset
from ehrql.tables.tpp import patients, ons_deaths,practice_registrations,clinical_events,addresses,apcs
from codelists import *

dataset = create_dataset()

dataset.configure_dummy_data(population_size=10000)

index_date = "2020-01-01"
# index_date_dt = datetime.strptime(index_date, "%Y-%m-%d")
# index_year = index_date_dt.year
dataset.define_population(patients.exists_for_patient())

#Core
dataset.sex = patients.sex
dataset.date_of_birth = patients.date_of_birth
dataset.date_of_death = ons_deaths.date

prac_reg = practice_registrations.for_patient_on(index_date)
dataset.prac_stp =  prac_reg.practice_stp
dataset.prac_region = prac_reg.practice_nuts1_region_name

patient_address = addresses.for_patient_on(index_date)
dataset.imd_decile = patient_address.imd_decile
dataset.msoa_code = patient_address.msoa_code

dataset.ethnic_group = (
    clinical_events.where(clinical_events.snomedct_code.is_in(ethnicity_codelist))
    .where(clinical_events.date.is_before(index_date))
    .sort_by(clinical_events.date)
    .last_for_patient()
    .snomedct_code.to_category(ethnicity_codelist)
)

#Quality assurance
dataset.qa_pregnancy = clinical_events.where(
        clinical_events.snomedct_code.is_in(pregnancy_snomed)).exists_for_patient()
dataset.qa_prostate = clinical_events.where(
        clinical_events.snomedct_code.is_in(prostate_snomed)).exists_for_patient()

#Multimorbidity
mlists = {
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

multi_cols = []
for name, mlist in mlists.items():
    mdate = (clinical_events.where(clinical_events.snomedct_code.is_in(mlist))
                            .where(clinical_events.date.is_before(index_date))
            ).date.maximum_for_patient()
    dataset.add_column(f"m_{name}", mdate)
    multi_cols += [f"m_{name}"]

#Outcomes
olists = {
    "spec_dementia": [specified_dementia_snomed,specified_dementia_icd],
    "unspec_dementia": [unspecified_dementia_snomed,unspecified_dementia_icd],
    "alzheimers":[alzheimers_snomed,alzheimers_icd], 
    "cjd":[cjd_snomed,cjd_icd] , 
    "parkinsons":[parkinsons_snomed,parkinsons_icd], 
    "frontotemporal":[frontotemporal_snomed,frontotemporal_icd], 
    "motor":[motor_snomed,motor_icd], 
    "palsy":[palsy_snomed,palsy_icd], 
    "vascular":[vascular_snomed,vascular_icd], 
    "huntingtons":[huntingtons_snomed,huntingtons_icd], 
    "multiatrophy":[multiatrophy_snomed,multiatrophy_icd], 
    "corticobasal":[corticobasal_snomed], 
    "postcortical":[postcortical_snomed], 
    "lewybody":[lewybody_snomed]
}

for name, olist in olists.items():
    if len(olist)==2:
        dataset.add_column(f'o_prim_{name}',clinical_events.where(clinical_events.snomedct_code.is_in(olist[0]))
                                                            .date.minimum_for_patient()
                            )
        dataset.add_column(f'o_sec_{name}',apcs.where(apcs.all_diagnoses.contains_any_of(olist[1]))
                                               .admission_date.minimum_for_patient()
                            )
        dataset.add_column(f'o_death_{name}',ons_deaths.cause_of_death_is_in(olist[1])
                            )
    else:
        dataset.add_column(f'o_prim_{name}',clinical_events.where(clinical_events.snomedct_code.is_in(olist[0]))
                                                            .date.minimum_for_patient()
                            )
    

                         
                         

# multimorbid_weights = {
#     "alcohol": 0.65,
#     "anxiety": 0.5,
#     "af":1.34, 
#     "cancer":1.53 , 
#     "ckd":0.53, 
#     "tissue":0.43, 
#     "copd":1.46, 
#     "chd":0.49, 
#     "dementia":2.5, 
#     "diabetes":0.75, 
#     "epilepsy":0.92, 
#     "hearloss":0.09, 
#     "hf":1.18, 
#     "bowel":0.21, 
#     "psychosis":0.64, 
#     "stroke":0.8, 
#     "athma":0.19, 
#     "hypertension":0.08, 
#     "constipation":1.12, 
#     "pain":0.92   

# }

# cms = clinical_events.exists_for_patient().as_int().as_float() * 0  

# for codelist, weight in [  
#    (alcohol_codelist, 0.65),  
#    (anxiety_codelist, 0.05),  
#    (af_codelist, 1.34),  
#    (cancer_codelist, 1.53),  
#    (ckd_codelist, 0.53),  
#    (tissue_codelist, 0.43),  
#    (copd_codelist, 1.46),  
#    (chd_codelist, 0.49),  
#    (dementia_codelist, 2.50),  
#    (diabetes_codelist, 0.75),  
#    (epilepsy_codelist, 0.92),  
#    (hearloss_codelist, 0.09),  
#    (hf_codelist, 1.18),  
#    (bowel_codelist, 0.21),  
#    (psychosis_codelist, 0.64),  
#    (stroke_codelist, 0.80),  
#    (athma_codelist, 0.19),  
#    (hypertension_codelist, 0.08),  
#    (constipation_codelist, 1.12),  
#    (pain_codelist, 0.92),  
# ]:  
#     cms += (  
#         clinical_events.where(  
#             clinical_events.snomedct_code.is_in(codelist)  
#         ).where(  
#             clinical_events.date.is_before(index_date)  
#         ).exists_for_patient().as_int().as_float()  
#         * weight  
#     )  

# dataset.cms = cms  
    
    
# dataset.cambridge_index = dataset[multi_cols].sum(axis=1)

