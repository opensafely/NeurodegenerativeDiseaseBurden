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
from datetime import date, timedelta
import calendar

# Create dataset
dataset = create_dataset()

# Configure dummy data
dataset.configure_dummy_data(population_size=2000)

# Specify start, end and mid dates
start_date = get_parameter(name="start_date")
end_date = get_parameter(name="end_date")
death_date = minimum_of(patients.date_of_death, ons_deaths.date)
pat_end_date = minimum_of(end_date, death_date, practice_registrations.for_patient_on(start_date).end_date) 
start_date_default = "1900-01-01"

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
cms_parts = get_cms_on_date(start_date, death_date, return_components=True)

dataset.cov_num_cms = cms_parts["cms"]
dataset.cov_bin_cms_alcohol = cms_parts["alcohol"]
dataset.cov_bin_cms_anxiety = cms_parts["anxiety"]
dataset.cov_bin_cms_af = cms_parts["af"]
dataset.cov_bin_cms_cancer = cms_parts["cancer"]
dataset.cov_bin_cms_ckd = cms_parts["ckd"]
dataset.cov_bin_cms_tissue = cms_parts["tissue"]
dataset.cov_bin_cms_copd = cms_parts["copd"]
dataset.cov_bin_cms_chd = cms_parts["chd"]
dataset.cov_bin_cms_dementia = cms_parts["dementia"]
dataset.cov_bin_cms_diabetes = cms_parts["diabetes"]
dataset.cov_bin_cms_epilepsy = cms_parts["epilepsy"]
dataset.cov_bin_cms_hearing_loss = cms_parts["hearing_loss"]
dataset.cov_bin_cms_hf = cms_parts["hf"]
dataset.cov_bin_cms_bowel = cms_parts["bowel"]
dataset.cov_bin_cms_psychosis = cms_parts["psychosis"]
dataset.cov_bin_cms_stroke = cms_parts["stroke"]
dataset.cov_bin_cms_asthma = cms_parts["asthma"]
dataset.cov_bin_cms_hypertension = cms_parts["hypertension"]
dataset.cov_bin_cms_constipation = cms_parts["constipation"]
dataset.cov_bin_cms_pain = cms_parts["pain"]

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
olists["dementia"] = {
    "snomed": specified_dementia_snomed+unspecified_dementia_snomed+alzheimers_snomed+vascular_snomed+frontotemporal_snomed+lewybody_snomed, 
    "icd": specified_dementia_icd+unspecified_dementia_icd+alzheimers_icd+vascular_icd+frontotemporal_icd
}

# Prevalent status for any dementia before start date
prev_dementia_start = []
prev_dementia_start.append(
                prevalent_tpp(olists["dementia"]["snomed"], start_date, death_date)
            )
prev_dementia_start.append(
                prevalent_apc(olists["dementia"]["icd"], start_date, death_date)
            )
prevalent_dementia_start = maximum_of(*prev_dementia_start)

# First incident date among dementia subtypes during follow up by data source
inci_dementia_source = {}
inci_dementia_min = {}
for name in ["osd", "ud", "ad", "vd", "ftd", "dlb"]:
    incident = {}
    if "snomed" in olists[name]:
        incident["primary"] = first_matching_tpp_between(olists[name]["snomed"], start_date, pat_end_date, death_date)
    if "icd" in olists[name]:
        incident["secondary"] = first_matching_apc_between(olists[name]["icd"], start_date, pat_end_date, death_date, only_prim_diagnoses=False)
        incident["death"] = first_matching_death_between(olists[name]["icd"], start_date, pat_end_date, death_date) 
    if len(incident) ==1:
        tmp_incident_date = list(incident.values())[0]
    else:
        tmp_incident_date = minimum_of(*incident.values())
    inci_dementia_min[name] = tmp_incident_date   
    inci_dementia_source[name] = incident
inci_dementia_1 = minimum_of(*inci_dementia_min.values())
inci_dementia_status = case(
            when(
                (inci_dementia_1 == inci_dementia_min['ad'])&
                ((inci_dementia_1 != inci_dementia_min['vd'])|
                 (inci_dementia_min['vd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['osd'])|
                 (inci_dementia_min['osd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['ftd'])|
                 (inci_dementia_min['ftd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['dlb'])|
                 (inci_dementia_min['dlb'].is_null()))
                ).then('ad'),
            when(
                (inci_dementia_1 == inci_dementia_min['vd'])&
                ((inci_dementia_1 != inci_dementia_min['ad'])|
                 (inci_dementia_min['ad'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['osd'])|
                 (inci_dementia_min['osd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['ftd'])|
                 (inci_dementia_min['ftd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['dlb'])|
                 (inci_dementia_min['dlb'].is_null()))
                ).then('vd'), 
            when(
                (inci_dementia_1 == inci_dementia_min['ud'])&
                ((inci_dementia_1 != inci_dementia_min['vd'])|
                 (inci_dementia_min['vd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['osd'])|
                 (inci_dementia_min['osd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['ad'])|
                 (inci_dementia_min['ud'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['ftd'])|
                 (inci_dementia_min['ftd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['dlb'])|
                 (inci_dementia_min['dlb'].is_null()))
                ).then('ud'),   
            when(
                (inci_dementia_1 == inci_dementia_min['ftd'])&
                ((inci_dementia_1 != inci_dementia_min['vd'])|
                 (inci_dementia_min['vd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['osd'])|
                 (inci_dementia_min['osd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['ad'])|
                 (inci_dementia_min['ftd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['dlb'])|
                 (inci_dementia_min['dlb'].is_null()))
                ).then('ftd'), 
            when(
                (inci_dementia_1 == inci_dementia_min['dlb'])&
                ((inci_dementia_1 != inci_dementia_min['vd'])|
                 (inci_dementia_min['vd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['osd'])|
                 (inci_dementia_min['osd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['ftd'])|
                 (inci_dementia_min['ftd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['ad'])|
                 (inci_dementia_min['dlb'].is_null()))
                ).then('dlb'), 
            when(
                (inci_dementia_1 == inci_dementia_min['ad'])&
                (inci_dementia_1 == inci_dementia_min['vd'])&
                ((inci_dementia_1 != inci_dementia_min['osd'])|
                 (inci_dementia_min['osd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['ftd'])|
                 (inci_dementia_min['ftd'].is_null()))&
                ((inci_dementia_1 != inci_dementia_min['dlb'])|
                 (inci_dementia_min['dlb'].is_null()))
                ).then('advdmixed'),
            when(inci_dementia_1.is_not_null()).then('osdmixed'),  
            otherwise = None     
        )

# prevalent dementia subtypes before mid time point
inci_dementia_mid = {}
for name in ["osd", "ud", "ad", "vd", "ftd", "dlb"]:
    incident = []
    if "snomed" in olists[name]:
        incident.append(
            first_matching_tpp_between(olists[name]["snomed"], start_date_default, mid_date, death_date)
        )
    if "icd" in olists[name]:
        incident.append(
            first_matching_apc_between(olists[name]["icd"], start_date_default, mid_date, death_date, only_prim_diagnoses=False)
        )
        incident.append(
            first_matching_death_between(olists[name]["icd"], start_date_default, mid_date, death_date) 
        )
    if len(incident) ==1:
        tmp_incident_date = incident[0]
    else:
        tmp_incident_date = minimum_of(*incident)  
    inci_dementia_mid[name] = tmp_incident_date
inci_dementia_mid_1 = minimum_of(*inci_dementia_mid.values())
prevalent_dementia_mid = case(
            when(
                (inci_dementia_mid_1 == inci_dementia_mid['ad'])&
                ((inci_dementia_mid_1 != inci_dementia_mid['vd'])|
                    (inci_dementia_mid['vd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['osd'])|
                    (inci_dementia_mid['osd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['ftd'])|
                    (inci_dementia_mid['ftd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['dlb'])|
                    (inci_dementia_mid['dlb'].is_null()))
                ).then('ad'),
            when(
                (inci_dementia_mid_1 == inci_dementia_mid['vd'])&
                ((inci_dementia_mid_1 != inci_dementia_mid['ad'])|
                    (inci_dementia_mid['ad'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['osd'])|
                    (inci_dementia_mid['osd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['ftd'])|
                    (inci_dementia_mid['ftd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['dlb'])|
                    (inci_dementia_mid['dlb'].is_null()))
                ).then('vd'), 
            when(
                (inci_dementia_mid_1 == inci_dementia_mid['ud'])&
                ((inci_dementia_mid_1 != inci_dementia_mid['vd'])|
                    (inci_dementia_mid['vd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['osd'])|
                    (inci_dementia_mid['osd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['ad'])|
                    (inci_dementia_mid['ud'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['ftd'])|
                    (inci_dementia_mid['ftd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['dlb'])|
                    (inci_dementia_mid['dlb'].is_null()))
                ).then('ud'),   
            when(
                (inci_dementia_mid_1 == inci_dementia_mid['ftd'])&
                ((inci_dementia_mid_1 != inci_dementia_mid['vd'])|
                    (inci_dementia_mid['vd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['osd'])|
                    (inci_dementia_mid['osd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['ad'])|
                    (inci_dementia_mid['ftd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['dlb'])|
                    (inci_dementia_mid['dlb'].is_null()))
                ).then('ftd'), 
            when(
                (inci_dementia_mid_1 == inci_dementia_mid['dlb'])&
                ((inci_dementia_mid_1 != inci_dementia_mid['vd'])|
                    (inci_dementia_mid['vd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['osd'])|
                    (inci_dementia_mid['osd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['ftd'])|
                    (inci_dementia_mid['ftd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['ad'])|
                    (inci_dementia_mid['dlb'].is_null()))
                ).then('dlb'), 
            when(
                (inci_dementia_mid_1 == inci_dementia_mid['ad'])&
                (inci_dementia_mid_1 == inci_dementia_mid['vd'])&
                ((inci_dementia_mid_1 != inci_dementia_mid['osd'])|
                    (inci_dementia_mid['osd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['ftd'])|
                    (inci_dementia_mid['ftd'].is_null()))&
                ((inci_dementia_mid_1 != inci_dementia_mid['dlb'])|
                    (inci_dementia_mid['dlb'].is_null()))
                ).then('advdmixed'), 
            when(inci_dementia_mid_1.is_not_null()).then('osdmixed'),  
            otherwise = None
            )

for name, codes in olists.items():
    # For other neuro disease
    if name not in ["osd", "ud", "ad", "vd", 'ftd', 'dlb']:
        incident = {}
        prevalent_start = []
        prevalent_mid = []

        if "snomed" in codes:
            ## Primary care
            ### First incidence
            incident["primary"] = first_matching_tpp_between(codes["snomed"], start_date, pat_end_date, death_date)

            ### Identify prevalent cases
            prevalent_start.append(
                prevalent_tpp(codes["snomed"], start_date, death_date)
            )

            prevalent_mid.append(
                prevalent_tpp(codes["snomed"], mid_date_prev, death_date)
            )

        if "icd" in codes:
            ## Secondary care
            ### Frist incidence
            incident["secondary"] = first_matching_apc_between(codes["icd"], start_date, pat_end_date, death_date, only_prim_diagnoses=False)
            
            ### Identify prevalent cases
            prevalent_start.append(
                prevalent_apc(codes["icd"], start_date, death_date)
            )

            prevalent_mid.append(
                prevalent_apc(codes["icd"], mid_date_prev, death_date)
            )         
            
            ## Death
            ### First incidence
            incident["death"] = first_matching_death_between(codes["icd"], start_date, pat_end_date, death_date)
            
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
            tmp_incident_date = list(incident.values())[0]
        elif len(incident) > 1:
            tmp_incident_date  = minimum_of(*incident.values())

        setattr(
            dataset,
            f"inumer_bin_{name}",
            case(
                when(tmp_pnumer_bin_start == 1).then(0),
                when(tmp_incident_date.is_not_null()).then(1),
                otherwise=0,
            )
        )

        # Incidence denominator
        tmp_idenom_num = minimum_of(pat_end_date, tmp_incident_date)
        setattr(
            dataset,
            f"idenom_num_{name}",
            case(
                when(tmp_pnumer_bin_start == 1).then(0),
                otherwise = maximum_of(0,(tmp_idenom_num - start_date).days)
            )
        )

        # Add data source for first incidence
        if len(incident) == 1:
            setattr(
                    dataset,
                    f"inci_primary_bin_{name}",
                    case(
                        when(getattr(dataset, f"inumer_bin_{name}")==0).then(0),
                        when(list(incident.keys())[0] == "primary").then(1),
                        otherwise = 0                
                    )
            )
            setattr(
                    dataset,
                    f"inci_secondary_bin_{name}",
                    case(
                        when(getattr(dataset, f"inumer_bin_{name}")==0).then(0),
                        when(list(incident.keys())[0] == "secondary").then(1),
                        otherwise = 0                
                    )
            )
            setattr(
                    dataset,
                    f"inci_death_bin_{name}",
                    case(
                        when(getattr(dataset, f"inumer_bin_{name}")==0).then(0),
                        when(list(incident.keys())[0] == "death").then(1),
                        otherwise = 0                
                    )
            )
        else:
            setattr(
                    dataset,
                    f"inci_primary_bin_{name}",
                    case(
                        when(getattr(dataset, f"inumer_bin_{name}")==0).then(0),
                        when(tmp_incident_date == incident["primary"]).then(1),
                        otherwise = 0              
                    )
            )
            setattr(
                    dataset,
                    f"inci_secondary_bin_{name}",
                    case(
                        when(getattr(dataset, f"inumer_bin_{name}")==0).then(0),
                        when(tmp_incident_date == incident["secondary"]).then(1),
                        otherwise = 0              
                    )
            )
            setattr(
                    dataset,
                    f"inci_death_bin_{name}",
                    case(
                        when(getattr(dataset, f"inumer_bin_{name}")==0).then(0),
                        when(tmp_incident_date == incident["death"]).then(1),
                        otherwise = 0              
                    )
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

# For dementia subtypes
for name in ['ad', 'vd', 'ud', 'ftd', 'dlb', 'advdmixed', 'osdmixed']:
    # Prevalence numerator
    setattr(dataset,
        f"pnumer_bin_{name}",
        case(
            when((death_date<mid_date)|~(practice_registrations.exists_for_patient_on(mid_date))).then(0),
            when(prevalent_dementia_mid == name).then(1),
            otherwise=0
            )
    )   

    # Incidence numerator 
    setattr(
        dataset,
        f"inumer_bin_{name}",
        case(
            when(prevalent_dementia_start == 1).then(0),
            when(inci_dementia_status == name).then(1),
            otherwise=0,
        )
    )

    # Incidence denominator
    tmp_idenom_num = minimum_of(pat_end_date, inci_dementia_1)
    setattr(
        dataset,
        f"idenom_num_{name}",
        case(
            when(prevalent_dementia_start == 1).then(0),
            otherwise = maximum_of(0,(tmp_idenom_num - start_date).days)
        )
    )

    #Add data source for first incidence
    if name not in ['advdmixed', 'osdmixed']:
        if len(inci_dementia_source[name]) == 1:
            setattr(
                    dataset,
                    f"inci_primary_bin_{name}",
                    case(
                        when(getattr(dataset, f"inumer_bin_{name}")==0).then(0),
                        when(list(inci_dementia_source[name].keys())[0] == "primary").then(1),
                        otherwise = 0                
                    )
            )
            setattr(
                    dataset,
                    f"inci_secondary_bin_{name}",
                    case(
                        when(getattr(dataset, f"inumer_bin_{name}")==0).then(0),
                        when(list(inci_dementia_source[name].keys())[0] == "secondary").then(1),
                        otherwise = 0                
                    )
            )
            setattr(
                    dataset,
                    f"inci_death_bin_{name}",
                    case(
                        when(getattr(dataset, f"inumer_bin_{name}")==0).then(0),
                        when(list(inci_dementia_source[name].keys())[0] == "death").then(1),
                        otherwise = 0                
                    )
            )
        else:    
            setattr(
                    dataset,
                    f"inci_primary_bin_{name}",
                    case(
                        when(getattr(dataset, f"inumer_bin_{name}")==0).then(0),
                        when(inci_dementia_1 == inci_dementia_source[name]["primary"]).then(1),
                        otherwise = 0              
                    )
            )
            setattr(
                    dataset,
                    f"inci_secondary_bin_{name}",
                    case(
                        when(getattr(dataset, f"inumer_bin_{name}")==0).then(0),
                        when(inci_dementia_1 == inci_dementia_source[name]["secondary"]).then(1),
                        otherwise = 0              
                    )
            )
            setattr(
                    dataset,
                    f"inci_death_bin_{name}",
                    case(
                        when(getattr(dataset, f"inumer_bin_{name}")==0).then(0),
                        when(inci_dementia_1 == inci_dementia_source[name]["death"]).then(1),
                        otherwise = 0              
                    )
            )
    
    # Case fatality numerator
    setattr(
        dataset,
        f"fnumer_bin_1y_{name}",
        case(when((getattr(dataset,f"inumer_bin_{name}")==1) & 
                ((death_date - inci_dementia_1).years <=1) &
                (practice_registrations.exists_for_patient_on(death_date))
                ).then(1),
            otherwise=0
        )
    )
    
    setattr(
        dataset,
        f"fnumer_bin_5y_{name}",
        case(when((getattr(dataset,f"inumer_bin_{name}")==1) & 
                ((death_date - inci_dementia_1).years <=5) &
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