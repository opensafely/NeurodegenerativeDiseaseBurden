from ehrql import case, when, maximum_of
from ehrql.tables.tpp import patients, clinical_events, ethnicity_from_sus, apcs, ons_deaths 
from ehrql.tables.core import medications
from datetime import date
from codelists import *

# Function to check dates are valid (i.e., not before or after death)

def check_date_validity(
    date_to_check,
    death_date,
    check_not_before_dob=True,
    check_not_after_death=True
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
            death_date.is_null()
            | (date_to_check <= death_date)
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

def get_cms_on_date(input_date, death_date, return_components=False):

    cms = clinical_events.exists_for_patient().as_int().as_float() * 0
    components = {}

    #any diagnosis ever before
    for name, codelist, weight in [
        ("alcohol", alcohol_codelist, 0.792243),
        ("af", af_codelist, 0.334891),
        ("copd", copd_codelist, 0.702181),
        ("dementia", dementia_codelist, 0.938001),
        ("diabetes", diabetes_codelist, 0.29467),
        ("hf", hf_codelist, 0.505245),
        ("cld", cld_codelist, 0.68621), # codelist for chronic liver disease and viral hepatitis missing 
        ("prostate", prostate_codelist, -0.18781), # codelist for prostate disorder missing
        ("learning", learning_codelist, 0.637273), # codelist for learning disability missing
        ("sclerosis", sclerosis_codelist, 0.761606), # codelist missing
        ("parkinsonism", parkinsonism_codelist, 0.546194), #codelist missing
        ("perivascular_leg", perivascular_codelist, 0.334558), #codelist missing
        ("psychosub_misuse", psychosub_codelist, 0.449321) #codelist missing
    ]:
        filtered = clinical_events.where(
            clinical_events.snomedct_code.is_in(codelist)
            ).where(
            clinical_events.date.is_before(input_date)
            )
        binary = (
            filtered.where(
            check_date_validity(filtered.date, death_date=death_date).is_not_null()
            ).exists_for_patient()
            .as_int()
            )
        cms += binary.as_float() * weight
        if return_components:
            components[name] = binary

    # first diag in last 5 years for cancer
    for name, codelist, weight in [
        ("cancer", cancer_codelist, 1.202615)
    ]:
        d = date.fromisoformat(input_date)
        earliest = f"{d.year-5}-{d.month:02d}-{d.day:02d}"
        filtered = clinical_events.where(
                clinical_events.snomedct_code.is_in(codelist)
                ).where(
                clinical_events.date.is_before(input_date)
                )
        filtered2 = filtered.where(
                check_date_validity(filtered.date, death_date=death_date).is_not_null()
                ).date.minimum_for_patient()
        binary = ((filtered2.is_not_null()) & (filtered2 >= earliest)).as_int()
        cms += binary.as_float() * weight
        if return_components:
            components[name] = binary

    # larger egfr of most recent two measurements < 60ml/min
    for name, codelist, weight in [
        ("ckd", ckd_codelist, 0.213652)
    ]:
        filtered = clinical_events.where(
            clinical_events.snomedct_code.is_in(codelist)
            ).where(
            clinical_events.date.is_before(input_date)
            )
        filtered2 = filtered.where(
            check_date_validity(filtered.date, death_date=death_date).is_not_null()
            )
        filtered3 = filtered2.sort_by(filtered2.date).last_for_patient()
        value1 = filtered3.numeric_value
        filtered4 = filtered2.where(filtered2.date < filtered3.date)
        value2 = filtered4.sort_by(filtered4.date).last_for_patient().numeric_value
        value = maximum_of(value1, value2)
        binary = ((value.is_not_null()) & (value < 60)).as_int()
        cms += binary.as_float() * weight
        if return_components:
            components[name] = binary

    # any diagnosis ever AND med last 12 months >=1, med list missing
    for name, codelist, medlist, weight in [
        ("epilepsy", epilepsy_codelist, epilepsy_medlist, 0.477465)
    ]:
        d = date.fromisoformat(input_date)
        earliest = f"{d.year-1}-{d.month:02d}-{d.day:02d}"
        filtered = clinical_events.where(
            clinical_events.snomedct_code.is_in(codelist)
            ).where(
            clinical_events.date.is_before(input_date)
            )
        diag = filtered.where(
            check_date_validity(filtered.date, death_date=death_date).is_not_null()
            ).exists_for_patient() 
        medfiltered = medications.where(
            medications.dmd_code.is_in(medlist)
            ).where(
            medications.date.is_before(input_date)
            ).where(
            medications.date.is_on_or_after(earliest)    
            )
        med = medfiltered.where(
            check_date_validity(medfiltered.date, death_date=death_date).is_not_null()
            ).exists_for_patient()
        binary = (diag & med).as_int()
        cms += binary.as_float() * weight
        if return_components:
            components[name] = binary

    # any diagnosis ever or med last 12 months >=4, med list missing
    for name, codelist, medlist, weight in [    
        ("bowel", bowel_codelist, bowel_medlist, -0.20368)
    ]:
        d = date.fromisoformat(input_date)
        earliest = f"{d.year-1}-{d.month:02d}-{d.day:02d}"
        filtered = clinical_events.where(
            clinical_events.snomedct_code.is_in(codelist)
            ).where(
            clinical_events.date.is_before(input_date)
            )
        diag = filtered.where(
            check_date_validity(filtered.date, death_date=death_date).is_not_null()
            ).exists_for_patient() 
        medfiltered = medications.where(
            medications.dmd_code.is_in(medlist)
            ).where(
            medications.date.is_before(input_date)
            ).where(
            medications.date.is_on_or_after(earliest)    
            )
        med = medfiltered.where(
            check_date_validity(medfiltered.date, death_date=death_date).is_not_null()
            ).date.count_distinct_for_patient() 
        binary = (diag | (med >= 4)).as_int()
        cms += binary.as_float() * weight
        if return_components:
            components[name] = binary

    #any disgnosis or ever med >=1, med list missing
    for name, codelist, medlist, weight in [           
        ("psychosis", psychosis_codelist, psychosis_medlist, 0.482469)
    ]:
        filtered = clinical_events.where(
                    clinical_events.snomedct_code.is_in(codelist)
                    ).where(
                    clinical_events.date.is_before(input_date)
                    )
        diag = filtered.where(
            check_date_validity(filtered.date, death_date=death_date).is_not_null()
            ).exists_for_patient() 
        medfiltered = medications.where(
            medications.dmd_code.is_in(medlist)
            ).where(
            medications.date.is_before(input_date)
            )
        med = medfiltered.where(
            check_date_validity(medfiltered.date, death_date=death_date).is_not_null()
            ).exists_for_patient() 
        binary = (diag | med).as_int()
        cms += binary.as_float() * weight
        if return_components:
            components[name] = binary 

    # med last 12 months >=4, no need of diagnosis
    for name, medlist, weight in [ 
        ("constipation", constipation_medlist, 0.383006)
    ]:
        d = date.fromisoformat(input_date)
        earliest = f"{d.year-1}-{d.month:02d}-{d.day:02d}"
        
        medfiltered = medications.where(
            medications.dmd_code.is_in(medlist)
            ).where(
            medications.date.is_before(input_date)
            ).where(
            medications.date.is_on_or_after(earliest)    
            )
        med = medfiltered.where(
            check_date_validity(medfiltered.date, death_date=death_date).is_not_null()
            ).date.count_distinct_for_patient() 
        binary = (med >= 4).as_int()
        cms += binary.as_float() * weight
        if return_components:
            components[name] = binary   

    # last 12 months med1>=4 or med2>=4 or any diagnosis in last 12 months, anxiety med list missing
    for name, codelist, medlist1, medlist2, weight in [
        ("anxiety", anxiety_codelist, anxiety_medlist1, anxiety_medlist2, 0.324207)
    ]:
        d = date.fromisoformat(input_date)
        earliest = f"{d.year-1}-{d.month:02d}-{d.day:02d}"
        filtered = clinical_events.where(
            clinical_events.snomedct_code.is_in(codelist)
            ).where(
            clinical_events.date.is_before(input_date)
            ).where(
            clinical_events.date.is_on_or_after(earliest)
            )
        diag = filtered.where(
            check_date_validity(filtered.date, death_date=death_date).is_not_null()
            ).exists_for_patient() 
        medfiltered1 = medications.where(
            medications.dmd_code.is_in(medlist1)
            ).where(
            medications.date.is_before(input_date)
            ).where(
            medications.date.is_on_or_after(earliest)    
            )
        med1 = medfiltered1.where(
            check_date_validity(medfiltered1.date, death_date=death_date).is_not_null()
            ).date.count_distinct_for_patient()   
        medfiltered2 = medications.where(
            medications.dmd_code.is_in(medlist2)
            ).where(
            medications.date.is_before(input_date)
            ).where(
            medications.date.is_on_or_after(earliest)    
            )
        med2 = medfiltered2.where(
            check_date_validity(medfiltered2.date, death_date=death_date).is_not_null()
            ).date.count_distinct_for_patient() 
        binary = (diag | (med1 >= 4) | (med2 >= 4)).as_int()
        cms += binary.as_float() * weight
        if return_components:
            components[name] = binary

    # last 12 months med1 >=4 or (last 12 months med2 >=4 AND no diagnosis for epilepsy ever), med list missing
    for name, codelist, medlist1, medlist2, weight in [   
        ("pain", epilepsy_codelist, pain_medlist1, pain_medlist2, 0.445521)
    ]:    
        d = date.fromisoformat(input_date)
        earliest = f"{d.year-1}-{d.month:02d}-{d.day:02d}"
        filtered = clinical_events.where(
            clinical_events.snomedct_code.is_in(codelist)
            ).where(
            clinical_events.date.is_before(input_date)
            )
        diag = filtered.where(
            check_date_validity(filtered.date, death_date=death_date).is_not_null()
            ).exists_for_patient() 
        medfiltered1 = medications.where(
            medications.dmd_code.is_in(medlist1)
            ).where(
            medications.date.is_before(input_date)
            ).where(
            medications.date.is_on_or_after(earliest)    
            )
        med1 = medfiltered1.where(
            check_date_validity(medfiltered1.date, death_date=death_date).is_not_null()
            ).date.count_distinct_for_patient()   
        medfiltered2 = medications.where(
            medications.dmd_code.is_in(medlist2)
            ).where(
            medications.date.is_before(input_date)
            ).where(
            medications.date.is_on_or_after(earliest)    
            )
        med2 = medfiltered2.where(
            check_date_validity(medfiltered2.date, death_date=death_date).is_not_null()
            ).date.count_distinct_for_patient() 
        binary = (((~diag) & (med2 >= 4))| (med1 >= 4)).as_int()
        cms += binary.as_float() * weight
        if return_components:
            components[name] = binary

    if return_components:
        components["cms"] = cms
        return components

    return cms

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

def first_matching_tpp_between(codelist, start_date, end_date, death_date):
    query = (
        clinical_events
        .where(clinical_events.snomedct_code.is_in(codelist))
        .where(clinical_events.date.is_on_or_between(start_date, end_date))
    )

    valid_date = check_date_validity(clinical_events.date, death_date=death_date)

    return (
        query
        .where(valid_date.is_not_null())
        .sort_by(valid_date)
        .first_for_patient()
        .date
    )

# Function to obtain indicator for prevalent clinical event in TPP

def prevalent_tpp(codelist, date, death_date):
    query = (
        clinical_events
        .where(clinical_events.snomedct_code.is_in(codelist))
        .where(clinical_events.date.is_before(date))
    )

    valid_date = check_date_validity(clinical_events.date, death_date=death_date)

    return (
        query
        .where(valid_date.is_not_null())
        .exists_for_patient()
        .as_int()
    )

# Function to obtain valid date of clinical event in SUS during time period

def first_matching_apc_between(codelist, start_date, end_date, death_date, only_prim_diagnoses=False):
    query = apcs.where(
        apcs.admission_date.is_on_or_between(start_date, end_date)
    )

    if only_prim_diagnoses:
        query = query.where(apcs.primary_diagnosis.is_in(codelist))
    else:
        query = query.where(apcs.all_diagnoses.contains_any_of(codelist))

    valid_date = check_date_validity(apcs.admission_date, death_date=death_date)

    return (
        query
        .where(valid_date.is_not_null())
        .sort_by(valid_date)
        .first_for_patient()
        .admission_date
    )

# Function to obtain indicator for prevalent clinical event in SUS

def prevalent_apc(codelist, date, death_date):
    query = apcs.where(
        apcs.admission_date.is_before(date)
    )

    query = query.where(apcs.all_diagnoses.contains_any_of(codelist))

    valid_date = check_date_validity(apcs.admission_date, death_date=death_date)

    return (
        query
        .where(valid_date.is_not_null())
        .exists_for_patient()
        .as_int()
    )

# Function to obtain valid date of clinical event in death registry during time period

def first_matching_death_between(codelist, start_date, end_date, death_date):
    raw_date = case(
        when(
            ons_deaths.cause_of_death_is_in(codelist)
            & death_date.is_on_or_between(start_date, end_date)
        ).then(death_date)
    )

    valid_date = check_date_validity(raw_date, death_date=death_date)

    return case(
        when(valid_date.is_not_null()).then(valid_date)
    )
