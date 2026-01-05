from ehrql import codelist_from_csv

prostate_snomed = codelist_from_csv(
    "codelists/user-RochelleKnight-prostate_cancer_snomed.csv",
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

athma_codelist = codelist_from_csv(
    "codelists/nhsd-primary-care-domain-refsets-ast_cod.csv",
    column="code"
)
hypertension_codelist = codelist_from_csv(
    "codelists/nhsd-primary-care-domain-refsets-hyp_cod.csv",
    column="code"
)

constipation_codelist = codelist_from_csv(
    "codelists/",
    column="code"
)

pain_codelist = codelist_from_csv(
    "codelists/",
    column="code"
)



