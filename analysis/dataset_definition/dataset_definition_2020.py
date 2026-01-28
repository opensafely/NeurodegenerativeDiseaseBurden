from ehrql import create_dataset, case, when, minimum_of
from ehrql.tables.tpp import (patients, ons_deaths, practice_registrations, clinical_events,
                              addresses, apcs)
from codelists import *
from variable_helper_functions import get_latest_ethnicity, check_date_validity

dataset = create_dataset()

dataset.configure_dummy_data(population_size=10000)

index_date = "2020-01-01"

dataset.define_population(patients.exists_for_patient())

#Core
dataset.var_date_birth = patients.date_of_birth
dataset.var_date_death = ons_deaths.date

prac_reg = practice_registrations.for_patient_on(index_date)
dataset.var_cat_icb =  prac_reg.practice_stp
dataset.var_bin_registered = prac_reg.exists_for_patient()
dataset.var_date_deregistered = prac_reg.end_date

dataset.cov_num_age = patients.age_on(index_date)
dataset.cov_cat_sex = patients.sex
dataset.cov_cat_region = prac_reg.practice_nuts1_region_name

patient_address = addresses.for_patient_on(index_date)
dataset.cov_cat_imd = patient_address.imd_decile
dataset.cov_cat_msoa = patient_address.msoa_code

dataset.cov_cat_ethnicity = get_latest_ethnicity(index_date,
                                                 ethnicity_codelist, grouping=16)

#Quality assurance
dataset.qa_bin_pregnancy = clinical_events.where(
        clinical_events.snomedct_code.is_in(pregnancy_snomed)).exists_for_patient()
dataset.qa_bin_prostatecancer = ((clinical_events.where(
        clinical_events.snomedct_code.is_in(prostate_snomed)).exists_for_patient()) | 
        (apcs.where(apcs.all_diagnoses.contains_any_of(prostate_icd)).exists_for_patient())
        )

#Multimorbidity
mlists = {
    "alcohol": alcohol_codelist,
    "anxdepression": anxiety_codelist,
    "af":af_codelist, 
    "cancer":cancer_codelist , 
    "ckd":ckd_codelist, 
    "ctd":tissue_codelist, 
    "copd":copd_codelist, 
    "chd":chd_codelist, 
    "dementia":dementia_codelist, 
    "diabetes":diabetes_codelist, 
    "epilepsy":epilepsy_codelist, 
    "hearingloss":hearloss_codelist, 
    "hf":hf_codelist, 
    "ibs":bowel_codelist, 
    "pbpd":psychosis_codelist, 
    "tia":stroke_codelist, 
    "asthma":athma_codelist, 
    "hypertension":hypertension_codelist, 
    "constipation":constipation_codelist, 
    "osteoarthritis":pain_codelist   
}

for name, mlist in mlists.items():
    mdate = check_date_validity(clinical_events.where(clinical_events.snomedct_code.is_in(mlist))
                            .where(clinical_events.date.is_before(index_date))
                            .date
            )
    dataset.add_column(f"cms_date_{name}", mdate.maximum_for_patient())
    

#Outcomes
olists = {
    "osd": [specified_dementia_snomed,specified_dementia_icd],
    "ud": [unspecified_dementia_snomed,unspecified_dementia_icd],
    "ad":[alzheimers_snomed,alzheimers_icd], 
    "cjd":[cjd_snomed,cjd_icd] , 
    "pd":[parkinsons_snomed,parkinsons_icd], 
    "ftd":[frontotemporal_snomed,frontotemporal_icd], 
    "mnd":[motor_snomed,motor_icd], 
    "psp":[palsy_snomed,palsy_icd], 
    "vd":[vascular_snomed,vascular_icd], 
    "hd":[huntingtons_snomed,huntingtons_icd], 
    "msa":[multiatrophy_snomed,multiatrophy_icd], 
    "cbd":[corticobasal_snomed], 
    "pca":[postcortical_snomed], 
    "dlb":[lewybody_snomed]
}

for name, olist in olists.items():
    if len(olist)==2:
        odate_tpp = check_date_validity(clinical_events.where(clinical_events.snomedct_code.is_in(olist[0])).date)
        dataset.add_column(f'out_date_{name}_tpp',odate_tpp.minimum_for_patient()
                            )
        odate_sus = check_date_validity(apcs.where(apcs.all_diagnoses.contains_any_of(olist[1])).admission_date)
        dataset.add_column(f'out_date_{name}_sus',odate_sus.minimum_for_patient()
                            )
        dataset.add_column(f'out_date_{name}_death',case(when(ons_deaths.cause_of_death_is_in(olist[1])).then(ons_deaths.date))
                            )
        cols = [getattr(dataset,col) for col in [f'out_date_{name}_tpp',f'out_date_{name}_sus',f'out_date_{name}_death']]
        dataset.add_column(f'out_date_{name}',minimum_of(*cols))
    else:
        odate_tpp = check_date_validity(clinical_events.where(clinical_events.snomedct_code.is_in(olist[0])).date)
        dataset.add_column(f'out_date_{name}_tpp',odate_tpp.minimum_for_patient()
                            )
        dataset.add_column(f'out_date_{name}',getattr(dataset,f'out_date_{name}_tpp'))
    