"""Dash app extracted from DAVI-CA2.ipynb for cloud deployment on Render.

This file is generated from the notebook's dashboard cell and intentionally keeps
notebook logic intact while adding server-friendly startup and data loading.
"""

from __future__ import annotations

import os
import re
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import dash
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Cleaned-Data"


def _load_cleaned_excel(filename: str) -> pd.DataFrame:
    """Load a cleaned workbook from the repository's Cleaned-Data folder."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing required data file: {path}")
    return pd.read_excel(path)


# Notebook dashboard cell expects these DataFrames to already exist.
df_course_codes = _load_cleaned_excel("Course Codes.xlsx")
df_student_profile = _load_cleaned_excel("Student Profiles.xlsx")
df_student_result = _load_cleaned_excel("Student Results.xlsx")
df_student_survey = _load_cleaned_excel("Student Survey.xlsx")

# =========================
# 0) Imports + Constants
# =========================
warnings.filterwarnings("ignore")






STUDENT_ID_COL = "Student Id"
DERIVED_COURSE_COL = "Course Code (Derived)"
COURSE_NAME_COL = "Course Name (Derived)"
COURSE_CODE_MASTER_COL = "Code"
COURSE_NAME_MASTER_COL = "Course Name"
COURSE_DISPLAY_COL = COURSE_NAME_COL
ENGAGEMENT_COL = "Engagement Score"
PERFORMANCE_INDEX_COL = "Performance Index"
RISK_FLAG_COL = "Risk Flag"
MOMENTUM_GAP_COL = "Momentum Gap"
COURSE_LEVEL_COL = "Course Level"
COURSE_FUNDING_COL = "Course Funding"
HIGHEST_EDU_COL = "Highest Qualification"
PERCEPTION_SCORE_COL = "Perception Score"
RISK_SCORE_COL = "Risk Score"
RISK_TIER_COL = "Risk Tier"
EXPECTED_GPA_COL = "Expected GPA"


# Profile
GENDER_COL = "Gender"
COMPLETION_DATE_COL = "Completion Date"

# Result
GPA_COL = "Gpa"
ATTEND_COL = "Attendance"
PERIOD_COL = "Period"

# Survey
SELF_STUDY_COL = "Self-Study Hrs"
LIKERT_COLS = [
    "Prior Knowledge",
    "Course Relevance",
    "Teaching Support",
    "Company Support",
    "Family Support",
]

TOP_N_MIN = 3
TOP_N_MAX = 20
MIN_COURSE_COUNT = 5
MIN_CORR_PAIRS = 5
MIN_DIST_COURSES = 3
GPA_PAD_RATIO = 0.08
GPA_PAD_MIN = 0.2
CORR_RANGE_PAD = 0.15
CORR_RANGE_MAX = 1.0

PERCEPTION_LABEL_MAP = {
    PERCEPTION_SCORE_COL: "Perception Score (Composite)",
    SELF_STUDY_COL: "Self-Study Hours",
}

# Dashboard 1 visual system (cute pastel on light canvas)
DASH1_COLORWAY = ["#FF8FB1", "#7BDFF2", "#FFD166", "#BDE0FE", "#CDB4DB", "#A0E8AF"]
DASH1_BG = "#FFF5F8"
DASH1_PLOT_BG = "#FFFFFF"
DASH1_GRID = "rgba(140, 126, 150, 0.25)"
DASH1_TEXT = "#3B2E3A"
DASH1_MUTED = "#8C7E96"
DASH1_FONT = "Nunito, Segoe UI, Arial, sans-serif"

DASH1_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=DASH1_FONT, size=12, color=DASH1_TEXT),
        colorway=DASH1_COLORWAY,
        hoverlabel=dict(bgcolor="#FFF0F6", font_color="#3B2E3A", font_size=12, font_family=DASH1_FONT),
        title=dict(x=0.02, xanchor="left"),
        margin=dict(l=48, r=28, t=72, b=64),
        xaxis=dict(showgrid=True, gridcolor=DASH1_GRID, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=DASH1_GRID, zeroline=False),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.0,
            bgcolor="rgba(255, 255, 255, 0.85)",
            bordercolor="rgba(140, 126, 150, 0.25)",
            borderwidth=1,
            font=dict(size=10, color=DASH1_TEXT),
            itemsizing="constant",
        ),
    )
)




# =========================
# 1) Helper Functions (PEP 257 + Google Docstrings)
# =========================
def to_string_clean(series: pd.Series) -> pd.Series:
    """Convert a Series to pandas string dtype and normalise blanks/dashes to NA.

    Args:
        series: Input Series.

    Returns:
        Cleaned pandas string Series.
    """
    s = series.astype("string").str.strip()
    return s.replace({"": pd.NA, "-": pd.NA, "N.A.": "N.A.", "N.A": "N.A."})


def extract_course_code(student_id: pd.Series) -> pd.Series:
    """Extract the first 4 digits of Student Id as a derived Course Code.

    Args:
        student_id: Series containing student identifiers.

    Returns:
        Series of extracted 4-digit course codes (string dtype).
    """
    s = to_string_clean(student_id)
    return s.str.extract(r"^(\d{4})", expand=False).astype("string")



def _build_course_name_map(df_codes: Optional[pd.DataFrame]) -> Dict[str, str]:
    """Build a mapping of course code to course name."""
    if df_codes is None:
        return {}
    if COURSE_CODE_MASTER_COL not in df_codes.columns or COURSE_NAME_MASTER_COL not in df_codes.columns:
        return {}
    codes = (
        df_codes[COURSE_CODE_MASTER_COL]
        .astype("string")
        .str.strip()
        .replace({"": pd.NA})
    )
    codes = codes.str.zfill(4)
    names = df_codes[COURSE_NAME_MASTER_COL].astype("string").str.strip()
    mapping = {}
    for code, name in zip(codes, names):
        if pd.isna(code):
            continue
        if pd.isna(name) or name == "":
            mapping[str(code)] = str(code)
        else:
            mapping[str(code)] = str(name)
    return mapping
def safe_float(series: pd.Series, dtype: str = "Float32") -> pd.Series:
    """Coerce a Series to numeric float, safely preserving missing values.

    Args:
        series: Input Series.
        dtype: Target pandas dtype.

    Returns:
        Numeric Series with nullable float dtype.
    """
    return pd.to_numeric(series, errors="coerce").astype(dtype)


def safe_int(series: pd.Series, dtype: str = "Int16") -> pd.Series:
    """Coerce a Series to numeric integer, safely preserving missing values.

    Args:
        series: Input Series.
        dtype: Target pandas dtype.

    Returns:
        Numeric Series with nullable integer dtype.
    """
    return pd.to_numeric(series, errors="coerce").astype(dtype)


def add_completion_status(df: pd.DataFrame) -> pd.DataFrame:
    """Add a Completion Status label without fabricating completion dates.

    Logic:
    - If Completion Date is missing/blank/'N.A.' => Ongoing
    - Else => Completed

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with a new 'Completion Status' column.
    """
    out = df.copy()

    if COMPLETION_DATE_COL not in out.columns:
        out["Completion Status"] = "N.A."
        return out

    c = to_string_clean(out[COMPLETION_DATE_COL])
    ongoing_mask = c.isna() | c.eq("N.A.")
    out["Completion Status"] = np.where(ongoing_mask, "Ongoing", "Completed")
    return out


def build_analytics_df(
    df_student_profile: pd.DataFrame,
    df_student_result: pd.DataFrame,
    df_student_survey: pd.DataFrame,
    df_course_codes: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Build an analytics-ready DataFrame for plotting (Notebook-friendly).

    Merge strategy:
    - Base: df_student_profile
    - Left join df_student_result on Student Id
    - Left join df_student_survey on Student Id

    Adds:
    - Course Code (Derived)
    - Course Name (Derived)
    - Completion Status

    Args:
        df_student_profile: Student Profile dataset.
        df_student_result: Student Result dataset.
        df_student_survey: Student Survey dataset.
        df_course_codes: Optional course codes reference table.

    Returns:
        Merged analytics DataFrame.
    """
    profile = df_student_profile.copy()
    result = df_student_result.copy()
    survey = df_student_survey.copy()

    for df in (profile, result, survey):
        if STUDENT_ID_COL not in df.columns:
            raise KeyError(f"Missing required column '{STUDENT_ID_COL}' in one dataset.")
        df[STUDENT_ID_COL] = to_string_clean(df[STUDENT_ID_COL])

    # Derive course code from profile (source of truth)
    profile[DERIVED_COURSE_COL] = extract_course_code(profile[STUDENT_ID_COL]).str.zfill(4)

    course_map = _build_course_name_map(df_course_codes)
    if course_map:
        profile[COURSE_NAME_COL] = profile[DERIVED_COURSE_COL].map(course_map)
        profile[COURSE_NAME_COL] = (
            profile[COURSE_NAME_COL]
            .fillna(profile[DERIVED_COURSE_COL])
            .astype("string")
        )
    else:
        profile[COURSE_NAME_COL] = profile[DERIVED_COURSE_COL].astype("string")


    # Light normalisation for commonly used columns
    if GENDER_COL in profile.columns:
        profile[GENDER_COL] = to_string_clean(profile[GENDER_COL]).fillna("N.A.")

    if HIGHEST_EDU_COL in profile.columns:
        profile[HIGHEST_EDU_COL] = to_string_clean(profile[HIGHEST_EDU_COL]).fillna("N.A.")

    if PERIOD_COL in result.columns:
        result[PERIOD_COL] = to_string_clean(result[PERIOD_COL]).fillna("N.A.")

    if GPA_COL in result.columns:
        result[GPA_COL] = safe_float(result[GPA_COL], "Float32")

    if ATTEND_COL in result.columns:
        result[ATTEND_COL] = safe_int(result[ATTEND_COL], "Int16")

    if SELF_STUDY_COL in survey.columns:
        survey[SELF_STUDY_COL] = safe_int(survey[SELF_STUDY_COL], "Int16")

    for col in LIKERT_COLS:
        if col in survey.columns:
            survey[col] = safe_int(survey[col], "Int8")

    merged = (
        profile.merge(result, on=STUDENT_ID_COL, how="left", suffixes=("", "_result"))
        .merge(survey, on=STUDENT_ID_COL, how="left", suffixes=("", "_survey"))
    )

    merged = add_completion_status(merged)

    # Unify Period for filtering: prefer result Period; else survey Period if exists
    period_candidates: List[pd.Series] = []
    if PERIOD_COL in merged.columns:
        period_candidates.append(merged[PERIOD_COL])
    if f"{PERIOD_COL}_survey" in merged.columns:
        period_candidates.append(merged[f"{PERIOD_COL}_survey"])

    if period_candidates:
        unified = period_candidates[0].copy()
        for s in period_candidates[1:]:
            unified = unified.fillna(s)
        merged["Period (Unified)"] = unified
    else:
        merged["Period (Unified)"] = pd.NA

    return merged


def filter_df(
    df: pd.DataFrame,
    courses: Optional[Tuple[str, ...]],
    periods: Optional[Tuple[str, ...]],
    genders: Optional[Tuple[str, ...]],
    statuses: Optional[Tuple[str, ...]],
    gpa_range: Tuple[float, float],
    attendance_range: Tuple[int, int],
    course_levels: Optional[Tuple[str, ...]] = None,
    highest_edus: Optional[Tuple[str, ...]] = None,
    funding_types: Optional[Tuple[str, ...]] = None,
    apply_gpa_att: bool = True,
    apply_courses: bool = True,
    apply_course_levels: bool = True,
    apply_highest_edu: bool = True,
    apply_funding: bool = True,
) -> pd.DataFrame:
    """Filter analytics DataFrame based on UI selections.

    Args:
        df: Analytics DataFrame.
        courses: Selected courses.
        course_levels: Selected course levels.
        highest_edus: Selected highest qualification values.
        funding_types: Selected funding types.
        periods: Selected periods.
        genders: Selected genders.
        statuses: Selected completion statuses.
        gpa_range: (min, max) GPA range.
        attendance_range: (min, max) Attendance range.
        apply_gpa_att: Whether to apply GPA/attendance range filters.
        apply_courses: Whether to apply course filter.
        apply_course_levels: Whether to apply course level filter.
        apply_highest_edu: Whether to apply highest qualification filter.
        apply_funding: Whether to apply funding filter.

    Returns:
        Filtered DataFrame.
    """
    out = df.copy()

    course_col = COURSE_DISPLAY_COL if COURSE_DISPLAY_COL in out.columns else DERIVED_COURSE_COL



    if courses and apply_courses:
        out = out[out[course_col].isin(list(courses))]

    if course_levels and apply_course_levels:
        if COURSE_LEVEL_COL in out.columns:
            out = out[out[COURSE_LEVEL_COL].isin(list(course_levels))]
        else:
            tokens = [str(level).strip().lower() for level in course_levels if str(level).strip()]
            if tokens:
                course_series = out[course_col].astype("string").str.lower().fillna("")
                mask = course_series.apply(lambda name: any(tok in name for tok in tokens))
                out = out[mask]

    if highest_edus and apply_highest_edu and HIGHEST_EDU_COL in out.columns:
        out = out[out[HIGHEST_EDU_COL].isin(list(highest_edus))]

    if funding_types and apply_funding and COURSE_FUNDING_COL in out.columns:
        out = out[out[COURSE_FUNDING_COL].isin(list(funding_types))]

    if periods:
        out = out[out["Period (Unified)"].isin(list(periods))]

    if genders and GENDER_COL in out.columns:
        out = out[out[GENDER_COL].isin(list(genders))]

    if statuses and "Completion Status" in out.columns:
        out = out[out["Completion Status"].isin(list(statuses))]

    if apply_gpa_att:
        if GPA_COL in out.columns:
            lo, hi = gpa_range
            out = out[out[GPA_COL].between(lo, hi, inclusive="both")]

        if ATTEND_COL in out.columns:
            lo, hi = attendance_range
            out = out[out[ATTEND_COL].between(lo, hi, inclusive="both")]

    return out



def _apply_dynamic_risk(
    df: pd.DataFrame,
    gpa_threshold: float,
    att_threshold: float,
) -> pd.DataFrame:
    """Apply threshold-based risk tiers using GPA and attendance only."""
    out = df.copy()

    gpa_vals = (
        pd.to_numeric(out[GPA_COL], errors="coerce")
        if GPA_COL in out.columns
        else pd.Series(np.nan, index=out.index)
    )
    att_vals = (
        pd.to_numeric(out[ATTEND_COL], errors="coerce")
        if ATTEND_COL in out.columns
        else pd.Series(np.nan, index=out.index)
    )

    gpa_default = float(gpa_vals.median()) if gpa_vals.notna().any() else 0.0
    att_default = float(att_vals.median()) if att_vals.notna().any() else 0.0

    def _coerce_threshold(value, fallback):
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(fallback)

    gpa_threshold = _coerce_threshold(gpa_threshold, gpa_default)
    att_threshold = _coerce_threshold(att_threshold, att_default)

    data_mask = gpa_vals.notna() | att_vals.notna()
    if not data_mask.any():
        return out

    gpa_below = pd.Series(False, index=out.index, dtype="boolean")
    att_below = pd.Series(False, index=out.index, dtype="boolean")
    if gpa_vals.notna().any():
        gpa_below = (gpa_vals < gpa_threshold).fillna(False)
    if att_vals.notna().any():
        att_below = (att_vals < att_threshold).fillna(False)
    gpa_below = gpa_below.fillna(False)
    att_below = att_below.fillna(False)

    both_below = gpa_below & att_below
    one_below = gpa_below ^ att_below

    risk_score = pd.Series(np.nan, index=out.index, dtype=float)
    risk_score[data_mask] = np.select(
        [both_below[data_mask], one_below[data_mask]],
        [1.0, 0.5],
        default=0.0,
    )
    out[RISK_SCORE_COL] = risk_score

    tier_series = pd.Series(pd.NA, index=out.index, dtype="string")
    tier_series[data_mask] = np.select(
        [both_below[data_mask], one_below[data_mask]],
        ["High", "Medium"],
        default="Low",
    )
    out[RISK_TIER_COL] = tier_series

    risk_flag = pd.Series(np.where(both_below, 1, 0), index=out.index).astype("Int64")
    risk_flag[~data_mask] = pd.NA
    out[RISK_FLAG_COL] = risk_flag

    return out


def _apply_dash1_layout(fig: go.Figure, title: str, height: int = 440, subtitle: Optional[str] = None) -> go.Figure:
    """Apply the Dashboard 1 visual system to a figure."""
    full_title = title
    if subtitle:
        full_title = f"{title}<br><span style='font-size:11px;color:{DASH1_MUTED}'>{subtitle}</span>"
    fig.update_layout(
        template=DASH1_TEMPLATE,
        title=dict(
            text=full_title,
            x=0.01,
            xanchor="left",
            y=0.97,
            yanchor="top",
            font=dict(size=18, color=DASH1_TEXT),
        ),
        height=height,
        margin=dict(l=56, r=28, t=120, b=64),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(8,12,22,0.85)",
            bordercolor="rgba(140, 126, 150, 0.25)",
            borderwidth=1,
            font=dict(size=10, color=DASH1_TEXT),
        ),
        hovermode="closest",
        transition=dict(duration=350, easing="cubic-in-out"),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor=DASH1_GRID,
        zeroline=False,
        title_standoff=10,
        tickfont=dict(color=DASH1_TEXT),
        title_font=dict(color=DASH1_TEXT),
        tickformat=".3g",
        hoverformat=".3g",
        linecolor="rgba(148,163,184,0.2)",
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=DASH1_GRID,
        zeroline=False,
        title_standoff=10,
        tickfont=dict(color=DASH1_TEXT),
        title_font=dict(color=DASH1_TEXT),
        tickformat=".3g",
        hoverformat=".3g",
        linecolor="rgba(148,163,184,0.2)",
    )
    return fig

def _sort_periods(periods: List[str]) -> List[str]:
    """Sort period labels by year/semester when possible, otherwise by name."""
    def _key(p: str) -> Tuple[int, int, str]:
        s = str(p)
        year_match = re.search(r"(\d{4})", s)
        sem_match = re.search(r"(?:Sem|S)\s*([12])", s, re.IGNORECASE)
        year = int(year_match.group(1)) if year_match else 9999
        sem = int(sem_match.group(1)) if sem_match else 9
        return (year, sem, s)
    return sorted(periods, key=_key)

def _latest_semester_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """Return the latest period per student for snapshot-style metrics."""
    if STUDENT_ID_COL not in df.columns:
        return df
    if "Period (Unified)" not in df.columns:
        return df

    temp = df.copy()
    periods = temp["Period (Unified)"].astype("string")
    period_list = periods.dropna().unique().tolist()
    ordered = _sort_periods([str(p) for p in period_list])
    rank = {p: i for i, p in enumerate(ordered)}
    temp["_period_rank"] = periods.map(rank).fillna(-1).astype(int)
    temp = temp.sort_values([STUDENT_ID_COL, "_period_rank"])
    latest = temp.groupby(STUDENT_ID_COL, dropna=False, observed=False).tail(1)
    return latest.drop(columns=["_period_rank"])


def make_kpi_figure(df: pd.DataFrame, total_override: Optional[float] = None) -> go.Figure:
    """Create a summary panel for risk share distribution."""
    title = "Risk Threshold Pulse: Share"
    subtitle = "Shares show low/high risk based on GPA/attendance thresholds." 

    if df.empty:
        fig = _apply_dash1_layout(go.Figure(), title, height=420, subtitle=subtitle)
        fig.add_annotation(
            text="No data after filters.",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=12, color=DASH1_MUTED),
        )
        return fig

    tier_series = None
    if RISK_TIER_COL in df.columns:
        tier_series = df[RISK_TIER_COL].astype("string").str.strip().str.title()
    elif RISK_SCORE_COL in df.columns:
        scores = pd.to_numeric(df[RISK_SCORE_COL], errors="coerce")
        clean = scores.dropna()
        if not clean.empty and clean.isin([0, 1]).all():
            tier_series = pd.Series(np.where(scores == 1, "High", "Low"), index=df.index)
        else:
            tier_series = pd.Series(
                np.where(scores >= 0.7, "High", np.where(scores >= 0.5, "Medium", "Low")),
                index=df.index,
            )
    elif GPA_COL in df.columns and ATTEND_COL in df.columns:
        gpa_vals = pd.to_numeric(df[GPA_COL], errors="coerce")
        att_vals = pd.to_numeric(df[ATTEND_COL], errors="coerce")
        mask = gpa_vals.notna() & att_vals.notna()
        if mask.any():
            gpa_med = float(gpa_vals[mask].median())
            att_med = float(att_vals[mask].median())
            low_low = (gpa_vals < gpa_med) & (att_vals < att_med)
            low_mix = (gpa_vals < gpa_med) ^ (att_vals < att_med)
            tier_series = pd.Series(
                np.where(low_low, "High", np.where(low_mix, "Medium", "Low")),
                index=df.index,
            )

    if tier_series is None:
        fig = _apply_dash1_layout(go.Figure(), f"{title} (Unavailable)", height=420, subtitle=subtitle)
        fig.add_annotation(
            text="Risk tiers unavailable.",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=12, color=DASH1_MUTED),
        )
        return fig

    tier_series = tier_series.dropna()
    counts = tier_series.value_counts()
    total = float(counts.sum()) if counts.sum() else 1.0
    if total_override is not None:
        total = float(total_override)
    else:
        profile_count = _get_profile_student_count()
        if profile_count is not None:
            total = float(profile_count)
            globals()["PROFILE_STUDENT_COUNT"] = int(profile_count)
    color_map = {"High": "#EF4444", "Medium": "#F4B400", "Low": "#22C55E"}
    preferred = ["High", "Medium", "Low"]
    order = [(tier, color_map[tier]) for tier in preferred if tier in counts.index]
    if not order:
        order = [(tier, color_map.get(tier, DASH1_COLORWAY[0])) for tier in counts.index.tolist()]

    labels = [t[0] for t in order]
    values = [int(counts.get(tier, 0)) for tier in labels]
    colors = [t[1] for t in order]
    if not labels:
        fig = _apply_dash1_layout(go.Figure(), f"{title} (Unavailable)", height=420, subtitle=subtitle)
        fig.add_annotation(
            text="Risk tiers unavailable.",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=12, color=DASH1_MUTED),
        )
        return fig

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                sort=False,
                marker=dict(colors=colors, line=dict(color="rgba(15,23,42,0.6)", width=1)),
                textinfo="label+percent",
                textposition="outside",
                hovertemplate="%{label}<br>Share=%{percent}<br>N=%{value}<extra></extra>",
            )
        ]
    )
    fig.update_layout(showlegend=False)

    tier_phrase = "low/high" if "Medium" not in counts.index else "low/medium/high"
    subtitle = f"Total students: {int(total)}. Shares show {tier_phrase} risk based on GPA/attendance thresholds."
    fig = _apply_dash1_layout(fig, title, height=420, subtitle=subtitle)
    return fig


def make_dashboard_1_figures(
    df: pd.DataFrame,
    top_n: int = 12,
    gpa_threshold: Optional[float] = None,
    att_threshold: Optional[float] = None,
    total_override: Optional[float] = None,
) -> Dict[str, go.Figure]:
    """Create Dashboard 1 figures (Outcomes & Risk).

    Charts:
    - Risk threshold share (KPI)
    - Attendance vs GPA with thresholds + linear fit
    - Risk quadrant density (low/high GPA vs attendance)
    - Funding x course level matrix (mean GPA)
    - GPA by highest qualification (box)

    Args:
        df: Filtered analytics DataFrame.
        top_n: Number of courses to display in course-level charts.
        gpa_threshold: GPA threshold for risk overlay lines.
        att_threshold: Attendance threshold for risk overlay lines.

    Returns:
        Dict of figures keyed by name.
    """
    figs: Dict[str, go.Figure] = {}

    def _course_label_margin(labels: List[str], min_margin: int = 200, max_margin: int = 360) -> int:
        if not labels:
            return min_margin
        max_len = max(len(str(label)) for label in labels)
        return min(max_margin, max(min_margin, int(max_len * 9)))


    snapshot_df = _latest_semester_snapshot(df)

    if total_override is None and STUDENT_ID_COL in snapshot_df.columns:
        outcome_mask = pd.Series(False, index=snapshot_df.index)
        if GPA_COL in snapshot_df.columns:
            outcome_mask |= pd.to_numeric(snapshot_df[GPA_COL], errors="coerce").notna()
        if ATTEND_COL in snapshot_df.columns:
            outcome_mask |= pd.to_numeric(snapshot_df[ATTEND_COL], errors="coerce").notna()
        if outcome_mask.any():
            total_override = float(snapshot_df.loc[outcome_mask, STUDENT_ID_COL].nunique())
        else:
            profile_count = _get_profile_student_count()
            if profile_count is not None:
                total_override = float(profile_count)
                globals()["PROFILE_STUDENT_COUNT"] = int(profile_count)


    risk_series = None
    if RISK_TIER_COL in snapshot_df.columns:
        risk_series = snapshot_df[RISK_TIER_COL].astype("string").str.strip().str.title()
    elif RISK_SCORE_COL in snapshot_df.columns:
        scores = pd.to_numeric(snapshot_df[RISK_SCORE_COL], errors="coerce")
        risk_series = pd.Series(
            np.select(
                [scores >= 0.7, scores >= 0.5],
                ["High", "Medium"],
                default="Low",
            ),
            index=snapshot_df.index,
        )
        risk_series = risk_series.where(scores.notna(), other=pd.NA).astype("string")
    elif RISK_FLAG_COL in snapshot_df.columns:
        flags = pd.to_numeric(snapshot_df[RISK_FLAG_COL], errors="coerce")
        risk_series = pd.Series(np.where(flags == 1, "High", "Low"), index=snapshot_df.index)
        risk_series = risk_series.where(flags.notna(), other=pd.NA).astype("string")

    risk_color_map = {"High": "#EF4444", "Medium": "#F4B400", "Low": "#22C55E"}

    safe_top_n = int(top_n) if top_n else 12
    safe_top_n = max(TOP_N_MIN, min(safe_top_n, TOP_N_MAX))
    course_col = COURSE_DISPLAY_COL if COURSE_DISPLAY_COL in snapshot_df.columns else DERIVED_COURSE_COL
    course_count = int(snapshot_df[course_col].nunique(dropna=True)) if course_col in snapshot_df.columns else 0

    if course_count > 0:
        safe_top_n = min(safe_top_n, course_count)
    course_title_suffix = f"Top {safe_top_n}"
    if course_count > 0 and safe_top_n >= course_count:
        course_title_suffix = "All Courses"



    figs["kpi"] = make_kpi_figure(snapshot_df, total_override=total_override)

    def _make_highest_edu_gpa(df_local: pd.DataFrame):
        """Build GPA distribution by highest qualification (top groups)."""
        subtitle = "Box shows GPA spread by highest qualification (top groups by cohort size)."
        if HIGHEST_EDU_COL not in df_local.columns or GPA_COL not in df_local.columns:
            return go.Figure(), None, "Unavailable", subtitle

        edu_df = df_local[[HIGHEST_EDU_COL, GPA_COL]].copy()
        edu_df[HIGHEST_EDU_COL] = edu_df[HIGHEST_EDU_COL].astype("string").str.strip()
        edu_df[GPA_COL] = pd.to_numeric(edu_df[GPA_COL], errors="coerce")
        edu_df = edu_df[
            edu_df[HIGHEST_EDU_COL].notna()
            & edu_df[GPA_COL].notna()
            & (edu_df[HIGHEST_EDU_COL].str.len() > 0)
        ].copy()
        if edu_df.empty:
            return go.Figure(), None, "Unavailable", subtitle

        counts = edu_df[HIGHEST_EDU_COL].value_counts()
        top_n_edu = min(8, len(counts))
        top_labels = counts.head(top_n_edu).index.tolist()
        edu_df["_edu_group"] = np.where(
            edu_df[HIGHEST_EDU_COL].isin(top_labels), edu_df[HIGHEST_EDU_COL], "Other"
        )
        edu_df["_count"] = edu_df["_edu_group"].map(edu_df["_edu_group"].value_counts())
        order = (
            edu_df.groupby("_edu_group", observed=False)[GPA_COL]
            .median()
            .sort_values()
            .index.tolist()
        )

        suffix = "All Qualifications" if len(counts) <= top_n_edu else f"Top {top_n_edu} + Other"
        fig = px.box(
            edu_df,
            x=GPA_COL,
            y="_edu_group",
            points="outliers",
            custom_data=["_count"],
        )
        fig.update_traces(
            marker=dict(color="rgba(34,211,238,0.7)"),
            line=dict(color="rgba(226,232,240,0.65)"),
            hovertemplate=(
                "Qualification=%{y}<br>GPA=%{x:.2f}"
                "<br>Students=%{customdata[0]}<extra></extra>"
            ),
        )
        fig.update_layout(showlegend=False)
        fig.update_yaxes(title="Highest Qualification", categoryorder="array", categoryarray=order)
        fig.update_xaxes(title="GPA")
        return fig, order, suffix, subtitle

    edu_fig, edu_order, edu_suffix, edu_subtitle = _make_highest_edu_gpa(snapshot_df)
    edu_title = f"GPA by Highest Qualification ({edu_suffix})"
    figs["gpa_dist"] = _apply_dash1_layout(
        edu_fig,
        edu_title,
        height=440,
        subtitle=f"{edu_subtitle} Filters ignored: GPA/attendance range and highest qualification.",
    )
    if edu_order:
        figs["gpa_dist"].update_layout(
            margin=dict(l=_course_label_margin(edu_order), r=28, t=140, b=64)
        )
    else:
        figs["gpa_dist"].update_layout(margin=dict(t=140), title=dict(y=0.94))

    if GPA_COL in snapshot_df.columns and ATTEND_COL in snapshot_df.columns:
        hover_fields = []
        hovertemplate_parts = ["Attendance=%{x:.3g}%", "GPA=%{y:.3g}"]
        scatter_kwargs = {
            "x": ATTEND_COL,
            "y": GPA_COL,
        }
        scatter_kwargs["labels"] = {ATTEND_COL: "Attendance (%)", GPA_COL: "GPA", course_col: "Course"}

        scatter_df = snapshot_df.copy()
        risk_col = None
        if RISK_TIER_COL in scatter_df.columns:
            scatter_df["_risk_tier"] = scatter_df[RISK_TIER_COL].astype("string").str.strip().str.title()
            risk_col = "_risk_tier"
        elif RISK_SCORE_COL in scatter_df.columns:
            scores = pd.to_numeric(scatter_df[RISK_SCORE_COL], errors="coerce")
            scatter_df["_risk_tier"] = np.where(
                scores >= 0.7,
                "High",
                np.where(scores >= 0.5, "Medium", "Low"),
            )
            risk_col = "_risk_tier"
        elif RISK_FLAG_COL in scatter_df.columns:
            flags = pd.to_numeric(scatter_df[RISK_FLAG_COL], errors="coerce")
            scatter_df["_risk_tier"] = np.where(flags == 1, "High", "Low")
            risk_col = "_risk_tier"

        if risk_col is not None:
            scatter_kwargs["color"] = risk_col
            scatter_kwargs["color_discrete_map"] = {"High": "#EF4444", "Medium": "#F4B400", "Low": "#22C55E"}
            hover_fields.append(risk_col)
            risk_idx = len(hover_fields) - 1
            hovertemplate_parts.append(f"Risk=%{{customdata[{risk_idx}]}}")
        elif course_col in scatter_df.columns:
            course_count = scatter_df[course_col].nunique(dropna=True)
            if course_count <= 8:
                scatter_kwargs["color"] = course_col
                hover_fields.append(course_col)
                course_idx = len(hover_fields) - 1
                hovertemplate_parts.append(f"Course=%{{customdata[{course_idx}]}}")

        if "Completion Status" in scatter_df.columns:
            scatter_kwargs["symbol"] = "Completion Status"
            scatter_kwargs["symbol_map"] = {"Completed": "circle", "Ongoing": "triangle-up"}
            hover_fields.append("Completion Status")
            status_idx = len(hover_fields) - 1
            hovertemplate_parts.append(f"Status=%{{customdata[{status_idx}]}}")

        if hover_fields:
            scatter_kwargs["custom_data"] = hover_fields
        title_text = "Attendance vs GPA (Threshold Overlay)"
        gpa_vs_att = px.scatter(
            scatter_df,
            title=title_text,
            **scatter_kwargs,
        )
        gpa_vs_att.update_traces(
            marker=dict(opacity=0.8, line=dict(width=0)),
            hovertemplate="<br>".join(hovertemplate_parts) + "<extra></extra>",
        )
        gpa_vs_att.update_xaxes(title="Attendance (%)")
        gpa_vs_att.update_yaxes(title="GPA")
        show_legend = False
        if "color" in scatter_kwargs:
            legend_title = "Risk Tier" if scatter_kwargs["color"] == risk_col else "Course"
            gpa_vs_att.update_layout(legend_title_text=legend_title)
            show_legend = True
        if "symbol" in scatter_kwargs:
            show_legend = True
        if not show_legend:
            gpa_vs_att.update_layout(showlegend=False)

        x_vals = pd.to_numeric(scatter_df[ATTEND_COL], errors="coerce")
        y_vals = pd.to_numeric(scatter_df[GPA_COL], errors="coerce")
        mask = x_vals.notna() & y_vals.notna()
        if mask.sum() >= 4:
            att_q1, att_q3 = np.quantile(x_vals[mask], [0.25, 0.75])
            gpa_q1, gpa_q3 = np.quantile(y_vals[mask], [0.25, 0.75])
            gpa_vs_att.add_vline(x=float(att_q1), line_dash="dot", line_color="rgba(30,36,48,0.35)")
            gpa_vs_att.add_vline(x=float(att_q3), line_dash="dot", line_color="rgba(30,36,48,0.35)")
            gpa_vs_att.add_hline(y=float(gpa_q1), line_dash="dot", line_color="rgba(30,36,48,0.35)")
            gpa_vs_att.add_hline(y=float(gpa_q3), line_dash="dot", line_color="rgba(30,36,48,0.35)")

        if mask.sum() >= 2 and x_vals[mask].nunique() > 1:
            slope, intercept = np.polyfit(x_vals[mask], y_vals[mask], 1)
            corr = float(np.corrcoef(x_vals[mask], y_vals[mask])[0, 1])
            x_line = np.array([x_vals[mask].min(), x_vals[mask].max()])
            y_line = slope * x_line + intercept
            gpa_vs_att.add_trace(
                go.Scatter(
                    x=x_line,
                    y=y_line,
                    mode="lines",
                    name=f"Linear fit (r={corr:.2f})",
                    line=dict(color="#F4B400", width=2),
                    hovertemplate=f"Linear fit<br>y={slope:.3f}x+{intercept:.3f}<extra></extra>",
                )
            )

        gpa_thr = None
        att_thr = None
        try:
            gpa_thr = float(gpa_threshold) if gpa_threshold is not None else None
        except (TypeError, ValueError):
            gpa_thr = None
        try:
            att_thr = float(att_threshold) if att_threshold is not None else None
        except (TypeError, ValueError):
            att_thr = None

        if att_thr is not None and np.isfinite(att_thr):
            gpa_vs_att.add_vline(x=float(att_thr), line_dash="dash", line_color="rgba(239,68,68,0.7)")
        if gpa_thr is not None and np.isfinite(gpa_thr):
            gpa_vs_att.add_hline(y=float(gpa_thr), line_dash="dash", line_color="rgba(239,68,68,0.7)")

        figs["gpa_vs_att"] = _apply_dash1_layout(
            gpa_vs_att,
            title_text,
            height=480,
            subtitle="Color shows risk tier; symbol shows completion status. Dotted lines mark quartiles; dashed lines show thresholds; line shows linear fit.",
        )
    else:
        figs["gpa_vs_att"] = _apply_dash1_layout(
            go.Figure(),
            "Attendance vs GPA (Threshold Overlay) (Unavailable)",
            height=480,
            subtitle="Color shows risk tier; symbol shows completion status. Dotted lines mark quartiles; dashed lines show thresholds; line shows linear fit.",
        )
    # --- Risk quadrant density (GPA vs attendance) ---
    if GPA_COL in snapshot_df.columns and ATTEND_COL in snapshot_df.columns:
        gpa_vals = pd.to_numeric(snapshot_df[GPA_COL], errors="coerce")
        att_vals = pd.to_numeric(snapshot_df[ATTEND_COL], errors="coerce")
        mask = gpa_vals.notna() & att_vals.notna()
        if mask.any():
            gpa_fallback = float(gpa_vals[mask].median())
            att_fallback = float(att_vals[mask].median())
            try:
                gpa_thr = float(gpa_threshold) if gpa_threshold is not None else gpa_fallback
            except (TypeError, ValueError):
                gpa_thr = gpa_fallback
            try:
                att_thr = float(att_threshold) if att_threshold is not None else att_fallback
            except (TypeError, ValueError):
                att_thr = att_fallback

            quad_df = pd.DataFrame(
                {
                    "GPA": gpa_vals[mask],
                    "Attendance": att_vals[mask],
                }
            )
            quad_df["GPA Band"] = np.where(quad_df["GPA"] >= gpa_thr, "High GPA", "Low GPA")
            quad_df["Attendance Band"] = np.where(
                quad_df["Attendance"] >= att_thr, "High Attendance", "Low Attendance"
            )

            quad = (
                quad_df.groupby(["GPA Band", "Attendance Band"], observed=False)
                .size()
                .reset_index(name="Count")
            )
            pivot = quad.pivot(index="GPA Band", columns="Attendance Band", values="Count")
            pivot = pivot.reindex(
                index=["Low GPA", "High GPA"],
                columns=["Low Attendance", "High Attendance"],
            ).fillna(0)
            total = float(pivot.values.sum())
            pct = pivot / total * 100.0 if total > 0 else pivot.copy()
            text = [
                [
                    f"{int(cnt)}<br>({pct_val:.1f}%)" if total > 0 else f"{int(cnt)}"
                    for cnt, pct_val in zip(row_cnt, row_pct)
                ]
                for row_cnt, row_pct in zip(pivot.values, pct.values)
            ]

            heat = go.Figure(
                data=go.Heatmap(
                    z=pivot.values,
                    x=pivot.columns.tolist(),
                    y=pivot.index.tolist(),
                    text=text,
                    texttemplate="%{text}",
                    textfont=dict(color=DASH1_TEXT, size=12),
                    colorscale=[[0.0, "#0F172A"], [0.5, "#2563EB"], [1.0, "#EF4444"]],
                    hovertemplate="GPA=%{y}<br>Attendance=%{x}<br>Students=%{z}<extra></extra>",
                )
            )
            heat.update_xaxes(title="Attendance Band")
            heat.update_yaxes(title="GPA Band")
            heat.update_layout(showlegend=False)
            heat.add_annotation(
                x="Low Attendance",
                y="Low GPA",
                text="High Risk Pocket",
                showarrow=True,
                arrowhead=2,
                arrowcolor="#EF4444",
                font=dict(color="#F8FAFC", size=11),
                bgcolor="rgba(239,68,68,0.25)",
            )
            figs["risk_quadrant"] = _apply_dash1_layout(
                heat,
                "Risk Quadrant Density",
                height=360,
                subtitle=(
                    "Quadrant shares based on GPA & attendance thresholds; focus on Low GPA + Low Attendance."
                ),
            )
        else:
            figs["risk_quadrant"] = _apply_dash1_layout(
                go.Figure(),
                "Risk Quadrant Density (Unavailable)",
                height=360,
                subtitle=(
                    "Quadrant shares based on GPA & attendance thresholds; focus on Low GPA + Low Attendance."
                ),
            )
    else:
        figs["risk_quadrant"] = _apply_dash1_layout(
            go.Figure(),
            "Risk Quadrant Density (Unavailable)",
            height=360,
            subtitle=(
                "Quadrant shares based on GPA & attendance thresholds; focus on Low GPA + Low Attendance."
            ),
        )

    if ATTEND_COL in snapshot_df.columns and "Completion Status" in snapshot_df.columns:
        att_df = snapshot_df[[ATTEND_COL, "Completion Status"]].copy()
        att_df[ATTEND_COL] = pd.to_numeric(att_df[ATTEND_COL], errors="coerce")
        status_series = att_df["Completion Status"].astype("string").str.strip().str.lower()
        att_df = att_df[att_df[ATTEND_COL].notna() & status_series.notna()].copy()
        if not att_df.empty:
            bins = list(range(0, 101, 10))
            labels = [f"{bins[i]}-{bins[i+1]}" for i in range(len(bins) - 1)]
            att_df["Band"] = pd.cut(
                att_df[ATTEND_COL], bins=bins, labels=labels, include_lowest=True
            )
            att_df["Completed"] = status_series == "completed"
            band_stats = (
                att_df.groupby("Band", dropna=False, observed=False)["Completed"]
                .agg(["mean", "count"])
                .reset_index()
            )
            band_stats = band_stats[band_stats["Band"].notna()]
            band_stats["Rate"] = band_stats["mean"] * 100.0
            comp_fig = go.Figure()
            comp_fig.add_trace(
                go.Bar(
                    x=band_stats["Band"].astype(str),
                    y=band_stats["Rate"],
                    marker_color=DASH1_COLORWAY[0],
                    text=[f"{val:.3g}%" for val in band_stats["Rate"]],
                    textposition="outside",
                    customdata=band_stats[["count"]].to_numpy(),
                    hovertemplate=(
                        "Attendance Band=%{x}<br>Completion=%{y:.3g}%"
                        "<br>Students=%{customdata[0]}<extra></extra>"
                    ),
                )
            )
            comp_fig.update_yaxes(title="Completion Rate (%)", range=[0, 100])
            comp_fig.update_xaxes(title="Attendance Band (%)")
            figs["completion_by_att"] = _apply_dash1_layout(
                comp_fig,
                "Completion Rate by Attendance Band",
                height=360,
                subtitle="Higher bars indicate stronger completion in that attendance band.",
            )
        else:
            figs["completion_by_att"] = _apply_dash1_layout(
                go.Figure(),
                "Completion Rate by Attendance Band (Unavailable)",
                height=360,
                subtitle="Higher bars indicate stronger completion in that attendance band.",
            )
    else:
        figs["completion_by_att"] = _apply_dash1_layout(
            go.Figure(),
            "Completion Rate by Attendance Band (Unavailable)",
            height=360,
            subtitle="Higher bars indicate stronger completion in that attendance band.",
        )

    # --- Funding x Course Level matrix ---
    if COURSE_FUNDING_COL in snapshot_df.columns and COURSE_LEVEL_COL in snapshot_df.columns and GPA_COL in snapshot_df.columns:
        matrix_df = snapshot_df[[COURSE_FUNDING_COL, COURSE_LEVEL_COL, GPA_COL, STUDENT_ID_COL]].copy()
        matrix_df[COURSE_FUNDING_COL] = matrix_df[COURSE_FUNDING_COL].astype("string").str.strip()
        matrix_df[COURSE_LEVEL_COL] = matrix_df[COURSE_LEVEL_COL].astype("string").str.strip()
        matrix_df[GPA_COL] = pd.to_numeric(matrix_df[GPA_COL], errors="coerce")
        matrix_df = matrix_df[
            matrix_df[COURSE_FUNDING_COL].notna()
            & (matrix_df[COURSE_FUNDING_COL].str.len() > 0)
            & matrix_df[COURSE_LEVEL_COL].notna()
            & (matrix_df[COURSE_LEVEL_COL].str.len() > 0)
            & matrix_df[GPA_COL].notna()
        ].copy()
        if not matrix_df.empty:
            stats = (
                matrix_df.groupby([COURSE_LEVEL_COL, COURSE_FUNDING_COL], observed=False)
                .agg(**{"Mean GPA": (GPA_COL, "mean"), "Students": (STUDENT_ID_COL, "nunique")})
                .reset_index()
            )
            level_candidates = stats[COURSE_LEVEL_COL].unique().tolist()
            preferred_levels = ["Certificate", "Diploma", "Specialist Diploma", "Other"]
            level_order = [lvl for lvl in preferred_levels if lvl in level_candidates]
            level_order += [lvl for lvl in level_candidates if lvl not in level_order]
            funding_order = (
                stats.groupby(COURSE_FUNDING_COL, observed=False)["Mean GPA"]
                .mean()
                .sort_values(ascending=False)
                .index.tolist()
            )
            pivot = (
                stats.pivot(index=COURSE_LEVEL_COL, columns=COURSE_FUNDING_COL, values="Mean GPA")
                .reindex(index=level_order, columns=funding_order)
            )
            count_pivot = (
                stats.pivot(index=COURSE_LEVEL_COL, columns=COURSE_FUNDING_COL, values="Students")
                .reindex(index=level_order, columns=funding_order)
                .fillna(0)
            )
            text = []
            for lvl in pivot.index:
                row = []
                for fund in pivot.columns:
                    mean_val = pivot.loc[lvl, fund]
                    count_val = count_pivot.loc[lvl, fund]
                    if pd.isna(mean_val):
                        row.append("")
                    else:
                        row.append(f"{mean_val:.2f}<br>n={int(count_val)}")
                text.append(row)

            heat = go.Figure(
                data=go.Heatmap(
                    z=pivot.values,
                    x=pivot.columns.tolist(),
                    y=pivot.index.tolist(),
                    text=text,
                    texttemplate="%{text}",
                    textfont=dict(size=11, color=DASH1_TEXT),
                    zmin=0,
                    zmax=4,
                    colorscale=[[0.0, "#0B1222"], [0.5, "#2563EB"], [1.0, "#38BDF8"]],
                    hovertemplate="Level=%{y}<br>Funding=%{x}<br>Mean GPA=%{z:.2f}<extra></extra>",
                )
            )
            heat.update_xaxes(title="Funding Type")
            heat.update_yaxes(title="Course Level")
            figs["funding_level_matrix"] = _apply_dash1_layout(
                heat,
                "Funding x Course Level Outcomes",
                height=420,
                subtitle="Heatmap shows mean GPA by funding and course level; labels include cohort size.",
            )
        else:
            figs["funding_level_matrix"] = _apply_dash1_layout(
                go.Figure(),
                "Funding x Course Level Outcomes (Unavailable)",
                height=420,
                subtitle="Heatmap shows mean GPA by funding and course level; labels include cohort size.",
            )
    else:
        figs["funding_level_matrix"] = _apply_dash1_layout(
            go.Figure(),
            "Funding x Course Level Outcomes (Unavailable)",
            height=420,
            subtitle="Heatmap shows mean GPA by funding and course level; labels include cohort size.",
        )

    # --- Momentum gap by risk tier ---
    if MOMENTUM_GAP_COL in snapshot_df.columns and risk_series is not None:
        gap_vals = pd.to_numeric(snapshot_df[MOMENTUM_GAP_COL], errors="coerce")
        mask = gap_vals.notna() & risk_series.notna()
        if mask.any():
            plot_df = pd.DataFrame({"Gap": gap_vals[mask], "Risk Tier": risk_series[mask]})
            plot_df = plot_df[plot_df["Risk Tier"].isin(["High", "Medium", "Low"])]
            if not plot_df.empty:
                gap_fig = go.Figure()
                order = ["High", "Medium", "Low"]
                for tier in order:
                    vals = plot_df.loc[plot_df["Risk Tier"] == tier, "Gap"]
                    if vals.empty:
                        continue
                    gap_fig.add_trace(
                        go.Violin(
                            y=vals,
                            name=str(tier),
                            box=dict(visible=True),
                            meanline=dict(visible=True),
                            line_color=risk_color_map.get(tier, DASH1_COLORWAY[0]),
                            fillcolor=risk_color_map.get(tier, DASH1_COLORWAY[0]),
                            opacity=0.65,
                            hovertemplate="Risk Tier=%{x}<br>GPA Residual=%{y:.3g}<extra></extra>",
                        )
                    )
                gap_fig.add_hline(y=0, line_dash="dot", line_color="rgba(148,163,184,0.6)")
                gap_fig.update_xaxes(title="Risk Tier")
                gap_fig.update_yaxes(title="GPA Residual (Actual - Expected)")
                figs["momentum_gap"] = _apply_dash1_layout(
                    gap_fig,
                    "Momentum Gap by Risk Tier",
                    height=420,
                    subtitle="Highlights over- and under-performance relative to attendance expectations.",
                )
            else:
                figs["momentum_gap"] = _apply_dash1_layout(
                    go.Figure(),
                    "Momentum Gap by Risk Tier (Unavailable)",
                    height=420,
                    subtitle="Highlights over- and under-performance relative to attendance expectations.",
                )
        else:
            figs["momentum_gap"] = _apply_dash1_layout(
                go.Figure(),
                "Momentum Gap by Risk Tier (Unavailable)",
                height=420,
                subtitle="Highlights over- and under-performance relative to attendance expectations.",
            )
    else:
        figs["momentum_gap"] = _apply_dash1_layout(
            go.Figure(),
            "Momentum Gap by Risk Tier (Unavailable)",
            height=420,
            subtitle="Highlights over- and under-performance relative to attendance expectations.",
        )

    if GPA_COL in snapshot_df.columns and course_col in snapshot_df.columns:
        course_stats = (
            snapshot_df.groupby(course_col, dropna=False, observed=False)[GPA_COL]
            .agg(["mean", "count"])
            .reset_index()
            .rename(columns={"mean": "Mean GPA", "count": "Student Count"})
        )
        if not course_stats.empty:
            course_filtered = course_stats[course_stats["Student Count"] >= MIN_COURSE_COUNT]
            if course_filtered.empty:
                course_filtered = course_stats.copy()

            course_top = (
                course_filtered.sort_values("Mean GPA", ascending=False)
                .head(safe_top_n)
                .sort_values("Mean GPA", ascending=True)
                .reset_index(drop=True)
            )

            course_fig = px.bar(
                course_top,
                x="Mean GPA",
                y=course_col,
                orientation="h",
                color="Mean GPA",
                color_continuous_scale=["#9AD0FF", "#0B6EFD"],
                hover_data={"Mean GPA": ":.3g", "Student Count": True},
                title="Mean GPA by Course",
                labels={course_col: "Course"},
            )
            course_fig.update_layout(coloraxis_showscale=False)
            course_fig.update_traces(
                text=[f"{val:.3g}" for val in course_top["Mean GPA"]],
                texttemplate="%{text}",
                textposition="outside",
                textfont=dict(color=DASH1_TEXT, size=11),
                cliponaxis=False,
                customdata=course_top[["Student Count"]].to_numpy(),
                hovertemplate="Course=%{y}<br>Mean GPA=%{x:.3g}<br>Students=%{customdata[0]}<extra></extra>",
            )
            course_fig.update_layout(showlegend=False)
            course_labels = course_top[course_col].tolist()
            course_fig.update_yaxes(
                categoryorder="array",
                categoryarray=course_labels,
                ticklabelposition="outside",
            )
            course_fig.update_xaxes(title="Mean GPA")
            course_fig.update_yaxes(title="")
            course_fig.update_yaxes(automargin=True)
            figs["mean_gpa_by_course"] = _apply_dash1_layout(
                course_fig, f"Mean GPA by Course ({course_title_suffix})", height=440, subtitle="Bars show mean GPA by course; hover for cohort size."
            )
            figs["mean_gpa_by_course"].update_layout(
                margin=dict(l=_course_label_margin(course_labels), r=28, t=74, b=64)
            )
        else:
            figs["mean_gpa_by_course"] = _apply_dash1_layout(
                go.Figure(), "Mean GPA by Course (Unavailable)", height=440, subtitle="Bars show mean GPA by course; hover for cohort size."
            )
    else:
        figs["mean_gpa_by_course"] = _apply_dash1_layout(
            go.Figure(), "Mean GPA by Course (Unavailable)", height=440, subtitle="Bars show mean GPA by course; hover for cohort size."
        )

    # --- Course outcome matrix (mean GPA vs risk rate) ---
    if course_col in snapshot_df.columns and GPA_COL in snapshot_df.columns:
        course_df = snapshot_df.copy()
        course_df[GPA_COL] = pd.to_numeric(course_df[GPA_COL], errors="coerce")
        course_df = course_df[course_df[GPA_COL].notna()].copy()
        if not course_df.empty:
            stats = (
                course_df.groupby(course_col, observed=False)
                .agg(
                    **{
                        "Mean GPA": (GPA_COL, "mean"),
                        "Students": (STUDENT_ID_COL, "nunique"),
                    }
                )
                .reset_index()
            )
            if risk_series is not None:
                course_df = course_df.assign(_risk=risk_series)
                risk_rate = (
                    course_df.assign(_risk_high=course_df["_risk"].eq("High"))
                    .groupby(course_col, observed=False)["_risk_high"]
                    .mean()
                    .mul(100.0)
                )
                stats = stats.merge(
                    risk_rate.rename("Risk Rate"),
                    left_on=course_col,
                    right_index=True,
                    how="left",
                )
            else:
                stats["Risk Rate"] = np.nan

            if COURSE_LEVEL_COL in course_df.columns:
                level_mode = (
                    course_df.groupby(course_col, observed=False)[COURSE_LEVEL_COL]
                    .agg(lambda s: s.mode().iat[0] if not s.mode().empty else "Other")
                    .rename(COURSE_LEVEL_COL)
                )
                stats = stats.merge(
                    level_mode,
                    left_on=course_col,
                    right_index=True,
                    how="left",
                )

            filtered = stats[stats["Students"] >= MIN_COURSE_COUNT].copy()
            if filtered.empty:
                filtered = stats.copy()

            if len(filtered) > safe_top_n:
                filtered = (
                    filtered.sort_values("Students", ascending=False)
                    .head(safe_top_n)
                    .reset_index(drop=True)
                )

            if filtered["Risk Rate"].notna().any():
                color_arg = COURSE_LEVEL_COL if COURSE_LEVEL_COL in filtered.columns else None
                bubble_fig = px.scatter(
                    filtered,
                    x="Mean GPA",
                    y="Risk Rate",
                    size="Students",
                    color=color_arg,
                    hover_name=course_col,
                    custom_data=["Students"],
                    size_max=60,
                )
                bubble_fig.update_traces(
                    marker=dict(opacity=0.78, line=dict(width=0.5, color="rgba(255,255,255,0.35)")),
                    hovertemplate=(
                        "Course=%{hovertext}<br>Mean GPA=%{x:.3g}<br>High Risk=%{y:.2f}%"
                        "<br>Students=%{customdata[0]}<extra></extra>"
                    ),
                )
                bubble_fig.update_xaxes(title="Mean GPA")
                bubble_fig.update_yaxes(title="High Risk %")

                try:
                    gpa_thr = float(gpa_threshold) if gpa_threshold is not None else None
                except (TypeError, ValueError):
                    gpa_thr = None
                if gpa_thr is not None and np.isfinite(gpa_thr):
                    bubble_fig.add_vline(x=float(gpa_thr), line_dash="dash", line_color="rgba(239,68,68,0.6)")
                if filtered["Risk Rate"].notna().any():
                    rr_med = float(filtered["Risk Rate"].median())
                    bubble_fig.add_hline(y=rr_med, line_dash="dot", line_color="rgba(148,163,184,0.6)")

                figs["course_matrix"] = _apply_dash1_layout(
                    bubble_fig,
                    f"Course Outcome Matrix ({course_title_suffix})",
                    height=460,
                    subtitle="Bubble size shows cohort size; top-right indicates strongest outcomes; top-left signals intervention candidates.",
                )
            else:
                figs["course_matrix"] = _apply_dash1_layout(
                    go.Figure(),
                    "Course Outcome Matrix (Unavailable)",
                    height=460,
                    subtitle="Bubble size shows cohort size; top-right indicates strongest outcomes; top-left signals intervention candidates.",
                )
        else:
            figs["course_matrix"] = _apply_dash1_layout(
                go.Figure(),
                "Course Outcome Matrix (Unavailable)",
                height=460,
                subtitle="Bubble size shows cohort size; top-right indicates strongest outcomes; top-left signals intervention candidates.",
            )
    else:
        figs["course_matrix"] = _apply_dash1_layout(
            go.Figure(),
            "Course Outcome Matrix (Unavailable)",
            height=460,
            subtitle="Bubble size shows cohort size; top-right indicates strongest outcomes; top-left signals intervention candidates.",
        )

    if COURSE_FUNDING_COL in snapshot_df.columns and GPA_COL in snapshot_df.columns:
        funding_df = snapshot_df[[COURSE_FUNDING_COL, GPA_COL]].copy()
        funding_df[COURSE_FUNDING_COL] = funding_df[COURSE_FUNDING_COL].astype("string").str.strip()
        funding_df[GPA_COL] = pd.to_numeric(funding_df[GPA_COL], errors="coerce")
        funding_df = funding_df[
            funding_df[COURSE_FUNDING_COL].notna()
            & funding_df[GPA_COL].notna()
            & (funding_df[COURSE_FUNDING_COL].str.len() > 0)
        ].copy()
        if not funding_df.empty:
            funding_counts = funding_df[COURSE_FUNDING_COL].value_counts()
            funding_df["_count"] = funding_df[COURSE_FUNDING_COL].map(funding_counts)
            order = (
                funding_df.groupby(COURSE_FUNDING_COL, observed=False)[GPA_COL]
                .median()
                .sort_values()
                .index.tolist()
            )
            funding_fig = px.violin(
                funding_df,
                x=GPA_COL,
                y=COURSE_FUNDING_COL,
                color=COURSE_FUNDING_COL,
                category_orders={COURSE_FUNDING_COL: order},
                points="outliers",
                box=True,
            )
            funding_fig.update_traces(
                meanline_visible=True,
                customdata=funding_df[["_count"]].to_numpy(),
                hovertemplate=(
                    "Funding=%{y}<br>GPA=%{x:.2f}"
                    "<br>Students=%{customdata[0]}<extra></extra>"
                ),
            )
            funding_fig.update_layout(showlegend=False)
            funding_fig.update_xaxes(title="GPA")
            funding_fig.update_yaxes(title="Course Funding", automargin=True)
            figs["funding_gpa"] = _apply_dash1_layout(
                funding_fig,
                "GPA Distribution by Funding Type",
                height=440,
                subtitle="Violin shows GPA spread by funding type. GPA/attendance range and funding filters not applied.",
            )
            figs["funding_gpa"].update_layout(
                margin=dict(l=_course_label_margin(order), r=28, t=140, b=64)
            )
        else:
            figs["funding_gpa"] = _apply_dash1_layout(
                go.Figure(),
                "GPA Distribution by Funding Type (Unavailable)",
                height=440,
                subtitle="Violin shows GPA spread by funding type. GPA/attendance range and funding filters not applied.",
            )
            figs["funding_gpa"].update_layout(margin=dict(t=140), title=dict(y=0.94))
    else:
        figs["funding_gpa"] = _apply_dash1_layout(
            go.Figure(),
            "GPA Distribution by Funding Type (Unavailable)",
            height=440,
            subtitle="Violin shows GPA spread by funding type. GPA/attendance range and funding filters not applied.",
        )
        figs["funding_gpa"].update_layout(margin=dict(t=140), title=dict(y=0.94))

    if COURSE_LEVEL_COL in snapshot_df.columns and GPA_COL in snapshot_df.columns:
        level_df = snapshot_df.copy()
        level_df = level_df[level_df[COURSE_LEVEL_COL].notna()]
        if not level_df.empty:
            risk_rate = None
            if RISK_SCORE_COL in level_df.columns:
                risk_series = pd.to_numeric(level_df[RISK_SCORE_COL], errors="coerce")
                level_df = level_df.assign(_risk=risk_series.ge(0.7))
                risk_rate = level_df.groupby(COURSE_LEVEL_COL, observed=False)["_risk"].mean() * 100.0
            elif RISK_FLAG_COL in level_df.columns:
                risk_series = pd.to_numeric(level_df[RISK_FLAG_COL], errors="coerce")
                level_df = level_df.assign(_risk=risk_series.eq(1))
                risk_rate = level_df.groupby(COURSE_LEVEL_COL, observed=False)["_risk"].mean() * 100.0

            level_stats = (
                level_df.groupby(COURSE_LEVEL_COL, observed=False)
                .agg(**{"Mean GPA": (GPA_COL, "mean"), "Students": (STUDENT_ID_COL, "nunique")})
                .reset_index()
            )
            if risk_rate is not None:
                level_stats = level_stats.merge(
                    risk_rate.rename("Risk Rate"),
                    left_on=COURSE_LEVEL_COL,
                    right_index=True,
                    how="left",
                )
            level_stats = level_stats.sort_values("Mean GPA", ascending=False)
            level_order = level_stats[COURSE_LEVEL_COL].tolist()

            level_fig = go.Figure()
            level_fig.add_trace(
                go.Bar(
                    x=level_stats[COURSE_LEVEL_COL],
                    y=level_stats["Mean GPA"],
                    name="Mean GPA",
                    marker_color=DASH1_COLORWAY[2],
                    text=[f"{val:.3g}" for val in level_stats["Mean GPA"]],
                    textposition="outside",
                    textfont=dict(color=DASH1_TEXT, size=11),
                    customdata=level_stats[["Students"]].to_numpy(),
                    hovertemplate="Level=%{x}<br>Mean GPA=%{y:.3g}<br>Students=%{customdata[0]}<extra></extra>",
                )
            )
            if "Risk Rate" in level_stats.columns:
                level_fig.add_trace(
                    go.Scatter(
                        x=level_stats[COURSE_LEVEL_COL],
                        y=level_stats["Risk Rate"],
                        name="High Risk %",
                        mode="lines+markers+text",
                        text=[f"{val:.3g}%" for val in level_stats["Risk Rate"]],
                        textposition="top center",
                        textfont=dict(color="#F8FAFC", size=10),
                        yaxis="y2",
                        line=dict(color=DASH1_COLORWAY[1], width=2),
                        marker=dict(size=7, color=DASH1_COLORWAY[1]),
                        hovertemplate="Level=%{x}<br>High Risk=%{y:.3g}%<extra></extra>",
                    )
                )
            level_fig.update_layout(
                legend_title_text="Metric",
                yaxis=dict(title="Mean GPA", range=[0, 4]),
                yaxis2=dict(title="High Risk %", range=[0, 100], overlaying="y", side="right"),
                showlegend=True,
            )
            level_fig.update_xaxes(title="Course Level", categoryorder="array", categoryarray=level_order)
            figs["level_performance"] = _apply_dash1_layout(
                level_fig, "Course Level Outcomes", height=440, subtitle="Use to prioritise programmes with lower GPA and higher risk. GPA/attendance range and course filters not applied."
            )
        else:
            figs["level_performance"] = _apply_dash1_layout(
                go.Figure(), "Course Level Outcomes (Unavailable)", height=440, subtitle="Use to prioritise programmes with lower GPA and higher risk. GPA/attendance range and course filters not applied."
            )
    else:
        figs["level_performance"] = _apply_dash1_layout(
            go.Figure(), "Course Level Outcomes (Unavailable)", height=440, subtitle="Use to prioritise programmes with lower GPA and higher risk. GPA/attendance range and course filters not applied."
        )

    if GPA_COL in df.columns and "Period (Unified)" in df.columns:
        period_df = df.copy()
        period_series = period_df["Period (Unified)"].astype("string")
        period_mask = period_series.notna() & ~period_series.str.strip().str.lower().isin(["n.a.", "na"])
        period_df = period_df[period_mask]
        if STUDENT_ID_COL in period_df.columns:
            period_df = period_df.drop_duplicates([STUDENT_ID_COL, "Period (Unified)"], keep="last")
        period_gpa = (
            period_df.groupby("Period (Unified)", observed=False)[GPA_COL]
            .mean()
            .reset_index(name="Mean GPA")
        )
        if not period_gpa.empty:
            period_order = _sort_periods(period_gpa["Period (Unified)"].tolist())
            period_gpa["Period (Unified)"] = pd.Categorical(
                period_gpa["Period (Unified)"], categories=period_order, ordered=True
            )
            period_gpa = period_gpa.sort_values("Period (Unified)")

            period_fig = go.Figure()
            period_fig.add_trace(
                go.Scatter(
                    x=period_gpa["Period (Unified)"],
                    y=period_gpa["Mean GPA"],
                    mode="lines+markers+text",
                    text=[f"{val:.3g}" for val in period_gpa["Mean GPA"]],
                    textposition="top center",
                    textfont=dict(color=DASH1_TEXT, size=10),
                    line=dict(color=DASH1_COLORWAY[3], width=3),
                    marker=dict(size=7, color=DASH1_COLORWAY[3]),
                    hovertemplate="Period=%{x}<br>Mean GPA=%{y:.3g}<extra></extra>",
                )
            )
            period_fig.update_xaxes(title="Period")
            period_fig.update_yaxes(title="Mean GPA", range=[0, 4])
            period_fig.update_layout(showlegend=False)
            if len(period_gpa) >= 2:
                diffs = period_gpa["Mean GPA"].diff()
                diffs = diffs.dropna()
                if not diffs.empty:
                    idx = diffs.abs().idxmax()
                    delta_gpa = diffs.loc[idx]
                    period_fig.add_annotation(
                        x=period_gpa.loc[idx, "Period (Unified)"],
                        y=period_gpa.loc[idx, "Mean GPA"],
                        text=f"{delta_gpa:+.3g} vs prior term",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=1,
                        ax=0,
                        ay=-30,
                        font=dict(size=11, color="#E2E8F0"),
        bgcolor="rgba(8,12,22,0.6)",
        bordercolor="rgba(148,163,184,0.3)",
        borderwidth=1,
        borderpad=4,
                    )
            figs["gpa_by_period"] = _apply_dash1_layout(
                period_fig, "GPA Trend by Term", height=340, subtitle="Line tracks average GPA by period."
            )
        else:
            figs["gpa_by_period"] = _apply_dash1_layout(
                go.Figure(), "GPA Trend by Term (Unavailable)", height=340, subtitle="Line tracks average GPA by period."
            )
    else:
        figs["gpa_by_period"] = _apply_dash1_layout(
            go.Figure(), "GPA Trend by Term (Unavailable)", height=340, subtitle="Line tracks average GPA by period."
        )

    if "Period (Unified)" in df.columns:
        cohort_df = df.copy()
        if STUDENT_ID_COL in cohort_df.columns:
            cohort_df = cohort_df.drop_duplicates([STUDENT_ID_COL, "Period (Unified)"], keep="last")
        period_series = cohort_df["Period (Unified)"].astype("string")
        period_series = period_series[period_series.notna()]
        period_series = period_series[~period_series.str.strip().str.lower().isin(["n.a.", "na"])]
        period_counts = period_series.value_counts()
        if not period_counts.empty:
            period_order = _sort_periods(period_counts.index.tolist())
            period_counts = period_counts.reindex(period_order)
            trend_fig = go.Figure()
            trend_fig.add_trace(
                go.Scatter(
                    x=period_counts.index.tolist(),
                    y=period_counts.values.tolist(),
                    mode="lines+markers+text",
                    text=period_counts.values.tolist(),
                    textposition="top center",
                    textfont=dict(color=DASH1_TEXT, size=10),
                    fill="tozeroy",
                    fillcolor="rgba(0,194,168,0.18)",
                    line=dict(color=DASH1_COLORWAY[2], width=3),
                    marker=dict(size=7, color=DASH1_COLORWAY[2]),
                    hovertemplate="Period=%{x}<br>Students=%{y}<extra></extra>",
                )
            )
            trend_fig.update_xaxes(title="Period")
            trend_fig.update_yaxes(title="Students")
            trend_fig.update_layout(showlegend=False)
            figs["cohort_trend"] = _apply_dash1_layout(
                trend_fig, "Cohort Size by Term", height=340, subtitle="Area shows unique students per period."
            )
        else:
            figs["cohort_trend"] = _apply_dash1_layout(
                go.Figure(), "Cohort Size by Term (Unavailable)", height=340, subtitle="Area shows unique students per period."
            )
    else:
        figs["cohort_trend"] = _apply_dash1_layout(
            go.Figure(), "Cohort Size by Term (Unavailable)", height=340, subtitle="Area shows unique students per period."
        )

    if "Completion Status" in snapshot_df.columns:
        status_series = snapshot_df["Completion Status"].fillna("N.A.").astype("string")
        status_counts = status_series.value_counts().rename_axis("Completion Status").reset_index(name="Count")
        status_fig = px.pie(
            status_counts,
            names="Completion Status",
            values="Count",
            hole=0.62,
            color="Completion Status",
            color_discrete_sequence=DASH1_COLORWAY,
        )
        status_fig.update_traces(
            textinfo="percent+label",
            textposition="inside",
            textfont=dict(color="#F8FAFC", size=12),
            hovertemplate="Status=%{label}<br>Count=%{value}<br>Share=%{percent}<extra></extra>",
        )
        total_students = int(status_counts["Count"].sum())
        pull = [0.04 if label == "Ongoing" else 0 for label in status_counts["Completion Status"].tolist()]
        status_fig.update_traces(pull=pull)
        status_fig.add_annotation(
            text=f"{total_students}<br>students",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color=DASH1_TEXT),
        )
        status_fig.update_layout(showlegend=False)
        figs["completion_mix"] = _apply_dash1_layout(
            status_fig, "Completion Status Mix", height=320, subtitle="Donut shows overall completion distribution."
        )
    else:
        figs["completion_mix"] = _apply_dash1_layout(
            go.Figure(), "Completion Status Mix (Unavailable)", height=320, subtitle="Donut shows overall completion distribution."
        )

    return figs



def make_dashboard_2_figures(df: pd.DataFrame) -> Dict[str, go.Figure]:
    """Create Dashboard 2 figures (Perceptions & Study Behaviour).

    Charts:
    - Perception score by risk tier (box)
    - Perception construct + study gap by risk tier (ranked)

    Args:
        df: Filtered analytics DataFrame.

    Returns:
        Dict of figures keyed by name.
    """
    figs: Dict[str, go.Figure] = {}
    snapshot_df = _latest_semester_snapshot(df).copy()
    course_col = COURSE_DISPLAY_COL if COURSE_DISPLAY_COL in snapshot_df.columns else DERIVED_COURSE_COL

    likert_available = [c for c in LIKERT_COLS if c in snapshot_df.columns]

    if PERCEPTION_SCORE_COL not in snapshot_df.columns and likert_available:
        snapshot_df[PERCEPTION_SCORE_COL] = snapshot_df[likert_available].mean(axis=1, skipna=True)

    risk_series = None
    if RISK_TIER_COL in snapshot_df.columns:
        risk_series = snapshot_df[RISK_TIER_COL].astype("string")
    elif RISK_FLAG_COL in snapshot_df.columns:
        risk_series = snapshot_df[RISK_FLAG_COL].map({1: "High", 0: "Low"}).astype("string")
    if risk_series is not None:
        risk_series = risk_series.str.title()

    risk_color_map = {"High": "#EF4444", "Medium": "#F4B400", "Low": "#22C55E"}


    if PERCEPTION_SCORE_COL in snapshot_df.columns and risk_series is not None:
        perc_vals = pd.to_numeric(snapshot_df[PERCEPTION_SCORE_COL], errors="coerce")
        mask = perc_vals.notna() & risk_series.notna()
        if mask.any():
            plot_df = snapshot_df.loc[mask, [PERCEPTION_SCORE_COL]].copy()
            plot_df["Risk Tier"] = risk_series[mask]
            plot_df = plot_df[plot_df["Risk Tier"].isin(["High", "Medium", "Low"])].copy()
            if not plot_df.empty:
                order = ["High", "Medium", "Low"]
                fig = go.Figure()
                for idx, tier in enumerate(order):
                    vals = plot_df.loc[plot_df["Risk Tier"] == tier, PERCEPTION_SCORE_COL]
                    if vals.empty:
                        continue
                    fig.add_trace(
                        go.Box(
                            y=vals,
                            name=str(tier),
                            boxmean=True,
                            marker_color=risk_color_map.get(tier, DASH1_COLORWAY[idx % len(DASH1_COLORWAY)]),
                            hovertemplate="Risk Tier=%{x}<br>Perception=%{y:.3g}<extra></extra>",
                        )
                    )
                fig.update_xaxes(title="Risk Tier")
                fig.update_yaxes(title="Perception Score")
                figs["perception_by_gpa_band"] = _apply_dash1_layout(
                    fig,
                    "Perception Score by Risk Tier",
                    height=440,
                    subtitle="Compares perception scores between high- and low-risk students.",
                )
            else:
                figs["perception_by_gpa_band"] = _apply_dash1_layout(
                    go.Figure(),
                    "Perception Score by Risk Tier (Unavailable)",
                    height=380,
                    subtitle="Compares perception scores between high- and low-risk students.",
                )
        else:
            figs["perception_by_gpa_band"] = _apply_dash1_layout(
                go.Figure(),
                "Perception Score by Risk Tier (Unavailable)",
                height=380,
                subtitle="Compares perception scores between high- and low-risk students.",
            )
    else:
        figs["perception_by_gpa_band"] = _apply_dash1_layout(
            go.Figure(),
            "Perception Score by Risk Tier (Unavailable)",
            height=380,
            subtitle="Compares perception scores between high- and low-risk students.",
        )

    if SELF_STUDY_COL in snapshot_df.columns and risk_series is not None:
        study_vals = pd.to_numeric(snapshot_df[SELF_STUDY_COL], errors="coerce")
        mask = study_vals.notna() & risk_series.notna()
        if mask.any():
            plot_df = snapshot_df.loc[mask, [SELF_STUDY_COL]].copy()
            plot_df["Risk Tier"] = risk_series[mask]
            plot_df = plot_df[plot_df["Risk Tier"].isin(["High", "Medium", "Low"])].copy()
            if not plot_df.empty:
                order = ["High", "Medium", "Low"]
                fig = go.Figure()
                for idx, tier in enumerate(order):
                    vals = plot_df.loc[plot_df["Risk Tier"] == tier, SELF_STUDY_COL]
                    if vals.empty:
                        continue
                    fig.add_trace(
                        go.Violin(
                            y=vals,
                            name=str(tier),
                            box=dict(visible=True),
                            meanline=dict(visible=True),
                            line_color=risk_color_map.get(tier, DASH1_COLORWAY[idx % len(DASH1_COLORWAY)]),
                            fillcolor=risk_color_map.get(tier, DASH1_COLORWAY[idx % len(DASH1_COLORWAY)]),
                            opacity=0.65,
                            hovertemplate="Risk Tier=%{x}<br>Study Hours=%{y:.3g}<extra></extra>",
                        )
                    )
                fig.update_xaxes(title="Risk Tier")
                fig.update_yaxes(title="Self-Study Hours")
                figs["study_hours_vs_gpa"] = _apply_dash1_layout(
                    fig,
                    "Study Hours by Risk Tier",
                    height=440,
                    subtitle="Shows how study time differs between high-, medium-, and low-risk students.",
                )
            else:
                figs["study_hours_vs_gpa"] = _apply_dash1_layout(
                    go.Figure(),
                    "Study Hours by Risk Tier (Unavailable)",
                    height=380,
                    subtitle="Shows how study time differs between high-, medium-, and low-risk students.",
                )
        else:
            figs["study_hours_vs_gpa"] = _apply_dash1_layout(
                go.Figure(),
                "Study Hours by Risk Tier (Unavailable)",
                height=380,
                subtitle="Shows how study time differs between high-, medium-, and low-risk students.",
            )
    else:
        figs["study_hours_vs_gpa"] = _apply_dash1_layout(
            go.Figure(),
            "Study Hours by Risk Tier (Unavailable)",
            height=380,
            subtitle="Shows how study time differs between high-, medium-, and low-risk students.",
        )

    # --- Perception radar (Likert profile) ---
    if likert_available and risk_series is not None:
        radar_df = snapshot_df.copy()
        radar_df["Risk Tier"] = risk_series
        categories = [PERCEPTION_LABEL_MAP.get(c, c) for c in likert_available]
        order = ["High", "Medium", "Low"]
        radar_fig = go.Figure()
        for tier in order:
            tier_vals = (
                radar_df.loc[radar_df["Risk Tier"] == tier, likert_available]
                .apply(pd.to_numeric, errors="coerce")
            )
            if tier_vals.notna().any().any():
                means = tier_vals.mean().values
                radar_fig.add_trace(
                    go.Scatterpolar(
                        r=means,
                        theta=categories,
                        fill="toself",
                        name=str(tier),
                        line_color=risk_color_map.get(tier, DASH1_COLORWAY[0]),
                        opacity=0.6,
                        hovertemplate="%{theta}<br>Mean=%{r:.2f}<extra></extra>",
                    )
                )
        radar_fig.update_layout(
            polar=dict(
                radialaxis=dict(range=[1, 5], tickfont=dict(color=DASH1_TEXT), gridcolor=DASH1_GRID)
            ),
            showlegend=True,
        )
        figs["perception_radar"] = _apply_dash1_layout(
            radar_fig,
            "Perception Radar by Risk Tier",
            height=420,
            subtitle="Profiles show average Likert scores across risk tiers.",
        )
    else:
        figs["perception_radar"] = _apply_dash1_layout(
            go.Figure(),
            "Perception Radar by Risk Tier (Unavailable)",
            height=420,
            subtitle="Profiles show average Likert scores across risk tiers.",
        )

    # --- Perception vs GPA scatter ---
    if PERCEPTION_SCORE_COL in snapshot_df.columns and GPA_COL in snapshot_df.columns:
        plot_df = snapshot_df[[PERCEPTION_SCORE_COL, GPA_COL]].copy()
        plot_df[PERCEPTION_SCORE_COL] = pd.to_numeric(plot_df[PERCEPTION_SCORE_COL], errors="coerce")
        plot_df[GPA_COL] = pd.to_numeric(plot_df[GPA_COL], errors="coerce")
        plot_df = plot_df[plot_df[PERCEPTION_SCORE_COL].notna() & plot_df[GPA_COL].notna()].copy()
        if not plot_df.empty:
            if risk_series is not None:
                plot_df["Risk Tier"] = risk_series.loc[plot_df.index]
            size_col = None
            if SELF_STUDY_COL in snapshot_df.columns:
                plot_df[SELF_STUDY_COL] = pd.to_numeric(snapshot_df.loc[plot_df.index, SELF_STUDY_COL], errors="coerce")
                size_col = SELF_STUDY_COL

            scatter = px.scatter(
                plot_df,
                x=PERCEPTION_SCORE_COL,
                y=GPA_COL,
                color="Risk Tier" if risk_series is not None else None,
                size=size_col,
                size_max=18,
                opacity=0.75,
                labels={PERCEPTION_SCORE_COL: "Perception Score", GPA_COL: "GPA"},
                color_discrete_map=risk_color_map,
            )
            scatter.update_traces(
                marker=dict(line=dict(width=0.5, color="rgba(255,255,255,0.35)")),
                hovertemplate="Perception=%{x:.2f}<br>GPA=%{y:.2f}<extra></extra>",
            )
            vals_x = plot_df[PERCEPTION_SCORE_COL]
            vals_y = plot_df[GPA_COL]
            if len(plot_df) >= 3 and vals_x.nunique() > 1:
                slope, intercept = np.polyfit(vals_x, vals_y, 1)
                corr = float(np.corrcoef(vals_x, vals_y)[0, 1])
                x_line = np.array([vals_x.min(), vals_x.max()])
                y_line = slope * x_line + intercept
                scatter.add_trace(
                    go.Scatter(
                        x=x_line,
                        y=y_line,
                        mode="lines",
                        name=f"Trend (r={corr:.2f})",
                        line=dict(color="#F4B400", width=2),
                        hovertemplate=f"Trend line<br>r={corr:.2f}<extra></extra>",
                    )
                )
            figs["perception_vs_gpa"] = _apply_dash1_layout(
                scatter,
                "Perception vs GPA",
                height=420,
                subtitle="Higher perception scores should align with stronger GPA outcomes.",
            )
        else:
            figs["perception_vs_gpa"] = _apply_dash1_layout(
                go.Figure(),
                "Perception vs GPA (Unavailable)",
                height=420,
                subtitle="Higher perception scores should align with stronger GPA outcomes.",
            )
    else:
        figs["perception_vs_gpa"] = _apply_dash1_layout(
            go.Figure(),
            "Perception vs GPA (Unavailable)",
            height=420,
            subtitle="Higher perception scores should align with stronger GPA outcomes.",
        )

    # --- Construct gaps by risk tier (High vs Low) ---
    gap_cols = list(likert_available)
    if SELF_STUDY_COL in snapshot_df.columns:
        gap_cols.append(SELF_STUDY_COL)
    if gap_cols and risk_series is not None:
        risk_df = snapshot_df.copy()
        risk_df["_risk_group"] = risk_series
        risk_df = risk_df[risk_df["_risk_group"].isin(["High", "Low"])].copy()
        rows = []
        for col in gap_cols:
            vals = pd.to_numeric(risk_df[col], errors="coerce")
            hi = vals[risk_df["_risk_group"] == "High"].dropna()
            lo = vals[risk_df["_risk_group"] == "Low"].dropna()
            if len(hi) < MIN_CORR_PAIRS or len(lo) < MIN_CORR_PAIRS:
                continue
            gap = float(lo.mean() - hi.mean())
            rows.append(
                {
                    "Factor": PERCEPTION_LABEL_MAP.get(col, col),
                    "Gap": gap,
                    "Low Mean": float(lo.mean()),
                    "High Mean": float(hi.mean()),
                    "N Low": int(len(lo)),
                    "N High": int(len(hi)),
                }
            )

        gap_df = pd.DataFrame(rows)
        if not gap_df.empty:
            gap_df["Abs Gap"] = gap_df["Gap"].abs()
            gap_df = gap_df.sort_values("Abs Gap", ascending=False)
            gap_df["Color"] = np.where(gap_df["Gap"] >= 0, "#38BDF8", "#EF4444")

            gap_fig = go.Figure(
                data=[
                    go.Bar(
                        x=gap_df["Gap"],
                        y=gap_df["Factor"],
                        orientation="h",
                        marker_color=gap_df["Color"],
                        text=[f"{v:+.2f}" for v in gap_df["Gap"]],
                        textposition="outside",
                        textfont=dict(color=DASH1_TEXT, size=11),
                        customdata=gap_df[["Low Mean", "High Mean", "N Low", "N High"]].to_numpy(),
                        hovertemplate=(
                            "Factor=%{y}<br>Gap (Low-High)=%{x:.2f}"
                            "<br>Low Mean=%{customdata[0]:.2f} (N=%{customdata[2]})"
                            "<br>High Mean=%{customdata[1]:.2f} (N=%{customdata[3]})<extra></extra>"
                        ),
                    )
                ]
            )
            gap_fig.add_vline(x=0, line_width=1, line_dash="dot", line_color="rgba(148,163,184,0.6)")
            gap_fig.update_xaxes(title="Mean score gap (Low - High risk)")
            gap_fig.update_yaxes(title="", automargin=True, categoryorder="array", categoryarray=gap_df["Factor"].tolist(), autorange="reversed")
            figs["construct_corr"] = _apply_dash1_layout(
                gap_fig,
                "Perception Construct Gaps by Risk Tier",
                height=440,
                subtitle="Positive values indicate higher scores among low-risk students (includes self-study hours).",
            )
        else:
            figs["construct_corr"] = _apply_dash1_layout(
                go.Figure(),
                "Perception Construct Gaps by Risk Tier (Unavailable)",
                height=440,
                subtitle="Positive values indicate higher scores among low-risk students (includes self-study hours).",
            )
    else:
        figs["construct_corr"] = _apply_dash1_layout(
            go.Figure(),
            "Perception Construct Gaps by Risk Tier (Unavailable)",
            height=440,
            subtitle="Positive values indicate higher scores among low-risk students (includes self-study hours).",
        )

    # --- Perception driver strength (corr with GPA) ---
    driver_cols = []
    for c in [PERCEPTION_SCORE_COL, SELF_STUDY_COL] + likert_available:
        if c in snapshot_df.columns and c not in driver_cols:
            driver_cols.append(c)
    if GPA_COL in snapshot_df.columns and driver_cols:
        rows = []
        for col in driver_cols:
            vals = snapshot_df[[col, GPA_COL]].apply(pd.to_numeric, errors="coerce")
            mask = vals[col].notna() & vals[GPA_COL].notna()
            if mask.sum() < MIN_CORR_PAIRS:
                continue
            corr_val = float(np.corrcoef(vals.loc[mask, col], vals.loc[mask, GPA_COL])[0, 1])
            risk_corr = np.nan
            if RISK_SCORE_COL in snapshot_df.columns:
                risk_vals = pd.to_numeric(snapshot_df[RISK_SCORE_COL], errors="coerce")
                mask2 = vals[col].notna() & risk_vals.notna()
                if mask2.sum() >= MIN_CORR_PAIRS:
                    risk_corr = float(np.corrcoef(vals.loc[mask2, col], risk_vals.loc[mask2])[0, 1])
            rows.append(
                {
                    "Factor": PERCEPTION_LABEL_MAP.get(col, col),
                    "Corr": corr_val,
                    "Risk Corr": risk_corr,
                    "N": int(mask.sum()),
                }
            )
        driver_df = pd.DataFrame(rows)
        if not driver_df.empty:
            driver_df["Abs"] = driver_df["Corr"].abs()
            driver_df = driver_df.sort_values("Abs", ascending=False)
            if len(driver_df) > 10:
                driver_df = driver_df.head(10)
            driver_df["Color"] = np.where(driver_df["Corr"] >= 0, "#38BDF8", "#EF4444")

            driver_fig = go.Figure(
                data=[
                    go.Bar(
                        x=driver_df["Corr"],
                        y=driver_df["Factor"],
                        orientation="h",
                        marker_color=driver_df["Color"],
                        text=[f"{v:+.2f}" for v in driver_df["Corr"]],
                        textposition="outside",
                        textfont=dict(color=DASH1_TEXT, size=11),
                        customdata=driver_df[["N", "Risk Corr"]].to_numpy(),
                        hovertemplate=(
                            "Factor=%{y}<br>Corr with GPA=%{x:.2f}"
                            "<br>N=%{customdata[0]}<br>Corr with Risk=%{customdata[1]:.2f}<extra></extra>"
                        ),
                    )
                ]
            )
            driver_fig.add_vline(x=0, line_dash="dot", line_color="rgba(148,163,184,0.6)")
            driver_fig.update_xaxes(title="Correlation with GPA")
            driver_fig.update_yaxes(title="", automargin=True, autorange="reversed")
            figs["perception_drivers"] = _apply_dash1_layout(
                driver_fig,
                "Perception Driver Strength",
                height=420,
                subtitle="Top constructs with strongest association to GPA; hover shows risk correlation.",
            )
        else:
            figs["perception_drivers"] = _apply_dash1_layout(
                go.Figure(),
                "Perception Driver Strength (Unavailable)",
                height=420,
                subtitle="Top constructs with strongest association to GPA; hover shows risk correlation.",
            )
    else:
        figs["perception_drivers"] = _apply_dash1_layout(
            go.Figure(),
            "Perception Driver Strength (Unavailable)",
            height=420,
            subtitle="Top constructs with strongest association to GPA; hover shows risk correlation.",
        )

    # --- Engagement vs performance index ---
    if ENGAGEMENT_COL in snapshot_df.columns and PERFORMANCE_INDEX_COL in snapshot_df.columns:
        evp_df = snapshot_df[[ENGAGEMENT_COL, PERFORMANCE_INDEX_COL]].copy()
        evp_df[ENGAGEMENT_COL] = pd.to_numeric(evp_df[ENGAGEMENT_COL], errors="coerce")
        evp_df[PERFORMANCE_INDEX_COL] = pd.to_numeric(evp_df[PERFORMANCE_INDEX_COL], errors="coerce")
        evp_df = evp_df[evp_df[ENGAGEMENT_COL].notna() & evp_df[PERFORMANCE_INDEX_COL].notna()].copy()
        if not evp_df.empty:
            if risk_series is not None:
                evp_df["Risk Tier"] = risk_series.loc[evp_df.index]
            evp_fig = px.scatter(
                evp_df,
                x=ENGAGEMENT_COL,
                y=PERFORMANCE_INDEX_COL,
                color="Risk Tier" if risk_series is not None else None,
                color_discrete_map=risk_color_map,
                opacity=0.75,
                labels={
                    ENGAGEMENT_COL: "Engagement Score",
                    PERFORMANCE_INDEX_COL: "Performance Index",
                },
            )
            evp_fig.update_traces(
                marker=dict(line=dict(width=0.5, color="rgba(255,255,255,0.35)")),
                hovertemplate="Engagement=%{x:.2f}<br>Performance=%{y:.2f}<extra></extra>",
            )
            evp_fig.add_vline(x=0.5, line_dash="dot", line_color="rgba(148,163,184,0.6)")
            evp_fig.add_hline(y=0.5, line_dash="dot", line_color="rgba(148,163,184,0.6)")
            figs["engagement_vs_perf"] = _apply_dash1_layout(
                evp_fig,
                "Engagement vs Performance",
                height=420,
                subtitle="Quadrants surface high-engagement/low-performance and low-engagement/high-performance segments.",
            )
        else:
            figs["engagement_vs_perf"] = _apply_dash1_layout(
                go.Figure(),
                "Engagement vs Performance (Unavailable)",
                height=420,
                subtitle="Quadrants surface high-engagement/low-performance and low-engagement/high-performance segments.",
            )
    else:
        figs["engagement_vs_perf"] = _apply_dash1_layout(
            go.Figure(),
            "Engagement vs Performance (Unavailable)",
            height=420,
            subtitle="Quadrants surface high-engagement/low-performance and low-engagement/high-performance segments.",
        )

    # --- Correlation map (perception + study + outcomes) ---
    corr_cols = []
    for c in (
        PERCEPTION_SCORE_COL,
        SELF_STUDY_COL,
        GPA_COL,
        ATTEND_COL,
    ):
        if c in snapshot_df.columns:
            corr_cols.append(c)
    for c in likert_available:
        if c in snapshot_df.columns:
            corr_cols.append(c)

    corr_cols = [c for i, c in enumerate(corr_cols) if c not in corr_cols[:i]]
    if len(corr_cols) >= 2:
        numeric = snapshot_df[corr_cols].apply(pd.to_numeric, errors="coerce")
        corr = numeric.corr()

        corr_values = corr.values
        corr_text = np.vectorize(lambda v: f"{v:.3g}" if np.isfinite(v) else "")(corr_values)
        heat = go.Figure(
            data=go.Heatmap(
                z=corr_values,
                text=corr_text,
                texttemplate="%{text}",
                textfont=dict(size=10, color=DASH1_TEXT),
                x=corr.columns,
                y=corr.index,
                zmin=-1,
                zmid=0,
                zmax=1,
                colorscale=[[0.0, "#EF4444"], [0.5, "#111827"], [1.0, "#38BDF8"]],
                xgap=1,
                ygap=1,
                colorbar=dict(title="Corr", len=0.75, thickness=12, tickvals=[-1, -0.5, 0, 0.5, 1]),
                hovertemplate="X=%{x}<br>Y=%{y}<br>Corr=%{z:.3g}<extra></extra>",
            )
        )
        annotations = []
        corr_no_diag = corr.copy()
        np.fill_diagonal(corr_no_diag.values, np.nan)
        corr_stack = corr_no_diag.stack(future_stack=True)
        if not corr_stack.empty:
            pos_pair = corr_stack.idxmax()
            pos_val = float(corr_stack.max())
            neg_pair = corr_stack.idxmin()
            neg_val = float(corr_stack.min())
            summary_text = (
                f"Strongest +: {pos_pair[0]} x {pos_pair[1]} ({pos_val:.3g}) | "
                f"Strongest -: {neg_pair[0]} x {neg_pair[1]} ({neg_val:.3g})"
            )
            annotations.append(
                dict(
                    x=0.0,
                    y=1.14,
                    xref="paper",
                    yref="paper",
                    text=f"<b>{summary_text}</b>",
                    showarrow=False,
                    align="left",
                    font=dict(size=11, color="#F8FAFC"),
                    bgcolor="rgba(2,6,23,0.88)",
                    bordercolor="rgba(148,163,184,0.35)",
                    borderwidth=1,
                    borderpad=4,
                )
            )
        for i, row in enumerate(corr_values):
            for j, val in enumerate(row):
                is_strong = abs(val) >= 0.35
                color = "#F8FAFC" if is_strong else "#E2E8F0"
                bg_color = "rgba(2,6,23,0.85)" if is_strong else "rgba(15,23,42,0.55)"
                annotations.append(
                    dict(
                        x=corr.columns[j],
                        y=corr.index[i],
                        text=f"{val:.3g}",
                        showarrow=False,
                        font=dict(size=11, color=color),
                        bgcolor=bg_color,
                        bordercolor="rgba(148,163,184,0.35)",
                        borderwidth=1,
                        borderpad=2,
                    )
                )
        heat.update_layout(showlegend=False, margin=dict(l=90, r=50, t=120, b=90), annotations=annotations)
        heat.update_xaxes(tickangle=-30, automargin=True, tickfont=dict(size=9, color=DASH1_TEXT))
        heat.update_yaxes(automargin=True, tickfont=dict(size=9, color=DASH1_TEXT))
        figs["corr_heatmap"] = _apply_dash1_layout(
            heat, "Perception & Outcome Correlation Map", height=500, subtitle="Cell values show correlation strength across variables."
        )
    else:
        figs["corr_heatmap"] = _apply_dash1_layout(
            go.Figure(), "Perception & Outcome Correlation Map (Unavailable)", height=440, subtitle="Cell values show correlation strength across variables."
        )
    return figs
























# === Dynamic risk + targeting + premium charts ===
FUNDING_GROUP_COL = "Funding Group"
ATTENDANCE_BAND_COL = "Attendance Band"
GPA_BAND_COL = "GPA Band"
STUDY_HOURS_BAND_COL = "Study Hours Band"
RISK_DYNAMIC_COL = "Risk (Dynamic)"
LOW_GPA_FLAG_COL = "Low GPA Flag"
LOW_ATT_FLAG_COL = "Low Attendance Flag"
QUADRANT_COL = "Quadrant Label"
SUPPORT_INDEX_COL = "Support Index"
ENGAGEMENT_INDEX_COL = "Engagement Index"
BEHAVIOUR_INDEX_COL = "Behaviour Index"
PERIOD_UNIFIED_COL = "Period (Unified)"

RISK_COLOR_MAP = {
    "Low": "#22C55E",
    "Medium": "#F4B400",
    "High": "#EF4444",
}


def _normalise_0_1(series: pd.Series) -> pd.Series:
    vals = pd.to_numeric(series, errors="coerce")
    if vals.notna().sum() == 0:
        return pd.Series(np.nan, index=series.index)
    min_val = float(vals.min())
    max_val = float(vals.max())
    if min_val == max_val:
        return pd.Series(0.5, index=series.index)
    return (vals - min_val) / (max_val - min_val)


def _safe_string(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip()


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if COURSE_LEVEL_COL not in out.columns:
        course_source = None
        if COURSE_NAME_COL in out.columns:
            course_source = out[COURSE_NAME_COL].astype("string")
        elif DERIVED_COURSE_COL in out.columns:
            course_source = out[DERIVED_COURSE_COL].astype("string")
        if course_source is not None:
            lower = course_source.str.lower().fillna("")
            out[COURSE_LEVEL_COL] = np.select(
                [
                    lower.str.startswith("specialist diploma"),
                    lower.str.startswith("diploma"),
                    lower.str.startswith("certificate"),
                ],
                ["Specialist Diploma", "Diploma", "Certificate"],
                default="Other",
            )

    if COURSE_LEVEL_COL not in out.columns:
        out[COURSE_LEVEL_COL] = "Unknown"

    if HIGHEST_EDU_COL not in out.columns:
        out[HIGHEST_EDU_COL] = "Unknown"

    if FUNDING_GROUP_COL not in out.columns:
        if COURSE_FUNDING_COL in out.columns:
            raw = _safe_string(out[COURSE_FUNDING_COL]).str.lower()

            def _map_funding(val: str) -> str:
                if not val or val in ("n.a.", "na", "nan"):
                    return "Unknown"
                if "sponsor" in val or "sdf" in val:
                    return "Sponsored"
                if "individual" in val or "sfc" in val:
                    return "Individual"
                return "Other"

            out[FUNDING_GROUP_COL] = raw.apply(_map_funding).astype("string")
        else:
            out[FUNDING_GROUP_COL] = "Unknown"

    if ATTENDANCE_BAND_COL not in out.columns and ATTEND_COL in out.columns:
        att_vals = pd.to_numeric(out[ATTEND_COL], errors="coerce")
        out[ATTENDANCE_BAND_COL] = pd.cut(
            att_vals,
            bins=[-np.inf, 70, 80, 90, np.inf],
            labels=["<70", "70-79", "80-89", "90+"],
        ).astype("string")

    if GPA_BAND_COL not in out.columns and GPA_COL in out.columns:
        gpa_vals = pd.to_numeric(out[GPA_COL], errors="coerce")
        out[GPA_BAND_COL] = pd.cut(
            gpa_vals,
            bins=[-np.inf, 2.0, 2.5, 3.0, 3.5, 4.0],
            labels=["<2.0", "2.0-2.49", "2.5-2.99", "3.0-3.49", "3.5-4.0"],
        ).astype("string")

    if STUDY_HOURS_BAND_COL not in out.columns and SELF_STUDY_COL in out.columns:
        study_vals = pd.to_numeric(out[SELF_STUDY_COL], errors="coerce")
        out[STUDY_HOURS_BAND_COL] = pd.cut(
            study_vals,
            bins=[-np.inf, 3, 6, 10, np.inf],
            labels=["<3", "3-6", "6-10", "10+"],
        ).astype("string")

    support_cols = [c for c in ["Teaching Support", "Company Support", "Family Support"] if c in out.columns]
    engage_cols = [c for c in ["Prior Knowledge", "Course Relevance"] if c in out.columns]

    if support_cols:
        support_vals = out[support_cols].apply(pd.to_numeric, errors="coerce")
        out[SUPPORT_INDEX_COL] = _normalise_0_1(support_vals.mean(axis=1, skipna=True))
    if engage_cols:
        engage_vals = out[engage_cols].apply(pd.to_numeric, errors="coerce")
        out[ENGAGEMENT_INDEX_COL] = _normalise_0_1(engage_vals.mean(axis=1, skipna=True))
    if SELF_STUDY_COL in out.columns:
        out[BEHAVIOUR_INDEX_COL] = _normalise_0_1(out[SELF_STUDY_COL])

    return out


def compute_risk_3level(df: pd.DataFrame, gpa_thr: float, att_thr: float) -> pd.DataFrame:
    out = df.copy()
    gpa_vals = pd.to_numeric(out[GPA_COL], errors="coerce") if GPA_COL in out.columns else pd.Series(np.nan, index=out.index)
    att_vals = pd.to_numeric(out[ATTEND_COL], errors="coerce") if ATTEND_COL in out.columns else pd.Series(np.nan, index=out.index)

    low_gpa = gpa_vals < gpa_thr
    low_att = att_vals < att_thr
    both = low_gpa & low_att
    one = low_gpa ^ low_att

    risk = pd.Series(pd.NA, index=out.index, dtype="string")
    mask = gpa_vals.notna() & att_vals.notna()
    risk.loc[mask & both] = "High"
    risk.loc[mask & one] = "Medium"
    risk.loc[mask & ~both & ~one] = "Low"

    cat_type = pd.api.types.CategoricalDtype(categories=["Low", "Medium", "High"], ordered=True)
    out[RISK_DYNAMIC_COL] = risk.astype(cat_type)

    out[LOW_GPA_FLAG_COL] = pd.Series(np.where(gpa_vals.notna(), low_gpa, pd.NA), index=out.index).astype("boolean")
    out[LOW_ATT_FLAG_COL] = pd.Series(np.where(att_vals.notna(), low_att, pd.NA), index=out.index).astype("boolean")

    quadrant = pd.Series("Unknown", index=out.index, dtype="string")
    quadrant.loc[mask & ~low_gpa & ~low_att] = "Q1 Maintain"
    quadrant.loc[mask & ~low_gpa & low_att] = "Q2 Attendance Coaching"
    quadrant.loc[mask & low_gpa & ~low_att] = "Q3 Academic Coaching"
    quadrant.loc[mask & low_gpa & low_att] = "Q4 Immediate Intervention"
    out[QUADRANT_COL] = quadrant

    return out


def make_targeting_table(df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    if df.empty:
        empty = pd.DataFrame(
            columns=[
                PERIOD_UNIFIED_COL,
                COURSE_LEVEL_COL,
                FUNDING_GROUP_COL,
                HIGHEST_EDU_COL,
                ATTENDANCE_BAND_COL,
                "n_students",
                "avg_gpa",
                "avg_attendance",
                "high_risk_rate",
                "med_risk_rate",
                "low_risk_rate",
                "low_gpa_rate",
                "low_att_rate",
                "priority_index",
                "lift",
            ]
        )
        return empty, 0.0

    period_col = PERIOD_UNIFIED_COL if PERIOD_UNIFIED_COL in df.columns else PERIOD_COL
    group_cols = [period_col, COURSE_LEVEL_COL, FUNDING_GROUP_COL, HIGHEST_EDU_COL, ATTENDANCE_BAND_COL]

    overall_high = float((df[RISK_DYNAMIC_COL] == "High").mean()) if RISK_DYNAMIC_COL in df.columns else 0.0
    overall_high = overall_high if overall_high > 0 else 1e-9

    def _rate(series, value):
        if series.empty:
            return 0.0
        return float((series == value).mean())

    grouped = df.groupby(group_cols, dropna=False, observed=False)
    tbl = grouped.agg(
        n_students=(STUDENT_ID_COL, "nunique"),
        avg_gpa=(GPA_COL, "mean"),
        avg_attendance=(ATTEND_COL, "mean"),
        high_risk_rate=(RISK_DYNAMIC_COL, lambda s: _rate(s, "High")),
        med_risk_rate=(RISK_DYNAMIC_COL, lambda s: _rate(s, "Medium")),
        low_risk_rate=(RISK_DYNAMIC_COL, lambda s: _rate(s, "Low")),
        low_gpa_rate=(LOW_GPA_FLAG_COL, "mean"),
        low_att_rate=(LOW_ATT_FLAG_COL, "mean"),
    ).reset_index()

    tbl["priority_index"] = tbl["n_students"] * tbl["high_risk_rate"]
    tbl["lift"] = tbl["high_risk_rate"] / overall_high
    tbl = tbl.sort_values("priority_index", ascending=False)
    return tbl, overall_high


def make_kpi_cards_data(df: pd.DataFrame, targeting_df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total": 0,
            "avg_gpa": float("nan"),
            "avg_att": float("nan"),
            "high": float("nan"),
            "medium": float("nan"),
            "top_segment": "N.A.",
        }
    total = int(df[STUDENT_ID_COL].nunique()) if STUDENT_ID_COL in df.columns else len(df)
    avg_gpa = float(pd.to_numeric(df[GPA_COL], errors="coerce").mean()) if GPA_COL in df.columns else float("nan")
    avg_att = float(pd.to_numeric(df[ATTEND_COL], errors="coerce").mean()) if ATTEND_COL in df.columns else float("nan")
    high = float((df[RISK_DYNAMIC_COL] == "High").mean() * 100.0) if RISK_DYNAMIC_COL in df.columns else float("nan")
    med = float((df[RISK_DYNAMIC_COL] == "Medium").mean() * 100.0) if RISK_DYNAMIC_COL in df.columns else float("nan")
    top_segment = "N.A."
    if not targeting_df.empty:
        row = targeting_df.iloc[0]
        top_segment = f"{row.get(COURSE_LEVEL_COL, 'N.A.')} | {row.get(FUNDING_GROUP_COL, 'N.A.')} | {row.get(ATTENDANCE_BAND_COL, 'N.A.')}"
    return {
        "total": total,
        "avg_gpa": avg_gpa,
        "avg_att": avg_att,
        "high": high,
        "medium": med,
        "top_segment": top_segment,
    }


def make_recommendations(targeting_df: pd.DataFrame) -> list[dict]:
    recs = []
    if targeting_df.empty:
        return recs
    top = targeting_df.head(3)
    for _, row in top.iterrows():
        cohort = f"{row.get(COURSE_LEVEL_COL, 'N.A.')} | {row.get(FUNDING_GROUP_COL, 'N.A.')} | {row.get(HIGHEST_EDU_COL, 'N.A.')} | {row.get(ATTENDANCE_BAND_COL, 'N.A.')}"
        evidence = (
            f"n={int(row.get('n_students', 0))}, "
            f"High risk={row.get('high_risk_rate', 0):.0%}, "
            f"Lift={row.get('lift', 0):.2f}, "
            f"Avg GPA={row.get('avg_gpa', float('nan')):.2f}, "
            f"Avg attendance={row.get('avg_attendance', float('nan')):.1f}%"
        )
        suggestion = "Attendance coaching" if row.get("low_att_rate", 0) >= row.get("low_gpa_rate", 0) else "Academic support"
        expected = "Reduce high-risk rates by addressing the breached threshold."
        recs.append({
            "cohort": cohort,
            "evidence": evidence,
            "suggestion": suggestion,
            "expected": expected,
        })
    return recs


def make_sunburst_chart(df: pd.DataFrame, value_mode: str = "count") -> go.Figure:
    if df.empty:
        return _dash_empty_figure("Risk Composition Map")

    path_cols = [COURSE_LEVEL_COL, FUNDING_GROUP_COL, HIGHEST_EDU_COL, ATTENDANCE_BAND_COL, RISK_DYNAMIC_COL]
    data = df.copy()
    for col in path_cols:
        if col not in data.columns:
            data[col] = "Unknown"
        data[col] = data[col].astype("string").fillna("Unknown")

    grouped = data.groupby(path_cols, dropna=False, observed=False).agg(
        n_students=(STUDENT_ID_COL, "nunique"),
        avg_gpa=(GPA_COL, "mean"),
        avg_attendance=(ATTEND_COL, "mean"),
    ).reset_index()

    seg_cols = [COURSE_LEVEL_COL, FUNDING_GROUP_COL, HIGHEST_EDU_COL, ATTENDANCE_BAND_COL]
    seg = data.groupby(seg_cols, dropna=False, observed=False)[RISK_DYNAMIC_COL].apply(lambda s: (s == "High").mean()).reset_index(name="high_risk_rate")
    grouped = grouped.merge(seg, on=seg_cols, how="left")
    grouped["priority_index"] = grouped["n_students"] * grouped["high_risk_rate"]

    value_col = "n_students" if value_mode == "count" else "priority_index"
    fig = px.sunburst(
        grouped,
        path=path_cols,
        values=value_col,
        color="high_risk_rate",
        color_continuous_scale=[[0.0, "#22C55E"], [0.5, "#F4B400"], [1.0, "#EF4444"]],
    )
    custom_cols = seg_cols + ["avg_gpa", "avg_attendance", "high_risk_rate"]
    fig.update_traces(
        hovertemplate=(
            "<b>%{label}</b><br>Students=%{value:.0f}<br>"
            "Avg GPA=%{customdata[4]:.2f}<br>Avg attendance=%{customdata[5]:.1f}%<br>"
            "High risk rate=%{customdata[6]:.0%}<extra></extra>"
        ),
        customdata=grouped[custom_cols].to_numpy(),
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return _apply_dash1_layout(
        fig,
        "Risk Composition Map: Where Support Should Be Targeted",
        height=500,
        subtitle="Hierarchy shows course level, funding, qualification, attendance band, and dynamic risk.",
    )


def make_sankey_chart(df: pd.DataFrame, value_mode: str = "count") -> go.Figure:
    if df.empty:
        return _dash_empty_figure("Driver Flow")

    data = df.copy()
    for col in [FUNDING_GROUP_COL, ATTENDANCE_BAND_COL, RISK_DYNAMIC_COL]:
        if col not in data.columns:
            data[col] = "Unknown"

    if LOW_GPA_FLAG_COL in data.columns:
        data["Low GPA Outcome"] = np.where(data[LOW_GPA_FLAG_COL].fillna(False), "Low GPA", "Not Low GPA")
    else:
        data["Low GPA Outcome"] = np.where(pd.to_numeric(data[GPA_COL], errors="coerce") < 2.5, "Low GPA", "Not Low GPA")

    if value_mode == "impact":
        seg = data.groupby([FUNDING_GROUP_COL, ATTENDANCE_BAND_COL], observed=False)[RISK_DYNAMIC_COL].apply(lambda s: (s == "High").mean()).reset_index(name="high_risk_rate")
        seg["priority_index"] = seg["high_risk_rate"]
        data = data.merge(seg, on=[FUNDING_GROUP_COL, ATTENDANCE_BAND_COL], how="left")
        data["weight"] = data["priority_index"].fillna(0) + 1e-6
    else:
        data["weight"] = 1.0

    levels = [FUNDING_GROUP_COL, ATTENDANCE_BAND_COL, RISK_DYNAMIC_COL, "Low GPA Outcome"]
    labels = []
    for col in levels:
        labels.extend(data[col].astype("string").fillna("Unknown").unique().tolist())
    labels = list(dict.fromkeys(labels))
    label_index = {label: i for i, label in enumerate(labels)}

    def _links(src_col, tgt_col):
        tmp = data.groupby([src_col, tgt_col], observed=False)["weight"].sum().reset_index()
        return (
            tmp[src_col].map(label_index).tolist(),
            tmp[tgt_col].map(label_index).tolist(),
            tmp["weight"].tolist(),
        )

    s1, t1, v1 = _links(levels[0], levels[1])
    s2, t2, v2 = _links(levels[1], levels[2])
    s3, t3, v3 = _links(levels[2], levels[3])

    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=18,
                    thickness=16,
                    line=dict(color="rgba(148,163,184,0.4)", width=0.5),
                    label=labels,
                    color="rgba(15,23,42,0.9)",
                ),
                link=dict(
                    source=s1 + s2 + s3,
                    target=t1 + t2 + t3,
                    value=v1 + v2 + v3,
                    color="rgba(56,189,248,0.35)",
                ),
            )
        ]
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return _apply_dash1_layout(
        fig,
        "Driver Flow: Funding -> Attendance Band -> Risk -> Low GPA",
        height=500,
        subtitle="Toggle between counts and impact to assess targeting intensity.",
    )


def make_quadrant_scatter(df: pd.DataFrame, gpa_thr: float, att_thr: float) -> go.Figure:
    if df.empty:
        return _dash_empty_figure("GPA vs Attendance Quadrants")
    plot_df = df.copy()
    plot_df[GPA_COL] = pd.to_numeric(plot_df[GPA_COL], errors="coerce")
    plot_df[ATTEND_COL] = pd.to_numeric(plot_df[ATTEND_COL], errors="coerce")
    plot_df = plot_df[plot_df[GPA_COL].notna() & plot_df[ATTEND_COL].notna()].copy()
    if plot_df.empty:
        return _dash_empty_figure("GPA vs Attendance Quadrants")

    size_col = SELF_STUDY_COL if SELF_STUDY_COL in plot_df.columns else None
    if size_col:
        plot_df[size_col] = pd.to_numeric(plot_df[size_col], errors="coerce").fillna(0)
        plot_df[size_col] = plot_df[size_col].clip(lower=0)
        if plot_df[size_col].sum() <= 0:
            size_col = None
    fig = px.scatter(
        plot_df,
        x=ATTEND_COL,
        y=GPA_COL,
        color=RISK_DYNAMIC_COL,
        size=size_col,
        size_max=18,
        opacity=0.75,
        color_discrete_map=RISK_COLOR_MAP,
        labels={ATTEND_COL: "Attendance (%)", GPA_COL: "GPA"},
    )
    fig.update_traces(
        hovertemplate="Attendance=%{x:.1f}%<br>GPA=%{y:.2f}<extra></extra>",
        marker=dict(line=dict(width=0.4, color="rgba(255,255,255,0.3)")),
    )
    fig.add_vline(x=float(att_thr), line_dash="dash", line_color="rgba(239,68,68,0.8)")
    fig.add_hline(y=float(gpa_thr), line_dash="dash", line_color="rgba(239,68,68,0.8)")
    fig.add_annotation(x=att_thr + 5, y=gpa_thr + 0.2, text="Maintain", showarrow=False)
    fig.add_annotation(x=att_thr + 5, y=gpa_thr - 0.4, text="Academic Coaching", showarrow=False)
    fig.add_annotation(x=att_thr - 20, y=gpa_thr + 0.2, text="Attendance Coaching", showarrow=False)
    fig.add_annotation(x=att_thr - 20, y=gpa_thr - 0.4, text="Immediate Intervention", showarrow=False)
    return _apply_dash1_layout(
        fig,
        "GPA vs Attendance Quadrants (Threshold-Driven Risk)",
        height=520,
        subtitle="Quadrants align to dynamic thresholds and intervention labels.",
    )


def make_parcats_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _dash_empty_figure("Categorical Journeys Into Risk")
    dims = []
    for col, label in [
        (COURSE_LEVEL_COL, "Course Level"),
        (FUNDING_GROUP_COL, "Funding Group"),
        (HIGHEST_EDU_COL, "Highest Qualification"),
        (ATTENDANCE_BAND_COL, "Attendance Band"),
        (RISK_DYNAMIC_COL, "Risk"),
    ]:
        if col in df.columns:
            dims.append(dict(label=label, values=df[col].astype("string").fillna("Unknown")))
    if not dims:
        return _dash_empty_figure("Categorical Journeys Into Risk")

    risk_vals = df[RISK_DYNAMIC_COL].astype("string").fillna("Unknown") if RISK_DYNAMIC_COL in df.columns else pd.Series("Unknown", index=df.index)
    color_vals = risk_vals.map({"Low": 0, "Medium": 1, "High": 2}).fillna(0)

    fig = go.Figure(
        data=[
            go.Parcats(
                dimensions=dims,
                line=dict(color=color_vals, colorscale=[[0.0, "#22C55E"], [0.5, "#F4B400"], [1.0, "#EF4444"]]),
                labelfont=dict(size=11, color=DASH1_TEXT),
            )
        ]
    )
    return _apply_dash1_layout(
        fig,
        "Categorical Journeys Into Risk",
        height=520,
        subtitle="Track pathways from programme context into risk tiers.",
    )


def make_lift_heatmap(df: pd.DataFrame, mode: str = "funding") -> go.Figure:
    if df.empty:
        return _dash_empty_figure("High-Risk Lift Heatmap")

    overall_high = float((df[RISK_DYNAMIC_COL] == "High").mean()) if RISK_DYNAMIC_COL in df.columns else 0.0
    overall_high = overall_high if overall_high > 0 else 1e-9

    if mode == "course":
        col_key = COURSE_LEVEL_COL
    else:
        col_key = FUNDING_GROUP_COL

    row_key = ATTENDANCE_BAND_COL
    if row_key not in df.columns or col_key not in df.columns:
        return _dash_empty_figure("High-Risk Lift Heatmap")

    grouped = df.groupby([row_key, col_key], observed=False)[RISK_DYNAMIC_COL].apply(lambda s: (s == "High").mean()).reset_index(name="high_risk_rate")
    grouped["lift"] = grouped["high_risk_rate"] / overall_high

    pivot = grouped.pivot(index=row_key, columns=col_key, values="lift")
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale=[[0.0, "#0B1222"], [0.5, "#2563EB"], [1.0, "#EF4444"]],
            hovertemplate="%{y} | %{x}<br>Lift=%{z:.2f}<extra></extra>",
        )
    )
    fig.update_xaxes(title="Funding Group" if mode == "funding" else "Course Level")
    fig.update_yaxes(title="Attendance Band")
    return _apply_dash1_layout(
        fig,
        "High-Risk Lift Heatmap (Above Baseline)",
        height=420,
        subtitle="Lift >1 indicates segments above the overall high-risk baseline.",
    )


def make_gpa_distribution(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _dash_empty_figure("GPA Distribution by Funding and Qualification")

    from plotly.subplots import make_subplots
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Funding Group", "Highest Qualification"))

    if FUNDING_GROUP_COL in df.columns:
        for risk in ["Low", "Medium", "High"]:
            vals = df.loc[df[RISK_DYNAMIC_COL] == risk, GPA_COL]
            fig.add_trace(
                go.Violin(
                    y=vals,
                    name=risk,
                    legendgroup=risk,
                    scalegroup=risk,
                    line_color=RISK_COLOR_MAP.get(risk),
                    fillcolor=RISK_COLOR_MAP.get(risk),
                    opacity=0.5,
                    box=dict(visible=True),
                    meanline=dict(visible=True),
                ),
                row=1,
                col=1,
            )

    if HIGHEST_EDU_COL in df.columns:
        for risk in ["Low", "Medium", "High"]:
            vals = df.loc[df[RISK_DYNAMIC_COL] == risk, GPA_COL]
            fig.add_trace(
                go.Violin(
                    y=vals,
                    name=risk,
                    legendgroup=risk,
                    scalegroup=risk,
                    line_color=RISK_COLOR_MAP.get(risk),
                    fillcolor=RISK_COLOR_MAP.get(risk),
                    opacity=0.5,
                    box=dict(visible=True),
                    meanline=dict(visible=True),
                    showlegend=False,
                ),
                row=1,
                col=2,
            )

    fig.update_layout(violinmode="overlay", height=420)
    return _apply_dash1_layout(
        fig,
        "GPA Distribution by Funding and Qualification",
        height=420,
        subtitle="Distributions split by risk tier to avoid averages-only views.",
    )


def make_radar_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _dash_empty_figure("What Distinguishes High Risk Students")

    axes = []
    labels = []
    for col in ["Prior Knowledge", "Course Relevance", "Teaching Support", "Company Support", "Family Support", SELF_STUDY_COL]:
        if col in df.columns:
            axes.append(col)
            labels.append(PERCEPTION_LABEL_MAP.get(col, col))

    if not axes:
        return _dash_empty_figure("What Distinguishes High Risk Students")

    fig = go.Figure()
    for risk in ["Low", "Medium", "High"]:
        subset = df[df[RISK_DYNAMIC_COL] == risk]
        vals = subset[axes].apply(pd.to_numeric, errors="coerce")
        means = vals.mean(axis=0, skipna=True)
        means = _normalise_0_1(means)
        fig.add_trace(
            go.Scatterpolar(
                r=means.values,
                theta=labels,
                fill="toself",
                name=risk,
                line_color=RISK_COLOR_MAP.get(risk),
                opacity=0.6,
                hovertemplate="%{theta}: %{r:.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 1], tickfont=dict(color=DASH1_TEXT))),
        showlegend=True,
    )
    return _apply_dash1_layout(
        fig,
        "What Distinguishes High Risk Students (Perception + Support + Behaviour)",
        height=420,
        subtitle="Axes are normalised for comparability; gaps highlight intervention levers.",
    )


def make_cohort_trend(df: pd.DataFrame, mode: str = "course") -> go.Figure:
    if df.empty:
        return _dash_empty_figure("Risk Rate Over Period")

    period_col = PERIOD_UNIFIED_COL if PERIOD_UNIFIED_COL in df.columns else PERIOD_COL
    if period_col not in df.columns:
        return _dash_empty_figure("Risk Rate Over Period")

    group_col = COURSE_LEVEL_COL if mode == "course" else FUNDING_GROUP_COL
    if group_col not in df.columns:
        return _dash_empty_figure("Risk Rate Over Period")

    grouped = (
        df.groupby([period_col, group_col], observed=False)[RISK_DYNAMIC_COL]
        .apply(lambda s: (s == "High").mean() * 100.0)
        .reset_index(name="high_risk_rate")
    )

    period_order = _sort_periods(grouped[period_col].astype(str).unique().tolist()) if "_sort_periods" in globals() else sorted(grouped[period_col].astype(str).unique().tolist())
    grouped[period_col] = pd.Categorical(grouped[period_col].astype(str), categories=period_order, ordered=True)
    grouped = grouped.sort_values(period_col)

    fig = px.line(
        grouped,
        x=period_col,
        y="high_risk_rate",
        color=group_col,
        markers=True,
    )
    fig.update_traces(hovertemplate="Period=%{x}<br>High risk=%{y:.1f}%<extra></extra>")
    fig.update_yaxes(title="High-risk rate (%)")
    fig.update_xaxes(title="Period")

    return _apply_dash1_layout(
        fig,
        "Risk Rate Over Period",
        height=420,
        subtitle="Track risk trends over time by course level or funding group.",
    )

# =========================
# 4.5) Advanced Feature Engineering (Derived Metrics)
# =========================


def add_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Create derived metrics for risk, momentum, and course level."""
    out = df.copy()

    def _normalize(series: pd.Series) -> pd.Series:
        vals = pd.to_numeric(series, errors="coerce")
        if vals.notna().sum() == 0:
            return pd.Series(np.nan, index=series.index)
        min_val = float(vals.min())
        max_val = float(vals.max())
        if min_val == max_val:
            return pd.Series(0.5, index=series.index)
        return (vals - min_val) / (max_val - min_val)

    def _weighted_index(weighted_series):
        frames = []
        weights = []
        for series, weight in weighted_series:
            if series is None:
                continue
            frames.append(series)
            weights.append(weight)
        if not frames:
            return pd.Series(np.nan, index=out.index)
        data = pd.concat(frames, axis=1).apply(pd.to_numeric, errors="coerce")
        w = np.array(weights, dtype=float)
        valid = data.notna().values
        weighted = data.fillna(0).to_numpy(dtype=float) * w
        weight_sum = (valid * w).sum(axis=1)
        numer = weighted.sum(axis=1)
        score = np.divide(numer, weight_sum, out=np.full_like(weight_sum, np.nan, dtype=float), where=weight_sum != 0)
        score = pd.Series(score, index=data.index)
        return score

    course_source = None
    if COURSE_NAME_COL in out.columns:
        course_source = out[COURSE_NAME_COL].astype("string")
    elif DERIVED_COURSE_COL in out.columns:
        course_source = out[DERIVED_COURSE_COL].astype("string")

    if course_source is not None:
        lower = course_source.str.lower().fillna("")
        out[COURSE_LEVEL_COL] = np.select(
            [
                lower.str.startswith("specialist diploma"),
                lower.str.startswith("diploma"),
                lower.str.startswith("certificate"),
            ],
            ["Specialist Diploma", "Diploma", "Certificate"],
            default="Other",
        )

    likert_cols = [c for c in LIKERT_COLS if c in out.columns]
    if likert_cols:
        out[PERCEPTION_SCORE_COL] = out[likert_cols].mean(axis=1, skipna=True)

    if ATTEND_COL in out.columns:
        out["Attendance (Norm)"] = _normalize(out[ATTEND_COL])

    if GPA_COL in out.columns:
        out["GPA (Norm)"] = _normalize(out[GPA_COL])

    if GPA_COL in out.columns and ATTEND_COL in out.columns:
        gpa_vals = pd.to_numeric(out[GPA_COL], errors="coerce")
        att_vals = pd.to_numeric(out[ATTEND_COL], errors="coerce")
        mask = gpa_vals.notna() & att_vals.notna()
        if mask.sum() >= 2 and att_vals[mask].nunique() > 1:
            slope, intercept = np.polyfit(att_vals[mask], gpa_vals[mask], 1)
            out[EXPECTED_GPA_COL] = (slope * att_vals) + intercept
            out[MOMENTUM_GAP_COL] = gpa_vals - out[EXPECTED_GPA_COL]
        else:
            out[MOMENTUM_GAP_COL] = np.nan

    if "GPA (Norm)" in out.columns or "Attendance (Norm)" in out.columns:
        risk_score = _weighted_index(
            [
                ((1 - out["GPA (Norm)"]) if "GPA (Norm)" in out.columns else None, 0.65),
                ((1 - out["Attendance (Norm)"]) if "Attendance (Norm)" in out.columns else None, 0.35),
            ]
        )
        if risk_score.notna().any():
            risk_score = risk_score.clip(lower=0, upper=1)
            out[RISK_SCORE_COL] = risk_score
            out[RISK_TIER_COL] = pd.cut(
                risk_score,
                bins=[-np.inf, 0.5, 0.7, np.inf],
                labels=["Low", "Medium", "High"],
            )
            out[RISK_FLAG_COL] = (out[RISK_TIER_COL] == "High").astype("Int64")


    perception_norm = _normalize(out[PERCEPTION_SCORE_COL]) if PERCEPTION_SCORE_COL in out.columns else None
    study_norm = _normalize(out[SELF_STUDY_COL]) if SELF_STUDY_COL in out.columns else None
    attend_norm = out["Attendance (Norm)"] if "Attendance (Norm)" in out.columns else (
        _normalize(out[ATTEND_COL]) if ATTEND_COL in out.columns else None
    )

    engagement_score = _weighted_index(
        [
            (perception_norm, 0.45),
            (study_norm, 0.30),
            (attend_norm, 0.25),
        ]
    )
    if engagement_score.notna().any():
        out[ENGAGEMENT_COL] = engagement_score.clip(lower=0, upper=1)

    gpa_norm = out["GPA (Norm)"] if "GPA (Norm)" in out.columns else None
    performance_index = _weighted_index(
        [
            (gpa_norm, 0.70),
            (attend_norm, 0.30),
        ]
    )
    if performance_index.notna().any():
        out[PERFORMANCE_INDEX_COL] = performance_index.clip(lower=0, upper=1)

    return out


# =========================
# 2) Build Analytics DF (for plotting)
# =========================
analytics_df = build_analytics_df(
    df_student_profile=df_student_profile,
    df_student_result=df_student_result,
    df_student_survey=df_student_survey,
    df_course_codes=df_course_codes,
)


analytics_df = add_feature_engineering(analytics_df)

# =========================
# 5) Plotly Dash App (external)
# =========================


dash_df = analytics_df.copy()

course_col = COURSE_DISPLAY_COL if COURSE_DISPLAY_COL in dash_df.columns else DERIVED_COURSE_COL

period_options = []
if PERIOD_COL in dash_df.columns:
    period_options = sorted(dash_df[PERIOD_COL].dropna().astype(str).unique().tolist())

course_level_options = []
if COURSE_LEVEL_COL in dash_df.columns:
    raw_levels = dash_df[COURSE_LEVEL_COL].dropna().astype(str).unique().tolist()
    preferred = ["Certificate", "Diploma", "Specialist Diploma", "Other"]
    course_level_options = [lvl for lvl in preferred if lvl in raw_levels]
    course_level_options += [lvl for lvl in raw_levels if lvl not in course_level_options]

highest_edu_options = []
if HIGHEST_EDU_COL in dash_df.columns:
    edu_series = dash_df[HIGHEST_EDU_COL].dropna().astype("string").str.strip()
    edu_series = edu_series[edu_series.str.len() > 0]
    highest_edu_options = edu_series.unique().tolist()

funding_options = []
if COURSE_FUNDING_COL in dash_df.columns:
    funding_options = dash_df[COURSE_FUNDING_COL].dropna().astype(str).unique().tolist()

course_options = []
if course_col in dash_df.columns:
    course_options = dash_df[course_col].dropna().astype(str).unique().tolist()

likert_dim_options = []
if "LIKERT_COLS" in globals():
    likert_dim_options = [col for col in LIKERT_COLS if col in dash_df.columns]
else:
    likert_dim_options = [
        col for col in ["Prior Knowledge", "Course Relevance", "Teaching Support", "Company Support", "Family Support"]
        if col in dash_df.columns
    ]
likert_mode_options = [
    {"label": "Percent", "value": "Percent"},
    {"label": "Count", "value": "Count"},
]
self_study_col = SELF_STUDY_COL if "SELF_STUDY_COL" in globals() and SELF_STUDY_COL in dash_df.columns else None
support_dim_cols = [col for col in ["Teaching Support", "Company Support", "Family Support"] if col in dash_df.columns]

d2_study_toggle_options = [{"label": "Study Hours", "value": "study"}]
if support_dim_cols:
    d2_study_toggle_options.append({"label": "Support Index", "value": "support"})

d2_reg_x_options = []
if support_dim_cols:
    d2_reg_x_options.append({"label": "Support Index", "value": "_support_index"})
for col in likert_dim_options:
    d2_reg_x_options.append({"label": col, "value": col})
if self_study_col:
    d2_reg_x_options.append({"label": "Self-Study Hours", "value": self_study_col})

d2_reg_y_options = []
if GPA_COL in dash_df.columns:
    d2_reg_y_options.append({"label": "GPA", "value": GPA_COL})
if ATTEND_COL in dash_df.columns:
    d2_reg_y_options.append({"label": "Attendance", "value": ATTEND_COL})

d2_radar_toggle_options = [
    {"label": "Without Self-Study", "value": "without"},
    {"label": "With Self-Study", "value": "with"},
]

d2_gap_topn_max = max(1, len(likert_dim_options)) if likert_dim_options else 5
d2_gap_topn_default = min(3, d2_gap_topn_max)
d2_gap_measure_options = [
    {"label": "Mean", "value": "mean"},
    {"label": "Median", "value": "median"},
    {"label": "P10", "value": "p10"},
    {"label": "P90", "value": "p90"},
]
d2_gap_risk_options = [
    {"label": "High Risk", "value": "High"},
    {"label": "Medium Risk", "value": "Medium"},
    {"label": "Low Risk", "value": "Low"},
]





gpa_min = float(pd.to_numeric(dash_df[GPA_COL], errors="coerce").min()) if GPA_COL in dash_df.columns else 0.0
gpa_max = float(pd.to_numeric(dash_df[GPA_COL], errors="coerce").max()) if GPA_COL in dash_df.columns else 4.0
if np.isnan(gpa_min) or np.isnan(gpa_max):
    gpa_min, gpa_max = 0.0, 4.0
gpa_min = max(0.0, min(4.0, gpa_min))
gpa_max = max(0.0, min(4.0, gpa_max))
if gpa_min > gpa_max:
    gpa_min, gpa_max = 0.0, 4.0
gpa_min = round(gpa_min, 1)
gpa_max = round(gpa_max, 1)

att_min = float(pd.to_numeric(dash_df[ATTEND_COL], errors="coerce").min()) if ATTEND_COL in dash_df.columns else 0.0
att_max = float(pd.to_numeric(dash_df[ATTEND_COL], errors="coerce").max()) if ATTEND_COL in dash_df.columns else 100.0
if np.isnan(att_min) or np.isnan(att_max):
    att_min, att_max = 0.0, 100.0
att_min = max(0.0, min(100.0, att_min))
att_max = max(0.0, min(100.0, att_max))
if att_min > att_max:
    att_min, att_max = 0.0, 100.0
att_min = int(round(att_min))
att_max = int(round(att_max))


gpa_threshold_default = float(dash_df[GPA_COL].median()) if GPA_COL in dash_df.columns else 3.0
att_threshold_default = float(dash_df[ATTEND_COL].median()) if ATTEND_COL in dash_df.columns else 80.0
gpa_threshold_default = max(0.0, min(4.0, gpa_threshold_default))
att_threshold_default = max(0.0, min(100.0, att_threshold_default))
gpa_threshold_default = round(gpa_threshold_default, 1)
att_threshold_default = int(round(att_threshold_default))

logo_src = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQzDwzohm4UyVe35jdGwKSDC9GhOuI162xLEQ&s"

dashboard_1_config = {"displayModeBar": False}
dashboard_2_config = {"displayModeBar": False}

def _apply_filters(df, period, course_level, course_name, funding, qualification, gpa_range, att_range):
    out = df.copy()

    def _norm_list(values):
        if values is None:
            return []
        if isinstance(values, (list, tuple, set)):
            return [str(v) for v in values if v is not None and str(v).strip() != ""]
        return [str(values)]

    def _same_selection(selected, options):
        if not options:
            return True
        return set(selected) == set([str(o) for o in options])

    periods = _norm_list(period)
    levels = _norm_list(course_level)
    courses = _norm_list(course_name)
    funding_vals = _norm_list(funding)
    qualifications = _norm_list(qualification)

    if periods and "All" not in periods and PERIOD_COL in out.columns and not _same_selection(periods, period_options):
        out = out[out[PERIOD_COL].astype(str).isin(periods)]
    if levels and "All" not in levels and COURSE_LEVEL_COL in out.columns and not _same_selection(levels, course_level_options):
        out = out[out[COURSE_LEVEL_COL].astype(str).isin(levels)]
    if courses and "All" not in courses and course_col in out.columns and not _same_selection(courses, course_options):
        out = out[out[course_col].astype(str).isin(courses)]
    if funding_vals and "All" not in funding_vals and COURSE_FUNDING_COL in out.columns and not _same_selection(funding_vals, funding_options):
        out = out[out[COURSE_FUNDING_COL].astype(str).isin(funding_vals)]
    if qualifications and "All" not in qualifications and HIGHEST_EDU_COL in out.columns and not _same_selection(qualifications, highest_edu_options):
        out = out[out[HIGHEST_EDU_COL].astype(str).isin(qualifications)]
    if GPA_COL in out.columns and gpa_range is not None:
        if isinstance(gpa_range, (list, tuple)) and len(gpa_range) == 2:
            lo, hi = float(gpa_range[0]), float(gpa_range[1])
            full_range = abs(lo - float(gpa_min)) < 1e-6 and abs(hi - float(gpa_max)) < 1e-6
            if not full_range:
                out = out[pd.to_numeric(out[GPA_COL], errors="coerce").between(lo, hi, inclusive="both")]
    if ATTEND_COL in out.columns and att_range is not None:
        if isinstance(att_range, (list, tuple)) and len(att_range) == 2:
            lo, hi = float(att_range[0]), float(att_range[1])
            full_range = abs(lo - float(att_min)) < 1e-6 and abs(hi - float(att_max)) < 1e-6
            if not full_range:
                out = out[pd.to_numeric(out[ATTEND_COL], errors="coerce").between(lo, hi, inclusive="both")]
    return out


def _safe_mean(series):
    if series is None:
        return float("nan")
    vals = pd.to_numeric(series, errors="coerce")
    return float(vals.mean()) if vals.notna().any() else float("nan")


def _stat_value(series, stat):
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if vals.empty:
        return float("nan")
    stat = (stat or "mean").lower()
    if stat == "median":
        return float(vals.median())
    if stat == "p10":
        return float(vals.quantile(0.10))
    if stat == "p90":
        return float(vals.quantile(0.90))
    return float(vals.mean())


def _compute_kpis(
    df,
    gpa_thr,
    att_thr,
    use_latest_gpa=False,
    gpa_stat="mean",
    att_stat="mean",
    risk_tier="High",
):
    total = int(df[STUDENT_ID_COL].nunique()) if STUDENT_ID_COL in df.columns else int(len(df))

    gpa_source = df
    if use_latest_gpa and "_latest_semester_snapshot" in globals():
        try:
            gpa_source = _latest_semester_snapshot(df)
        except Exception:
            gpa_source = df
    avg_gpa = _stat_value(gpa_source[GPA_COL], gpa_stat) if GPA_COL in gpa_source.columns else float("nan")
    avg_att = _stat_value(df[ATTEND_COL], att_stat) if ATTEND_COL in df.columns else float("nan")

    risk_count = float("nan")
    risk_percent = float("nan")
    if GPA_COL in df.columns and ATTEND_COL in df.columns:
        risk_df = _apply_dynamic_risk(df, gpa_thr, att_thr)
        if RISK_TIER_COL in risk_df.columns:
            tiers = risk_df[RISK_TIER_COL].astype("string").str.strip().str.title()
            target = str(risk_tier or "High").strip().title()
            mask = tiers.eq(target)
            if STUDENT_ID_COL in risk_df.columns:
                total_students = int(risk_df[STUDENT_ID_COL].nunique())
                risk_count = int(risk_df.loc[mask, STUDENT_ID_COL].nunique())
            else:
                total_students = int(len(risk_df))
                risk_count = int(mask.sum())
            if total_students > 0:
                risk_percent = float(risk_count / total_students * 100.0)

    return {
        "total": total,
        "avg_gpa": avg_gpa,
        "avg_att": avg_att,
        "risk_count": risk_count,
        "risk_percent": risk_percent,
    }


def _format_int(value):
    if value is None or np.isnan(value):
        return "N.A."
    return f"{int(round(value)):,}"


def _format_number(value, decimals=2):
    if value is None or np.isnan(value):
        return "N.A."
    return f"{value:.{decimals}f}"


def _format_percent(value, decimals=1):
    if value is None or np.isnan(value):
        return "N.A."
    return f"{value:.{decimals}f}%"


def _delta_display(current, baseline, higher_is_good, decimals=2, unit=""):
    if current is None or baseline is None:
        return ("N.A.", "kpi-delta kpi-neutral")
    if np.isnan(current) or np.isnan(baseline):
        return ("N.A.", "kpi-delta kpi-neutral")

    diff = current - baseline
    if abs(diff) < 1e-6:
        return (f"- 0.00{unit} vs overall", "kpi-delta kpi-neutral")

    arrow = "\u25B2" if diff > 0 else "\u25BC"
    good = diff > 0 if higher_is_good else diff < 0
    cls = "kpi-delta kpi-good" if good else "kpi-delta kpi-bad"
    sign = "+" if diff > 0 else ""
    return (f"{arrow} {sign}{diff:.{decimals}f}{unit} vs overall", cls)


def _delta_display_count(current, baseline, higher_is_good=None):
    if current is None or baseline is None:
        return ("N.A.", "kpi-delta kpi-neutral")
    if np.isnan(current) or np.isnan(baseline):
        return ("N.A.", "kpi-delta kpi-neutral")

    diff = int(round(current - baseline))
    if diff == 0:
        return ("- 0.00 vs overall", "kpi-delta kpi-neutral")

    arrow = "\u25B2" if diff > 0 else "\u25BC"
    sign = "+" if diff > 0 else ""
    if higher_is_good is None:
        cls = "kpi-delta kpi-neutral"
    else:
        good = diff > 0 if higher_is_good else diff < 0
        cls = "kpi-delta kpi-good" if good else "kpi-delta kpi-bad"
    return (f"{arrow} {sign}{diff} vs overall", cls)


def _build_kpi_display(current, baseline, risk_tier="High", risk_mode="percent"):
    total_value = _format_int(current.get("total"))
    total_delta, total_class = _delta_display_count(current.get("total"), baseline.get("total"))

    gpa_value = _format_number(current.get("avg_gpa"), 2)
    gpa_delta, gpa_class = _delta_display(
        current.get("avg_gpa"),
        baseline.get("avg_gpa"),
        higher_is_good=True,
        decimals=2,
    )

    att_value = _format_percent(current.get("avg_att"), 1)
    att_delta, att_class = _delta_display(
        current.get("avg_att"),
        baseline.get("avg_att"),
        higher_is_good=True,
        decimals=1,
        unit="%",
    )

    risk_mode = (risk_mode or "percent").lower()
    risk_tier = str(risk_tier or "High").strip().title()
    higher_is_good_risk = risk_tier.lower() == "low"
    if risk_mode == "count":
        risk_value = _format_int(current.get("risk_count"))
        risk_delta, risk_class = _delta_display_count(
            current.get("risk_count"),
            baseline.get("risk_count"),
            higher_is_good=higher_is_good_risk,
        )
    else:
        risk_value = _format_percent(current.get("risk_percent"), 1)
        risk_delta, risk_class = _delta_display(
            current.get("risk_percent"),
            baseline.get("risk_percent"),
            higher_is_good=higher_is_good_risk,
            decimals=1,
            unit="%",
        )

    return {
        "total_value": total_value,
        "total_delta": total_delta,
        "total_class": total_class,
        "gpa_value": gpa_value,
        "gpa_delta": gpa_delta,
        "gpa_class": gpa_class,
        "att_value": att_value,
        "att_delta": att_delta,
        "att_class": att_class,
        "risk_value": risk_value,
        "risk_delta": risk_delta,
        "risk_class": risk_class,
    }


def _resolve_column(df: pd.DataFrame, candidates):
    if df is None or not isinstance(df, pd.DataFrame):
        return None
    lower_map = {str(col).lower(): col for col in df.columns}
    for cand in candidates:
        if cand in df.columns:
            return cand
        key = str(cand).lower()
        if key in lower_map:
            return lower_map[key]
    return None


def _flag_series(series: pd.Series) -> pd.Series:
    if series is None:
        return pd.Series(False)
    raw = series.copy()
    if raw.dtype == "boolean":
        return raw.fillna(False)
    if raw.dtype.kind in "if":
        return raw.fillna(0).astype(int).eq(1)
    text = raw.astype("string").str.strip().str.lower()
    return text.isin(["1", "yes", "y", "true", "t"])


def _attach_residency(df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[str]]:
    out = df.copy()
    res_col = _resolve_column(out, ["Residency", "Residence Status", "Nationality", "Citizenship"])
    if res_col:
        out["_residency"] = out[res_col].astype("string").str.strip()
        out["_residency"] = out["_residency"].replace({"": "Unknown", "N.A.": "Unknown"}).fillna("Unknown")
        return out, "_residency"

    citizen_col = _resolve_column(out, ["SG CITIZEN", "SG Citizen", "Citizen"])
    pr_col = _resolve_column(out, ["SG PR", "Permanent Resident"])
    foreign_col = _resolve_column(out, ["FOREIGNER", "Foreigner", "Foreign"])

    if citizen_col or pr_col or foreign_col:
        citizen = _flag_series(out[citizen_col]) if citizen_col else pd.Series(False, index=out.index)
        pr = _flag_series(out[pr_col]) if pr_col else pd.Series(False, index=out.index)
        foreign = _flag_series(out[foreign_col]) if foreign_col else pd.Series(False, index=out.index)
        out["_residency"] = np.select(
            [citizen, pr, foreign],
            ["Citizen", "PR", "Foreigner"],
            default="Other",
        )
        return out, "_residency"

    return out, None


def _attach_mode(df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[str]]:
    out = df.copy()
    mode_col = _resolve_column(
        out,
        ["FULL-TIME OR PART-TIME", "Full-Time Or Part-Time", "Full/Part-time", "Study Mode"],
    )
    if not mode_col:
        return out, None
    mode = out[mode_col].astype("string").str.strip().str.lower()
    mode = mode.replace({"full time": "Full-time", "full-time": "Full-time", "part time": "Part-time", "part-time": "Part-time"})
    out["_study_mode"] = mode.replace({"": "Unknown", "n.a.": "Unknown"}).fillna("Unknown").str.title()
    return out, "_study_mode"


def _attach_gender(df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[str]]:
    out = df.copy()
    gender_col = _resolve_column(out, ["Gender", "GENDER"])
    if not gender_col:
        return out, None
    out["_gender"] = out[gender_col].astype("string").str.strip().str.title()
    out["_gender"] = out["_gender"].replace({"": "Unknown", "N.A.": "Unknown"}).fillna("Unknown")
    return out, "_gender"


def _attach_age_group(df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[str]]:
    out = df.copy()
    dob_col = _resolve_column(out, ["DOB", "Date of Birth", "Birth Date"])
    if not dob_col:
        return out, None
    dob = pd.to_datetime(out[dob_col], errors="coerce")
    age = (pd.Timestamp.today() - dob).dt.days / 365.25
    out["_age"] = age
    bins = [0, 20, 30, 40, 200]
    labels = ["<20", "20-29", "30-39", "40+"]
    out["_age_group"] = pd.cut(out["_age"], bins=bins, labels=labels, right=False)
    out["_age_group"] = out["_age_group"].astype("string").fillna("Unknown")
    return out, "_age_group"


def _apply_plotly_theme(fig: go.Figure, theme: str = "light") -> go.Figure:
    # Keep chart styling consistent across light/dark mode.
    text = "#3B2E3A"
    grid = "rgba(140, 126, 150, 0.25)"
    legend_bg = "rgba(255, 255, 255, 0.92)"
    legend_border = "rgba(140, 126, 150, 0.25)"
    hover_bg = "#FFF0F6"
    hover_border = "rgba(255, 143, 177, 0.5)"

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Nunito, Segoe UI, Arial, sans-serif", size=12, color=text),
        hoverlabel=dict(
            bgcolor=hover_bg,
            bordercolor=hover_border,
            font=dict(color=text, size=12, family="Nunito, Segoe UI, Arial, sans-serif"),
        ),
        legend=dict(
            bgcolor=legend_bg,
            bordercolor=legend_border,
            borderwidth=1,
            font=dict(color=text, size=10),
            x=0.98,
            y=0.98,
            xanchor="right",
            yanchor="top",
        ),
    )
    fig.update_xaxes(
        gridcolor=grid,
        zeroline=False,
        linecolor="rgba(148,163,184,0.2)",
        tickfont=dict(color=text),
        title_font=dict(color=text),
    )
    fig.update_yaxes(
        gridcolor=grid,
        zeroline=False,
        linecolor="rgba(148,163,184,0.2)",
        tickfont=dict(color=text),
        title_font=dict(color=text),
    )
    return fig




def _survey_columns(df: pd.DataFrame) -> Tuple[List[str], Optional[str], List[str]]:
    default_likert = [
        "Prior Knowledge",
        "Course Relevance",
        "Teaching Support",
        "Company Support",
        "Family Support",
    ]
    likert_cols = globals().get("LIKERT_COLS", default_likert)
    likert_cols = [c for c in likert_cols if c in df.columns]
    self_col = globals().get("SELF_STUDY_COL", "Self-Study Hrs")
    self_col = self_col if self_col in df.columns else None
    support_cols = [c for c in ["Teaching Support", "Company Support", "Family Support"] if c in df.columns]
    return likert_cols, self_col, support_cols


def _compute_support_index(df: pd.DataFrame, support_cols: List[str]) -> pd.Series:
    if not support_cols:
        return pd.Series(np.nan, index=df.index)
    support_df = df[support_cols].apply(pd.to_numeric, errors="coerce")
    return support_df.mean(axis=1)


def _ensure_risk_tier(df: pd.DataFrame, gpa_thr: float, att_thr: float) -> pd.DataFrame:
    if GPA_COL in df.columns and ATTEND_COL in df.columns:
        out = _apply_dynamic_risk(df, gpa_thr, att_thr)
    else:
        out = df.copy()
        out[RISK_TIER_COL] = "Unknown"
    out[RISK_TIER_COL] = out[RISK_TIER_COL].astype("string").str.strip().str.title().fillna("Unknown")
    return out


def _compute_survey_kpis(df: pd.DataFrame, gpa_thr: float, att_thr: float) -> Dict[str, str]:
    likert_cols, self_col, support_cols = _survey_columns(df)
    risk_df = _ensure_risk_tier(df, gpa_thr, att_thr)
    support_index = _compute_support_index(risk_df, support_cols)
    risk_df = risk_df.copy()
    risk_df["_support_index"] = support_index
    high_df = risk_df[risk_df[RISK_TIER_COL] == "High"]

    avg_support_overall = float(pd.to_numeric(risk_df["_support_index"], errors="coerce").mean()) if support_cols else float("nan")
    avg_support_high = float(pd.to_numeric(high_df["_support_index"], errors="coerce").mean()) if support_cols else float("nan")

    avg_study_overall = float(pd.to_numeric(risk_df[self_col], errors="coerce").mean()) if self_col else float("nan")
    avg_study_high = float(pd.to_numeric(high_df[self_col], errors="coerce").mean()) if self_col else float("nan")

    lowest_dim = "N.A."
    lowest_value = float("nan")
    if likert_cols:
        means = {}
        for col in likert_cols:
            means[col] = float(pd.to_numeric(high_df[col], errors="coerce").mean())
        if means:
            lowest_dim = min(means, key=means.get)
            lowest_value = means[lowest_dim]

    return {
        "support_overall": _format_number(avg_support_overall, 2),
        "support_high": _format_number(avg_support_high, 2),
        "support_delta": _delta_display(avg_support_high, avg_support_overall, higher_is_good=True, decimals=2),
        "study_overall": _format_number(avg_study_overall, 2),
        "study_high": _format_number(avg_study_high, 2),
        "study_delta": _delta_display(avg_study_high, avg_study_overall, higher_is_good=True, decimals=2),
        "lowest_dim": lowest_dim if lowest_dim else "N.A.",
        "lowest_value": _format_number(lowest_value, 2),
    }


def make_dashboard_2_figures(
    df: pd.DataFrame,
    gpa_threshold: Optional[float] = None,
    att_threshold: Optional[float] = None,
    theme: str = "light",
    likert_dim: Optional[str] = None,
    likert_mode: str = "Percent",
    reg_x: Optional[str] = None,
    reg_y: Optional[str] = None,
    study_toggle: str = "study",
    radar_toggle: str = "without",
    gap_risk: Optional[str] = None,
    gap_measure: Optional[str] = None,
    gap_topn: Optional[int] = None,
) -> Dict[str, go.Figure]:
    figs: Dict[str, go.Figure] = {}

    def _safe_float(value, fallback):
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    gpa_thr = _safe_float(gpa_threshold, gpa_threshold_default)
    att_thr = _safe_float(att_threshold, att_threshold_default)

    risk_color_map = {"High": "#EF4444", "Medium": "#FBBF24", "Low": "#22C55E", "Unknown": "#A0AEC0"}
    likert_cols, self_col, support_cols = _survey_columns(df)
    risk_df = _ensure_risk_tier(df, gpa_thr, att_thr)
    risk_levels = ["Low", "Medium", "High"]
    risk_df[RISK_TIER_COL] = risk_df[RISK_TIER_COL].astype("string").str.title()

    # D2-1 Heatmap: Risk x Survey Dimension (z-score normalized by column)
    heat_fig = go.Figure()
    if likert_cols:
        dims = likert_cols + ([self_col] if self_col else [])

        # Convert selected dimensions to numeric and z-score each column
        dim_numeric = risk_df[dims].apply(pd.to_numeric, errors="coerce")
        dim_mean = dim_numeric.mean(skipna=True)
        dim_std = dim_numeric.std(skipna=True).replace(0, np.nan)
        dim_z = (dim_numeric - dim_mean) / dim_std

        def _stat_matrix(stat: str):
            z = []
            n_matrix = []
            raw_matrix = []
            for r in risk_levels:
                mask = risk_df[RISK_TIER_COL] == r
                row = []
                n_row = []
                raw_row = []
                for col in dims:
                    vals_z = pd.to_numeric(dim_z.loc[mask, col], errors="coerce").dropna()
                    vals_raw = pd.to_numeric(dim_numeric.loc[mask, col], errors="coerce").dropna()
                    if vals_z.empty:
                        row.append(np.nan)
                        n_row.append(0)
                        raw_row.append(np.nan)
                    else:
                        row.append(float(vals_z.median() if stat == "median" else vals_z.mean()))
                        n_row.append(int(vals_z.shape[0]))
                        raw_row.append(float(vals_raw.mean()) if not vals_raw.empty else np.nan)
                z.append(row)
                n_matrix.append(n_row)
                raw_matrix.append(raw_row)
            custom = np.dstack([np.array(n_matrix), np.array(raw_matrix)])
            return z, custom

        z_mean, custom_mean = _stat_matrix("mean")
        z_med, custom_med = _stat_matrix("median")

        heat_fig.add_trace(
            go.Heatmap(
                z=z_mean,
                x=dims,
                y=risk_levels,
                colorscale="RdBu",
                zmid=0,
                colorbar=dict(title="Z-score"),
                customdata=custom_mean,
                hovertemplate="Z=%{z:.2f}<br>n=%{customdata[0]}<br>Raw mean=%{customdata[1]:.2f}<extra></extra>",
            )
        )
        heat_fig.update_layout(
            title=dict(text="B1. Survey Drivers: Risk vs Dimension (Z-score Mean)", x=0.01),
            margin=dict(l=60, r=20, t=110, b=60),
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    x=0.98,
                    y=1.14,
                    xanchor="right",
                    yanchor="top",
                    bgcolor="rgba(255,255,255,0.95)",
                    bordercolor="rgba(140,126,150,0.25)",
                    buttons=[
                        dict(
                            label="Mean",
                            method="update",
                            args=[
                                {"z": [z_mean], "customdata": [custom_mean]},
                                {"title": {"text": "B1. Survey Drivers: Risk vs Dimension (Z-score Mean)"}},
                            ],
                        ),
                        dict(
                            label="Median",
                            method="update",
                            args=[
                                {"z": [z_med], "customdata": [custom_med]},
                                {"title": {"text": "B1. Survey Drivers: Risk vs Dimension (Z-score Median)"}},
                            ],
                        ),
                    ],
                )
            ],
        )
        figs["d2_heatmap"] = _apply_plotly_theme(heat_fig, theme)
    else:
        figs["d2_heatmap"] = _apply_plotly_theme(go.Figure(), theme)
        figs["d2_heatmap"].update_layout(title=dict(text="B1. Survey Drivers: Risk vs Dimension (Unavailable)", x=0.01))

    # D2-2 Likert Distribution (stacked)
    likert_fig = go.Figure()
    if likert_cols:
        ratings = [1, 2, 3, 4, 5]
        selected_dim = likert_dim if likert_dim in likert_cols else likert_cols[0]
        mode = (likert_mode or "Percent").strip().title()
        if mode not in ["Percent", "Count"]:
            mode = "Percent"

        values_by_rating = []
        for rating in ratings:
            values = []
            for r in risk_levels:
                sub = risk_df[risk_df[RISK_TIER_COL] == r]
                vals = pd.to_numeric(sub[selected_dim], errors="coerce")
                count = int((vals == rating).sum())
                if mode == "Percent":
                    total = int(vals.dropna().shape[0])
                    value = (count / total * 100.0) if total else 0.0
                else:
                    value = count
                values.append(value)
            values_by_rating.append(values)

        colors = ["#FFE2EA", "#FFB3C7", "#FFD166", "#BDE0FE", "#7BDFF2"]
        for idx, rating in enumerate(ratings):
            likert_fig.add_trace(
                go.Bar(
                    x=risk_levels,
                    y=values_by_rating[idx],
                    name=f"{rating}",
                    marker_color=colors[idx],
                )
            )
        likert_fig.update_layout(
            barmode="stack",
            title=dict(text=f"B3. Likert Profile: {selected_dim} ({mode})", x=0.01),
            margin=dict(l=50, r=20, t=110, b=60),
        )
        figs["d2_likert"] = _apply_plotly_theme(likert_fig, theme)
    else:
        figs["d2_likert"] = _apply_plotly_theme(go.Figure(), theme)
        figs["d2_likert"].update_layout(title=dict(text="B3. Likert Profile (Unavailable)", x=0.01))

    # D2-3 Self-study distribution
    study_fig = go.Figure()
    study_mode = (study_toggle or "study").lower()
    use_support = study_mode == "support" and bool(support_cols)
    if self_col or use_support:
        plot_label = "Support Index by Risk" if use_support else "Study Hours by Risk"
        y_axis_label = "Support Index" if use_support else "Study Hours"
        for risk in risk_levels:
            sub = risk_df[risk_df[RISK_TIER_COL] == risk]
            if use_support:
                values = _compute_support_index(sub, support_cols)
            else:
                values = pd.to_numeric(sub[self_col], errors="coerce")
            study_fig.add_trace(
                go.Violin(
                    x=[risk] * len(sub),
                    y=values,
                    name=risk,
                    legendgroup=risk,
                    scalegroup=risk,
                    box_visible=True,
                    meanline_visible=True,
                    points=False,
                    line_color=risk_color_map.get(risk, "#A0AEC0"),
                )
            )
        study_fig.update_layout(
            title=dict(text=f"B4. {plot_label}", x=0.01),
            margin=dict(l=50, r=20, t=110, b=60),
            yaxis_title=y_axis_label,
        )
        figs["d2_self_study"] = _apply_plotly_theme(study_fig, theme)
    else:
        figs["d2_self_study"] = _apply_plotly_theme(go.Figure(), theme)
        figs["d2_self_study"].update_layout(title=dict(text="B4. Self-Study Hours by Risk (Unavailable)", x=0.01))

    # D2-4 Regression scatter: Outcome vs Survey Dimension
    bubble_fig = go.Figure()
    x_candidates = [c for c in likert_cols]
    if support_cols:
        x_candidates = ["_support_index"] + x_candidates
    if self_col:
        x_candidates = x_candidates + [self_col]
    x_choice = reg_x if reg_x in x_candidates else (x_candidates[0] if x_candidates else None)
    y_candidates = [col for col in [GPA_COL, ATTEND_COL] if col in risk_df.columns]
    y_choice = reg_y if reg_y in y_candidates else (y_candidates[0] if y_candidates else None)

    if x_choice and y_choice:
        reg_df = risk_df.copy()
        if x_choice == "_support_index":
            reg_df["_x"] = _compute_support_index(reg_df, support_cols)
            x_label = "Support Index"
        else:
            reg_df["_x"] = pd.to_numeric(reg_df[x_choice], errors="coerce")
            x_label = x_choice
        reg_df["_y"] = pd.to_numeric(reg_df[y_choice], errors="coerce")
        reg_df = reg_df[reg_df["_x"].notna() & reg_df["_y"].notna()]

        for risk in risk_levels:
            sub = reg_df[reg_df[RISK_TIER_COL] == risk]
            bubble_fig.add_trace(
                go.Scatter(
                    x=sub["_x"],
                    y=sub["_y"],
                    mode="markers",
                    name=risk,
                    marker=dict(
                        size=9,
                        color=risk_color_map.get(risk, "#A0AEC0"),
                        opacity=0.7,
                    ),
                    hovertemplate=f"{x_label}=%{{x:.2f}}<br>{y_choice}=%{{y:.2f}}<extra></extra>",
                )
            )

        if len(reg_df) > 1:
            slope, intercept = np.polyfit(reg_df["_x"], reg_df["_y"], 1)
            corr = float(np.corrcoef(reg_df["_x"], reg_df["_y"])[0, 1])
            x_line = np.linspace(reg_df["_x"].min(), reg_df["_x"].max(), 100)
            y_line = slope * x_line + intercept
            bubble_fig.add_trace(
                go.Scatter(
                    x=x_line,
                    y=y_line,
                    mode="lines",
                    name=f"Fit (r={corr:.2f})",
                    line=dict(color="#7BDFF2", width=2),
                    hovertemplate=f"y={slope:.3f}x+{intercept:.3f}<extra></extra>",
                )
            )

        bubble_fig.update_layout(
            title=dict(text=f"B2. Regression: {y_choice} vs {x_label}", x=0.01),
            margin=dict(l=50, r=20, t=110, b=60),
            xaxis_title=x_label,
            yaxis_title=y_choice,
        )
        figs["d2_bubble"] = _apply_plotly_theme(bubble_fig, theme)
    else:
        figs["d2_bubble"] = _apply_plotly_theme(go.Figure(), theme)
        figs["d2_bubble"].update_layout(title=dict(text="B2. Regression (Unavailable)", x=0.01))

    # D2-5 Quadrant scatter
    quad_fig = go.Figure()
    quad_pairs = []
    if "Course Relevance" in risk_df.columns and "Prior Knowledge" in risk_df.columns:
        quad_pairs.append(("Course Relevance", "Prior Knowledge", "Relevance vs Knowledge"))
    if "Teaching Support" in risk_df.columns and "Course Relevance" in risk_df.columns:
        quad_pairs.append(("Teaching Support", "Course Relevance", "Support vs Relevance"))
    if quad_pairs:
        def _build_quad(x_col, y_col):
            df_local = risk_df.copy()
            df_local["_x"] = pd.to_numeric(df_local[x_col], errors="coerce")
            df_local["_y"] = pd.to_numeric(df_local[y_col], errors="coerce")
            df_local["_size"] = pd.to_numeric(df_local[self_col], errors="coerce") if self_col else 5
            df_local = df_local[df_local["_x"].notna() & df_local["_y"].notna()]
            traces = []
            for risk in risk_levels:
                sub = df_local[df_local[RISK_TIER_COL] == risk]
                traces.append(
                    go.Scatter(
                        x=sub["_x"],
                        y=sub["_y"],
                        mode="markers",
                        name=risk,
                        marker=dict(
                            size=sub["_size"].fillna(0) * 2 + 8,
                            color=risk_color_map.get(risk, "#A0AEC0"),
                            opacity=0.75,
                        ),
                    )
                )
            med_x = float(np.nanmedian(df_local["_x"]))
            med_y = float(np.nanmedian(df_local["_y"]))
            x_min, x_max = float(df_local["_x"].min()), float(df_local["_x"].max())
            y_min, y_max = float(df_local["_y"].min()), float(df_local["_y"].max())
            shapes = [
                dict(type="line", x0=med_x, x1=med_x, y0=df_local["_y"].min(), y1=df_local["_y"].max(), line=dict(color="rgba(123,223,242,0.4)", dash="dot")),
                dict(type="line", y0=med_y, y1=med_y, x0=df_local["_x"].min(), x1=df_local["_x"].max(), line=dict(color="rgba(123,223,242,0.4)", dash="dot")),
            ]
            annotations = [
                dict(x=x_min, y=y_min, xanchor="left", yanchor="bottom", text=f"Low {x_col}<br>Low {y_col}", showarrow=False, font=dict(size=10, color="#8C7E96")),
                dict(x=x_max, y=y_min, xanchor="right", yanchor="bottom", text=f"High {x_col}<br>Low {y_col}", showarrow=False, font=dict(size=10, color="#8C7E96")),
                dict(x=x_min, y=y_max, xanchor="left", yanchor="top", text=f"Low {x_col}<br>High {y_col}", showarrow=False, font=dict(size=10, color="#8C7E96")),
                dict(x=x_max, y=y_max, xanchor="right", yanchor="top", text=f"High {x_col}<br>High {y_col}", showarrow=False, font=dict(size=10, color="#8C7E96")),
            ]
            return traces, shapes, annotations

        base_x, base_y, base_label = quad_pairs[0]
        base_traces, base_shapes, base_annotations = _build_quad(base_x, base_y)
        for tr in base_traces:
            quad_fig.add_trace(tr)
        quad_fig.update_layout(
            title=dict(text=f"B5. Quadrants: {base_label}", x=0.01),
            xaxis_title=base_x,
            yaxis_title=base_y,
            margin=dict(l=50, r=20, t=110, b=60),
            shapes=base_shapes,
            annotations=base_annotations,
        )

        buttons = []
        for x_col, y_col, label in quad_pairs:
            traces, shapes, annotations = _build_quad(x_col, y_col)
            buttons.append(
                dict(
                    label=label,
                    method="update",
                    args=[
                        {"x": [t.x for t in traces], "y": [t.y for t in traces]},
                        {
                            "title": {"text": f"Quadrants: {label}"},
                            "xaxis": {"title": x_col},
                            "yaxis": {"title": y_col},
                            "shapes": shapes,
                            "annotations": annotations,
                        },
                    ],
                )
            )
        quad_fig.update_layout(
            updatemenus=[
                dict(
                    type="dropdown",
                    x=0.98,
                    y=1.15,
                    xanchor="right",
                    yanchor="top",
                    bgcolor="#FFFFFF",
                    bordercolor="rgba(140,126,150,0.35)",
                    font=dict(color="#2C1F33"),
                    buttons=buttons,
                )
            ]
        )
        figs["d2_quadrant"] = _apply_plotly_theme(quad_fig, theme)
    else:
        figs["d2_quadrant"] = _apply_plotly_theme(go.Figure(), theme)
        figs["d2_quadrant"].update_layout(title=dict(text="B5. Quadrants (Unavailable)", x=0.01))

    # D2-6 Radar profile by risk
    radar_fig = go.Figure()
    if likert_cols:
        include_self = (radar_toggle or "without").lower() == "with" and self_col
        axes = likert_cols.copy()
        if include_self and self_col:
            axes.append(self_col)

        # Keep all radar dimensions on a comparable 1-5 scale.
        self_scaled_col = "_self_study_1to5"
        if include_self and self_col:
            self_vals = pd.to_numeric(risk_df[self_col], errors="coerce")
            vmin = float(self_vals.min()) if self_vals.notna().any() else float("nan")
            vmax = float(self_vals.max()) if self_vals.notna().any() else float("nan")
            if np.isfinite(vmin) and np.isfinite(vmax) and vmax > vmin:
                risk_df[self_scaled_col] = 1.0 + 4.0 * ((self_vals - vmin) / (vmax - vmin))
            elif self_vals.notna().any():
                risk_df[self_scaled_col] = 3.0
            else:
                risk_df[self_scaled_col] = np.nan

        for risk in risk_levels:
            sub = risk_df[risk_df[RISK_TIER_COL] == risk]
            values = []
            for col in axes:
                source_col = self_scaled_col if (include_self and self_col and col == self_col) else col
                vals = pd.to_numeric(sub[source_col], errors="coerce").dropna()
                values.append(float(vals.mean()) if not vals.empty else np.nan)
            radar_fig.add_trace(
                go.Scatterpolar(
                    r=values,
                    theta=axes,
                    name=risk,
                    line=dict(color=risk_color_map.get(risk, "#A0AEC0")),
                    fill="toself",
                    opacity=0.5,
                )
            )

        title_suffix = "With Self-Study (1-5 scaled)" if include_self else "Without Self-Study"
        radar_fig.update_layout(
            title=dict(text=f"B6. Survey Profile: Average by Risk ({title_suffix})", x=0.01),
            margin=dict(l=40, r=20, t=110, b=40),
            polar=dict(radialaxis=dict(visible=True, range=[1, 5])),
        )
        figs["d2_radar"] = _apply_plotly_theme(radar_fig, theme)
    else:
        figs["d2_radar"] = _apply_plotly_theme(go.Figure(), theme)
        figs["d2_radar"].update_layout(title=dict(text="B6. Survey Profile (Unavailable)", x=0.01))

    # D2-8 Correlation Heatmap (Plotly Express)
    corr_fig = go.Figure()
    if likert_cols and (GPA_COL in risk_df.columns or ATTEND_COL in risk_df.columns):
        corr_targets = [col for col in [GPA_COL, ATTEND_COL, self_col] if col and col in risk_df.columns]
        data_cols = likert_cols + corr_targets
        corr_data = risk_df[data_cols].apply(pd.to_numeric, errors="coerce")

        def _corr_matrix(method: str):
            corr = corr_data.corr(method=method)
            return corr.loc[likert_cols, corr_targets]

        pear_survey = _corr_matrix("pearson")
        spear_survey = _corr_matrix("spearman")

        corr_fig = px.imshow(
            pear_survey.values,
            x=pear_survey.columns.tolist(),
            y=pear_survey.index.tolist(),
            color_continuous_scale="RdBu",
            zmin=-1,
            zmax=1,
            aspect="auto",
        )
        corr_fig.update_traces(hovertemplate="Corr=%{z:.2f}<extra></extra>")
        corr_fig.update_layout(
            title=dict(text="B7. Correlation: Survey vs Outcomes (Pearson)", x=0.01),
            margin=dict(l=60, r=20, t=110, b=60),
            coloraxis_colorbar=dict(title="Corr"),
            updatemenus=[
                dict(
                    type="dropdown",
                    x=0.98,
                    y=1.15,
                    xanchor="right",
                    yanchor="top",
                    bgcolor="rgba(255,255,255,0.95)",
                    bordercolor="rgba(140,126,150,0.25)",
                    buttons=[
                        dict(
                            label="Pearson: Survey vs Outcomes",
                            method="update",
                            args=[
                                {"z": [pear_survey.values], "x": [pear_survey.columns.tolist()], "y": [pear_survey.index.tolist()]},
                                {"title": {"text": "B7. Correlation: Survey vs Outcomes (Pearson)"}},
                            ],
                        ),
                        dict(
                            label="Spearman: Survey vs Outcomes",
                            method="update",
                            args=[
                                {"z": [spear_survey.values], "x": [spear_survey.columns.tolist()], "y": [spear_survey.index.tolist()]},
                                {"title": {"text": "Correlation: Survey vs Outcomes (Spearman)"}},
                            ],
                        ),
                    ],
                )
            ],
        )
        figs["d2_corr"] = _apply_plotly_theme(corr_fig, theme)
    else:
        figs["d2_corr"] = _apply_plotly_theme(go.Figure(), theme)
        figs["d2_corr"].update_layout(title=dict(text="B7. Correlation (Unavailable)", x=0.01))

    # D2-9 High Risk gaps
    gap_fig = go.Figure()
    if likert_cols:
        gap_df = risk_df.copy()
        target_level = (gap_risk or "High").title()
        if target_level not in risk_levels:
            target_level = "High"
        measure = (gap_measure or "mean").lower()

        def _gap_data(df_local, top_n=None):
            target = df_local[df_local[RISK_TIER_COL] == target_level]
            overall = df_local
            dims = []
            values = []
            gaps = []
            for col in likert_cols:
                target_mean = _stat_value(target[col], measure)
                overall_mean = _stat_value(overall[col], measure)
                dims.append(col)
                values.append(target_mean)
                gaps.append(target_mean - overall_mean)
            order = np.argsort(values)
            dims = [dims[i] for i in order]
            values = [values[i] for i in order]
            gaps = [gaps[i] for i in order]
            if top_n:
                dims = dims[:top_n]
                values = values[:top_n]
                gaps = gaps[:top_n]
            return dims, values, gaps

        max_n = len(likert_cols)
        top_n = gap_topn if gap_topn else max_n
        top_n = int(max(1, min(max_n, top_n)))

        base_dims, base_vals, base_gaps = _gap_data(gap_df, top_n=top_n)
        gap_fig.add_trace(
            go.Bar(
                x=base_vals,
                y=base_dims,
                orientation="h",
                marker_color="#FF8FB1",
                customdata=base_gaps,
                hovertemplate=f"%{{y}}<br>{target_level} Risk {measure.title()}=%{{x:.2f}}<br>Gap vs Overall=%{{customdata:.2f}}<extra></extra>",
            )
        )
        gap_fig.update_layout(
            title=dict(text=f"B8. Risk Priorities: Lowest Dimensions ({target_level} Risk)", x=0.01),
            xaxis_title=f"{target_level} Risk {measure.title()} Score",
            margin=dict(l=160, r=20, t=110, b=60),
        )
        figs["d2_gap"] = _apply_plotly_theme(gap_fig, theme)
    else:
        figs["d2_gap"] = _apply_plotly_theme(go.Figure(), theme)
        figs["d2_gap"].update_layout(title=dict(text="B8. High Risk Priorities (Unavailable)", x=0.01))

    return figs
def make_dashboard_1_figures(
    df: pd.DataFrame,
    top_n: int = 12,
    gpa_threshold: Optional[float] = None,
    att_threshold: Optional[float] = None,
    total_override: Optional[float] = None,
    hotspot_df: Optional[pd.DataFrame] = None,
    sunburst_df: Optional[pd.DataFrame] = None,
    theme: str = "light",
) -> Dict[str, go.Figure]:
    """Create Dashboard 1 figures (Outcomes & Risk)."""
    figs: Dict[str, go.Figure] = {}

    snapshot_df = _latest_semester_snapshot(df) if "_latest_semester_snapshot" in globals() else df.copy()

    def _safe_float(value, fallback):
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    gpa_thr = _safe_float(gpa_threshold, gpa_threshold_default)
    att_thr = _safe_float(att_threshold, att_threshold_default)

    risk_color_map = {"High": "#EF4444", "Medium": "#FBBF24", "Low": "#22C55E", "Unknown": "#A0AEC0"}

    def _ensure_risk(frame: pd.DataFrame) -> pd.DataFrame:
        if GPA_COL in frame.columns and ATTEND_COL in frame.columns:
            out = _apply_dynamic_risk(frame, gpa_thr, att_thr)
        else:
            out = frame.copy()
            out[RISK_TIER_COL] = "Unknown"
        out[RISK_TIER_COL] = out[RISK_TIER_COL].astype("string").str.strip().str.title()
        out[RISK_TIER_COL] = out[RISK_TIER_COL].fillna("Unknown")
        return out

    risk_snapshot = _ensure_risk(snapshot_df)
    risk_full = _ensure_risk(df)

    # Attach optional cohort fields
    risk_snapshot, residency_col = _attach_residency(risk_snapshot)
    risk_snapshot, mode_col = _attach_mode(risk_snapshot)
    risk_snapshot, gender_col = _attach_gender(risk_snapshot)
    risk_snapshot, _ = _attach_age_group(risk_snapshot)

    risk_full, residency_full = _attach_residency(risk_full)
    risk_full, mode_full = _attach_mode(risk_full)
    risk_full, gender_full = _attach_gender(risk_full)
    # ----------------------------
    # D1-1 Dynamic Risk Map
    # ----------------------------
    if GPA_COL in risk_snapshot.columns and ATTEND_COL in risk_snapshot.columns:
        scatter_df = risk_snapshot.copy()
        scatter_df["_gpa"] = pd.to_numeric(scatter_df[GPA_COL], errors="coerce")
        scatter_df["_att"] = pd.to_numeric(scatter_df[ATTEND_COL], errors="coerce")
        scatter_df = scatter_df[scatter_df["_gpa"].notna() & scatter_df["_att"].notna()].copy()

        scatter_df["_student"] = (
            scatter_df[STUDENT_ID_COL].astype("string") if STUDENT_ID_COL in scatter_df.columns else "N.A."
        )
        scatter_df["_course"] = (
            scatter_df[course_col].astype("string") if course_col in scatter_df.columns else "N.A."
        )
        scatter_df["_period"] = (
            scatter_df[PERIOD_COL].astype("string") if PERIOD_COL in scatter_df.columns else "N.A."
        )
        scatter_df["_residency"] = (
            scatter_df[residency_col].astype("string") if residency_col else "N.A."
        )
        scatter_df["_mode"] = (
            scatter_df[mode_col].astype("string") if mode_col else "N.A."
        )

        custom_cols = ["_student", "_course", "_period", "_residency", "_mode"]
        risk_map = px.scatter(
            scatter_df,
            x="_att",
            y="_gpa",
            color=RISK_TIER_COL,
            color_discrete_map=risk_color_map,
            labels={"_att": "Attendance (%)", "_gpa": "GPA"},
            custom_data=custom_cols,
        )
        risk_map.update_traces(
            marker=dict(size=9, opacity=0.85, line=dict(width=0)),
            hovertemplate=(
                "<b>Student</b>: %{customdata[0]}"
                "<br><b>Course</b>: %{customdata[1]}"
                "<br><b>Period</b>: %{customdata[2]}"
                "<br><b>GPA</b>: %{y:.2f}"
                "<br><b>Attendance</b>: %{x:.1f}%"
                "<br><b>Residency</b>: %{customdata[3]}"
                "<br><b>Mode</b>: %{customdata[4]}<extra></extra>"
            ),
        )
        risk_map.update_xaxes(title="Attendance (%)")
        risk_map.update_yaxes(title="GPA")

        if np.isfinite(att_thr):
            risk_map.add_vline(x=float(att_thr), line_dash="dash", line_color="rgba(255,143,177,0.65)")
        if np.isfinite(gpa_thr):
            risk_map.add_hline(y=float(gpa_thr), line_dash="dash", line_color="rgba(255,143,177,0.65)")

        # Linear regression line + density toggle
        if not scatter_df.empty:
            if scatter_df["_att"].nunique() > 1:
                slope, intercept = np.polyfit(scatter_df["_att"], scatter_df["_gpa"], 1)
                corr = float(np.corrcoef(scatter_df["_att"], scatter_df["_gpa"])[0, 1])
                x_line = np.linspace(scatter_df["_att"].min(), scatter_df["_att"].max(), 100)
                y_line = slope * x_line + intercept
                risk_map.add_trace(
                    go.Scatter(
                        x=x_line,
                        y=y_line,
                        mode="lines",
                        name=f"Linear fit (r={corr:.2f})",
                        line=dict(color="#7BDFF2", width=2),
                        hovertemplate=f"y={slope:.3f}x+{intercept:.3f}<extra></extra>",
                    )
                )

            density_fig = px.density_heatmap(
                scatter_df,
                x="_att",
                y="_gpa",
                nbinsx=25,
                nbinsy=20,
                color_continuous_scale=[[0.0, "#BDE0FE"], [0.5, "#FFAFCC"], [1.0, "#FF6F91"]],
            )
            density_trace = density_fig.data[0]
            density_trace.visible = False
            density_trace.opacity = 0.75
            density_trace.showlegend = False
            density_trace.showscale = False
            density_trace.hovertemplate = (
                "Attendance=%{x:.1f}%<br>GPA=%{y:.2f}<br>Density=%{z}<extra></extra>"
            )
            risk_map.add_trace(density_trace)

            total_traces = len(risk_map.data)
            vis_points = [True] * total_traces
            vis_points[-1] = False
            vis_density = [False] * total_traces
            vis_density[-1] = True

            risk_map.update_layout(
                updatemenus=[
                    dict(
                        type="buttons",
                        direction="left",
                        x=0.98,
                        y=1.15,
                        xanchor="right",
                        yanchor="top",
                        bgcolor="rgba(255,255,255,0.85)",
                        bordercolor="rgba(140,126,150,0.25)",
                        buttons=[
                            dict(label="Points", method="update", args=[{"visible": vis_points}]),
                            dict(label="Density", method="update", args=[{"visible": vis_density}]),
                        ],
                    )
                ],
                coloraxis_showscale=False,
                uirevision="risk_map_view",
            )

        risk_map.update_layout(
            showlegend=True,
            legend=dict(x=0.01, y=0.99, xanchor="left", yanchor="top"),
        )
        figs["gpa_vs_att"] = _apply_plotly_theme(risk_map, theme)
        figs["gpa_vs_att"].update_layout(
            title=dict(text="A1. Risk Map: GPA vs Attendance", x=0.01),
            margin=dict(l=56, r=28, t=110, b=64),
        )
    else:
        figs["gpa_vs_att"] = _apply_plotly_theme(go.Figure(), theme)
        figs["gpa_vs_att"].update_layout(
            title=dict(text="A1. Risk Map: GPA vs Attendance (Unavailable)", x=0.01),
            margin=dict(l=56, r=28, t=110, b=64),
        )
    # ----------------------------
    # D1-2 Sunburst - Risk Concentration by Cohort
    # ----------------------------
    sun_source = sunburst_df if sunburst_df is not None else snapshot_df
    sun_source = _latest_semester_snapshot(sun_source) if "_latest_semester_snapshot" in globals() else sun_source.copy()
    sun_df = _ensure_risk(sun_source)
    sun_df[RISK_TIER_COL] = sun_df[RISK_TIER_COL].fillna("Unknown")
    sun_df = sun_df[
        sun_df[RISK_TIER_COL]
        .astype("string")
        .str.strip()
        .str.lower()
        .ne("unknown")
    ]
    sun_df, sun_residency_col = _attach_residency(sun_df)
    sun_df, sun_mode_col = _attach_mode(sun_df)
    sun_df, sun_gender_col = _attach_gender(sun_df)
    sun_df, _ = _attach_age_group(sun_df)

    level_col = COURSE_LEVEL_COL if COURSE_LEVEL_COL in sun_df.columns else (course_col if course_col in sun_df.columns else None)
    age_col = "_age_group" if "_age_group" in sun_df.columns else None
    qual_col = HIGHEST_EDU_COL if HIGHEST_EDU_COL in sun_df.columns else None
    fund_col = COURSE_FUNDING_COL if COURSE_FUNDING_COL in sun_df.columns else None

    def _build_sunburst(path_cols):
        if len(path_cols) < 2 or sun_df.empty:
            return None
        tmp = sun_df.copy()
        for col in path_cols:
            tmp[col] = tmp[col].astype("string").str.strip().replace({"": "Unknown"}).fillna("Unknown")

        counts = tmp.groupby(path_cols, observed=False).size().reset_index(name="Count")
        root_key = path_cols[1]
        root_totals = counts.groupby(root_key, observed=False)["Count"].sum().to_dict()

        nodes = {}
        max_level = len(path_cols)
        for _, row in counts.iterrows():
            count = int(row["Count"])
            path_vals = [str(row[col]) for col in path_cols]
            for i in range(max_level):
                prefix = path_vals[: i + 1]
                node_id = "|".join(prefix)
                if node_id not in nodes:
                    parent = "|".join(prefix[:-1]) if i > 0 else ""
                    nodes[node_id] = {
                        "label": prefix[-1],
                        "parent": parent,
                        "value": 0,
                        "path": prefix,
                    }
                nodes[node_id]["value"] += count

        ids, labels, parents, values, customdata, colors = [], [], [], [], [], []
        for node_id, node in nodes.items():
            ids.append(node_id)
            labels.append(node["label"])
            parents.append(node["parent"])
            values.append(node["value"])
            path = node["path"]
            root_risk = str(path[0]) if path else "Unknown"
            colors.append(risk_color_map.get(root_risk, "#A0AEC0"))
            root_val = path[1] if len(path) > 1 else None
            root_total = root_totals.get(root_val, node["value"]) if root_val else node["value"]
            pct_root = (node["value"] / root_total * 100.0) if root_total else 0.0
            padded = path + [""] * (max_level - len(path))
            customdata.append(padded + [pct_root])

        hovertemplate = (
            f"<b>%{{label}}</b><br>Count=%{{value}}"
            f"<br>% within group=%{{customdata[{max_level}]:.1f}}%<extra></extra>"
        )
        return {
            "ids": ids,
            "labels": labels,
            "parents": parents,
            "values": values,
            "customdata": customdata,
            "max_level": max_level,
            "path_cols": path_cols,
            "hovertemplate": hovertemplate,
            "colors": colors,
        }

    path_options = []
    if level_col:
        if sun_mode_col and sun_residency_col:
            path_options.append(("Risk -> Level -> Mode -> Residency", [RISK_TIER_COL, level_col, sun_mode_col, sun_residency_col]))
        if sun_gender_col and sun_residency_col:
            path_options.append(("Risk -> Level -> Gender -> Residency", [RISK_TIER_COL, level_col, sun_gender_col, sun_residency_col]))
        if sun_residency_col:
            path_options.append(("Risk -> Level -> Residency", [RISK_TIER_COL, level_col, sun_residency_col]))
        if sun_mode_col:
            path_options.append(("Risk -> Level -> Mode", [RISK_TIER_COL, level_col, sun_mode_col]))
        if sun_gender_col:
            path_options.append(("Risk -> Level -> Gender", [RISK_TIER_COL, level_col, sun_gender_col]))
        if age_col:
            path_options.append(("Risk -> Level -> Age Group", [RISK_TIER_COL, level_col, age_col]))
        if qual_col:
            path_options.append(("Risk -> Level -> Highest Qualification", [RISK_TIER_COL, level_col, qual_col]))
        if fund_col:
            path_options.append(("Risk -> Level -> Funding", [RISK_TIER_COL, level_col, fund_col]))

    if fund_col and sun_residency_col:
        path_options.append(("Risk -> Funding -> Residency", [RISK_TIER_COL, fund_col, sun_residency_col]))
    if qual_col and sun_residency_col:
        path_options.append(("Risk -> Highest Qualification -> Residency", [RISK_TIER_COL, qual_col, sun_residency_col]))

    sun_configs = []
    for label, cols in path_options:
        cfg = _build_sunburst(cols)
        if cfg is not None:
            cfg["label"] = label
            sun_configs.append(cfg)

    if sun_configs:
        first = sun_configs[0]
        sun = go.Figure(
            data=[
                go.Sunburst(
                    ids=first["ids"],
                    labels=first["labels"],
                    parents=first["parents"],
                    values=first["values"],
                    branchvalues="total",
                    maxdepth=first["max_level"],
                    marker=dict(
                        colors=first["colors"],
                        line=dict(color="rgba(0,0,0,0.08)", width=1),
                    ),
                    customdata=first["customdata"],
                    meta=first["path_cols"],
                    hovertemplate=first["hovertemplate"],
                )
            ]
        )
        buttons = []
        for cfg in sun_configs:
            buttons.append(
                dict(
                    label=cfg["label"],
                    method="update",
                    args=[
                        {
                            "ids": [cfg["ids"]],
                            "labels": [cfg["labels"]],
                            "parents": [cfg["parents"]],
                            "values": [cfg["values"]],
                            "customdata": [cfg["customdata"]],
                            "meta": [cfg["path_cols"]],
                            "maxdepth": [cfg["max_level"]],
                            "hovertemplate": [cfg["hovertemplate"]],
                            "marker.colors": [cfg["colors"]],
                        },
                        {"title": {"text": "A2. Risk Concentration: Cohorts"}},
                    ],
                )
            )
        sun.update_layout(
            title=dict(text="A2. Risk Concentration: Cohorts", x=0.01),
            margin=dict(l=10, r=10, t=110, b=10),
            showlegend=False,
            updatemenus=[
                dict(
                    type="dropdown",
                    x=0.98,
                    y=1.12,
                    xanchor="right",
                    yanchor="top",
                    buttons=buttons,
                    bgcolor="rgba(255,255,255,0.92)",
                    bordercolor="rgba(140,126,150,0.25)",
                )
            ],
        )
        figs["risk_quadrant"] = _apply_plotly_theme(sun, theme)
    else:
        figs["risk_quadrant"] = _apply_plotly_theme(go.Figure(), theme)
        figs["risk_quadrant"].update_layout(
            title=dict(text="A2. Risk Concentration: Cohorts (Unavailable)", x=0.01),
            margin=dict(l=10, r=10, t=110, b=10),
        )
    # ----------------------------
    # ----------------------------
    # D1-3 Sankey - Risk Transition Flow
    # ----------------------------
    sankey_fig = go.Figure()
    if PERIOD_COL in risk_full.columns and STUDENT_ID_COL in risk_full.columns:
        sankey_df = risk_full.copy()
        if "Completion Status" in sankey_df.columns:
            status = sankey_df["Completion Status"].astype("string").str.strip().str.lower()
            sankey_df = sankey_df[status.ne("ongoing")]

        period_vals = sankey_df[PERIOD_COL].astype("string").dropna().unique().tolist()

        def _period_key(val):
            match = re.search(r"(\d+)", str(val))
            return int(match.group(1)) if match else 999

        period_vals = sorted(period_vals, key=_period_key)

        if len(period_vals) >= 2:
            sub = sankey_df[sankey_df[PERIOD_COL].astype("string").isin(period_vals)].copy()
            sub = sub[[STUDENT_ID_COL, PERIOD_COL, RISK_TIER_COL]].dropna()
            pivot = sub.pivot_table(
                index=STUDENT_ID_COL,
                columns=PERIOD_COL,
                values=RISK_TIER_COL,
                aggfunc="first",
            )
            pivot = pivot[period_vals]
            total_students = int(pivot.dropna(how="all").shape[0])

            tiers = ["Low", "Medium", "High"]
            nodes = []
            node_colors = []
            node_index = {}
            node_x = []
            node_y = []
            tier_y = {"Low": 0.15, "Medium": 0.5, "High": 0.85}
            period_count = max(len(period_vals) - 1, 1)
            for p_idx, period in enumerate(period_vals):
                x_pos = p_idx / period_count
                for tier in tiers:
                    node_label = f"{period}: {tier}"
                    node_index[(period, tier)] = len(nodes)
                    nodes.append(node_label)
                    node_colors.append(risk_color_map.get(tier, "#A0AEC0"))
                    node_x.append(x_pos)
                    node_y.append(tier_y.get(tier, 0.5))

            sources, targets, values = [], [], []
            for i in range(len(period_vals) - 1):
                p1 = period_vals[i]
                p2 = period_vals[i + 1]
                transitions = pivot[[p1, p2]].dropna().groupby([p1, p2], observed=False).size()
                for (t1, t2), cnt in transitions.items():
                    if t1 not in tiers or t2 not in tiers:
                        continue
                    sources.append(node_index[(p1, t1)])
                    targets.append(node_index[(p2, t2)])
                    values.append(int(cnt))

            values_pct = [v / total_students * 100.0 for v in values] if total_students else [0] * len(values)
            sankey_fig.add_trace(
                go.Sankey(
                    node=dict(
                        label=nodes,
                        color=node_colors,
                        pad=18,
                        thickness=18,
                        x=node_x,
                        y=node_y,
                    ),
                    link=dict(
                        source=sources,
                        target=targets,
                        value=values,
                        color="rgba(255,143,177,0.45)",
                        customdata=values_pct,
                        hovertemplate="Flow=%{value} students<br>%{customdata:.1f}% of cohort<extra></extra>",
                    ),
                )
            )

            sankey_fig.update_layout(
                title=dict(text="A3. Risk Flow: Semester Transitions", x=0.01),
                margin=dict(l=20, r=20, t=110, b=20),
                showlegend=False,
            )
            figs["course_matrix"] = _apply_plotly_theme(sankey_fig, theme)
        else:
            figs["course_matrix"] = _apply_plotly_theme(go.Figure(), theme)
            figs["course_matrix"].update_layout(
                title=dict(text="A3. Risk Flow: Semester Transitions (Unavailable)", x=0.01),
                margin=dict(l=20, r=20, t=110, b=20),
            )
    else:
        figs["course_matrix"] = _apply_plotly_theme(go.Figure(), theme)
        figs["course_matrix"].update_layout(
            title=dict(text="A3. Risk Flow: Semester Transitions (Unavailable)", x=0.01),
            margin=dict(l=20, r=20, t=110, b=20),
        )

# ----------------------------
    # D1-4 High Risk Hotspots Ranking
    # ----------------------------
    hotspot_fig = go.Figure()
    hot_source = hotspot_df if hotspot_df is not None else risk_snapshot
    hot_source = _ensure_risk(hot_source)
    hot_df = _latest_semester_snapshot(hot_source) if "_latest_semester_snapshot" in globals() else hot_source.copy()

    if course_col in hot_df.columns:
        hot_df[course_col] = hot_df[course_col].astype("string").str.strip()
        hot_df = hot_df[hot_df[course_col].notna() & (hot_df[course_col].str.len() > 0)]
        if not hot_df.empty:
            counts = (
                hot_df.groupby([course_col, RISK_TIER_COL], observed=False)
                .size()
                .reset_index(name="Count")
            )
            totals = counts.groupby(course_col, observed=False)["Count"].sum().rename("Total")
            counts = counts.join(totals, on=course_col)
            counts["Pct"] = counts["Count"] / counts["Total"] * 100.0
            pivot = counts.pivot(index=course_col, columns=RISK_TIER_COL, values="Pct").fillna(0)
            pivot["At-Risk"] = pivot.get("High", 0) + pivot.get("Medium", 0)
            pivot["High"] = pivot.get("High", 0)
            pivot["Medium"] = pivot.get("Medium", 0)
            pivot["Low"] = pivot.get("Low", 0)

            def _top_n(n):
                top = pivot.sort_values("High", ascending=False).head(n)
                return top

            max_top = min(6, len(pivot)) if len(pivot) else 1
            top_options = list(range(1, max_top + 1))
            default_n = 3 if max_top >= 3 else max_top

            top_df = _top_n(default_n)
            courses = top_df.index.tolist()

            hotspot_fig.add_trace(
                go.Bar(
                    x=top_df["High"],
                    y=courses,
                    orientation="h",
                    name="High Risk %",
                    marker_color=risk_color_map.get("High", "#EF4444"),
                    hovertemplate="%{y}<br>High Risk=%{x:.1f}%<extra></extra>",
                )
            )
            hotspot_fig.add_trace(
                go.Bar(
                    x=top_df["Medium"],
                    y=courses,
                    orientation="h",
                    name="Medium Risk %",
                    marker_color=risk_color_map.get("Medium", "#FBBF24"),
                    visible=False,
                    hovertemplate="%{y}<br>Medium Risk=%{x:.1f}%<extra></extra>",
                )
            )
            hotspot_fig.add_trace(
                go.Bar(
                    x=top_df["At-Risk"],
                    y=courses,
                    orientation="h",
                    name="At-Risk %",
                    marker_color="#FF8FB1",
                    visible=False,
                    hovertemplate="%{y}<br>At-Risk=%{x:.1f}%<extra></extra>",
                )
            )
            hotspot_fig.add_trace(
                go.Bar(
                    x=top_df["Low"],
                    y=courses,
                    orientation="h",
                    name="Low Risk %",
                    marker_color=risk_color_map.get("Low", "#22C55E"),
                    visible=False,
                )
            )
            hotspot_fig.add_trace(
                go.Bar(
                    x=top_df["Medium"],
                    y=courses,
                    orientation="h",
                    name="Medium Risk %",
                    marker_color=risk_color_map.get("Medium", "#FBBF24"),
                    visible=False,
                )
            )
            hotspot_fig.add_trace(
                go.Bar(
                    x=top_df["High"],
                    y=courses,
                    orientation="h",
                    name="High Risk %",
                    marker_color=risk_color_map.get("High", "#EF4444"),
                    visible=False,
                )
            )

            hotspot_fig.update_layout(
                barmode="group",
                title=dict(text="A4. Risk Hotspots: Courses", x=0.01),
                margin=dict(l=200, r=20, t=120, b=70),
                xaxis=dict(range=[0, 100], autorange=False, title="Risk %"),
                updatemenus=[
                    dict(
                        type="buttons",
                        direction="left",
                        x=0.98,
                        y=1.18,
                        xanchor="right",
                        yanchor="top",
                        buttons=[
                            dict(
                                label="High Risk %",
                                method="update",
                                args=[{"visible": [True, False, False, False, False, False]}, {"barmode": "group"}],
                            ),
                            dict(
                                label="Medium Risk %",
                                method="update",
                                args=[{"visible": [False, True, False, False, False, False]}, {"barmode": "group"}],
                            ),
                            dict(
                                label="At-Risk %",
                                method="update",
                                args=[{"visible": [False, False, True, False, False, False]}, {"barmode": "group"}],
                            ),
                            dict(
                                label="Stacked Mix",
                                method="update",
                                args=[
                                    {"visible": [False, False, False, True, True, True]},
                                    {"barmode": "stack"},
                                ],
                            ),
                        ],
                    )
                ],
            )

            if top_options:
                steps = []
                for n in top_options:
                    top_df_n = _top_n(n)
                    courses_n = top_df_n.index.tolist()
                    step = dict(
                        method="update",
                        args=[
                            {
                                "x": [
                                    top_df_n["High"],
                                    top_df_n["Medium"],
                                    top_df_n["At-Risk"],
                                    top_df_n["Low"],
                                    top_df_n["Medium"],
                                    top_df_n["High"],
                                ],
                                "y": [courses_n] * 6,
                            }
                        ],
                        label=f"Top {n}",
                    )
                    steps.append(step)
                default_idx = max(0, top_options.index(default_n)) if default_n in top_options else 0
                hotspot_fig.update_layout(
                    sliders=[
                        dict(
                            active=default_idx,
                            currentvalue={"prefix": "Top N: "},
                            steps=steps,
                            x=0.02,
                            y=-0.06,
                        )
                    ]
                )

            figs["funding_level_matrix"] = _apply_plotly_theme(hotspot_fig, theme)
        else:
            figs["funding_level_matrix"] = _apply_plotly_theme(go.Figure(), theme)
    else:
        figs["funding_level_matrix"] = _apply_plotly_theme(go.Figure(), theme)
    if "funding_level_matrix" in figs:
        figs["funding_level_matrix"].update_layout(
            title=dict(text="A4. Risk Hotspots: Courses", x=0.01),
            margin=dict(l=200, r=20, t=120, b=80),
            legend=dict(x=0.98, y=0.02, xanchor="right", yanchor="bottom"),
        )

# ----------------------------
    # D1-5 Risk Over Time Trend Line
    # ----------------------------
    trend_fig = go.Figure()
    if PERIOD_COL in risk_full.columns and STUDENT_ID_COL in risk_full.columns:
        trend_df = risk_full.copy()
        trend_df[PERIOD_COL] = trend_df[PERIOD_COL].astype("string")

        def _period_key(val):
            match = re.search(r"(\d+)", str(val))
            return int(match.group(1)) if match else 999

        period_order = sorted(trend_df[PERIOD_COL].dropna().unique().tolist(), key=_period_key)

        def _risk_rate(df_local, group_col=None):
            if group_col:
                grp = df_local.groupby([group_col, PERIOD_COL], observed=False)
            else:
                grp = df_local.groupby([PERIOD_COL], observed=False)
            counts = grp.apply(lambda x: (x[RISK_TIER_COL] == "High").sum()).rename("High")
            totals = grp.size().rename("Total")
            stats = pd.concat([counts, totals], axis=1).reset_index()
            stats["Rate"] = stats["High"] / stats["Total"] * 100.0
            return stats

        def _sort_period(stats):
            stats["_pkey"] = stats[PERIOD_COL].apply(_period_key)
            return stats.sort_values(["_pkey", PERIOD_COL]).drop(columns=["_pkey"])

        overall_stats = _sort_period(_risk_rate(trend_df))
        overall_raw = go.Scatter(
            x=overall_stats[PERIOD_COL],
            y=overall_stats["Rate"],
            mode="lines+markers",
            name="Overall",
            marker=dict(color="#FF8FB1"),
            visible=True,
        )
        trend_fig.add_trace(overall_raw)

        course_group_col = COURSE_LEVEL_COL if COURSE_LEVEL_COL in trend_df.columns else (course_col if course_col in trend_df.columns else None)
        course_label = "Course Level" if course_group_col == COURSE_LEVEL_COL else "Course"

        course_raw = []
        if course_group_col:
            course_stats = _sort_period(_risk_rate(trend_df, course_group_col))
            groups = course_stats.groupby(course_group_col, observed=False)["Total"].sum().sort_values(ascending=False)
            top_groups = groups.index.tolist()
            if course_group_col != COURSE_LEVEL_COL:
                top_groups = top_groups[:6]
            for name in top_groups:
                sub = course_stats[course_stats[course_group_col] == name]
                course_raw.append(
                    go.Scatter(
                        x=sub[PERIOD_COL],
                        y=sub["Rate"],
                        mode="lines+markers",
                        name=f"{course_label}: {name}",
                        visible=False,
                    )
                )

        res_raw = []
        if residency_full:
            res_stats = _sort_period(_risk_rate(trend_df, residency_full))
            res_groups = res_stats.groupby(residency_full, observed=False)["Total"].sum().sort_values(ascending=False).index.tolist()
            for name in res_groups:
                sub = res_stats[res_stats[residency_full] == name]
                res_raw.append(
                    go.Scatter(
                        x=sub[PERIOD_COL],
                        y=sub["Rate"],
                        mode="lines+markers",
                        name=f"Residency: {name}",
                        visible=False,
                    )
                )

        for tr in course_raw + res_raw:
            trend_fig.add_trace(tr)

        total_traces = len(trend_fig.data)

        def _vis_for(section):
            vis = [False] * total_traces
            if section == "overall":
                vis[0] = True
                return vis
            idx = 1
            if section == "course":
                count = len(course_raw)
                for i in range(count):
                    vis[idx + i] = True
                return vis
            idx = 1 + len(course_raw)
            if section == "residency":
                count = len(res_raw)
                for i in range(count):
                    vis[idx + i] = True
            return vis

        buttons = [
            dict(label="Overall", method="update", args=[{"visible": _vis_for("overall")}, {"title": {"text": "A5. Risk Trend: High Risk Rate"}}]),
        ]
        if course_raw:
            buttons.extend([
                dict(label=f"By {course_label}", method="update", args=[{"visible": _vis_for("course")}, {"title": {"text": f"Risk Trend: By {course_label}"}}]),
            ])
        if res_raw:
            buttons.extend([
                dict(label="By Residency", method="update", args=[{"visible": _vis_for("residency")}, {"title": {"text": "Risk Trend: By Residency"}}]),
            ])

        trend_fig.update_layout(
            title=dict(text="A5. Risk Trend: High Risk Rate", x=0.01),
            margin=dict(l=60, r=40, t=120, b=60),
            yaxis_title="Risk Rate (%)",
            updatemenus=[
                dict(
                    type="dropdown",
                    x=0.98,
                    y=1.15,
                    xanchor="right",
                    yanchor="top",
                    buttons=buttons,
                    bgcolor="rgba(255,255,255,0.92)",
                    bordercolor="rgba(140,126,150,0.25)",
                )
            ],
        )
        figs["cohort_trend"] = _apply_plotly_theme(trend_fig, theme)
    else:
        figs["cohort_trend"] = _apply_plotly_theme(go.Figure(), theme)
        figs["cohort_trend"].update_layout(
            title=dict(text="A5. Risk Trend: High Risk Rate (Unavailable)", x=0.01),
            margin=dict(l=60, r=40, t=120, b=60),
        )

# D1-6 GPA Distribution by Risk
    # ----------------------------
    gpa_fig = go.Figure()
    if GPA_COL in risk_full.columns:
        dist_df = risk_full.copy()
        dist_df[GPA_COL] = pd.to_numeric(dist_df[GPA_COL], errors="coerce")
        dist_df = dist_df[dist_df[GPA_COL].notna()]
        tiers = ["Low", "Medium", "High"]

        traces = []
        for tier in tiers:
            sub = dist_df[dist_df[RISK_TIER_COL] == tier]
            traces.append(
                go.Violin(
                    y=sub[GPA_COL],
                    x=[tier] * len(sub),
                    name=tier,
                    legendgroup=tier,
                    scalegroup=tier,
                    box_visible=True,
                    meanline_visible=True,
                    points=False,
                    visible=True,
                    line_color=risk_color_map.get(tier, "#A0AEC0"),
                )
            )

        for tr in traces:
            gpa_fig.add_trace(tr)

        gpa_fig.update_layout(
            title=dict(text="A6. Distribution: GPA by Risk", x=0.01),
            margin=dict(l=50, r=20, t=110, b=60),
            yaxis_title="GPA",
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    x=0.98,
                    y=1.12,
                    xanchor="right",
                    yanchor="top",
                    buttons=[
                        dict(label="Points off", method="restyle", args=[{"points": False}]),
                        dict(label="Points on", method="restyle", args=[{"points": "all"}]),
                    ],
                ),
            ],
        )
        figs["gpa_dist"] = _apply_plotly_theme(gpa_fig, theme)
    else:
        figs["gpa_dist"] = _apply_plotly_theme(go.Figure(), theme)
        figs["gpa_dist"].update_layout(title=dict(text="A6. Distribution: GPA by Risk (Unavailable)", x=0.01))

    # ----------------------------
    # D1-7 Attendance Distribution by Risk
    # ----------------------------
    att_fig = go.Figure()
    if ATTEND_COL in risk_full.columns:
        dist_df = risk_full.copy()
        dist_df[ATTEND_COL] = pd.to_numeric(dist_df[ATTEND_COL], errors="coerce")
        dist_df = dist_df[dist_df[ATTEND_COL].notna()]
        tiers = ["Low", "Medium", "High"]

        traces = []
        for tier in tiers:
            sub = dist_df[dist_df[RISK_TIER_COL] == tier]
            traces.append(
                go.Violin(
                    y=sub[ATTEND_COL],
                    x=[tier] * len(sub),
                    name=tier,
                    legendgroup=tier,
                    scalegroup=tier,
                    box_visible=True,
                    meanline_visible=True,
                    points=False,
                    visible=True,
                    line_color=risk_color_map.get(tier, "#A0AEC0"),
                )
            )

        for tr in traces:
            att_fig.add_trace(tr)

        att_fig.update_layout(
            title=dict(text="A7. Distribution: Attendance by Risk", x=0.01),
            margin=dict(l=50, r=20, t=110, b=60),
            yaxis_title="Attendance (%)",
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    x=0.98,
                    y=1.12,
                    xanchor="right",
                    yanchor="top",
                    buttons=[
                        dict(label="Points off", method="restyle", args=[{"points": False}]),
                        dict(label="Points on", method="restyle", args=[{"points": "all"}]),
                    ],
                ),
            ],
        )
        figs["kpi"] = _apply_plotly_theme(att_fig, theme)
    else:
        figs["kpi"] = _apply_plotly_theme(go.Figure(), theme)
        figs["kpi"].update_layout(title=dict(text="A7. Distribution: Attendance by Risk (Unavailable)", x=0.01))

    return figs


def _filters_active(period, course_level, course_name, funding, qualification, gpa_range, att_range):
    def _norm_list(values):
        if values is None:
            return []
        if isinstance(values, (list, tuple, set)):
            return [str(v) for v in values if v is not None and str(v).strip() != ""]
        return [str(values)]

    def _same_selection(selected, options):
        if not options:
            return True
        return set(selected) == set([str(o) for o in options])

    periods = _norm_list(period)
    levels = _norm_list(course_level)
    courses = _norm_list(course_name)
    fundings = _norm_list(funding)
    quals = _norm_list(qualification)

    if not _same_selection(periods, period_options):
        return True
    if not _same_selection(levels, course_level_options):
        return True
    if not _same_selection(courses, course_options):
        return True
    if not _same_selection(fundings, funding_options):
        return True
    if not _same_selection(quals, highest_edu_options):
        return True

    if isinstance(gpa_range, (list, tuple)) and len(gpa_range) == 2:
        if abs(float(gpa_range[0]) - float(gpa_min)) > 1e-6 or abs(float(gpa_range[1]) - float(gpa_max)) > 1e-6:
            return True
    if isinstance(att_range, (list, tuple)) and len(att_range) == 2:
        if abs(float(att_range[0]) - float(att_min)) > 1e-6 or abs(float(att_range[1]) - float(att_max)) > 1e-6:
            return True

    return False


init_df = dash_df.copy()
init_figs_1 = make_dashboard_1_figures(
    init_df,
    top_n=12,
    gpa_threshold=gpa_threshold_default,
    att_threshold=att_threshold_default,
    total_override=int(init_df[[GPA_COL, ATTEND_COL]].dropna().shape[0]) if GPA_COL in init_df.columns and ATTEND_COL in init_df.columns else None,
    hotspot_df=init_df,
    sunburst_df=init_df,
    theme="light",
)
init_figs_2 = make_dashboard_2_figures(
    init_df,
    gpa_threshold_default,
    att_threshold_default,
    theme="light",
    likert_dim=likert_dim_options[0] if likert_dim_options else None,
    likert_mode="Percent",
    reg_x=d2_reg_x_options[0]["value"] if d2_reg_x_options else None,
    reg_y=d2_reg_y_options[0]["value"] if d2_reg_y_options else None,
    study_toggle="study",
    radar_toggle="without",
    gap_risk="High",
    gap_measure="mean",
    gap_topn=d2_gap_topn_default,
)
init_figs_2 = {key: _apply_plotly_theme(fig, "light") for key, fig in init_figs_2.items()}

base_kpis = _compute_kpis(
    dash_df,
    gpa_threshold_default,
    att_threshold_default,
    use_latest_gpa=True,
    gpa_stat="mean",
    att_stat="mean",
    risk_tier="High",
)
base_display = _build_kpi_display(base_kpis, base_kpis, risk_tier="High", risk_mode="percent")


DASH_THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Nunito:wght@300;400;600;700&display=swap');

:root {
  --bg: #FFF5F8;
  --bg-accent: #FEE9F1;
  --panel: #FFFFFF;
  --panel-soft: #FFF0F6;
  --panel-bright: #FFFFFF;
  --border: rgba(140, 126, 150, 0.14);
  --text: #2C1F2E;
  --muted: #5F5168;
  --accent: #FF8FB1;
  --accent-2: #7BDFF2;
  --accent-3: #BDE0FE;
  --accent-4: #FFD166;
  --danger: #FF6B6B;
  --shadow: 0 14px 24px rgba(59, 46, 58, 0.08);
  --glow: 0 0 0 6px rgba(255, 143, 177, 0.12);
}

.theme-dark {
  --bg: #1A1522;
  --bg-accent: #241B2E;
  --panel: #2A2234;
  --panel-soft: #332840;
  --panel-bright: #FFF5F8;
  --border: rgba(231, 214, 255, 0.2);
  --text: #F7F2FB;
  --muted: #D9CDE6;
  --accent: #FF8FB1;
  --accent-2: #7BDFF2;
  --accent-3: #BDE0FE;
  --accent-4: #FFD166;
  --danger: #FF7A8A;
  --shadow: 0 18px 36px rgba(0, 0, 0, 0.35);
  --glow: 0 0 0 6px rgba(123, 223, 242, 0.18);
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: 'Nunito', 'Segoe UI', sans-serif;
}

.dash-root {
  background:
    radial-gradient(circle at 15% 0%, rgba(255, 143, 177, 0.18) 0%, rgba(255, 143, 177, 0) 55%),
    radial-gradient(circle at 85% 10%, rgba(123, 223, 242, 0.2) 0%, rgba(123, 223, 242, 0) 50%),
    radial-gradient(circle at 30% 80%, rgba(189, 224, 254, 0.25) 0%, rgba(189, 224, 254, 0) 50%),
    linear-gradient(180deg, #FFF7FB 0%, #FFF5F8 55%, #FEE9F1 100%);
  min-height: 100vh;
  padding: 20px;
  position: relative;
  transition: background 0.35s ease, color 0.35s ease;
  color: var(--text);
}

.dash-root::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(255, 255, 255, 0.45) 1px, transparent 1px);
  background-size: 36px 36px;
  opacity: 0.2;
  pointer-events: none;
}

.theme-dark.dash-root {
  background:
    radial-gradient(circle at 15% 0%, rgba(255, 143, 177, 0.15) 0%, rgba(255, 143, 177, 0) 55%),
    radial-gradient(circle at 85% 15%, rgba(123, 223, 242, 0.2) 0%, rgba(123, 223, 242, 0) 50%),
    radial-gradient(circle at 25% 80%, rgba(189, 224, 254, 0.2) 0%, rgba(189, 224, 254, 0) 45%),
    linear-gradient(180deg, #221B2D 0%, #1A1522 60%, #15101C 100%);
}

.theme-dark.dash-root::before {
  background-image: radial-gradient(rgba(255, 255, 255, 0.25) 1px, transparent 1px);
  opacity: 0.12;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.page-classification {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 999px;
  font-family: 'Nunito', 'Segoe UI', sans-serif;
  font-size: 12px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: var(--text);
  background: var(--panel);
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  margin-bottom: 12px;
}

.brand-block {
  display: flex;
  gap: 14px;
  align-items: center;
  background: var(--panel);
  padding: 10px 14px;
  border-radius: 18px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}

.brand-logo {
  width: 82px;
  height: 56px;
  border-radius: 16px;
  border: 1px solid rgba(255, 143, 177, 0.35);
  box-shadow: 0 10px 20px rgba(255, 143, 177, 0.25);
  background: #FFFFFF;
  object-fit: contain;
  padding: 6px;
}

.brand-title {
  font-family: 'Fredoka', 'Nunito', sans-serif;
  font-size: 24px;
  font-weight: 600;
  letter-spacing: 0.2px;
}

.brand-subtitle {
  font-size: 12px;
  color: var(--muted);
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.theme-toggle {
  background: var(--panel);
  border: 1px solid var(--border);
  padding: 8px 12px;
  border-radius: 999px;
  box-shadow: var(--shadow);
}

.theme-toggle label {
  font-weight: 600;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 10px;
  line-height: 1;
}

.theme-toggle label span {
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.theme-light .theme-toggle label span {
  color: #2C1F2E;
  transition: color 0.2s ease;
}

.theme-light .theme-toggle label span:hover {
  color: #7A5AF8;
}

.theme-dark .theme-toggle label span {
  color: #FFFFFF;
  transition: color 0.2s ease;
}

.theme-dark .theme-toggle label span:hover {
  color: #FF8FB1;
}

.theme-toggle input[type="checkbox"] {
  appearance: none;
  width: 44px;
  height: 24px;
  background: rgba(140, 126, 150, 0.3);
  border-radius: 999px;
  position: relative;
  cursor: pointer;
  transition: background 0.2s ease;
  border: 1px solid rgba(140, 126, 150, 0.3);
}

.theme-toggle input[type="checkbox"]::after {
  content: "";
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  border-radius: 999px;
  background: #FFFFFF;
  box-shadow: 0 4px 8px rgba(59, 46, 58, 0.25);
  transition: transform 0.2s ease;
}

.theme-toggle input[type="checkbox"]:checked {
  background: var(--accent-2);
  border-color: rgba(123, 223, 242, 0.6);
}

.theme-toggle input[type="checkbox"]:checked::after {
  transform: translateX(18px);
}

.filter-toggle {
  background: var(--accent);
  color: #FFFFFF;
  border: none;
  padding: 10px 20px;
  border-radius: 999px;
  font-weight: 600;
  letter-spacing: 0.2px;
  cursor: pointer;
  box-shadow: 0 12px 20px rgba(255, 143, 177, 0.35);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.filter-toggle:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

.objective-panel {
  background: var(--panel);
  border: 1px solid rgba(140, 126, 150, 0.1);
  border-radius: 18px;
  padding: 16px 18px;
  box-shadow: var(--shadow);
  margin-bottom: 14px;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.objective-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: var(--muted);
  margin-bottom: 6px;
}

.objective-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.filter-panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 18px;
  box-shadow: var(--shadow);
  overflow: hidden;
  max-height: 0;
  opacity: 0;
  transform: translateY(-8px);
  transition: max-height 0.45s ease, opacity 0.3s ease, transform 0.3s ease;
  margin-bottom: 16px;
  pointer-events: none;
  backdrop-filter: blur(6px);
}

.filter-panel.is-open {
  max-height: 1200px;
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}

.filter-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--panel-soft);
  border-bottom: 1px solid var(--border);
}

.filter-panel__title {
  font-weight: 700;
  letter-spacing: 0.3px;
}

.filter-close {
  border: none;
  background: rgba(255, 107, 107, 0.16);
  color: var(--danger);
  width: 32px;
  height: 32px;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
}

.control-panel {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 10px;
  padding: 14px 16px 18px;
  align-items: start;
  grid-auto-flow: dense;
}

.span-2 { grid-column: span 2; }
.span-3 { grid-column: span 3; }
.span-4 { grid-column: span 4; }
.span-5 { grid-column: span 5; }
.span-6 { grid-column: span 6; }
.span-12 { grid-column: span 12; }

.control-card {
  background: var(--panel-soft);
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid var(--border);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  min-width: 0;
}

.control-card label {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 6px;
  display: block;
  font-weight: 600;
}

.control-card:hover {
  box-shadow: 0 12px 20px rgba(59, 46, 58, 0.12);
  border-color: rgba(255, 143, 177, 0.5);
}

.filter-card {
  min-height: 230px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.65), rgba(255, 240, 246, 0.85));
  overflow: hidden;
}

.filter-card.compact {
  min-height: 190px;
}

.theme-dark .filter-card {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02));
  border-color: rgba(255, 255, 255, 0.18);
}

.theme-dark .filter-card:hover {
  border-color: rgba(255, 143, 177, 0.65);
  box-shadow: 0 12px 20px rgba(255, 143, 177, 0.18);
}

.filter-card .filter-checklist {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px 10px;
  align-content: start;
  padding-right: 4px;
  min-width: 0;
  width: 100%;
}

.filter-card.wide .filter-checklist {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.course-card .filter-checklist {
  grid-template-columns: repeat(2, minmax(240px, 1fr));
  column-gap: 14px;
}

.course-card .filter-checklist label {
  font-size: 12px;
  padding: 6px 8px;
}

.course-card {
  min-height: 170px;
}

.filter-checklist label {
  display: flex !important;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid var(--border);
  padding: 6px 10px;
  border-radius: 999px;
  width: 100%;
  justify-content: flex-start;
  color: var(--text);
  min-width: 0;
  white-space: nowrap;
  line-height: 1.2;
  box-sizing: border-box;
  max-width: 100%;
  flex-wrap: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
}

.filter-checklist label span {
  display: block;
  min-width: 0;
  flex: 1 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.filter-checklist input[type="checkbox"] {
  accent-color: var(--accent);
  width: 16px;
  height: 16px;
}

.theme-dark .filter-checklist label {
  background: rgba(255, 255, 255, 0.24);
  border-color: rgba(255, 255, 255, 0.4);
  color: #F9F5FF;
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.22);
}

.theme-dark .control-card label {
  color: var(--muted);
}

.risk-card {
  grid-column: span 6;
  background: linear-gradient(135deg, rgba(255, 143, 177, 0.16), rgba(123, 223, 242, 0.16));
  padding: 10px 12px;
}

.risk-card .filter-checklist label {
  background: rgba(255, 255, 255, 0.7);
}

.risk-title {
  font-weight: 700;
  font-size: 14px;
  color: var(--text);
}

.risk-caption {
  font-size: 12px;
  color: var(--muted);
  margin-top: 4px;
  margin-bottom: 10px;
}

.risk-sliders {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.risk-slider {
  background: var(--panel);
  border-radius: 14px;
  border: 1px solid var(--border);
  padding: 8px 10px;
  box-shadow: var(--shadow);
}

.question-panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 14px 16px;
  margin: 14px 0 12px;
  box-shadow: 0 12px 24px rgba(59, 46, 58, 0.1);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.question-panel:hover {
  box-shadow: 0 18px 28px rgba(59, 46, 58, 0.14);
  border-color: rgba(123, 223, 242, 0.5);
}

.question-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1.1px;
  color: var(--muted);
  margin-bottom: 6px;
}

.question-text {
  font-size: 14px;
  font-weight: 600;
}

.dash-tabs-wrapper {
  margin-top: 8px;
}

.dash-tabs {
  border: none !important;
}

.dash-tab {
  background: var(--panel-soft) !important;
  border: 1px solid var(--border) !important;
  color: var(--muted) !important;
  padding: 8px 18px !important;
  border-radius: 999px !important;
  font-weight: 600 !important;
  margin-right: 10px;
}

.dash-tab--selected {
  background: var(--accent) !important;
  border-color: transparent !important;
  color: #FFFFFF !important;
  box-shadow: 0 12px 20px rgba(255, 143, 177, 0.3);
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 14px;
}

.chart-card {
  background: var(--panel);
  border-radius: 20px;
  padding: 10px;
  border: 1px solid var(--border);
  box-shadow: 0 12px 24px rgba(59, 46, 58, 0.1);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  grid-column: span 4;
}

.chart-span-4 {
  grid-column: span 4;
}

.chart-span-5 {
  grid-column: span 5;
}

.chart-span-6 {
  grid-column: span 6;
}

.chart-span-7 {
  grid-column: span 7;
}

.chart-span-8 {
  grid-column: span 8;
}

.chart-span-12 {
  grid-column: span 12;
}

.chart-card:hover {
  box-shadow: 0 20px 32px rgba(59, 46, 58, 0.14), var(--glow);
  border-color: rgba(255, 143, 177, 0.55);
}

.chart-card:focus-within {
  box-shadow: 0 20px 32px rgba(59, 46, 58, 0.14), var(--glow);
  border-color: rgba(255, 143, 177, 0.55);
}

.chart-card:has(.js-plotly-plot:hover) {
  box-shadow: 0 20px 32px rgba(59, 46, 58, 0.14), var(--glow);
  border-color: rgba(255, 143, 177, 0.55);
}

.chart-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 6px 8px;
  flex-wrap: wrap;
}

.chart-toolbar--stack {
  flex-direction: column;
  align-items: stretch;
}

.chart-control {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chart-control__label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: var(--muted);
  font-family: 'Nunito', 'Segoe UI', sans-serif;
}

.annotation-text-g {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: var(--muted);
  font-family: 'Nunito', 'Segoe UI', sans-serif;
}

.chart-toolbar .kpi-dropdown {
  min-width: 160px;
}

.chart-toolbar .kpi-dropdown--small {
  min-width: 120px;
}

.chart-toolbar .kpi-dropdown--wide {
  min-width: 240px;
}

.chart-toolbar .rc-slider {
  margin-top: 6px;
}

.gap-slider-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
  letter-spacing: 0.2px;
  font-family: 'Nunito', 'Segoe UI', sans-serif;
}

.chart-slider {
  margin-top: 6px;
  padding: 4px 6px 10px;
  border-radius: 14px;
  background: rgba(255, 240, 246, 0.6);
  border: 1px solid var(--border);
}

.theme-dark .chart-slider {
  background: rgba(51, 40, 64, 0.6);
}

.chart-toolbar .Select-control,
.chart-toolbar .kpi-dropdown .Select-control {
  background-color: var(--panel) !important;
  opacity: 1 !important;
}

.gap-slider .rc-slider-rail {
  background-color: rgba(122, 111, 102, 0.2) !important;
}

.gap-slider .rc-slider-track {
  background-color: var(--accent) !important;
}

.gap-slider .rc-slider-handle {
  border-color: var(--accent) !important;
  background-color: #FFFFFF !important;
  box-shadow: var(--glow) !important;
}

.gap-slider .rc-slider-mark-text {
  font-size: 11px;
  color: var(--muted) !important;
  font-weight: 600;
}

@media (max-width: 1400px) {
  .chart-card,
  .chart-span-4,
  .chart-span-5,
  .chart-span-6 {
    grid-column: span 6;
  }

  .chart-span-7,
  .chart-span-8,
  .chart-span-12 {
    grid-column: span 12;
  }
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
  position: relative;
  z-index: 1;
}

.kpi-card {
  background: var(--panel);
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 18px;
  padding: 14px 16px;
  box-shadow: var(--shadow);
  position: relative;
  overflow: visible;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  display: grid;
  grid-template-rows: 26px 44px 24px;
  align-items: center;
  gap: 2px;
  z-index: 1;
}

.kpi-card::after {
  content: "";
  position: absolute;
  right: -20px;
  top: -20px;
  width: 90px;
  height: 90px;
  background: radial-gradient(circle, rgba(255, 143, 177, 0.22), rgba(255, 143, 177, 0));
  opacity: 0.55;
  filter: blur(6px);
  pointer-events: none;
  z-index: 0;
}

.kpi-card:nth-child(2)::after {
  background: radial-gradient(circle, rgba(123, 223, 242, 0.22), rgba(123, 223, 242, 0));
}

.kpi-card:nth-child(3)::after {
  background: radial-gradient(circle, rgba(255, 209, 102, 0.22), rgba(255, 209, 102, 0));
}

.kpi-card:nth-child(4)::after {
  background: radial-gradient(circle, rgba(189, 224, 254, 0.24), rgba(189, 224, 254, 0));
}

.kpi-card:hover {
  box-shadow: 0 20px 32px rgba(59, 46, 58, 0.14);
  border-color: rgba(189, 224, 254, 0.6);
}

.kpi-card:focus-within {
  z-index: 50;
}

.kpi-card::before {
  content: "";
  position: absolute;
  inset: 1px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  pointer-events: none;
  z-index: 0;
}

.kpi-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: var(--muted);
  grid-row: 1;
}

.kpi-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  grid-row: 1;
  min-height: 26px;
}

.kpi-dropdown-group {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.kpi-card > * {
  position: relative;
  z-index: 1;
}

.kpi-dropdown {
  min-width: 96px;
  max-width: 120px;
  z-index: 5;
  position: relative;
}

.kpi-dropdown--tiny {
  min-width: 70px;
  max-width: 86px;
  width: 70px;
}

.kpi-dropdown--small {
  min-width: 100px;
  max-width: 120px;
  width: 108px;
}

.kpi-dropdown .Select-control {
  min-height: 26px !important;
  border-radius: 999px !important;
  padding: 0 6px !important;
  background: #FFF0F6 !important;
  background-color: #FFF0F6 !important;
  border: 1px solid var(--border) !important;
  box-shadow: none !important;
  cursor: pointer;
  position: relative;
  z-index: 6;
}

.kpi-dropdown--tiny .Select-control {
  width: 70px !important;
}

.kpi-dropdown--tiny .Select-value-label,
.kpi-dropdown--tiny .Select-placeholder {
  max-width: 32px !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

.kpi-dropdown--small .Select-control {
  width: 108px !important;
}

.kpi-dropdown--small .Select-value-label,
.kpi-dropdown--small .Select-placeholder {
  max-width: 80px !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

.kpi-dropdown--tiny .Select-arrow-zone {
  padding-left: 4px !important;
}

.kpi-dropdown .Select-placeholder,
.kpi-dropdown .Select-value-label {
  font-size: 11px !important;
  font-weight: 700 !important;
  color: #2C1F2E !important;
}

.kpi-dropdown .Select-input input {
  color: #2C1F2E !important;
}


.kpi-dropdown .Select-arrow-zone {
  color: var(--muted) !important;
}

.kpi-dropdown .Select-menu-outer {
  border-radius: 12px !important;
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  box-shadow: var(--shadow) !important;
  z-index: 99999 !important;
  position: fixed !important;
  width: 220px !important;
}

.kpi-card:focus-within .kpi-value,
.kpi-card:focus-within .kpi-delta {
  z-index: 0;
}

.kpi-dropdown .VirtualizedSelectOption {
  font-size: 12px !important;
  color: var(--text) !important;
}

.kpi-dropdown .VirtualizedSelectFocusedOption {
  background: rgba(255, 143, 177, 0.16) !important;
}

.kpi-value {
  font-size: 26px;
  font-weight: 700;
  font-family: 'Fredoka', 'Nunito', sans-serif;
  margin-top: 0;
  grid-row: 2;
  display: flex;
  align-items: center;
}

.kpi-delta {
  margin-top: 6px;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
  display: inline-block;
  background: rgba(140, 126, 150, 0.12);
  color: var(--muted);
  grid-row: 3;
}

.kpi-delta:empty {
  display: none;
}

.kpi-good {
  background: rgba(34, 197, 94, 0.18);
  color: #16794f;
}

.kpi-bad {
  background: rgba(248, 113, 113, 0.18);
  color: #b42324;
}

.kpi-neutral {
  background: rgba(140, 126, 150, 0.12);
  color: var(--muted);
}

.theme-dark .kpi-card {
  background: var(--panel);
}

.theme-dark .chart-card {
  background: var(--panel-bright);
  border-color: rgba(255, 255, 255, 0.35);
}

.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td,
.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th {
  background-color: #FFF0F6 !important;
  color: var(--text) !important;
}

.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th {
  background-color: #FEE1ED !important;
}

.Select-control {
  background-color: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  min-height: 34px !important;
  box-shadow: none !important;
}

.Select-placeholder, .Select-value-label, .Select-input {
  color: var(--text) !important;
}

.Select-menu-outer {
  background-color: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  box-shadow: var(--shadow) !important;
}

.VirtualizedSelectOption {
  color: var(--text) !important;
}

.VirtualizedSelectFocusedOption {
  background-color: rgba(255, 143, 177, 0.2) !important;
  color: var(--text) !important;
}

input[type="text"],
input[type="number"] {
  background: var(--panel) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 6px 10px !important;
  box-shadow: none !important;
}

input[type="text"]::placeholder,
input[type="number"]::placeholder {
  color: var(--muted) !important;
}

.theme-dark .Select-control {
  background-color: #2A2234 !important;
  border-color: rgba(231, 214, 255, 0.35) !important;
}

.theme-dark .Select-placeholder,
.theme-dark .Select-value-label,
.theme-dark .Select-input {
  color: #F7F2FB !important;
}

.theme-dark .Select-input input {
  color: #F7F2FB !important;
  background: transparent !important;
}

.theme-dark .Select-menu-outer {
  background-color: #2A2234 !important;
  border-color: rgba(231, 214, 255, 0.35) !important;
}

.theme-dark .VirtualizedSelectOption {
  color: #F7F2FB !important;
}

.theme-dark .VirtualizedSelectFocusedOption {
  background-color: rgba(123, 223, 242, 0.22) !important;
  color: #F7F2FB !important;
}

.theme-dark .kpi-dropdown .Select-control {
  background-color: #EDE7F2 !important;
  border-color: rgba(140, 126, 150, 0.28) !important;
}

.theme-dark .kpi-dropdown .Select-menu-outer {
  background-color: #F5F1F8 !important;
  border-color: rgba(140, 126, 150, 0.28) !important;
}

.theme-dark .kpi-dropdown .Select-placeholder,
.theme-dark .kpi-dropdown .Select-value-label,
.theme-dark .kpi-dropdown .Select-input,
.theme-dark .kpi-dropdown .Select-input input,
.theme-dark .kpi-dropdown .VirtualizedSelectOption,
.theme-dark .kpi-dropdown .VirtualizedSelectFocusedOption {
  color: #2C1F2E !important;
}

.theme-dark .kpi-dropdown .VirtualizedSelectFocusedOption {
  background-color: rgba(255, 143, 177, 0.2) !important;
}

.rc-slider-rail {
  background-color: rgba(122, 111, 102, 0.2) !important;
}

.rc-slider-track {
  background-color: var(--accent) !important;
}

.rc-slider-handle {
  border-color: var(--accent) !important;
  background-color: #FFFFFF !important;
  box-shadow: var(--glow) !important;
}

.rc-slider-mark-text {
  color: var(--muted) !important;
  font-weight: 600;
  opacity: 0.9;
}

.theme-dark .rc-slider-rail {
  background-color: rgba(255, 255, 255, 0.25) !important;
}

.theme-dark .rc-slider-track {
  background-color: #FFFFFF !important;
}

.theme-dark .dash-slider-track,
body.theme-dark .dash-slider-track,
html.theme-dark .dash-slider-track {
  background-color: #FFFFFF !important;
}

.theme-dark .rc-slider-handle {
  border-color: #FFFFFF !important;
  background-color: #FFFFFF !important;
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.2) !important;
}

.theme-dark .rc-slider-dot {
  border-color: rgba(255, 255, 255, 0.6) !important;
  background-color: #FFFFFF !important;
}

.theme-dark .rc-slider-mark-text {
  color: #FFFFFF !important;
  opacity: 0.98;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.45);
  font-weight: 700;
}

.theme-dark .rc-slider-mark,
.theme-dark .rc-slider-mark-text,
body.theme-dark .rc-slider-mark,
body.theme-dark .rc-slider-mark-text,
html.theme-dark .rc-slider-mark,
html.theme-dark .rc-slider-mark-text {
  color: #FFFFFF !important;
  fill: #FFFFFF !important;
  opacity: 1 !important;
}

.theme-dark #filter-panel .rc-slider-mark-text,
.theme-dark .risk-card .rc-slider-mark-text,
.theme-dark .risk-slider .rc-slider-mark-text {
  color: #FFFFFF !important;
  fill: #FFFFFF !important;
  opacity: 1 !important;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.45);
}

.theme-dark #gpa-range .rc-slider-mark-text,
.theme-dark #att-range .rc-slider-mark-text,
.theme-dark #gpa-threshold .rc-slider-mark-text,
.theme-dark #att-threshold .rc-slider-mark-text,
.theme-dark #gpa-range .rc-slider-mark-text-active,
.theme-dark #att-range .rc-slider-mark-text-active,
.theme-dark #gpa-threshold .rc-slider-mark-text-active,
.theme-dark #att-threshold .rc-slider-mark-text-active,
body.theme-dark #gpa-range .rc-slider-mark-text,
body.theme-dark #att-range .rc-slider-mark-text,
body.theme-dark #gpa-threshold .rc-slider-mark-text,
body.theme-dark #att-threshold .rc-slider-mark-text,
body.theme-dark #gpa-range .rc-slider-mark-text-active,
body.theme-dark #att-range .rc-slider-mark-text-active,
body.theme-dark #gpa-threshold .rc-slider-mark-text-active,
body.theme-dark #att-threshold .rc-slider-mark-text-active,
html.theme-dark #gpa-range .rc-slider-mark-text,
html.theme-dark #att-range .rc-slider-mark-text,
html.theme-dark #gpa-threshold .rc-slider-mark-text,
html.theme-dark #att-threshold .rc-slider-mark-text,
html.theme-dark #gpa-range .rc-slider-mark-text-active,
html.theme-dark #att-range .rc-slider-mark-text-active,
html.theme-dark #gpa-threshold .rc-slider-mark-text-active,
html.theme-dark #att-threshold .rc-slider-mark-text-active {
  color: #FFFFFF !important;
  fill: #FFFFFF !important;
  opacity: 1 !important;
  font-weight: 700 !important;
  -webkit-text-fill-color: #FFFFFF !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.45) !important;
}

.theme-dark .dash-slider-mark,
.theme-dark .dash-slider-mark-outside-selection,
body.theme-dark .dash-slider-mark,
body.theme-dark .dash-slider-mark-outside-selection,
html.theme-dark .dash-slider-mark,
html.theme-dark .dash-slider-mark-outside-selection {
  color: #FFFFFF !important;
  fill: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  opacity: 1 !important;
  font-weight: 700 !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.45) !important;
}

.theme-dark .att-range-tooltip-1-content,
body.theme-dark .att-range-tooltip-1-content,
html.theme-dark .att-range-tooltip-1-content {
  color: #000000 !important;
}

.theme-dark #att-range-tooltip-1-content,
body.theme-dark #att-range-tooltip-1-content,
html.theme-dark #att-range-tooltip-1-content {
  color: #000000 !important;
}

.theme-dark #gpa-threshold-tooltip-1-content,
body.theme-dark #gpa-threshold-tooltip-1-content,
html.theme-dark #gpa-threshold-tooltip-1-content,
.theme-dark #att-threshold-tooltip-1-content,
body.theme-dark #att-threshold-tooltip-1-content,
html.theme-dark #att-threshold-tooltip-1-content {
  color: #000000 !important;
}

.theme-dark #att-range-tooltip-2-content,
body.theme-dark #att-range-tooltip-2-content,
html.theme-dark #att-range-tooltip-2-content,
.theme-dark #gpa-range-tooltip-2-content,
body.theme-dark #gpa-range-tooltip-2-content,
html.theme-dark #gpa-range-tooltip-2-content,
.theme-dark #gpa-range-tooltip-1-content,
body.theme-dark #gpa-range-tooltip-1-content,
html.theme-dark #gpa-range-tooltip-1-content {
  color: #000000 !important;
}

.dash-options-list-option:hover .dash-options-list-option-text,
.dash-options-list-option-selected:hover .dash-options-list-option-text {
  color: #7A5AF8 !important;
}

.theme-dark .dash-options-list-option:hover .dash-options-list-option-text,
.theme-dark .dash-options-list-option-selected:hover .dash-options-list-option-text,
body.theme-dark .dash-options-list-option:hover .dash-options-list-option-text,
body.theme-dark .dash-options-list-option-selected:hover .dash-options-list-option-text,
html.theme-dark .dash-options-list-option:hover .dash-options-list-option-text,
html.theme-dark .dash-options-list-option-selected:hover .dash-options-list-option-text {
  color: #FF8FB1 !important;
}

.theme-dark .dash-dropdown-value,
body.theme-dark .dash-dropdown-value,
html.theme-dark .dash-dropdown-value {
  color: #2C1F2E !important;
  background: #EDE7F2 !important;
  border-color: rgba(140, 126, 150, 0.28) !important;
}

body.theme-dark .Select-control,
html.theme-dark .Select-control,
body.theme-dark .Select-menu-outer,
html.theme-dark .Select-menu-outer {
  background-color: #2A2234 !important;
  border-color: rgba(231, 214, 255, 0.35) !important;
}

body.theme-dark .Select-placeholder,
body.theme-dark .Select-value-label,
body.theme-dark .Select-input,
html.theme-dark .Select-placeholder,
html.theme-dark .Select-value-label,
html.theme-dark .Select-input {
  color: #F7F2FB !important;
}

body.theme-dark .Select-input input,
html.theme-dark .Select-input input {
  color: #F7F2FB !important;
  background: transparent !important;
}

.theme-dark .range-display {
  color: #F7F2FB;
  opacity: 0.95;
}

.theme-dark input[type="text"],
.theme-dark input[type="number"] {
  background: #2A2234 !important;
  color: #F7F2FB !important;
  border: 1px solid rgba(231, 214, 255, 0.35) !important;
}

.rc-slider-tooltip {
  display: none !important;
}

.range-display {
  margin-top: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  text-align: right;
}

@media (max-width: 900px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }

  .chart-card,
  .chart-span-4,
  .chart-span-5,
  .chart-span-6,
  .chart-span-7,
  .chart-span-8,
  .chart-span-12 {
    grid-column: span 1;
  }

  .control-panel {
    grid-template-columns: 1fr;
  }

  .risk-card {
    grid-column: span 1;
  }

  .span-2,
  .span-3,
  .span-4,
  .span-5,
  .span-6,
  .span-12 {
    grid-column: span 1;
  }
}
.objective-panel::after {
  content: "";
  position: absolute;
  right: -30px;
  top: -30px;
  width: 100px;
  height: 100px;
  background: radial-gradient(circle, rgba(189, 224, 254, 0.22), rgba(189, 224, 254, 0));
  filter: blur(6px);
}

.theme-dark .objective-panel {
  border-color: rgba(255, 255, 255, 0.12);
}

.theme-dark .objective-panel::after {
  background: radial-gradient(circle, rgba(123, 223, 242, 0.2), rgba(123, 223, 242, 0));
}

.objective-panel:hover {
  box-shadow: 0 18px 30px rgba(59, 46, 58, 0.14);
  border-color: rgba(255, 143, 177, 0.45);
}

"""

THEME_SYNC_JS = """
(() => {
  const syncTheme = () => {
    const root = document.getElementById("app-root");
    if (!root) {
      return false;
    }
    const isDark = root.classList.contains("theme-dark");
    document.body.classList.toggle("theme-dark", isDark);
    document.body.classList.toggle("theme-light", !isDark);
    document.documentElement.classList.toggle("theme-dark", isDark);
    document.documentElement.classList.toggle("theme-light", !isDark);
    return true;
  };

  const startObserver = () => {
    const root = document.getElementById("app-root");
    if (!root) {
      setTimeout(startObserver, 120);
      return;
    }
    const observer = new MutationObserver(syncTheme);
    observer.observe(root, { attributes: true, attributeFilter: ["class"] });
    syncTheme();
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startObserver);
  } else {
    startObserver();
  }
})();

"""

dash_app = Dash(__name__, assets_ignore='.*')
dash_app.index_string = f"""
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>Student Performance Intelligence</title>
        {{%favicon%}}
        {{%css%}}
        <style>{DASH_THEME_CSS}</style>
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
            <script>{THEME_SYNC_JS}</script>
        </footer>
    </body>
</html>
"""

dash_app.layout = html.Div(
    id="app-root",
    className="dash-root theme-light",
    children=[
        html.Div("Official (Closed), Non-Sensitive", className="page-classification"),
        html.Div(
            className="top-bar",
            children=[
                html.Div(
                    className="brand-block",
                    children=[
                        html.Img(src=logo_src, className="brand-logo"),
                        html.Div(
                            [
                                html.Div("Singapore Polytechnic", className="brand-title"),
                                html.Div("Student Performance Intelligence", className="brand-subtitle"),
                            ]
                        ),
                    ],
                ),
                html.Div(
                    className="top-actions",
                    children=[
                        dcc.Checklist(
                            id="theme-switch",
                            options=[{"label": "Dark mode", "value": "dark"}],
                            value=[],
                            className="theme-toggle",
                            labelStyle={"display": "flex", "alignItems": "center", "gap": "10px"},
                        ),
                        html.Button("Filters", id="filter-toggle", className="filter-toggle"),
                    ],
                ),
            ],
        ),
        html.Div(
            className="kpi-row",
            children=[
                html.Div(
                    className="kpi-card",
                    children=[
                        html.Div("Total Students", className="kpi-label"),
                        html.Div(base_display["total_value"], id="kpi-total-value", className="kpi-value"),
                        html.Div(base_display["total_delta"], id="kpi-total-delta", className=base_display["total_class"]),
                    ],
                ),
                html.Div(
                    className="kpi-card",
                    children=[
                        html.Div(
                            className="kpi-label-row",
                            children=[
                                html.Div("GPA (Mean)", id="kpi-gpa-label", className="kpi-label"),
                                dcc.Dropdown(
                                    id="gpa-kpi-stat",
                                    options=[
                                        {"label": "Mean", "value": "mean"},
                                        {"label": "Median", "value": "median"},
                                        {"label": "P10", "value": "p10"},
                                        {"label": "P90", "value": "p90"},
                                    ],
                                    value="mean",
                                    clearable=False,
                                    className="kpi-dropdown",
                                ),
                            ],
                        ),
                        html.Div(base_display["gpa_value"], id="kpi-gpa-value", className="kpi-value"),
                        html.Div(base_display["gpa_delta"], id="kpi-gpa-delta", className=base_display["gpa_class"]),
                    ],
                ),
                html.Div(
                    className="kpi-card",
                    children=[
                        html.Div(
                            className="kpi-label-row",
                            children=[
                                html.Div("Attendance (Mean)", id="kpi-att-label", className="kpi-label"),
                                dcc.Dropdown(
                                    id="att-kpi-stat",
                                    options=[
                                        {"label": "Mean", "value": "mean"},
                                        {"label": "Median", "value": "median"},
                                        {"label": "P10", "value": "p10"},
                                        {"label": "P90", "value": "p90"},
                                    ],
                                    value="mean",
                                    clearable=False,
                                    className="kpi-dropdown",
                                ),
                            ],
                        ),
                        html.Div(base_display["att_value"], id="kpi-att-value", className="kpi-value"),
                        html.Div(base_display["att_delta"], id="kpi-att-delta", className=base_display["att_class"]),
                    ],
                ),
                html.Div(
                    className="kpi-card",
                    children=[
                        html.Div(
                            className="kpi-label-row",
                            children=[
                                html.Div("High Risk (Percent)", id="kpi-risk-label", className="kpi-label"),
                                html.Div(
                                    className="kpi-dropdown-group",
                                    children=[
                                        dcc.Dropdown(
                                            id="risk-tier",
                                            options=[
                                                {"label": "High", "value": "High"},
                                                {"label": "Medium", "value": "Medium"},
                                                {"label": "Low", "value": "Low"},
                                            ],
                                            value="High",
                                            clearable=False,
                                            className="kpi-dropdown kpi-dropdown--small",
                                        ),
                                        dcc.Dropdown(
                                            id="risk-mode",
                                            options=[
                                                {"label": "%", "value": "percent"},
                                                {"label": "#", "value": "count"},
                                            ],
                                            value="percent",
                                            clearable=False,
                                            className="kpi-dropdown kpi-dropdown--tiny",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(base_display["risk_value"], id="kpi-risk-value", className="kpi-value"),
                        html.Div(base_display["risk_delta"], id="kpi-risk-delta", className=base_display["risk_class"]),
                    ],
                ),
            ],
        ),
        html.Div(
            className="objective-panel",
            children=[
                html.Div("Research Objective", className="objective-label"),
                html.Div(
                    "Understand how academic outcomes, engagement, and learning behaviours interact to identify at-risk cohorts and guide targeted support.",
                    className="objective-text",
                ),
            ],
        ),
        dcc.Store(id="filter-panel-state", data={"open": True}),
        dcc.Store(id="sunburst-filter", data={}),
        html.Div(
            id="filter-panel",
            className="filter-panel is-open",
            children=[
                html.Div(
                    className="filter-panel__header",
                    children=[
                        html.Div("Filters", className="filter-panel__title"),
                        html.Button("X", id="filter-close", className="filter-close"),
                    ],
                ),
                html.Div(
                    className="control-panel",
                    children=[
                        html.Div(
                            className="control-card filter-card compact span-3",
                            children=[
                                html.Label("Period"),
                                dcc.Checklist(
                                    id="period-filter",
                                    options=[{"label": p, "value": p} for p in period_options],
                                    value=period_options,
                                    className="filter-checklist",
                                ),
                            ],
                        ),
                        html.Div(
                            className="control-card filter-card compact span-3",
                            children=[
                                html.Label("Course level"),
                                dcc.Checklist(
                                    id="course-level-filter",
                                    options=[{"label": p, "value": p} for p in course_level_options],
                                    value=course_level_options,
                                    className="filter-checklist",
                                ),
                            ],
                        ),
                        html.Div(
                            className="control-card filter-card compact span-3",
                            children=[
                                html.Label("Funding"),
                                dcc.Checklist(
                                    id="funding-filter",
                                    options=[{"label": p, "value": p} for p in funding_options],
                                    value=funding_options,
                                    className="filter-checklist",
                                ),
                            ],
                        ),
                        html.Div(
                            className="control-card filter-card compact span-3",
                            children=[
                                html.Label("Highest Qualification"),
                                dcc.Checklist(
                                    id="qualification-filter",
                                    options=[{"label": p, "value": p} for p in highest_edu_options],
                                    value=highest_edu_options,
                                    className="filter-checklist",
                                ),
                            ],
                        ),
                        html.Div(
                            className="control-card filter-card wide course-card span-12",
                            children=[
                                html.Label("Course"),
                                dcc.Checklist(
                                    id="course-filter",
                                    options=[{"label": p, "value": p} for p in course_options],
                                    value=course_options,
                                    className="filter-checklist",
                                ),
                            ],
                        ),
                        html.Div(
                            className="control-card span-3",
                            children=[
                                html.Label("GPA range"),
                                dcc.RangeSlider(
                                    id="gpa-range",
                                    min=0.0,
                                    max=4.0,
                                    step=0.1,
                                    value=[gpa_min, gpa_max],
                                    marks={0: "0.0", 2: "2.0", 4: "4.0"},
                                    tooltip={"always_visible": False, "placement": "bottom", "format": {"specifier": ".1f"}},
                                ),
                                html.Div(id="gpa-range-display", className="range-display"),
                            ],
                        ),
                        html.Div(
                            className="control-card span-3",
                            children=[
                                html.Label("Attendance range (%)"),
                                dcc.RangeSlider(
                                    id="att-range",
                                    min=0.0,
                                    max=100.0,
                                    step=1.0,
                                    value=[att_min, att_max],
                                    marks={0: "0", 50: "50", 100: "100"},
                                    tooltip={"always_visible": False, "placement": "bottom", "format": {"specifier": ".0f"}},
                                ),
                                html.Div(id="att-range-display", className="range-display"),
                            ],
                        ),
                        html.Div(
                            className="control-card risk-card span-6",
                            children=[
                                html.Div("Risk Score Thresholds", className="risk-title"),
                                html.Div(
                                    "Adjust GPA and attendance cutoffs used in risk scoring.",
                                    className="risk-caption",
                                ),
                                html.Div(
                                    className="risk-sliders",
                                    children=[
                                        html.Div(
                                            className="risk-slider",
                                            children=[
                                                html.Label("GPA threshold"),
                                                dcc.Slider(
                                                    id="gpa-threshold",
                                                    min=0.0,
                                                    max=4.0,
                                                    step=0.1,
                                                    value=gpa_threshold_default,
                                                    marks={0: "0.0", 2: "2.0", 4: "4.0"},
                                                    tooltip={"always_visible": False, "placement": "bottom", "format": {"specifier": ".1f"}},
                                                ),
                                                html.Div(id="gpa-threshold-display", className="range-display"),
                                            ],
                                        ),
                                        html.Div(
                                            className="risk-slider",
                                            children=[
                                                html.Label("Attendance threshold (%)"),
                                                dcc.Slider(
                                                    id="att-threshold",
                                                    min=0.0,
                                                    max=100.0,
                                                    step=1.0,
                                                    value=att_threshold_default,
                                                    marks={0: "0", 50: "50", 100: "100"},
                                                    tooltip={"always_visible": False, "placement": "bottom", "format": {"specifier": ".0f"}},
                                                ),
                                                html.Div(id="att-threshold-display", className="range-display"),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        dcc.Tabs(
            id="dashboard-tabs",
            value="dash-1",
            className="dash-tabs",
            parent_className="dash-tabs-wrapper",
            children=[
                dcc.Tab(
                    label="Dashboard 1 - Risk Profile & Trend",
                    value="dash-1",
                    className="dash-tab",
                    selected_className="dash-tab--selected",
                    children=[
                        html.Div(
                            className="question-panel",
                            children=[
                                html.Div("Research Question - Dashboard 1 (Goh Kun Ming)", className="question-label"),
                                html.Div(
                                    "How do student background factors and semester trends in GPA and attendance reveal emerging risk patterns?",
                                    className="question-text",
                                ),
                            ],
                        ),
                        html.Div(className="chart-grid", children=[
                            html.Div(dcc.Graph(id="gpa-vs-att", figure=init_figs_1.get("gpa_vs_att", go.Figure()), config=dashboard_1_config), className="chart-card chart-span-7"),
                            html.Div(dcc.Graph(id="risk-quadrant", figure=init_figs_1.get("risk_quadrant", go.Figure()), config=dashboard_1_config), className="chart-card chart-span-5"),
                            html.Div(dcc.Graph(id="course-matrix", figure=init_figs_1.get("course_matrix", go.Figure()), config=dashboard_1_config), className="chart-card chart-span-12"),
                            html.Div(dcc.Graph(id="funding-level-matrix", figure=init_figs_1.get("funding_level_matrix", go.Figure()), config=dashboard_1_config), className="chart-card chart-span-6"),
                            html.Div(dcc.Graph(id="cohort-trend", figure=init_figs_1.get("cohort_trend", go.Figure()), config=dashboard_1_config), className="chart-card chart-span-6"),
                            html.Div(dcc.Graph(id="gpa-dist", figure=init_figs_1.get("gpa_dist", go.Figure()), config=dashboard_1_config), className="chart-card chart-span-6"),
                            html.Div(dcc.Graph(id="kpi-chart", figure=init_figs_1.get("kpi", go.Figure()), config=dashboard_1_config), className="chart-card chart-span-6"),
                        ]),
                    ],
                ),
                dcc.Tab(
                    label="Dashboard 2 - Survey Drivers & Intervention Prioritisation",
                    value="dash-2",
                    className="dash-tab",
                    selected_className="dash-tab--selected",
                    children=[
                        html.Div(
                            className="question-panel",
                            children=[
                                html.Div("Research Question - Dashboard 2 (Goh Jenson)", className="question-label"),
                                html.Div(
                                    "Which modifiable survey factors differentiate at-risk students, and what targeted interventions should be prioritised?",
                                    className="question-text",
                                ),
                            ],
                        ),
                        html.Div(
                            className="kpi-row kpi-row--survey",
                            children=[
                                html.Div(
                                    className="kpi-card",
                                    children=[
                                        html.Div("Avg Support Index (High Risk)", className="kpi-title"),
                                        html.Div(id="d2-support-value", className="kpi-value"),
                                        html.Div(id="d2-support-delta", className="kpi-delta"),
                                    ],
                                ),
                                html.Div(
                                    className="kpi-card",
                                    children=[
                                        html.Div("Avg Self-Study (High Risk)", className="kpi-title"),
                                        html.Div(id="d2-study-value", className="kpi-value"),
                                        html.Div(id="d2-study-delta", className="kpi-delta"),
                                    ],
                                ),
                                html.Div(
                                    className="kpi-card",
                                    children=[
                                        html.Div("Lowest Dimension (High Risk)", className="kpi-title"),
                                        html.Div(id="d2-lowest-dim", className="kpi-value"),
                                        html.Div(id="d2-lowest-value", className="kpi-delta"),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(className="chart-grid", children=[
                            html.Div(
                                className="chart-card chart-span-7",
                                children=[
                                    dcc.Graph(id="d2-heatmap", figure=init_figs_2.get("d2_heatmap", go.Figure()), config=dashboard_2_config),
                                ],
                            ),
                            html.Div(
                                className="chart-card chart-span-5",
                                children=[
                                    html.Div(
                                        className="chart-toolbar",
                                        children=[
                                            html.Div(
                                                className="chart-control",
                                                children=[
                                                    html.Div("X-Axis", className="chart-control__label"),
                                                    dcc.Dropdown(
                                                        id="d2-reg-x",
                                                        options=d2_reg_x_options,
                                                        value=d2_reg_x_options[0]["value"] if d2_reg_x_options else None,
                                                        clearable=False,
                                                        className="kpi-dropdown",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="chart-control",
                                                children=[
                                                    html.Div("Y-Axis", className="chart-control__label"),
                                                    dcc.Dropdown(
                                                        id="d2-reg-y",
                                                        options=d2_reg_y_options,
                                                        value=d2_reg_y_options[0]["value"] if d2_reg_y_options else None,
                                                        clearable=False,
                                                        className="kpi-dropdown kpi-dropdown--small",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    dcc.Graph(id="d2-bubble", figure=init_figs_2.get("d2_bubble", go.Figure()), config=dashboard_2_config),
                                ],
                            ),
                            html.Div(
                                className="chart-card chart-span-6",
                                children=[
                                    html.Div(
                                        className="chart-toolbar",
                                        children=[
                                            html.Div(
                                                className="chart-control",
                                                children=[
                                                    html.Div("Dimension", className="chart-control__label"),
                                                    dcc.Dropdown(
                                                        id="d2-likert-dim",
                                                        options=[{"label": col, "value": col} for col in likert_dim_options],
                                                        value=likert_dim_options[0] if likert_dim_options else None,
                                                        clearable=False,
                                                        className="kpi-dropdown kpi-dropdown--wide",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="chart-control",
                                                children=[
                                                    html.Div("Metric", className="chart-control__label"),
                                                    dcc.Dropdown(
                                                        id="d2-likert-mode",
                                                        options=likert_mode_options,
                                                        value="Percent",
                                                        clearable=False,
                                                        className="kpi-dropdown kpi-dropdown--small",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    dcc.Graph(id="d2-likert", figure=init_figs_2.get("d2_likert", go.Figure()), config=dashboard_2_config),
                                ],
                            ),
                            html.Div(
                                className="chart-card chart-span-6",
                                children=[
                                    html.Div(
                                        className="chart-toolbar",
                                        children=[
                                            html.Div(
                                                className="chart-control",
                                                children=[
                                                    html.Div("Metric", className="chart-control__label"),
                                                    dcc.Dropdown(
                                                        id="d2-study-toggle",
                                                        options=d2_study_toggle_options,
                                                        value="study",
                                                        clearable=False,
                                                        className="kpi-dropdown kpi-dropdown--wide",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    dcc.Graph(id="d2-self-study", figure=init_figs_2.get("d2_self_study", go.Figure()), config=dashboard_2_config),
                                ],
                            ),
                            html.Div(
                                className="chart-card chart-span-6",
                                children=[
                                    dcc.Graph(id="d2-quadrant", figure=init_figs_2.get("d2_quadrant", go.Figure()), config=dashboard_2_config),
                                ],
                            ),
                            html.Div(
                                className="chart-card chart-span-6",
                                children=[
                                    html.Div(
                                        className="chart-toolbar",
                                        children=[
                                            html.Div(
                                                className="chart-control",
                                                children=[
                                                    html.Div("Profile", className="chart-control__label"),
                                                    dcc.Dropdown(
                                                        id="d2-radar-toggle",
                                                        options=d2_radar_toggle_options,
                                                        value="without",
                                                        clearable=False,
                                                        className="kpi-dropdown kpi-dropdown--wide",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    dcc.Graph(id="d2-radar", figure=init_figs_2.get("d2_radar", go.Figure()), config=dashboard_2_config),
                                ],
                            ),
                            html.Div(
                                className="chart-card chart-span-12",
                                children=[
                                    dcc.Graph(id="d2-corr", figure=init_figs_2.get("d2_corr", go.Figure()), config=dashboard_2_config),
                                ],
                            ),
                            html.Div(
                                className="chart-card chart-span-12",
                                children=[
                                    html.Div(
                                        className="chart-toolbar",
                                        children=[
                                            html.Div(
                                                className="chart-control",
                                                children=[
                                                    html.Div("Risk Level", className="chart-control__label"),
                                                    dcc.Dropdown(
                                                        id="d2-gap-risk",
                                                        options=d2_gap_risk_options,
                                                        value="High",
                                                        clearable=False,
                                                        className="kpi-dropdown kpi-dropdown--small",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="chart-control",
                                                children=[
                                                    html.Div("Measure", className="chart-control__label"),
                                                    dcc.Dropdown(
                                                        id="d2-gap-measure",
                                                        options=d2_gap_measure_options,
                                                        value="mean",
                                                        clearable=False,
                                                        className="kpi-dropdown kpi-dropdown--small",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="chart-slider",
                                        children=[
                                            html.Div(f"Top N: Top {d2_gap_topn_default}", id="d2-gap-topn-label", className="gap-slider-label"),
                                            dcc.Slider(
                                                id="d2-gap-topn",
                                                min=1,
                                                max=d2_gap_topn_max,
                                                step=1,
                                                value=d2_gap_topn_default,
                                                marks={n: f"Top {n}" for n in range(1, d2_gap_topn_max + 1)},
                                                className="gap-slider",
                                            ),
                                        ],
                                    ),
                                    dcc.Graph(id="d2-gap", figure=init_figs_2.get("d2_gap", go.Figure()), config=dashboard_2_config),
                                ],
                            ),
                        ]),
                    ],
                ),
            ],
        ),
    ],
)


@dash_app.callback(
    Output("filter-panel-state", "data"),
    Input("filter-toggle", "n_clicks"),
    Input("filter-close", "n_clicks"),
    State("filter-panel-state", "data"),
    prevent_initial_call=True,
)
def _toggle_filter_panel(open_clicks, close_clicks, state):
    current = state or {"open": True}
    ctx = dash.callback_context
    if not ctx.triggered:
        return current
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger == "filter-toggle":
        return {"open": not current.get("open", True)}
    if trigger == "filter-close":
        return {"open": False}
    return current


@dash_app.callback(
    Output("filter-panel", "className"),
    Input("filter-panel-state", "data"),
)
def _render_filter_panel(state):
    is_open = True
    if isinstance(state, dict):
        is_open = state.get("open", True)
    return "filter-panel is-open" if is_open else "filter-panel"


@dash_app.callback(
    Output("sunburst-filter", "data"),
    Input("risk-quadrant", "clickData"),
    State("sunburst-filter", "data"),
    prevent_initial_call=True,
)
def _update_sunburst_filter(click_data, current):
    if not click_data or "points" not in click_data:
        return current or {}
    point = click_data["points"][0]
    custom = point.get("customdata") or []
    meta = point.get("data", {}).get("meta")

    # Prefer the path metadata attached to the sunburst trace.
    if isinstance(meta, (list, tuple)) and meta:
        path_cols = list(meta)
    else:
        tmp = dash_df.copy()
        tmp, res_col = _attach_residency(tmp)
        tmp, mode_col = _attach_mode(tmp)
        tmp, gender_col = _attach_gender(tmp)
        level_col = COURSE_LEVEL_COL if COURSE_LEVEL_COL in tmp.columns else (course_col if course_col in tmp.columns else None)

        path_cols = [RISK_TIER_COL]
        if level_col:
            path_cols.append(level_col)
        if mode_col:
            path_cols.append(mode_col)
        elif gender_col:
            path_cols.append(gender_col)
        if res_col:
            path_cols.append(res_col)

    filters = {}
    for idx, col in enumerate(path_cols):
        if idx < len(custom):
            val = custom[idx]
            if val and str(val).strip() not in ["Unknown", "None", "nan"]:
                filters[col] = str(val)

    selection_id = point.get("id") or "|".join([filters.get(col, "") for col in path_cols])
    if isinstance(current, dict) and current.get("id") == selection_id:
        return {}
    return {"id": selection_id, "filters": filters}


def _apply_sunburst_filters(df, sunburst_filter, gpa_thr, att_thr):
    if not isinstance(sunburst_filter, dict) or not sunburst_filter.get("filters"):
        return df
    filters = sunburst_filter.get("filters", {})
    out = df.copy()
    if RISK_TIER_COL in filters:
        out = _apply_dynamic_risk(out, gpa_thr, att_thr)
    needs_res = "_residency" in filters
    needs_mode = "_study_mode" in filters
    needs_gender = "_gender" in filters
    if needs_res:
        out, _ = _attach_residency(out)
    if needs_mode:
        out, _ = _attach_mode(out)
    if needs_gender:
        out, _ = _attach_gender(out)
    for col_key, value in filters.items():
        if col_key in out.columns:
            out = out[out[col_key].astype("string") == str(value)]
    return out


@dash_app.callback(
    Output("app-root", "className"),
    Input("theme-switch", "value"),
)
def _switch_theme(value):
    if isinstance(value, (list, tuple)) and "dark" in value:
        return "dash-root theme-dark"
    return "dash-root theme-light"


@dash_app.callback(
    [
        Output("kpi-total-value", "children"),
        Output("kpi-total-delta", "children"),
        Output("kpi-total-delta", "className"),
        Output("kpi-gpa-value", "children"),
        Output("kpi-gpa-delta", "children"),
        Output("kpi-gpa-delta", "className"),
        Output("kpi-gpa-label", "children"),
        Output("kpi-att-value", "children"),
        Output("kpi-att-delta", "children"),
        Output("kpi-att-delta", "className"),
        Output("kpi-att-label", "children"),
        Output("kpi-risk-value", "children"),
        Output("kpi-risk-delta", "children"),
        Output("kpi-risk-delta", "className"),
        Output("kpi-risk-label", "children"),
        Output("gpa-range-display", "children"),
        Output("att-range-display", "children"),
        Output("gpa-threshold-display", "children"),
        Output("att-threshold-display", "children"),
        Output("kpi-chart", "figure"),
        Output("gpa-vs-att", "figure"),
        Output("risk-quadrant", "figure"),
        Output("funding-level-matrix", "figure"),
        Output("gpa-dist", "figure"),
        Output("course-matrix", "figure"),
        Output("cohort-trend", "figure"),
        Output("d2-support-value", "children"),
        Output("d2-support-delta", "children"),
        Output("d2-support-delta", "className"),
        Output("d2-study-value", "children"),
        Output("d2-study-delta", "children"),
        Output("d2-study-delta", "className"),
        Output("d2-lowest-dim", "children"),
        Output("d2-lowest-value", "children"),
        Output("d2-gap-topn-label", "children"),
        Output("d2-heatmap", "figure"),
        Output("d2-likert", "figure"),
        Output("d2-self-study", "figure"),
        Output("d2-bubble", "figure"),
        Output("d2-quadrant", "figure"),
        Output("d2-radar", "figure"),
        Output("d2-corr", "figure"),
        Output("d2-gap", "figure"),
    ],
    [
        Input("period-filter", "value"),
        Input("course-level-filter", "value"),
        Input("course-filter", "value"),
        Input("funding-filter", "value"),
        Input("qualification-filter", "value"),
        Input("gpa-range", "value"),
        Input("att-range", "value"),
        Input("gpa-threshold", "value"),
        Input("att-threshold", "value"),
        Input("gpa-kpi-stat", "value"),
        Input("att-kpi-stat", "value"),
        Input("risk-tier", "value"),
        Input("risk-mode", "value"),
        Input("d2-likert-dim", "value"),
        Input("d2-likert-mode", "value"),
        Input("d2-reg-x", "value"),
        Input("d2-reg-y", "value"),
        Input("d2-study-toggle", "value"),
        Input("d2-radar-toggle", "value"),
        Input("d2-gap-risk", "value"),
        Input("d2-gap-measure", "value"),
        Input("d2-gap-topn", "value"),
        Input("sunburst-filter", "data"),
        Input("theme-switch", "value"),
    ],
)

def _update_dash(
    period,
    course_level,
    course_name,
    funding,
    qualification,
    gpa_range,
    att_range,
    gpa_thr,
    att_thr,
    gpa_stat,
    att_stat,
    risk_tier,
    risk_mode,
    d2_likert_dim,
    d2_likert_mode,
    d2_reg_x,
    d2_reg_y,
    d2_study_toggle,
    d2_radar_toggle,
    d2_gap_risk,
    d2_gap_measure,
    d2_gap_topn,
    sunburst_filter,
    theme_value,
):
    theme = "dark" if isinstance(theme_value, (list, tuple)) and "dark" in theme_value else "light"
    gpa_thr = gpa_threshold_default if gpa_thr is None else float(gpa_thr)
    att_thr = att_threshold_default if att_thr is None else float(att_thr)
    filtered_df = _apply_filters(
        dash_df,
        period,
        course_level,
        course_name,
        funding,
        qualification,
        gpa_range,
        att_range,
    )
    filtered_df = _apply_sunburst_filters(filtered_df, sunburst_filter, gpa_thr, att_thr)

    hotspot_df = _apply_filters(
        dash_df,
        period,
        None,
        None,
        funding,
        qualification,
        gpa_range,
        att_range,
    )
    hotspot_df = _apply_sunburst_filters(hotspot_df, sunburst_filter, gpa_thr, att_thr)

    sunburst_df = _apply_filters(
        dash_df,
        None,
        None,
        None,
        None,
        None,
        gpa_range,
        att_range,
    )
    total_override = None
    if GPA_COL in filtered_df.columns and ATTEND_COL in filtered_df.columns:
        total_override = int(filtered_df[[GPA_COL, ATTEND_COL]].dropna().shape[0])

    filters_active = _filters_active(
        period,
        course_level,
        course_name,
        funding,
        qualification,
        gpa_range,
        att_range,
    )
    gpa_stat = gpa_stat or "mean"
    att_stat = att_stat or "mean"
    risk_tier = risk_tier or "High"
    risk_mode = risk_mode or "percent"

    base_kpis_dynamic = _compute_kpis(
        dash_df,
        gpa_thr,
        att_thr,
        use_latest_gpa=True,
        gpa_stat=gpa_stat,
        att_stat=att_stat,
        risk_tier=risk_tier,
    )
    current_kpis = _compute_kpis(
        filtered_df,
        gpa_thr,
        att_thr,
        use_latest_gpa=not filters_active,
        gpa_stat=gpa_stat,
        att_stat=att_stat,
        risk_tier=risk_tier,
    )
    display = _build_kpi_display(current_kpis, base_kpis_dynamic, risk_tier=risk_tier, risk_mode=risk_mode)
    survey_kpis = _compute_survey_kpis(filtered_df, gpa_thr, att_thr)
    support_delta_text, support_delta_class = survey_kpis["support_delta"]
    study_delta_text, study_delta_class = survey_kpis["study_delta"]
    gap_label_value = int(d2_gap_topn) if d2_gap_topn else d2_gap_topn_default
    gap_label = f"Top N: Top {gap_label_value}"

    gpa_range_display = "N.A."
    if isinstance(gpa_range, (list, tuple)) and len(gpa_range) == 2:
        gpa_range_display = f"{float(gpa_range[0]):.1f} - {float(gpa_range[1]):.1f}"

    att_range_display = "N.A."
    if isinstance(att_range, (list, tuple)) and len(att_range) == 2:
        att_range_display = f"{int(round(att_range[0]))} - {int(round(att_range[1]))}"

    gpa_thr_display = "N.A."
    if gpa_thr is not None:
        gpa_thr_display = f"{float(gpa_thr):.1f}"

    att_thr_display = "N.A."
    if att_thr is not None:
        att_thr_display = f"{int(round(att_thr))}"

    label_map = {
        "mean": "Mean",
        "median": "Median",
        "p10": "P10",
        "p90": "P90",
    }
    gpa_label = f"GPA ({label_map.get(gpa_stat, 'Mean')})"
    att_label = f"Attendance ({label_map.get(att_stat, 'Mean')})"
    risk_label = f"{str(risk_tier).title()} Risk ({'%' if risk_mode == 'percent' else 'Count'})"

    figs_1 = make_dashboard_1_figures(
        filtered_df,
        top_n=12,
        gpa_threshold=float(gpa_thr),
        att_threshold=float(att_thr),
        total_override=total_override,
        hotspot_df=hotspot_df,
        sunburst_df=sunburst_df,
        theme=theme,
    )
    figs_2 = make_dashboard_2_figures(
        filtered_df,
        gpa_thr,
        att_thr,
        theme=theme,
        likert_dim=d2_likert_dim,
        likert_mode=d2_likert_mode,
        reg_x=d2_reg_x,
        reg_y=d2_reg_y,
        study_toggle=d2_study_toggle,
        radar_toggle=d2_radar_toggle,
        gap_risk=d2_gap_risk,
        gap_measure=d2_gap_measure,
        gap_topn=d2_gap_topn,
    )
    figs_2 = {key: _apply_plotly_theme(fig, theme) for key, fig in figs_2.items()}

    return (
        display["total_value"],
        display["total_delta"],
        display["total_class"],
        display["gpa_value"],
        display["gpa_delta"],
        display["gpa_class"],
        gpa_label,
        display["att_value"],
        display["att_delta"],
        display["att_class"],
        att_label,
        display["risk_value"],
        display["risk_delta"],
        display["risk_class"],
        risk_label,
        gpa_range_display,
        att_range_display,
        gpa_thr_display,
        att_thr_display,
        figs_1.get("kpi", go.Figure()),
        figs_1.get("gpa_vs_att", go.Figure()),
        figs_1.get("risk_quadrant", go.Figure()),
        figs_1.get("funding_level_matrix", go.Figure()),
        figs_1.get("gpa_dist", go.Figure()),
        figs_1.get("course_matrix", go.Figure()),
        figs_1.get("cohort_trend", go.Figure()),
        survey_kpis["support_high"],
        support_delta_text,
        support_delta_class,
        survey_kpis["study_high"],
        study_delta_text,
        study_delta_class,
        survey_kpis["lowest_dim"],
        survey_kpis["lowest_value"],
        gap_label,
        figs_2.get("d2_heatmap", go.Figure()),
        figs_2.get("d2_likert", go.Figure()),
        figs_2.get("d2_self_study", go.Figure()),
        figs_2.get("d2_bubble", go.Figure()),
        figs_2.get("d2_quadrant", go.Figure()),
        figs_2.get("d2_radar", go.Figure()),
        figs_2.get("d2_corr", go.Figure()),
        figs_2.get("d2_gap", go.Figure()),
    )

# Expose WSGI server for gunicorn.
server = dash_app.server


@server.route("/healthz")
def healthz():
    """Lightweight health endpoint for Render checks."""
    return "ok", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8050"))
    dash_app.run(host="0.0.0.0", port=port, debug=False)

