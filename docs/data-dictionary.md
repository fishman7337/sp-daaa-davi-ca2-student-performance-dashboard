# Data Dictionary

The project uses four source datasets and four cleaned datasets. Raw workbooks are stored in `data/raw/`; cleaned workbooks used by the app are stored in `data/processed/`.

## Raw Datasets

| Workbook | Rows | Columns | Fields |
| --- | ---: | ---: | --- |
| `Course Codes.xlsx` | 7 | 2 | `CODE`, `COURSE NAME` |
| `Student Profiles.xlsx` | 307 | 15 | `STUDENT ID`, `GENDER`, `SG CITIZEN`, `SG PR`, `FOREIGNER`, `COUNTRY OF OTHER NATIONALITY`, `DOB`, `HIGHEST QUALIFICATION`, `NAME OF QUALIFICATION AND INSTITUTION`, `DATE ATTAINED HIGHEST QUALIFICATION`, `DESIGNATION`, `COMMENCEMENT DATE`, `COMPLETION DATE`, `FULL-TIME OR PART-TIME`, `COURSE FUNDING` |
| `Student Results.xlsx` | 555 | 4 | `STUDENT ID`, `PERIOD`, `GPA`, `ATTENDANCE` |
| `Student Survey.xlsx` | 543 | 8 | `STUDENT ID`, `PERIOD`, `PRIOR KNOWLEDGE`, `COURSE RELEVANCE`, `TEACHING SUPPORT`, `COMPANY SUPPORT`, `FAMILY SUPPORT`, `SELF-STUDY HRS` |

## Processed Datasets

| Workbook | Rows | Columns | Fields |
| --- | ---: | ---: | --- |
| `Course Codes.xlsx` | 7 | 2 | `Code`, `Course Name` |
| `Student Profiles.xlsx` | 295 | 15 | `Student Id`, `Gender`, `Sg Citizen`, `Sg Pr`, `Foreigner`, `Country Of Other Nationality`, `Dob`, `Highest Qualification`, `Name Of Qualification And Institution`, `Date Attained Highest Qualification`, `Designation`, `Commencement Date`, `Completion Date`, `Full-Time Or Part-Time`, `Course Funding` |
| `Student Results.xlsx` | 522 | 4 | `Student Id`, `Period`, `Gpa`, `Attendance` |
| `Student Survey.xlsx` | 531 | 8 | `Student Id`, `Period`, `Prior Knowledge`, `Course Relevance`, `Teaching Support`, `Company Support`, `Family Support`, `Self-Study Hrs` |

## Notes

- `Student Id` is the common join key used across profile, result, and survey data.
- Course code is derived from the first four digits of `Student Id` and mapped to `Course Name`.
- Processed datasets are expected to be reproducible from the notebook cleaning workflow.
- The dashboard loads the processed workbooks only.
