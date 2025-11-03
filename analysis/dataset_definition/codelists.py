from ehrql import codelist_from_csv

prostate_cancer_snomed = codelist_from_csv(
    "codelists/user-RochelleKnight-prostate_cancer_snomed.csv",
    column="code"
)
