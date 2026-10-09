from ehrql import codelist_from_csv

ethnicity_codelist = codelist_from_csv(
    "codelists/opensafely-ethnicity-snomed-0removed.csv",
    column="code",
    category_column="Label_16",
)

#Multimorbidity

alcohol_codelist = codelist_from_csv(
    "codelists/bristol-cambridge-multimorbidity-score-alcohol-problems.csv",
    column="code"
)

anxiety_codelist = codelist_from_csv(
    "codelists/bristol-cambridge-multimorbidity-score-anxiety-or-depression.csv",
    column="code"
)

af_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_atrial-fibrillation.csv",
    column="code"
)

cancer_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_cancer.csv",
    column="code"
)

ckd_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_chronic-kidney-disease.csv",
    column="code"
)

copd_codelist = codelist_from_csv(
    "codelists/bristol-cambridge-multimorbidity-score-copd.csv",
    column="code"
)

dementia_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_dementia.csv",
    column="code"
)

diabetes_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_diabetes.csv",
    column="code"
)

epilepsy_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_epilepsy.csv",
    column="code"
)

hf_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_heart-failure.csv",
    column="code"
)

bowel_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_irritable-bowel-syndrome.csv",
    column="code"
)

psychosis_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_psychosisbipolar-disorder.csv",
    column="code"
)

cld_codelist = codelist_from_csv(
    "codelists/bristol-cambridge-multimorbidity-score-chronic-liver-disease-and-viral-hepatitis.csv",
    column="code"
)

prostate_codelist = codelist_from_csv(
    "codelists/bristol-cambridge-multimorbidity-score-disorder-of-prostate.csv",
    column="code"
)

learning_codelist = codelist_from_csv(
    "codelists/bristol-cambridge-multimorbidity-score-learning-disability.csv",
    column="code"
)

sclerosis_codelist = codelist_from_csv(
    "codelists/bristol-cambridge-multimorbidity-score-multiple-sclerosis.csv",
    column="code"
)

parkinsonism_codelist = codelist_from_csv(
    "codelists/bristol-cambridge-multimorbidity-score-parkinsonism.csv",
    column="code"
)

perivascular_codelist = codelist_from_csv(
    "codelists/bristol-cambridge-multimorbidity-score-peripheral-vascular-disease-leg.csv",
    column="code"
)

psychosub_codelist = codelist_from_csv(
    "codelists/bristol-cambridge-multimorbidity-score-substance-misuse.csv",
    column="code"
)

epilepsy_medlist = codelist_from_csv(
    "codelists/bristol-multimorbidity_prescription_epilepsy_bnf_dmd_converted.csv",
    column="dmd_id"
)

bowel_medlist = codelist_from_csv(
    "codelists/bristol-multimorbidity_prescription_anti_spasmodic_bnf-dmd.csv",
    column="dmd_id"
)

psychosis_medlist = codelist_from_csv(
    "codelists/bristol-multimorbidity_prescription_schizophrenia_bipolar_disorder_bnf-dmd.csv",
    column="dmd_id"
)

constipation_medlist = codelist_from_csv(
    "codelists/bristol-multimorbidity_prescription_constipation_bnf_dmd_converted.csv",
    column="dmd_id"
)

anxiety_medlist = codelist_from_csv(
    "codelists/bristol-multimorbidity_prescription_anxiolytics_anti_depressants_bnf-dmd.csv",
    column="dmd_id"
)

pain_medlist1 = codelist_from_csv(
    "codelists/bristol-multimorbidity_prescription_analgesics_opiods_exc_migraine_bnf_dmd_converted.csv",
    column="dmd_id"
)

pain_medlist2 = codelist_from_csv(
    "codelists/bristol-multimorbidity_prescription_antiepileptics_for_pain_bnf_dmd_converted.csv",
    column="dmd_id"
)


#Outcomes

specified_dementia_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-other-specified-snomed.csv",
    column="code"
)

specified_dementia_icd = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-other-specified-dementia-icd10.csv",
    column="code"
)

unspecified_dementia_icd = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-unspecified-dementia-icd10.csv",
    column="code"
)

unspecified_dementia_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-unspecified-dementia-snomed.csv",
    column="code"
)

alzheimers_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-alzheimers-disease-snomed.csv",
    column="code"
)

alzheimers_icd = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-alzheimers-disease.csv",
    column="code"
)

cjd_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-creutzfeldt-jakob-disease-snomed.csv",
    column="code"
)

cjd_icd = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-creutzfeldt-jakob-disease.csv",
    column="code"
)

parkinsons_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-parkinsons-disease-snomed.csv",
    column="code"
)

parkinsons_icd = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-parkinsons-disease.csv",
    column="code"
)

frontotemporal_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-frontotemporal-dementia-snomed.csv",
    column="code"
)

frontotemporal_icd = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-frontotemporal-dementia.csv",
    column="code"
)

motor_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-motor-neurone-disease-snomed.csv",
    column="code"
)

motor_icd = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-motor-neuron-disease.csv",
    column="code"
)

palsy_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-progressive-supranuclear-palsy-snomed.csv",
    column="code"
)

palsy_icd = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-progressive-supranuclear-palsy.csv",
    column="code"
)

vascular_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-vascular-dementia-snomed.csv",
    column="code"
)

vascular_icd = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-vascular-dementia.csv",
    column="code"
)

huntingtons_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-dementia-due-to-huntingtons-snomed.csv",
    column="code"
)

huntingtons_icd = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-huntington-disease.csv",
    column="code"
)

multiatrophy_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-multiple-system-atrophy-snomed.csv",
    column="code"
)

multiatrophy_icd = codelist_from_csv(
    "codelists/local/neuro_codelist_msa_icd.csv",
    column="code"
)

corticobasal_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-corticobasal-degeneration-snomed.csv",
    column="code"
)

lewybody_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-lewy-body-dementia-snomed.csv",
    column="code"
)



