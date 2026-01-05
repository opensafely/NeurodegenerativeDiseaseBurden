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
    .where(clinical_events.date.is_on_or_before(index_date))
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

