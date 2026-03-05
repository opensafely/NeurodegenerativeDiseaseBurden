from ehrql import case, when
from ehrql.tables.tpp import patients, clinical_events, ethnicity_from_sus, apcs, ons_deaths 
from codelists import *

# Function to check dates are valid (i.e., not before or after death)

def check_date_validity(
    date_to_check,
    check_not_before_dob=True,
    check_not_after_death=True,
):

    conditions = []

    ## Base requirement: must not be null
    conditions.append(date_to_check.is_not_null())

    ## Check not before DOB
    if check_not_before_dob:
        conditions.append(
            patients.date_of_birth.is_null()
            | (date_to_check >= patients.date_of_birth)
        )

    ## Check not after death
    if check_not_after_death:
        conditions.append(
            ons_deaths.date.is_null()
            | (date_to_check <= ons_deaths.date)
        )

    ## Combine all validity conditions
    is_valid = conditions[0]
    for cond in conditions[1:]:
        is_valid = is_valid & cond

    return case(
        when(is_valid).then(date_to_check),
        otherwise=None
    )

# Function to obtain Cambridge multimorbidity score

def get_cms_on_date(date):
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
        filtered = clinical_events.where(
            clinical_events.snomedct_code.is_in(codelist)
        ).where(
            clinical_events.date.is_before(date)
        )
        cms += (
            filtered.where(
                check_date_validity(filtered.date).is_not_null()
            ).exists_for_patient().as_int().as_float()
            * weight
        )

    return(cms)

# Function to obtain last recorded ethnicity in TPP or SUS

def get_latest_ethnicity(index_date, codelist, grouping=6):   
        latest_ethnicity_from_codes_category_num = (
            clinical_events.where(clinical_events.snomedct_code.is_in(codelist))
            .where(clinical_events.date.is_on_or_before(index_date))
            .sort_by(clinical_events.date)
            .last_for_patient()
            .snomedct_code.to_category(codelist)
        )

        if grouping == 6:
            latest_ethnicity_from_codes = case(
                when(latest_ethnicity_from_codes_category_num == "1").then("White"),
                when(latest_ethnicity_from_codes_category_num == "2").then("Mixed"),
                when(latest_ethnicity_from_codes_category_num == "3").then(
                    "Asian or Asian British"
                ),
                when(latest_ethnicity_from_codes_category_num == "4").then(
                    "Black or Black British"
                ),
                when(latest_ethnicity_from_codes_category_num == "5").then(
                    "Chinese or Other Ethnic Groups"
                ),
            )

            ethnicity_sus = case(
                when(ethnicity_from_sus.code.is_in(["A", "B", "C"])).then("White"),
                when(ethnicity_from_sus.code.is_in(["D", "E", "F", "G"])).then("Mixed"),
                when(ethnicity_from_sus.code.is_in(["H", "J", "K", "L"])).then(
                    "Asian or Asian British"
                ),
                when(ethnicity_from_sus.code.is_in(["M", "N", "P"])).then(
                    "Black or Black British"
                ),
                when(ethnicity_from_sus.code.is_in(["R", "S"])).then(
                    "Chinese or Other Ethnic Groups"
                ),
            )
        elif grouping == 16:
            latest_ethnicity_from_codes = case(
                when(latest_ethnicity_from_codes_category_num == "1").then("White British"),
                when(latest_ethnicity_from_codes_category_num == "2").then("White Irish"),
                when(latest_ethnicity_from_codes_category_num == "3").then("Other White"),
                when(latest_ethnicity_from_codes_category_num == "4").then(
                    "White and Caribbean"
                ),
                when(latest_ethnicity_from_codes_category_num == "5").then(
                    "White and African"
                ),
                when(latest_ethnicity_from_codes_category_num == "6").then(
                    "White and Asian"
                ),
                when(latest_ethnicity_from_codes_category_num == "7").then("Other Mixed"),
                when(latest_ethnicity_from_codes_category_num == "8").then("Indian"),
                when(latest_ethnicity_from_codes_category_num == "9").then("Pakistani"),
                when(latest_ethnicity_from_codes_category_num == "10").then("Bangladeshi"),
                when(latest_ethnicity_from_codes_category_num == "11").then(
                    "Other Asian"
                ),
                when(latest_ethnicity_from_codes_category_num == "12").then("Caribbean"),
                when(latest_ethnicity_from_codes_category_num == "13").then("African"),
                when(latest_ethnicity_from_codes_category_num == "14").then("Other Black"),
                when(latest_ethnicity_from_codes_category_num == "15").then("Chinese"),
                when(latest_ethnicity_from_codes_category_num == "16").then(
                    "All other ethnic groups"
                ),
            )

            ethnicity_sus = case(
                when(ethnicity_from_sus.code == "A").then("White British"),
                when(ethnicity_from_sus.code == "B").then("White Irish"),
                when(ethnicity_from_sus.code == "C").then("Other White"),
                when(ethnicity_from_sus.code == "D").then("White and Caribbean"),
                when(ethnicity_from_sus.code == "E").then("White and African"),
                when(ethnicity_from_sus.code == "F").then("White and Asian"),
                when(ethnicity_from_sus.code == "G").then("Other Mixed"),
                when(ethnicity_from_sus.code == "H").then("Indian"),
                when(ethnicity_from_sus.code == "J").then("Pakistani"),
                when(ethnicity_from_sus.code == "K").then("Bangladeshi"),
                when(ethnicity_from_sus.code == "L").then("Other Asian"),
                when(ethnicity_from_sus.code == "M").then("Caribbean"),
                when(ethnicity_from_sus.code == "N").then("African"),
                when(ethnicity_from_sus.code == "P").then("Other Black"),
                when(ethnicity_from_sus.code == "R").then("Chinese"),
                when(ethnicity_from_sus.code == "S").then("All other ethnic groups"),
            )

        ethnicity_combined = case(
            when(latest_ethnicity_from_codes.is_not_null()).then(
                latest_ethnicity_from_codes
            ),
            when(
                latest_ethnicity_from_codes.is_null() & ethnicity_sus.is_not_null()
            ).then(ethnicity_sus),
            otherwise="Missing",
        )

        return ethnicity_combined

# Function to obtain valid date of clinical event in TPP during time period

def first_matching_tpp_between(codelist, start_date, end_date):
    query = (
        clinical_events
        .where(clinical_events.snomedct_code.is_in(codelist))
        .where(clinical_events.date.is_on_or_between(start_date, end_date))
    )

    valid_date = check_date_validity(clinical_events.date)

    return (
        query
        .where(valid_date.is_not_null())
        .sort_by(valid_date)
        .first_for_patient()
        .date
    )

# Function to obtain valid date of clinical event in SUS during time period

def first_matching_apc_between(codelist, start_date, end_date, only_prim_diagnoses=False):
    query = apcs.where(
        apcs.admission_date.is_on_or_between(start_date, end_date)
    )

    if only_prim_diagnoses:
        query = query.where(apcs.primary_diagnosis.is_in(codelist))
    else:
        query = query.where(apcs.all_diagnoses.contains_any_of(codelist))

    valid_date = check_date_validity(apcs.admission_date)

    return (
        query
        .where(valid_date.is_not_null())
        .sort_by(valid_date)
        .first_for_patient()
        .admission_date
    )

# Function to obtain valid date of clinical event in death registry during time period

def first_matching_death_between(codelist, start_date, end_date):
    raw_date = case(
        when(
            ons_deaths.cause_of_death_is_in(codelist)
            & ons_deaths.date.is_on_or_between(start_date, end_date)
        ).then(ons_deaths.date)
    )

    valid_date = check_date_validity(raw_date)

    return case(
        when(valid_date.is_not_null()).then(valid_date)
    )