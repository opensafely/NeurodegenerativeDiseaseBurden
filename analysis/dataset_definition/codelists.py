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

