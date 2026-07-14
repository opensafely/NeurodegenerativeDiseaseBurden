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
dataset.configure_dummy_data(population_size=4000)

# Specify start age,  start date, end date and index date
start_age = get_parameter(name="start_age", type = int)
start_date = get_parameter(name="start_date")
end_date = get_parameter(name="end_date")
index_date = maximum_of(patients.date_of_birth + years(start_age), start_date)
death_date = minimum_of(patients.date_of_death, ons_deaths.date)
pat_end_date = minimum_of(end_date, death_date, practice_registrations.for_patient_on(index_date).end_date) 

## Entry age
dataset.entryage = case(
    when(index_date <= start_date).then(patients.age_on(start_date)),
    when((index_date > start_date)
         & (index_date <= pat_end_date)).then(start_age)
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
    "dlb": {"snomed": lewybody_snomed}
}
olists["dementia"] = {"snomed": specified_dementia_snomed+unspecified_dementia_snomed+alzheimers_snomed+vascular_snomed, 
                      "icd": specified_dementia_icd+unspecified_dementia_icd+alzheimers_icd+vascular_icd}

snomedlist = []
icdlist = []
for name, codes in olists.items():
    if "snomed" in codes:
        snomedlist += codes["snomed"]
    if "icd" in codes:
        icdlist += codes["icd"]  
olists["anyneuro"] = {"snomed": snomedlist,
                      "icd": icdlist}


# Generate inci status and survage for competing dementia subtypes
inci_dementia = {}
for name in ["osd", "ud", "ad", "vd"]:
    incident = {}
    if "snomed" in olists[name]:
        incident["primary"] = first_matching_tpp_between(olists[name]["snomed"], index_date, pat_end_date, death_date)
    
    if "icd" in olists[name]:
        incident["secondary"] = first_matching_apc_between(olists[name]["icd"], index_date, pat_end_date, death_date, only_prim_diagnoses=False)
        incident["death"] = first_matching_death_between(olists[name]["icd"], index_date, pat_end_date, death_date) 
    if len(incident) ==1:
        tmp_incident_date = list(incident.values())[0]
    else:
        tmp_incident_date = minimum_of(*incident.values())
    incident["min"] =  tmp_incident_date   
    inci_dementia[name] = incident

inci_dementia_1 = minimum_of(inci_dementia["osd"]["min"], inci_dementia["ud"]["min"], inci_dementia["ad"]["min"], inci_dementia["vd"]["min"])
inci_status = case(
            when(inci_dementia_1 == inci_dementia['ad']['min']).then("ad"),
            when(inci_dementia_1 == inci_dementia['vd']['min']).then("vd"),
            when(inci_dementia_1 == inci_dementia['osd']['min']).then("osd"),
            when(inci_dementia_1 == inci_dementia['ud']['min']).then("ud"),
            when((death_date >= index_date) & (death_date <= pat_end_date)).then("death"),
            otherwise="censored",
        )
setattr(dataset,
        f"event_dementia_compete",
        inci_status
    )
setattr(
        dataset,
        f"survage_dementia_compete",
        patients.age_on(minimum_of(pat_end_date, inci_dementia_1))
        )

# Generate prevalent status for all dementia
prev_dementia = []
prev_dementia.append(
                prevalent_tpp(olists["dementia"]["snomed"], index_date, death_date)
            )
prev_dementia.append(
                prevalent_apc(olists["dementia"]["icd"], index_date, death_date)
            )
prevalent_dementia = maximum_of(*prev_dementia)


for name, codes in olists.items():
    if name not in ["osd", "ud", "ad", "vd"]:
        incident = {}
        prevalent_start = []

        if "snomed" in codes:
            ## Primary care incidence
            incident["primary"] = first_matching_tpp_between(codes["snomed"], index_date, pat_end_date, death_date)
            
            ### Identify prevalent cases
            prevalent_start.append(
                prevalent_tpp(codes["snomed"], index_date, death_date)
            )
        
        if "icd" in codes:
            ## Secondary care incidence
            incident["secondary"] = first_matching_apc_between(codes["icd"], index_date, pat_end_date, death_date, only_prim_diagnoses=False)

            ## Death incidence
            incident["death"] = first_matching_death_between(codes["icd"], index_date, pat_end_date, death_date)
            
            ### Identify prevalent cases
            prevalent_start.append(
                prevalent_apc(codes["icd"], index_date, death_date)
            )

        # Add prevalance status
        if len(prevalent_start) == 1:
            tmp_prev = prevalent_start[0]
        elif len(prevalent_start) > 1:
            tmp_prev = maximum_of(*prevalent_start)

        setattr(
            dataset,
            f"prev_bin_{name}",
            tmp_prev
        )
        
        # Add incidence status
        if len(incident) ==1:
            tmp_incident_date = list(incident.values())[0]
        else:
            tmp_incident_date  = minimum_of(*incident.values())
              
        # Event: censored, neuro, death
        setattr(
            dataset,
            f"event_{name}",
            case(
                when(tmp_incident_date.is_not_null()).then("neuro"),
                when((death_date >= index_date) & (death_date <= pat_end_date)).then("death"),
                otherwise="censored",
            )
        )

        # Add data source
        if len(incident) == 1:
            setattr(
                    dataset,
                    f"event_{name}_source",
                    case(
                        when(getattr(dataset, f"event_{name}").is_in(["death", "censored"])).then(None),
                        otherwise = list(incident.values())[0]                
                    )
                    )
        else:
            setattr(
                    dataset,
                    f"event_{name}_source",
                    case(
                        when(getattr(dataset, f"event_{name}").is_in(["death", "censored"])).then(None),
                        when(tmp_incident_date == incident["secondary"]).then("secondary"),
                        when(tmp_incident_date == incident["primary"]).then("primary"),
                        when(tmp_incident_date == incident["death"]).then("death")                
                    )
                    )
        # Survage
        tmp_fu = minimum_of(pat_end_date, tmp_incident_date)
        setattr(
            dataset,
            f"survage_{name}",
            patients.age_on(tmp_fu)
        )
    else:
        #Prevalent status for any dementia
        setattr(
            dataset,
            f"prev_bin_{name}",
            prevalent_dementia
        )

        #Censor at dementia subtypes
        setattr(
            dataset,
            f"event_{name}",
            case(
                when(inci_status == "death").then("death"),
                when(inci_status == name).then("neuro"),
                otherwise="censored",
            )
        )

        #Add data source
        if len(inci_dementia[name]) == 1:
            setattr(
                dataset,
                f"event_{name}_source",
                case(
                    when(getattr(dataset, f"event_{name}").is_in(["death", "censored"])).then(None),
                    otherwise = list(inci_dementia[name].keys())[0],
                )
                )
        else:    
            setattr(
                dataset,
                f"event_{name}_source",
                case(
                    when(getattr(dataset, f"event_{name}").is_in(["death", "censored"])).then(None),
                    when(inci_dementia_1 == inci_dementia[name]["secondary"]).then("secondary"),
                    when(inci_dementia_1 == inci_dementia[name]["primary"]).then("primary"),
                    when(inci_dementia_1 == inci_dementia[name]["death"]).then("death"),
                )
                )

        # Survage
        tmp_fu = minimum_of(pat_end_date, inci_dementia_1)
        setattr(
            dataset,
            f"survage_{name}",
            patients.age_on(tmp_fu)
        )

# Define population
population = (
    ((death_date >= index_date)|(death_date.is_null()))
    & (practice_registrations.exists_for_patient_on(index_date)) 
    & (dataset.entryage <= 110) & (dataset.entryage >= start_age)
    )
dataset.define_population(population)