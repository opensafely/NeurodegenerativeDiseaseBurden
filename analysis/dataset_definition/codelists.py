from ehrql import codelist_from_csv

prostate_snomed = codelist_from_csv(
    "codelists/user-RochelleKnight-prostate_cancer_snomed.csv",
    column="code"
)

prostate_icd = codelist_from_csv(
    "codelists/user-RochelleKnight-prostate_cancer_icd10.csv",
    column="code"
)

pregnancy_snomed = codelist_from_csv(
    "codelists/nhsd-primary-care-domain-refsets-c19preg_cod.csv",
    column="code"
)

ethnicity_codelist = codelist_from_csv(
    "codelists/opensafely-ethnicity-snomed-0removed.csv",
    column="code",
    category_column="Label_16",
)

#Multimorbidity

alcohol_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_alcoholproblems.csv",
    column="code"
)

anxiety_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_anxietydepression.csv",
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

tissue_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_connective-tissue-disorder.csv",
    column="code"
)

copd_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_copd.csv",
    column="code"
)

chd_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_coronary-heart-disease.csv",
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

hearloss_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_hearing-loss.csv",
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

stroke_codelist = codelist_from_csv(
    "codelists/bristol-multimorbidity_stroketransient-ischemic-attack.csv",
    column="code"
)

asthma_codelist = codelist_from_csv(
    "codelists/nhsd-primary-care-domain-refsets-ast_cod.csv",
    column="code"
)

hypertension_codelist = codelist_from_csv(
    "codelists/nhsd-primary-care-domain-refsets-hyp_cod.csv",
    column="code"
)

constipation_codelist = codelist_from_csv(
    "codelists/nhsd-primary-care-domain-refsets-chronconstip_cod.csv", 
    column="code"
)

pain_codelist = codelist_from_csv(
    "codelists/opensafely-symptoms-pain.csv",
    column="code"
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
    "codelists/bristol-burden-of-neurodegenerative-diseases-motor-neuron-disease-snomed.csv",
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

postcortical_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-posterior-cortical-atrophy-snomed.csv",
    column="code"
)

lewybody_snomed = codelist_from_csv(
    "codelists/bristol-burden-of-neurodegenerative-diseases-diffuse-lewy-body-disease-snomed.csv",
    column="code"
)



