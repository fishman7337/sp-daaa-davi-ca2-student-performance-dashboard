from __future__ import annotations

from pathlib import Path

import pandas as pd

from conftest import PROJECT_ROOT


RAW_DATASETS = {
    "Course Codes.xlsx": ["CODE", "COURSE NAME"],
    "Student Profiles.xlsx": [
        "STUDENT ID",
        "GENDER",
        "SG CITIZEN",
        "SG PR",
        "FOREIGNER",
        "COUNTRY OF OTHER NATIONALITY",
        "DOB",
        "HIGHEST QUALIFICATION",
        "NAME OF QUALIFICATION AND INSTITUTION",
        "DATE ATTAINED HIGHEST QUALIFICATION",
        "DESIGNATION",
        "COMMENCEMENT DATE",
        "COMPLETION DATE",
        "FULL-TIME OR PART-TIME",
        "COURSE FUNDING",
    ],
    "Student Results.xlsx": ["STUDENT ID", "PERIOD", "GPA", "ATTENDANCE"],
    "Student Survey.xlsx": [
        "STUDENT ID",
        "PERIOD",
        "PRIOR KNOWLEDGE",
        "COURSE RELEVANCE",
        "TEACHING SUPPORT",
        "COMPANY SUPPORT",
        "FAMILY SUPPORT",
        "SELF-STUDY HRS",
    ],
}

PROCESSED_DATASETS = {
    "Course Codes.xlsx": ["Code", "Course Name"],
    "Student Profiles.xlsx": [
        "Student Id",
        "Gender",
        "Sg Citizen",
        "Sg Pr",
        "Foreigner",
        "Country Of Other Nationality",
        "Dob",
        "Highest Qualification",
        "Name Of Qualification And Institution",
        "Date Attained Highest Qualification",
        "Designation",
        "Commencement Date",
        "Completion Date",
        "Full-Time Or Part-Time",
        "Course Funding",
    ],
    "Student Results.xlsx": ["Student Id", "Period", "Gpa", "Attendance"],
    "Student Survey.xlsx": [
        "Student Id",
        "Period",
        "Prior Knowledge",
        "Course Relevance",
        "Teaching Support",
        "Company Support",
        "Family Support",
        "Self-Study Hrs",
    ],
}


def _assert_workbook_contract(folder: Path, expected: dict[str, list[str]]) -> None:
    for filename, expected_columns in expected.items():
        workbook = folder / filename
        assert workbook.exists(), f"Missing workbook: {workbook}"

        frame = pd.read_excel(workbook)
        assert not frame.empty, f"Workbook should not be empty: {workbook}"
        assert list(frame.columns) == expected_columns


def test_raw_workbooks_match_expected_contract() -> None:
    _assert_workbook_contract(PROJECT_ROOT / "data" / "raw", RAW_DATASETS)


def test_processed_workbooks_match_expected_contract() -> None:
    _assert_workbook_contract(PROJECT_ROOT / "data" / "processed", PROCESSED_DATASETS)


def test_processed_student_ids_have_strong_overlap_across_core_datasets() -> None:
    processed = PROJECT_ROOT / "data" / "processed"
    profiles = pd.read_excel(processed / "Student Profiles.xlsx")
    results = pd.read_excel(processed / "Student Results.xlsx")
    survey = pd.read_excel(processed / "Student Survey.xlsx")

    profile_ids = set(profiles["Student Id"].dropna())
    result_ids = set(results["Student Id"].dropna())
    survey_ids = set(survey["Student Id"].dropna())

    assert profile_ids
    assert len(result_ids & profile_ids) / len(result_ids) >= 0.95
    assert len(survey_ids & profile_ids) / len(survey_ids) >= 0.95
