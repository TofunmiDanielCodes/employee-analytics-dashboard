
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Employee Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>
.main {
    background-color: #0E1117;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

.metric-card {
    background: linear-gradient(135deg, #111827, #1F2937);
    padding: 18px;
    border-radius: 18px;
    border: 1px solid #374151;
}

h1, h2, h3 {
    font-weight: 700 !important;
}

[data-testid="stSidebar"] {
    background-color: #111827;
}

div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #111827, #1F2937);
    border: 1px solid #374151;
    padding: 15px;
    border-radius: 18px;
}

.plot-container > div {
    border-radius: 16px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("employee_data.xlsx")
    except:
        uploaded = st.file_uploader(
            "Upload employee_data.xlsx",
            type=["xlsx"]
        )

        if uploaded is None:
            st.warning("Please upload your employee dataset.")
            st.stop()

        df = pd.read_excel(uploaded)

    # ---------- CLEANING ----------
    df.columns = df.columns.str.strip().str.lower()

    # Strip spaces
    obj_cols = df.select_dtypes(include="object").columns
    for col in obj_cols:
        df[col] = df[col].astype(str).str.strip()

    # Dates
    if "date_of_birth" in df.columns:
        df["date_of_birth"] = pd.to_datetime(
            df["date_of_birth"],
            errors="coerce"
        )

    if "hire_date" in df.columns:
        df["hire_date"] = pd.to_datetime(
            df["hire_date"],
            errors="coerce"
        )

    # Missing IDs
    if "employee_id" in df.columns:
        mask = df["employee_id"].isna()
        generated = [
            f"EMP-{i+1:03d}" for i in range(mask.sum())
        ]
        df.loc[mask, "employee_id"] = generated

    # Salary cleanup
    if "salary" in df.columns:
        df["salary"] = pd.to_numeric(
            df["salary"],
            errors="coerce"
        )

        if "department" in df.columns:
            df["salary"] = (
                df.groupby("department")["salary"]
                .transform(lambda x: x.fillna(x.median()))
            )

    # Age + Tenure
    today = pd.Timestamp.today()

    if "date_of_birth" in df.columns:
        df["age"] = (
            (today - df["date_of_birth"]).dt.days / 365.25
        ).round(1)

    if "hire_date" in df.columns:
        df["tenure_years"] = (
            (today - df["hire_date"]).dt.days / 365.25
        ).round(1)

    # Gender grouping
    if "gender" in df.columns:
        df["gender_group"] = df["gender"].apply(
            lambda x:
            x if x in ["Male", "Female"]
            else "Other"
        )

    return df


df = load_data()

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("⚡ Employee Analytics")

departments = (
    sorted(df["department"].dropna().unique())
    if "department" in df.columns
    else []
)

genders = (
    sorted(df["gender_group"].dropna().unique())
    if "gender_group" in df.columns
    else []
)

selected_departments = st.sidebar.multiselect(
    "Department",
    departments,
    default=departments
)

selected_genders = st.sidebar.multiselect(
    "Gender",
    genders,
    default=genders
)

# FILTERING
filtered = df.copy()

if "department" in filtered.columns:
    filtered = filtered[
        filtered["department"].isin(selected_departments)
    ]

if "gender_group" in filtered.columns:
    filtered = filtered[
        filtered["gender_group"].isin(selected_genders)
    ]

# =========================================================
# HEADER
# =========================================================
st.title("🏢 Employee Analytics Intelligence Hub")
st.caption(
    "Advanced workforce analytics built with Streamlit + Plotly"
)

# =========================================================
# KPIs
# =========================================================
total_employees = len(filtered)

avg_salary = (
    filtered["salary"].mean()
    if "salary" in filtered.columns
    else 0
)

avg_age = (
    filtered["age"].mean()
    if "age" in filtered.columns
    else 0
)

avg_tenure = (
    filtered["tenure_years"].mean()
    if "tenure_years" in filtered.columns
    else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "👥 Total Employees",
    f"{total_employees:,}"
)

col2.metric(
    "💰 Avg Salary",
    f"${avg_salary:,.0f}"
)

col3.metric(
    "🎂 Avg Age",
    f"{avg_age:.1f} yrs"
)

col4.metric(
    "🕒 Avg Tenure",
    f"{avg_tenure:.1f} yrs"
)

st.divider()

# =========================================================
# ROW 1
# =========================================================
c1, c2 = st.columns([1.2, 1])

# ---------- SALARY BY DEPARTMENT ----------
with c1:

    st.subheader("💸 Salary Distribution by Department")

    dept_salary = (
        filtered.groupby("department")["salary"]
        .median()
        .sort_values(ascending=True)
        .reset_index()
    )

    fig = px.bar(
        dept_salary,
        x="salary",
        y="department",
        orientation="h",
        text_auto=".2s",
        color="salary",
        color_continuous_scale="Blues"
    )

    fig.update_layout(
        height=500,
        template="plotly_dark",
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ---------- GENDER DISTRIBUTION ----------
with c2:

    st.subheader("🧑‍🤝‍🧑 Gender Representation")

    gender_counts = (
        filtered["gender_group"]
        .value_counts()
        .reset_index()
    )

    gender_counts.columns = [
        "gender_group",
        "count"
    ]

    fig2 = px.pie(
        gender_counts,
        names="gender_group",
        values="count",
        hole=0.6
    )

    fig2.update_layout(
        height=500,
        template="plotly_dark"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

# =========================================================
# ROW 2
# =========================================================
c3, c4 = st.columns(2)

# ---------- AGE DISTRIBUTION ----------
with c3:

    st.subheader("📈 Employee Age Distribution")

    fig3 = px.histogram(
        filtered,
        x="age",
        nbins=25,
        color_discrete_sequence=["#60A5FA"]
    )

    fig3.add_vline(
        x=filtered["age"].mean(),
        line_dash="dash",
        annotation_text="Average Age"
    )

    fig3.update_layout(
        height=450,
        template="plotly_dark"
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

# ---------- TENURE ----------
with c4:

    st.subheader("🏆 Tenure by Department")

    fig4 = px.box(
        filtered,
        x="tenure_years",
        y="department",
        color="department"
    )

    fig4.update_layout(
        height=450,
        template="plotly_dark",
        showlegend=False
    )

    st.plotly_chart(
        fig4,
        use_container_width=True
    )

# =========================================================
# ROW 3
# =========================================================
st.subheader("📊 Salary vs Tenure Analysis")

scatter = px.scatter(
    filtered,
    x="tenure_years",
    y="salary",
    color="gender_group",
    size="age",
    hover_data=[
        "department",
        "job_title"
    ] if "job_title" in filtered.columns else None,
    trendline="ols"
)

scatter.update_layout(
    height=600,
    template="plotly_dark"
)

st.plotly_chart(
    scatter,
    use_container_width=True
)

# =========================================================
# PAY GAP ANALYSIS
# =========================================================
if (
    "gender_group" in filtered.columns and
    "salary" in filtered.columns
):

    st.subheader("⚖️ Gender Pay Gap Analysis")

    pay_gap = (
        filtered[
            filtered["gender_group"].isin(
                ["Male", "Female"]
            )
        ]
        .groupby(
            ["department", "gender_group"]
        )["salary"]
        .mean()
        .unstack()
    )

    if (
        "Male" in pay_gap.columns and
        "Female" in pay_gap.columns
    ):

        pay_gap["gap_pct"] = (
            (
                pay_gap["Male"] -
                pay_gap["Female"]
            )
            / pay_gap["Female"]
        ) * 100

        pay_gap = (
            pay_gap["gap_pct"]
            .sort_values()
            .reset_index()
        )

        fig5 = px.bar(
            pay_gap,
            x="gap_pct",
            y="department",
            orientation="h",
            color="gap_pct",
            color_continuous_scale="RdBu"
        )

        fig5.update_layout(
            height=500,
            template="plotly_dark"
        )

        st.plotly_chart(
            fig5,
            use_container_width=True
        )

# =========================================================
# DATA TABLE
# =========================================================
with st.expander("🗂️ View Cleaned Dataset"):

    st.dataframe(
        filtered,
        use_container_width=True,
        height=450
    )

# =========================================================
# DOWNLOAD
# =========================================================
csv = filtered.to_csv(index=False)

st.download_button(
    label="⬇️ Download Cleaned Dataset",
    data=csv,
    file_name="employee_data_cleaned.csv",
    mime="text/csv"
)

# =========================================================
# FOOTER
# =========================================================
st.divider()

st.caption(
    "Built by Oluwatofunmi IshoLaDaniel • Streamlit • Plotly"
)
