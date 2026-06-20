"""
🏢 Employee Analytics Dashboard
Run: streamlit run emp_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page Config ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Employee Analytics",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0F1117; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #161B27; border-right: 1px solid #2A2F45; }

    /* KPI cards */
    .kpi-card {
        background: linear-gradient(135deg, #1A1F35 0%, #232946 100%);
        border: 1px solid #2E3555;
        border-radius: 12px;
        padding: 20px 22px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .kpi-label { color: #8892A4; font-size: 12px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }
    .kpi-value { color: #EAEAEA; font-size: 28px; font-weight: 800; line-height: 1; }
    .kpi-sub   { color: #5B9BD5; font-size: 12px; margin-top: 5px; }

    /* Section headers */
    .section-header {
        color: #EAEAEA;
        font-size: 17px;
        font-weight: 700;
        border-left: 4px solid #5B9BD5;
        padding-left: 12px;
        margin: 8px 0 16px 0;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] { background-color: #161B27; border-radius: 10px; padding: 4px; gap: 4px; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; color: #8892A4; border-radius: 8px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #5B9BD5 !important; color: white !important; }

    /* Divider */
    hr { border-color: #2A2F45; }

    /* Dataframe */
    .stDataFrame { border-radius: 10px; overflow: hidden; }

    /* Metric delta */
    [data-testid="metric-container"] { background: #1A1F35; border-radius: 10px; padding: 10px 16px; border: 1px solid #2E3555; }
</style>
""", unsafe_allow_html=True)

# ── Colour palette (Plotly) ──────────────────────────────────────────────────────
BLUE      = "#5B9BD5"
AMBER     = "#F4A732"
GREEN     = "#4CAF82"
RED       = "#E05C5C"
PURPLE    = "#9B72CF"
TEAL      = "#3EC9C9"
DARK_BG   = "#0F1117"
CARD_BG   = "#1A1F35"
GRID      = "#2A2F45"
TEXT      = "#EAEAEA"
MUTED     = "#8892A4"

PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(color=TEXT, family="Inter, sans-serif"),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=GRID),
        colorway=[BLUE, AMBER, GREEN, RED, PURPLE, TEAL, "#FF9DA6", "#B8860B"],
        margin=dict(t=40, b=30, l=10, r=10),
    )
)

DEPT_COLORS = {
    "Accounting": BLUE, "Business Development": AMBER, "Engineering": GREEN,
    "Human Resources": RED, "Legal": PURPLE, "Marketing": TEAL,
    "Product Management": "#FF9DA6", "Research and Development": "#B8860B",
    "Sales": "#66C2A5", "Services": "#FC8D62", "Support": "#8DA0CB", "Training": "#E78AC3",
}

# ── Data loader ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel("employee_data.xlsx")

    # ── Dates
    df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], errors="coerce")
    df["hire_date"]     = pd.to_datetime(df["hire_date"],     errors="coerce")

    # ── Derived
    today = pd.Timestamp("today")
    df["age"]          = ((today - df["date_of_birth"]).dt.days / 365.25).fillna(0).astype(int)
    df["tenure_years"] = ((today - df["hire_date"]).dt.days / 365.25).round(1)
    df["hire_year"]    = df["hire_date"].dt.year

    # ── Gender grouping
    binary = {"Male", "Female"}
    df["gender_group"] = df["gender"].apply(
        lambda g: g if g in binary else "Non-Binary / Diverse"
    )

    # ── Missing salary → department median
    df["salary"] = df["salary"].fillna(df.groupby("department")["salary"].transform("median"))

    # ── Missing / duplicate employee_id
    null_mask = df["employee_id"].isnull()
    df.loc[null_mask, "employee_id"] = [f"SURR-{9000+i}" for i in range(null_mask.sum())]
    dup = df.duplicated(subset="employee_id", keep="first")
    df.loc[dup, "employee_id"] = (
        df.loc[dup, "employee_id"] + "-DUP-" +
        df[dup].groupby("employee_id").cumcount().add(1).astype(str)
    )

    # ── Age band
    df["age_band"] = pd.cut(
        df["age"], bins=[0,30,40,50,55,65,100],
        labels=["<30","30–39","40–49","50–54","55–64","65+"]
    )

    # ── Tenure band
    df["tenure_band"] = pd.cut(
        df["tenure_years"], bins=[0,2,5,10,15,20,100],
        labels=["0–2 yrs","3–5 yrs","6–10 yrs","11–15 yrs","16–20 yrs","20+ yrs"]
    )

    # ── Salary tier
    p33, p66 = df["salary"].quantile(0.33), df["salary"].quantile(0.66)
    df["salary_tier"] = pd.cut(
        df["salary"], bins=[0, p33, p66, df["salary"].max()+1],
        labels=["Lower Third", "Middle Third", "Top Third"]
    )

    return df

df_full = load_data()

# ── Sidebar ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏢 Employee Analytics")
    st.markdown("---")
    st.markdown("### 🎚️ Filters")

    departments = st.multiselect(
        "Department",
        options=sorted(df_full["department"].dropna().unique()),
        default=sorted(df_full["department"].dropna().unique()),
    )

    gender_opts = ["Male", "Female", "Non-Binary / Diverse"]
    genders = st.multiselect("Gender Group", gender_opts, default=gender_opts)

    salary_range = st.slider(
        "Salary Range ($)",
        min_value=int(df_full["salary"].min()),
        max_value=int(df_full["salary"].max()),
        value=(int(df_full["salary"].min()), int(df_full["salary"].max())),
        step=1000,
        format="$%d",
    )

    hire_years = sorted(df_full["hire_year"].dropna().unique().tolist())
    year_range = st.select_slider(
        "Hire Year Range",
        options=hire_years,
        value=(hire_years[0], hire_years[-1]),
    )

    st.markdown("---")
    st.markdown(f"<span style='color:{MUTED};font-size:12px'>1,000 employees · 12 departments</span>", unsafe_allow_html=True)

# ── Filter dataframe ─────────────────────────────────────────────────────────────
df = df_full[
    df_full["department"].isin(departments) &
    df_full["gender_group"].isin(genders) &
    df_full["salary"].between(salary_range[0], salary_range[1]) &
    df_full["hire_year"].between(year_range[0], year_range[1])
].copy()

# ── Header ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 24px 0 8px 0;'>
  <span style='color:#5B9BD5; font-size:13px; font-weight:700; letter-spacing:2px; text-transform:uppercase;'>HR Intelligence</span>
  <h1 style='color:#EAEAEA; font-size:32px; font-weight:900; margin:4px 0 0 0; line-height:1;'>Employee Analytics Dashboard</h1>
  <p style='color:#8892A4; margin:6px 0 0 0; font-size:14px;'>Workforce insights · Compensation · Diversity · Retention</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── KPI Row ──────────────────────────────────────────────────────────────────────
total      = len(df)
avg_sal    = df["salary"].mean()
median_sal = df["salary"].median()
avg_age    = df["age"].mean()
avg_tenure = df["tenure_years"].mean()
ret_risk   = len(df[df["age"] >= 55])
ret_pct    = ret_risk / total * 100 if total else 0
pay_gap    = ((df[df["gender_group"]=="Male"]["salary"].mean() -
               df[df["gender_group"]=="Female"]["salary"].mean()) /
              df[df["gender_group"]=="Male"]["salary"].mean() * 100) if total else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)

def kpi(col, label, value, sub=""):
    col.markdown(f"""
    <div class='kpi-card'>
      <div class='kpi-label'>{label}</div>
      <div class='kpi-value'>{value}</div>
      <div class='kpi-sub'>{sub}</div>
    </div>""", unsafe_allow_html=True)

kpi(c1, "Total Employees",    f"{total:,}",           f"{len(departments)} departments")
kpi(c2, "Avg Salary",         f"${avg_sal:,.0f}",     f"Median ${median_sal:,.0f}")
kpi(c3, "Avg Age",            f"{avg_age:.1f} yrs",   "Workforce average")
kpi(c4, "Avg Tenure",         f"{avg_tenure:.1f} yrs","Company loyalty")
kpi(c5, "Retirement Risk",    f"{ret_risk:,}",        f"{ret_pct:.1f}% aged 55+")
kpi(c6, "Gender Pay Gap",     f"{abs(pay_gap):.1f}%", "Male vs Female avg")

st.markdown("<br>", unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💰 Compensation",
    "⚖️ Diversity & Pay Equity",
    "👥 Workforce Profile",
    "📈 Hiring Trends",
    "🔎 Employee Explorer",
])

# ════════════════════════════════════════════════════════════════════
# TAB 1 — COMPENSATION
# ════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("<div class='section-header'>Salary Distribution Across the Organisation</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 1])

    # Histogram
    with col_a:
        fig = px.histogram(
            df, x="salary", nbins=40, color_discrete_sequence=[BLUE],
            title="Overall Salary Distribution",
            labels={"salary": "Salary (USD)"},
        )
        fig.add_vline(x=avg_sal,    line_dash="dash", line_color=AMBER, annotation_text=f"Avg ${avg_sal:,.0f}", annotation_position="top right")
        fig.add_vline(x=median_sal, line_dash="dot",  line_color=GREEN, annotation_text=f"Median ${median_sal:,.0f}", annotation_position="top left")
        fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=360)
        fig.update_traces(marker_line_color=DARK_BG, marker_line_width=0.5)
        st.plotly_chart(fig, use_container_width=True)

    # Box by department
    with col_b:
        dept_order = df.groupby("department")["salary"].median().sort_values().index.tolist()
        fig2 = px.box(
            df, x="salary", y="department", color="department",
            category_orders={"department": dept_order},
            title="Salary Spread by Department",
            color_discrete_map=DEPT_COLORS,
            labels={"salary": "Salary (USD)", "department": ""},
        )
        fig2.update_layout(**PLOTLY_TEMPLATE["layout"], height=360, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("<div class='section-header'>Department Payroll Intelligence</div>", unsafe_allow_html=True)

    dept_stats = df.groupby("department").agg(
        Headcount=("employee_id", "count"),
        Avg_Salary=("salary", "mean"),
        Median_Salary=("salary", "median"),
        Total_Payroll=("salary", "sum"),
    ).reset_index().sort_values("Total_Payroll", ascending=False)

    col_c, col_d = st.columns([3, 2])

    with col_c:
        fig3 = px.bar(
            dept_stats.sort_values("Avg_Salary"),
            x="Avg_Salary", y="department",
            color="Avg_Salary", color_continuous_scale=[[0, "#2C3E70"], [0.5, BLUE], [1, TEAL]],
            title="Average Salary by Department",
            labels={"Avg_Salary": "Avg Salary ($)", "department": ""},
            text=dept_stats.sort_values("Avg_Salary")["Avg_Salary"].apply(lambda v: f"${v:,.0f}"),
        )
        fig3.update_traces(textposition="outside")
        fig3.add_vline(x=avg_sal, line_dash="dash", line_color=AMBER, annotation_text="Company Avg")
        fig3.update_layout(**PLOTLY_TEMPLATE["layout"], height=420, coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        fig4 = px.scatter(
            dept_stats, x="Headcount", y="Avg_Salary",
            size="Total_Payroll", color="department",
            color_discrete_map=DEPT_COLORS,
            hover_name="department",
            title="Headcount vs Avg Salary<br><sup>Bubble = Total Payroll</sup>",
            labels={"Avg_Salary": "Avg Salary ($)", "Headcount": "Headcount"},
            text="department",
        )
        fig4.update_traces(textposition="top center", textfont_size=9)
        fig4.update_layout(**PLOTLY_TEMPLATE["layout"], height=420, showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

    # Salary tier breakdown
    st.markdown("---")
    st.markdown("<div class='section-header'>Salary Tier Distribution by Department</div>", unsafe_allow_html=True)

    tier_df = df.groupby(["department", "salary_tier"], observed=True).size().reset_index(name="count")
    tier_total = tier_df.groupby("department")["count"].transform("sum")
    tier_df["pct"] = (tier_df["count"] / tier_total * 100).round(1)

    fig5 = px.bar(
        tier_df, x="department", y="pct", color="salary_tier",
        barmode="stack",
        color_discrete_map={"Lower Third": RED, "Middle Third": AMBER, "Top Third": GREEN},
        title="Salary Tier Composition per Department (%)",
        labels={"pct": "% of Department", "department": "", "salary_tier": "Tier"},
    )
    fig5.update_layout(**PLOTLY_TEMPLATE["layout"], height=370,
                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
    fig5.update_xaxes(tickangle=-30)
    st.plotly_chart(fig5, use_container_width=True)


# ════════════════════════════════════════════════════════════════════
# TAB 2 — DIVERSITY & PAY EQUITY
# ════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-header'>Gender Pay Gap Analysis</div>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)

    gender_sal = df.groupby("gender_group")["salary"].agg(["mean","median","count"]).reset_index()
    gender_sal.columns = ["Gender", "Avg Salary", "Median Salary", "Count"]

    with col_a:
        fig = px.bar(
            gender_sal, x="Gender", y="Avg Salary",
            color="Gender",
            color_discrete_map={"Male": BLUE, "Female": AMBER, "Non-Binary / Diverse": GREEN},
            title="Avg Salary by Gender",
            text=gender_sal["Avg Salary"].apply(lambda v: f"${v:,.0f}"),
        )
        fig.update_traces(textposition="outside")
        fig.add_hline(y=avg_sal, line_dash="dash", line_color=RED, annotation_text="Company Avg")
        fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=360, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = px.violin(
            df, y="salary", x="gender_group", color="gender_group",
            box=True, points="outliers",
            color_discrete_map={"Male": BLUE, "Female": AMBER, "Non-Binary / Diverse": GREEN},
            title="Salary Distribution by Gender",
            labels={"salary": "Salary ($)", "gender_group": ""},
        )
        fig2.update_layout(**PLOTLY_TEMPLATE["layout"], height=360, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    with col_c:
        fig3 = px.pie(
            gender_sal, values="Count", names="Gender",
            color="Gender",
            color_discrete_map={"Male": BLUE, "Female": AMBER, "Non-Binary / Diverse": GREEN},
            title="Headcount by Gender",
            hole=0.55,
        )
        fig3.update_layout(**PLOTLY_TEMPLATE["layout"], height=360)
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.markdown("<div class='section-header'>Gender Representation by Department</div>", unsafe_allow_html=True)

    gender_dept = df.groupby(["department","gender_group"]).size().reset_index(name="count")
    gender_dept_total = gender_dept.groupby("department")["count"].transform("sum")
    gender_dept["pct"] = (gender_dept["count"] / gender_dept_total * 100).round(1)

    dept_female_order = (
        gender_dept[gender_dept["gender_group"]=="Female"]
        .groupby("department")["pct"].sum()
        .sort_values(ascending=True).index.tolist()
    )

    fig4 = px.bar(
        gender_dept,
        x="pct", y="department",
        color="gender_group",
        barmode="stack",
        category_orders={"department": dept_female_order},
        color_discrete_map={"Male": BLUE, "Female": AMBER, "Non-Binary / Diverse": GREEN},
        title="Gender Composition by Department (%)",
        labels={"pct": "% Share", "department": "", "gender_group": "Gender"},
        text=gender_dept["pct"].apply(lambda v: f"{v:.0f}%" if v >= 8 else ""),
    )
    fig4.add_vline(x=50, line_dash="dash", line_color=RED, annotation_text="50% Parity", annotation_position="top")
    fig4.update_layout(**PLOTLY_TEMPLATE["layout"], height=440,
                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig4, use_container_width=True)

    # Pay gap by department heatmap
    st.markdown("---")
    st.markdown("<div class='section-header'>Pay Gap Heatmap — Male vs Female Avg Salary per Department</div>", unsafe_allow_html=True)

    pivot = df[df["gender_group"].isin(["Male","Female"])].groupby(
        ["department","gender_group"]
    )["salary"].mean().unstack()
    pivot["Pay Gap %"] = ((pivot["Male"] - pivot["Female"]) / pivot["Male"] * 100).round(1)
    pivot = pivot.reset_index().sort_values("Pay Gap %", ascending=False)

    col_e, col_f = st.columns([2,1])
    with col_e:
        fig5 = go.Figure(go.Bar(
            x=pivot["department"], y=pivot["Pay Gap %"],
            marker_color=[RED if v > 0 else GREEN for v in pivot["Pay Gap %"]],
            text=[f"{v:.1f}%" for v in pivot["Pay Gap %"]],
            textposition="outside",
        ))
        fig5.add_hline(y=0, line_color=MUTED)
        fig5.update_layout(
            **PLOTLY_TEMPLATE["layout"], height=360,
            title="Pay Gap % by Department (positive = Male earns more)",
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig5, use_container_width=True)

    with col_f:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.dataframe(
            pivot[["department","Male","Female","Pay Gap %"]]
            .rename(columns={"Male":"Male Avg $","Female":"Female Avg $"})
            .style.format({"Male Avg $":"${:,.0f}","Female Avg $":"${:,.0f}","Pay Gap %":"{:.1f}%"})
            .background_gradient(subset=["Pay Gap %"], cmap="RdYlGn_r"),
            use_container_width=True, height=340,
        )


# ════════════════════════════════════════════════════════════════════
# TAB 3 — WORKFORCE PROFILE
# ════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-header'>Age & Tenure Profile</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        fig = px.histogram(
            df, x="age", nbins=30, color_discrete_sequence=[PURPLE],
            title="Age Distribution",
            labels={"age": "Age (years)"},
        )
        fig.add_vline(x=df["age"].mean(), line_dash="dash", line_color=AMBER,
                      annotation_text=f"Avg {df['age'].mean():.1f}")
        fig.add_vline(x=55, line_dash="dot", line_color=RED,
                      annotation_text="55 — Retirement Zone", annotation_position="top left")
        fig.add_vrect(x0=55, x1=df["age"].max(), fillcolor=RED, opacity=0.07, line_width=0)
        fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=340)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        age_band_counts = df["age_band"].value_counts().sort_index().reset_index()
        age_band_counts.columns = ["Age Band","Count"]
        fig2 = px.bar(
            age_band_counts, x="Age Band", y="Count",
            color="Count", color_continuous_scale=[[0,"#2C3E70"],[1,PURPLE]],
            title="Headcount by Age Band",
            text="Count",
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(**PLOTLY_TEMPLATE["layout"], height=340, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("<div class='section-header'>Tenure & Loyalty Analysis</div>", unsafe_allow_html=True)

    col_c, col_d = st.columns(2)

    with col_c:
        fig3 = px.scatter(
            df, x="tenure_years", y="salary",
            color="department", color_discrete_map=DEPT_COLORS,
            opacity=0.5, size_max=6,
            trendline="ols",
            title="Tenure vs Salary (with trend)",
            labels={"tenure_years":"Tenure (Years)","salary":"Salary ($)"},
        )
        fig3.update_layout(**PLOTLY_TEMPLATE["layout"], height=380)
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        tenure_sal = df.groupby("tenure_band", observed=True)["salary"].agg(["mean","median","count"]).reset_index()
        tenure_sal.columns = ["Tenure Band","Avg Salary","Median Salary","Count"]

        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=tenure_sal["Tenure Band"], y=tenure_sal["Avg Salary"],
            name="Avg Salary", marker_color=BLUE, text=tenure_sal["Avg Salary"].apply(lambda v: f"${v:,.0f}"),
            textposition="outside",
        ))
        fig4.add_trace(go.Scatter(
            x=tenure_sal["Tenure Band"], y=tenure_sal["Count"],
            name="Headcount", mode="lines+markers",
            line=dict(color=AMBER, width=2.5), marker=dict(size=8),
            yaxis="y2",
        ))
        fig4.update_layout(
            **PLOTLY_TEMPLATE["layout"], height=380,
            title="Avg Salary & Headcount by Tenure Band",
            yaxis=dict(title="Avg Salary ($)", gridcolor=GRID),
            yaxis2=dict(title="Headcount", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig4, use_container_width=True)

    # Department headcount treemap
    st.markdown("---")
    st.markdown("<div class='section-header'>Headcount Distribution — Treemap</div>", unsafe_allow_html=True)

    dept_head = df.groupby(["department","gender_group"]).size().reset_index(name="count")

    fig5 = px.treemap(
        dept_head, path=[px.Constant("All"), "department","gender_group"],
        values="count", color="department",
        color_discrete_map=DEPT_COLORS,
        title="Headcount Treemap — Department → Gender",
    )
    fig5.update_traces(textinfo="label+value+percent parent", root_color=CARD_BG)
    fig5.update_layout(**PLOTLY_TEMPLATE["layout"], height=440)
    st.plotly_chart(fig5, use_container_width=True)


# ════════════════════════════════════════════════════════════════════
# TAB 4 — HIRING TRENDS
# ════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-header'>Annual Hiring Trends</div>", unsafe_allow_html=True)

    hire_annual = df.groupby("hire_year").size().reset_index(name="hires")
    hire_annual["yoy_change"] = hire_annual["hires"].pct_change() * 100

    col_a, col_b = st.columns([3, 1])
    with col_a:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=hire_annual["hire_year"], y=hire_annual["hires"],
            name="Hires", marker_color=BLUE,
            text=hire_annual["hires"], textposition="outside",
        ))
        fig.add_trace(go.Scatter(
            x=hire_annual["hire_year"], y=hire_annual["yoy_change"],
            name="YoY Change %", mode="lines+markers",
            line=dict(color=AMBER, width=2.5), marker=dict(size=8),
            yaxis="y2",
        ))
        fig.update_layout(
            **PLOTLY_TEMPLATE["layout"], height=380,
            title="Annual Hires & Year-on-Year Growth",
            yaxis=dict(title="Number of Hires"),
            yaxis2=dict(title="YoY Change (%)", overlaying="y", side="right",
                        showgrid=False, zeroline=True, zerolinecolor=RED),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("<br>", unsafe_allow_html=True)
        peak_yr = hire_annual.loc[hire_annual["hires"].idxmax(), "hire_year"]
        peak_n  = hire_annual["hires"].max()
        st.metric("Peak Hire Year", str(int(peak_yr)), f"{int(peak_n)} hires")
        st.metric("Total Filtered Hires", f"{hire_annual['hires'].sum():,}")
        st.metric("Avg Hires/Year", f"{hire_annual['hires'].mean():.0f}")

    # Department hiring heatmap
    st.markdown("---")
    st.markdown("<div class='section-header'>Hiring Heatmap — Department × Year</div>", unsafe_allow_html=True)

    heat_df = df.groupby(["hire_year","department"]).size().reset_index(name="count")
    heat_pivot = heat_df.pivot(index="department", columns="hire_year", values="count").fillna(0)

    fig2 = px.imshow(
        heat_pivot, color_continuous_scale=[[0, CARD_BG],[0.3, "#2C3E70"],[1, TEAL]],
        title="Hiring Intensity — Department × Year",
        labels=dict(x="Hire Year", y="Department", color="Hires"),
        text_auto=True, aspect="auto",
    )
    fig2.update_layout(**PLOTLY_TEMPLATE["layout"], height=420)
    st.plotly_chart(fig2, use_container_width=True)

    # Stacked area
    st.markdown("---")
    st.markdown("<div class='section-header'>Cumulative Headcount Growth by Department</div>", unsafe_allow_html=True)

    dept_yr = df.groupby(["hire_year","department"]).size().reset_index(name="hires")
    dept_yr_pivot = dept_yr.pivot(index="hire_year", columns="department", values="hires").fillna(0).cumsum()
    dept_yr_melt  = dept_yr_pivot.reset_index().melt(id_vars="hire_year", var_name="department", value_name="cumulative")

    fig3 = px.area(
        dept_yr_melt, x="hire_year", y="cumulative",
        color="department", color_discrete_map=DEPT_COLORS,
        title="Cumulative Headcount Growth by Department",
        labels={"cumulative":"Cumulative Employees","hire_year":"Year"},
    )
    fig3.update_layout(**PLOTLY_TEMPLATE["layout"], height=400,
                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig3, use_container_width=True)


# ════════════════════════════════════════════════════════════════════
# TAB 5 — EMPLOYEE EXPLORER
# ════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("<div class='section-header'>Search & Explore Individual Employee Records</div>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)
    search_name = col_a.text_input("🔍 Search by Name", placeholder="First or last name...")
    search_dept = col_b.selectbox("Department", ["All"] + sorted(df["department"].dropna().unique().tolist()))
    search_title = col_c.text_input("🔍 Job Title contains", placeholder="e.g. Engineer, Manager...")

    exp_df = df.copy()
    if search_name:
        mask = (
            exp_df["first_name"].str.contains(search_name, case=False, na=False) |
            exp_df["last_name"].str.contains(search_name, case=False, na=False)
        )
        exp_df = exp_df[mask]
    if search_dept != "All":
        exp_df = exp_df[exp_df["department"] == search_dept]
    if search_title:
        exp_df = exp_df[exp_df["job_title"].str.contains(search_title, case=False, na=False)]

    st.caption(f"Showing {len(exp_df):,} records")

    display_cols = ["employee_id","first_name","last_name","gender","department","job_title","salary","age","tenure_years","hire_date","email"]
    st.dataframe(
        exp_df[display_cols].reset_index(drop=True)
        .style.format({"salary":"${:,.2f}","tenure_years":"{:.1f}","age":"{}"}),
        use_container_width=True, height=420,
    )

    # Quick stats on filtered set
    if len(exp_df) > 0:
        st.markdown("---")
        st.markdown("<div class='section-header'>Quick Stats on Current View</div>", unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Employees",    f"{len(exp_df):,}")
        s2.metric("Avg Salary",   f"${exp_df['salary'].mean():,.0f}")
        s3.metric("Avg Age",      f"{exp_df['age'].mean():.1f}")
        s4.metric("Avg Tenure",   f"{exp_df['tenure_years'].mean():.1f} yrs")

        col_viz1, col_viz2 = st.columns(2)
        with col_viz1:
            dept_cnt = exp_df["department"].value_counts().reset_index()
            dept_cnt.columns = ["Department","Count"]
            fig = px.bar(dept_cnt, x="Count", y="Department", orientation="h",
                         color="Count", color_continuous_scale=[[0,"#2C3E70"],[1,BLUE]],
                         title="Dept Breakdown (filtered)")
            fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=300, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        with col_viz2:
            fig2 = px.histogram(exp_df, x="salary", nbins=20,
                                color_discrete_sequence=[AMBER],
                                title="Salary Distribution (filtered)")
            fig2.update_layout(**PLOTLY_TEMPLATE["layout"], height=300)
            st.plotly_chart(fig2, use_container_width=True)


# ── Footer ────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<p style='text-align:center; color:{MUTED}; font-size:12px;'>"
    "🏢 Employee Analytics Dashboard · Built with Streamlit + Plotly · "
    f"Analysing {total:,} employees across {df['department'].nunique()} departments"
    "</p>",
    unsafe_allow_html=True,
)
