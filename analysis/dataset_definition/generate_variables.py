from ehrql import minimum_of, maximum_of
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

def generate_variables(dataset, start_date, end_date):

    # Core
    dataset.var_date_birth = patients.date_of_birth
    dataset.var_date_death = ons_deaths.date

    prac_reg = practice_registrations.for_patient_on(start_date)
    dataset.var_cat_icb = prac_reg.practice_stp
    dataset.var_bin_registered = prac_reg.exists_for_patient().as_int()
    dataset.var_date_deregistered = prac_reg.end_date

    dataset.cov_num_age = patients.age_on(start_date)
    dataset.cov_cat_sex = patients.sex
    dataset.cov_cat_region = prac_reg.practice_nuts1_region_name

    patient_address = addresses.for_patient_on(start_date)
    dataset.cov_cat_imd = patient_address.imd_decile
    dataset.cov_cat_msoa = patient_address.msoa_code

    dataset.cov_cat_ethnicity = get_latest_ethnicity(
        start_date, ethnicity_codelist, grouping=16
    )

    # Quality assurance
    dataset.qa_bin_pregnancy = clinical_events.where(
        clinical_events.snomedct_code.is_in(pregnancy_snomed)
    ).exists_for_patient().as_int()
    dataset.qa_bin_prostatecancer = (
        (
            clinical_events.where(
                clinical_events.snomedct_code.is_in(prostate_snomed)
            ).exists_for_patient()
        ) | (
            apcs.where(
                apcs.all_diagnoses.contains_any_of(prostate_icd)
            ).exists_for_patient()
        )
    ).as_int()

    # Multimorbidity
    mlists = {
        "alcohol": alcohol_codelist,
        "anxdepression": anxiety_codelist,
        "af": af_codelist,
        "cancer": cancer_codelist,
        "ckd": ckd_codelist,
        "ctd": tissue_codelist,
        "copd": copd_codelist,
        "chd": chd_codelist,
        "dementia": dementia_codelist,
        "diabetes": diabetes_codelist,
        "epilepsy": epilepsy_codelist,
        "hearingloss": hearloss_codelist,
        "hf": hf_codelist,
        "ibs": bowel_codelist,
        "pbpd": psychosis_codelist,
        "tia": stroke_codelist,
        "asthma": athma_codelist,
        "hypertension": hypertension_codelist,
        "constipation": constipation_codelist,
        "osteoarthritis": pain_codelist,
    }

    for name, mlist in mlists.items():
        mdate = clinical_events.where(
            (clinical_events.snomedct_code.is_in(mlist))
            & (clinical_events.date.is_before(start_date))
        ).date
        dataset.add_column(f"cms_date_{name}", mdate.maximum_for_patient())

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

        dates = []
        prevalent = []

        if "snomed" in codes:
            # Primary care
            ## First record in year
            setattr(
                dataset,
                f"out_date_{name}_tpp",
                first_matching_tpp_between(
                    codes["snomed"], start_date, end_date
                ).date,
            )
            dates.append(getattr(dataset, f"out_date_{name}_tpp"))
            ## Identify prevalent cases
            prevalent.append(
                clinical_events
                .where(clinical_events.snomedct_code.is_in(codes["snomed"]))
                .where(clinical_events.date.is_on_or_before(start_date))
                .exists_for_patient()
                .as_int()
            )

        if "icd" in codes:
            # Secondary care
            ## First record in year
            setattr(
                dataset,
                f"out_date_{name}_sus",
                first_matching_apc_between(
                    codes["icd"], start_date, end_date
                ).admission_date,
            )
            dates.append(getattr(dataset, f"out_date_{name}_sus"))
            ## Identify prevalent cases
            prevalent.append(
                apcs
                .where(apcs.primary_diagnosis.is_in(codes["icd"]))
                .where(apcs.admission_date.is_on_or_before(start_date))
                .exists_for_patient()
                .as_int()
            )
            
            # Death
            ## First record in year
            setattr(
                dataset,
                f"out_date_{name}_death",
                first_matching_death_between(codes["icd"], start_date, end_date),
            )
            dates.append(getattr(dataset, f"out_date_{name}_death"))

        if len(dates) == 1:
            setattr(
                dataset,
                f"out_date_{name}",
                dates[0],
            )
        elif len(dates) > 1:
            setattr(
                dataset,
                f"out_date_{name}",
                minimum_of(*dates),
            )

        if len(prevalent) == 1:
            setattr(dataset, f"prevalent_bin_{name}", prevalent[0])
        elif len(prevalent) > 1:
             setattr(
                dataset,
                f"prevalent_bin_{name}",
                maximum_of(*prevalent),
            )

    return dataset
