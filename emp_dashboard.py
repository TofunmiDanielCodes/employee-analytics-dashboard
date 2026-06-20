"""
Employee Analytics Dashboard
Run: streamlit run emp_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Employee Analytics",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0F1117; }
    [data-testid="stSidebar"] { background-color: #161B27; border-right: 1px solid #2A2F45; }
    .kpi-card {
        background: linear-gradient(135deg, #1A1F35 0%, #232946 100%);
        border: 1px solid #2E3555; border-radius: 12px;
        padding: 20px 22px; text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .kpi-label { color: #8892A4; font-size: 12px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }
    .kpi-value { color: #EAEAEA; font-size: 28px; font-weight: 800; line-height: 1; }
    .kpi-sub   { color: #5B9BD5; font-size: 12px; margin-top: 5px; }
    .section-header {
        color: #EAEAEA; font-size: 17px; font-weight: 700;
        border-left: 4px solid #5B9BD5; padding-left: 12px; margin: 8px 0 16px 0;
    }
    .stTabs [data-baseweb="tab-list"] { background-color: #161B27; border-radius: 10px; padding: 4px; gap: 4px; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; color: #8892A4; border-radius: 8px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #5B9BD5 !important; color: white !important; }
    hr { border-color: #2A2F45; }
    [data-testid="metric-container"] { background: #1A1F35; border-radius: 10px; padding: 10px 16px; border: 1px solid #2E3555; }
</style>
""", unsafe_allow_html=True)

# ── Colours ──────────────────────────────────────────────────────────────────
BLUE   = "#5B9BD5"
AMBER  = "#F4A732"
GREEN  = "#4CAF82"
RED    = "#E05C5C"
PURPLE = "#9B72CF"
TEAL   = "#3EC9C9"
BG     = "#1A1F35"
GRID   = "#2A2F45"
TEXT   = "#EAEAEA"
MUTED  = "#8892A4"

DEPT_COLORS = {
    "Accounting": BLUE, "Business Development": AMBER, "Engineering": GREEN,
    "Human Resources": RED, "Legal": PURPLE, "Marketing": TEAL,
    "Product Management": "#FF9DA6", "Research and Development": "#B8860B",
    "Sales": "#66C2A5", "Services": "#FC8D62", "Support": "#8DA0CB", "Training": "#E78AC3",
}

def theme(fig, height=400, showlegend=None, legend_h=False,
          xangle=None, yaxis2=None, colorscale=False):
    kw = dict(
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color=TEXT, family="Inter, sans-serif", size=13),
        title=dict(font=dict(color="#FFFFFF", size=15)),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, title_font=dict(color="#FFFFFF")),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, title_font=dict(color="#FFFFFF")),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=GRID),
        colorway=[BLUE, AMBER, GREEN, RED, PURPLE, TEAL, "#FF9DA6", "#B8860B"],
        margin=dict(t=50, b=30, l=10, r=10),
        height=height,
    )
    if showlegend is not None:
        kw["showlegend"] = showlegend
    if legend_h:
        kw["legend"] = dict(bgcolor="rgba(0,0,0,0)", bordercolor=GRID,
                            orientation="h", yanchor="bottom", y=1.02)
    if xangle is not None:
        kw["xaxis"] = dict(gridcolor=GRID, zerolinecolor=GRID,
                           linecolor=GRID, tickangle=xangle)
    if yaxis2 is not None:
        kw["yaxis2"] = yaxis2
    if colorscale:
        kw["coloraxis"] = dict(showscale=False)
    fig.update_layout(**kw)
    return fig

# ── Load & Clean Data ────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel("employee_data.xlsx")

    df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], errors="coerce")
    df["hire_date"]     = pd.to_datetime(df["hire_date"],     errors="coerce")

    today = pd.Timestamp("today")
    df["age"]          = ((today - df["date_of_birth"]).dt.days / 365.25).fillna(0).round(0).astype(int)
    df["tenure_years"] = ((today - df["hire_date"]).dt.days / 365.25).round(1)
    df["hire_year"]    = df["hire_date"].dt.year.astype("Int64")

    binary = {"Male", "Female"}
    df["gender_group"] = df["gender"].apply(
        lambda g: g if g in binary else "Non-Binary / Diverse"
    )

    df["salary"] = df["salary"].fillna(
        df.groupby("department")["salary"].transform("median")
    )

    null_mask = df["employee_id"].isnull()
    df.loc[null_mask, "employee_id"] = [
        f"SURR-{9000+i}" for i in range(null_mask.sum())
    ]
    dup = df.duplicated(subset="employee_id", keep="first")
    df.loc[dup, "employee_id"] = (
        df.loc[dup, "employee_id"] + "-DUP-" +
        df[dup].groupby("employee_id").cumcount().add(1).astype(str)
    )

    df["age_band"] = pd.cut(
        df["age"], bins=[0,30,40,50,55,65,200],
        labels=["<30","30–39","40–49","50–54","55–64","65+"]
    )
    df["tenure_band"] = pd.cut(
        df["tenure_years"], bins=[0,2,5,10,15,20,100],
        labels=["0–2 yrs","3–5 yrs","6–10 yrs","11–15 yrs","16–20 yrs","20+ yrs"]
    )
    p33 = df["salary"].quantile(0.33)
    p66 = df["salary"].quantile(0.66)
    df["salary_tier"] = pd.cut(
        df["salary"],
        bins=[0, p33, p66, df["salary"].max() + 1],
        labels=["Lower Third", "Middle Third", "Top Third"]
    )
    return df

df_full = load_data()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 style='color:#FFFFFF;font-weight:800;'>🏢 Employee Analytics</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<p style='color:#E0E6F0;font-size:15px;font-weight:700;margin-bottom:4px'>🎚️ Filters</p>", unsafe_allow_html=True)

    departments = st.multiselect(
        "Department",
        options=sorted(df_full["department"].dropna().unique()),
        default=sorted(df_full["department"].dropna().unique()),
    )
    gender_opts = ["Male", "Female", "Non-Binary / Diverse"]
    genders = st.multiselect("Gender Group", gender_opts, default=gender_opts)

    sal_min = int(df_full["salary"].min())
    sal_max = int(df_full["salary"].max())
    salary_range = st.slider(
        "Salary Range ($)", min_value=sal_min, max_value=sal_max,
        value=(sal_min, sal_max), step=1000, format="$%d",
    )

    all_years = sorted(df_full["hire_year"].dropna().astype(int).unique().tolist())
    year_range = st.select_slider(
        "Hire Year Range",
        options=all_years,
        value=(all_years[0], all_years[-1]),
    )

    st.markdown("---")
    st.markdown(f"<span style='color:{MUTED};font-size:12px'>1,000 employees · 12 departments</span>",
                unsafe_allow_html=True)

# ── Filter ───────────────────────────────────────────────────────────────────
df = df_full[
    df_full["department"].isin(departments) &
    df_full["gender_group"].isin(genders) &
    df_full["salary"].between(salary_range[0], salary_range[1]) &
    df_full["hire_year"].between(int(year_range[0]), int(year_range[1]))
].copy()

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding:24px 0 8px 0;'>
  <span style='color:#5B9BD5;font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase;'>HR Intelligence</span>
  <h1 style='color:#EAEAEA;font-size:32px;font-weight:900;margin:4px 0 0 0;line-height:1;'>Employee Analytics Dashboard</h1>
  <p style='color:#8892A4;margin:6px 0 0 0;font-size:14px;'>Workforce insights · Compensation · Diversity · Retention</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ── KPIs ─────────────────────────────────────────────────────────────────────
total      = len(df)
avg_sal    = df["salary"].mean()
median_sal = df["salary"].median()
avg_age    = df["age"].mean()
avg_ten    = df["tenure_years"].mean()
ret_risk   = len(df[df["age"] >= 55])
ret_pct    = ret_risk / total * 100 if total else 0
male_avg   = df[df["gender_group"] == "Male"]["salary"].mean()
female_avg = df[df["gender_group"] == "Female"]["salary"].mean()
pay_gap    = abs((male_avg - female_avg) / male_avg * 100) if male_avg else 0

def kpi(col, label, value, sub=""):
    col.markdown(f"""
    <div class='kpi-card'>
      <div class='kpi-label'>{label}</div>
      <div class='kpi-value'>{value}</div>
      <div class='kpi-sub'>{sub}</div>
    </div>""", unsafe_allow_html=True)

c1,c2,c3,c4,c5,c6 = st.columns(6)
kpi(c1, "Total Employees",  "1,000",                f"{len(departments)} depts")
kpi(c2, "Avg Salary",       f"${avg_sal:,.0f}",     f"Median ${median_sal:,.0f}")
kpi(c3, "Avg Age",          f"{avg_age:.1f} yrs",   "Workforce average")
kpi(c4, "Avg Tenure",       f"{avg_ten:.1f} yrs",   "Company loyalty")
kpi(c5, "Retirement Risk",  f"{ret_risk:,}",        f"{ret_pct:.1f}% aged 55+")
kpi(c6, "Gender Pay Gap",   f"{pay_gap:.1f}%",      "Male vs Female avg")
st.markdown("<br>", unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💰 Compensation",
    "⚖️ Diversity & Pay Equity",
    "👥 Workforce Profile",
    "📈 Hiring Trends",
    "🔎 Employee Explorer",
])

# ═══════════════════════════════════════════════════
# TAB 1 — COMPENSATION
# ═══════════════════════════════════════════════════
with tab1:
    st.markdown("<div class='section-header'>Salary Distribution</div>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        fig = px.histogram(df, x="salary", nbins=40,
                           color_discrete_sequence=[BLUE],
                           title="Overall Salary Distribution",
                           labels={"salary": "Salary (USD)"})
        fig.add_vline(x=avg_sal, line_dash="dash", line_color=AMBER,
                      annotation_text=f"Avg ${avg_sal:,.0f}")
        fig.add_vline(x=median_sal, line_dash="dot", line_color=GREEN,
                      annotation_text=f"Median ${median_sal:,.0f}")
        theme(fig, height=360)
        st.plotly_chart(fig, width='stretch')

    with col_b:
        dept_order = df.groupby("department")["salary"].median().sort_values().index.tolist()
        fig2 = px.box(df, x="salary", y="department",
                      color="department",
                      category_orders={"department": dept_order},
                      color_discrete_map=DEPT_COLORS,
                      title="Salary Spread by Department",
                      labels={"salary": "Salary (USD)", "department": ""})
        theme(fig2, height=360, showlegend=False)
        st.plotly_chart(fig2, width='stretch')

    st.markdown("---")
    st.markdown("<div class='section-header'>Department Payroll Intelligence</div>", unsafe_allow_html=True)

    dept_stats = df.groupby("department").agg(
        Headcount=("employee_id", "count"),
        Avg_Salary=("salary", "mean"),
        Total_Payroll=("salary", "sum"),
    ).reset_index().sort_values("Total_Payroll", ascending=False)

    col_c, col_d = st.columns(2)
    with col_c:
        ds_sorted = dept_stats.sort_values("Avg_Salary")
        fig3 = px.bar(ds_sorted, x="Avg_Salary", y="department",
                      color="Avg_Salary",
                      color_continuous_scale=[[0,"#2C3E70"],[0.5,BLUE],[1,TEAL]],
                      title="Average Salary by Department",
                      labels={"Avg_Salary":"Avg Salary ($)","department":""},
                      text=ds_sorted["Avg_Salary"].apply(lambda v: f"${v:,.0f}"))
        fig3.update_traces(textposition="outside")
        fig3.add_vline(x=avg_sal, line_dash="dash", line_color=AMBER,
                       annotation_text="Company Avg")
        theme(fig3, height=420, colorscale=True)
        st.plotly_chart(fig3, width='stretch')

    with col_d:
        fig4 = px.scatter(dept_stats, x="Headcount", y="Avg_Salary",
                          size="Total_Payroll", color="department",
                          color_discrete_map=DEPT_COLORS,
                          hover_name="department", text="department",
                          title="Headcount vs Avg Salary<br><sup>Bubble = Total Payroll</sup>",
                          labels={"Avg_Salary":"Avg Salary ($)"})
        fig4.update_traces(textposition="top center", textfont_size=9)
        theme(fig4, height=420, showlegend=False)
        st.plotly_chart(fig4, width='stretch')

    st.markdown("---")
    st.markdown("<div class='section-header'>Salary Tier Distribution by Department</div>", unsafe_allow_html=True)

    tier_df = df.groupby(["department","salary_tier"], observed=True).size().reset_index(name="count")
    tier_df["pct"] = (tier_df["count"] /
                      tier_df.groupby("department")["count"].transform("sum") * 100).round(1)
    fig5 = px.bar(tier_df, x="department", y="pct", color="salary_tier",
                  barmode="stack",
                  color_discrete_map={"Lower Third":RED,"Middle Third":AMBER,"Top Third":GREEN},
                  title=dict(text="Salary Tier Composition per Department (%)", font=dict(color="#FFFFFF")),
                  labels={"pct":"% of Dept","department":"","salary_tier":"Tier"})
    theme(fig5, height=370, legend_h=True, xangle=-30)
    st.plotly_chart(fig5, width='stretch')


# ═══════════════════════════════════════════════════
# TAB 2 — DIVERSITY & PAY EQUITY
# ═══════════════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-header'>Gender Pay Gap Analysis</div>", unsafe_allow_html=True)

    gender_sal = df.groupby("gender_group")["salary"].agg(["mean","median","count"]).reset_index()
    gender_sal.columns = ["Gender","Avg Salary","Median Salary","Count"]
    gcmap = {"Male":BLUE,"Female":AMBER,"Non-Binary / Diverse":GREEN}

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        fig = px.bar(gender_sal, x="Gender", y="Avg Salary", color="Gender",
                     color_discrete_map=gcmap, title="Avg Salary by Gender",
                     text=gender_sal["Avg Salary"].apply(lambda v: f"${v:,.0f}"))
        fig.update_traces(textposition="outside")
        fig.add_hline(y=avg_sal, line_dash="dash", line_color=RED,
                      annotation_text="Company Avg")
        theme(fig, height=360, showlegend=False)
        st.plotly_chart(fig, width='stretch')

    with col_b:
        fig2 = px.violin(df, y="salary", x="gender_group", color="gender_group",
                         box=True, points="outliers", color_discrete_map=gcmap,
                         title="Salary Distribution by Gender",
                         labels={"salary":"Salary ($)","gender_group":""})
        theme(fig2, height=360, showlegend=False)
        st.plotly_chart(fig2, width='stretch')

    with col_c:
        fig3 = px.pie(gender_sal, values="Count", names="Gender",
                      color="Gender", color_discrete_map=gcmap,
                      title="Headcount by Gender", hole=0.55)
        theme(fig3, height=360)
        st.plotly_chart(fig3, width='stretch')

    st.markdown("---")
    st.markdown("<div class='section-header'>Gender Representation by Department</div>", unsafe_allow_html=True)

    gd = df.groupby(["department","gender_group"]).size().reset_index(name="count")
    gd["pct"] = (gd["count"] / gd.groupby("department")["count"].transform("sum") * 100).round(1)
    dept_f_order = (gd[gd["gender_group"]=="Female"]
                    .groupby("department")["pct"].sum()
                    .sort_values().index.tolist())
    fig4 = px.bar(gd, x="pct", y="department", color="gender_group",
                  barmode="stack",
                  category_orders={"department": dept_f_order},
                  color_discrete_map=gcmap,
                  title="Gender Composition by Department (%)",
                  labels={"pct":"% Share","department":"","gender_group":"Gender"},
                  text=gd["pct"].apply(lambda v: f"{v:.0f}%" if v >= 8 else ""))
    fig4.add_vline(x=50, line_dash="dash", line_color=RED,
                   annotation_text="50% Parity")
    theme(fig4, height=440, legend_h=True)
    st.plotly_chart(fig4, width='stretch')

    st.markdown("---")
    st.markdown("<div class='section-header'>Pay Gap by Department</div>", unsafe_allow_html=True)

    pivot = (df[df["gender_group"].isin(["Male","Female"])]
             .groupby(["department","gender_group"])["salary"].mean().unstack())
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
            paper_bgcolor=BG, plot_bgcolor=BG,
            font=dict(color=TEXT), height=360,
            title=dict(text="Pay Gap % by Department (positive = Male earns more)", font=dict(color="#FFFFFF", size=15)),
            xaxis=dict(gridcolor=GRID, tickangle=-30),
            yaxis=dict(gridcolor=GRID),
            margin=dict(t=50, b=30, l=10, r=10),
        )
        st.plotly_chart(fig5, width='stretch')

    with col_f:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.dataframe(
            pivot[["department","Male","Female","Pay Gap %"]]
            .rename(columns={"Male":"Male Avg $","Female":"Female Avg $"})
            .style.format({"Male Avg $":"${:,.0f}","Female Avg $":"${:,.0f}","Pay Gap %":"{:.1f}%"}),
            width='stretch', height=340,
        )


# ═══════════════════════════════════════════════════
# TAB 3 — WORKFORCE PROFILE
# ═══════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-header'>Age & Tenure Profile</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.histogram(df, x="age", nbins=30,
                           color_discrete_sequence=[PURPLE],
                           title="Age Distribution",
                           labels={"age":"Age (years)"})
        fig.add_vline(x=df["age"].mean(), line_dash="dash", line_color=AMBER,
                      annotation_text=f"Avg {df['age'].mean():.1f}")
        fig.add_vline(x=55, line_dash="dot", line_color=RED,
                      annotation_text="Retirement Zone")
        fig.add_vrect(x0=55, x1=int(df["age"].max())+1,
                      fillcolor=RED, opacity=0.07, line_width=0)
        theme(fig, height=340)
        st.plotly_chart(fig, width='stretch')

    with col_b:
        ab = df["age_band"].value_counts().sort_index().reset_index()
        ab.columns = ["Age Band","Count"]
        fig2 = px.bar(ab, x="Age Band", y="Count",
                      color="Count",
                      color_continuous_scale=[[0,"#2C3E70"],[1,PURPLE]],
                      title="Headcount by Age Band", text="Count")
        fig2.update_traces(textposition="outside")
        theme(fig2, height=340, colorscale=True)
        st.plotly_chart(fig2, width='stretch')

    st.markdown("---")
    st.markdown("<div class='section-header'>Tenure & Loyalty Analysis</div>", unsafe_allow_html=True)

    col_c, col_d = st.columns(2)
    with col_c:
        fig3 = px.scatter(df, x="tenure_years", y="salary",
                          color="department", color_discrete_map=DEPT_COLORS,
                          opacity=0.5,
                          title="Tenure vs Salary (with trend)",
                          labels={"tenure_years":"Tenure (Years)","salary":"Salary ($)"})
        mask = df["tenure_years"].notna() & df["salary"].notna()
        z = np.polyfit(df.loc[mask,"tenure_years"], df.loc[mask,"salary"], 1)
        p = np.poly1d(z)
        x_line = np.linspace(df["tenure_years"].min(), df["tenure_years"].max(), 100)
        fig3.add_trace(go.Scatter(
            x=x_line, y=p(x_line), mode="lines",
            line=dict(color=RED, width=2.5, dash="dash"),
            name="Trend",
        ))
        theme(fig3, height=380)
        st.plotly_chart(fig3, width='stretch')

    with col_d:
        ts = df.groupby("tenure_band", observed=True)["salary"].agg(["mean","count"]).reset_index()
        ts.columns = ["Tenure Band","Avg Salary","Count"]
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=ts["Tenure Band"], y=ts["Avg Salary"],
            name="Avg Salary", marker_color=BLUE,
            text=ts["Avg Salary"].apply(lambda v: f"${v:,.0f}"),
            textposition="outside",
        ))
        fig4.add_trace(go.Scatter(
            x=ts["Tenure Band"], y=ts["Count"],
            name="Headcount", mode="lines+markers",
            line=dict(color=AMBER, width=2.5),
            marker=dict(size=8), yaxis="y2",
        ))
        fig4.update_layout(
            paper_bgcolor=BG, plot_bgcolor=BG,
            font=dict(color=TEXT), height=380,
            title=dict(text="Avg Salary & Headcount by Tenure Band", font=dict(color="#FFFFFF", size=15)),
            xaxis=dict(gridcolor=GRID),
            yaxis=dict(title="Avg Salary ($)", gridcolor=GRID),
            yaxis2=dict(title="Headcount", overlaying="y", side="right", showgrid=False),
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02),
            margin=dict(t=50, b=30, l=10, r=10),
        )
        st.plotly_chart(fig4, width='stretch')

    st.markdown("---")
    st.markdown("<div class='section-header'>Headcount Treemap</div>", unsafe_allow_html=True)
    dept_head = df.groupby(["department","gender_group"]).size().reset_index(name="count")
    fig5 = px.treemap(dept_head,
                      path=[px.Constant("All"),"department","gender_group"],
                      values="count", color="department",
                      color_discrete_map=DEPT_COLORS,
                      title="Headcount Treemap — Department → Gender")
    fig5.update_traces(textinfo="label+value+percent parent", root_color=BG)
    theme(fig5, height=440)
    st.plotly_chart(fig5, width='stretch')


# ═══════════════════════════════════════════════════
# TAB 4 — HIRING TRENDS
# ═══════════════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-header'>Annual Hiring Trends</div>", unsafe_allow_html=True)

    hire_annual = df.groupby("hire_year").size().reset_index(name="hires")
    hire_annual["hire_year"] = hire_annual["hire_year"].astype(int)
    hire_annual["yoy"] = hire_annual["hires"].pct_change() * 100

    col_a, col_b = st.columns([3,1])
    with col_a:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=hire_annual["hire_year"], y=hire_annual["hires"],
            name="Hires", marker_color=BLUE,
            text=hire_annual["hires"], textposition="outside",
        ))
        fig.add_trace(go.Scatter(
            x=hire_annual["hire_year"], y=hire_annual["yoy"],
            name="YoY %", mode="lines+markers",
            line=dict(color=AMBER, width=2.5),
            marker=dict(size=8), yaxis="y2",
        ))
        fig.update_layout(
            paper_bgcolor=BG, plot_bgcolor=BG,
            font=dict(color=TEXT), height=380,
            title=dict(text="Annual Hires & Year-on-Year Growth", font=dict(color="#FFFFFF", size=15)),
            xaxis=dict(gridcolor=GRID, dtick=1),
            yaxis=dict(title="Number of Hires", gridcolor=GRID),
            yaxis2=dict(title="YoY Change (%)", overlaying="y", side="right",
                        showgrid=False, zeroline=True, zerolinecolor=RED),
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02),
            margin=dict(t=50, b=30, l=10, r=10),
        )
        st.plotly_chart(fig, width='stretch')

    with col_b:
        st.markdown("<br>", unsafe_allow_html=True)
        peak_yr = int(hire_annual.loc[hire_annual["hires"].idxmax(), "hire_year"])
        peak_n  = int(hire_annual["hires"].max())
        st.metric("Peak Hire Year",    str(peak_yr),              f"{peak_n} hires")
        st.metric("Total Hires",       f"{hire_annual['hires'].sum():,}")
        st.metric("Avg Hires / Year",  f"{hire_annual['hires'].mean():.0f}")

    st.markdown("---")
    st.markdown("<div class='section-header'>Hiring Heatmap — Department × Year</div>", unsafe_allow_html=True)

    heat_df = df.groupby(["hire_year","department"]).size().reset_index(name="count")
    heat_df["hire_year"] = heat_df["hire_year"].astype(int)
    heat_pivot = heat_df.pivot(index="department", columns="hire_year", values="count").fillna(0)
    fig2 = px.imshow(
        heat_pivot,
        color_continuous_scale=[[0,BG],[0.3,"#2C3E70"],[1,TEAL]],
        title="Hiring Intensity — Department × Year",
        labels=dict(x="Hire Year", y="Department", color="Hires"),
        text_auto=True, aspect="auto",
    )
    theme(fig2, height=420)
    st.plotly_chart(fig2, width='stretch')

    st.markdown("---")
    st.markdown("<div class='section-header'>Cumulative Headcount Growth by Department</div>", unsafe_allow_html=True)

    dept_yr = df.groupby(["hire_year","department"]).size().reset_index(name="hires")
    dept_yr["hire_year"] = dept_yr["hire_year"].astype(int)
    dept_pivot = dept_yr.pivot(index="hire_year", columns="department", values="hires").fillna(0).cumsum()
    dept_melt  = dept_pivot.reset_index().melt(id_vars="hire_year", var_name="department", value_name="cumulative")
    fig3 = px.area(dept_melt, x="hire_year", y="cumulative",
                   color="department", color_discrete_map=DEPT_COLORS,
                   title="Cumulative Headcount Growth by Department",
                   labels={"cumulative":"Cumulative Employees","hire_year":"Year"})
    theme(fig3, height=400, legend_h=True)
    st.plotly_chart(fig3, width='stretch')


# ═══════════════════════════════════════════════════
# TAB 5 — EMPLOYEE EXPLORER
# ═══════════════════════════════════════════════════
with tab5:
    st.markdown("<div class='section-header'>Search & Explore Employee Records</div>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)
    search_name  = col_a.text_input("🔍 Name", placeholder="First or last name...")
    search_dept  = col_b.selectbox("Department", ["All"] + sorted(df["department"].dropna().unique().tolist()))
    search_title = col_c.text_input("🔍 Job Title contains", placeholder="e.g. Engineer, Manager...")

    exp = df.copy()
    if search_name:
        exp = exp[exp["first_name"].str.contains(search_name, case=False, na=False) |
                  exp["last_name"].str.contains(search_name, case=False, na=False)]
    if search_dept != "All":
        exp = exp[exp["department"] == search_dept]
    if search_title:
        exp = exp[exp["job_title"].str.contains(search_title, case=False, na=False)]

    st.caption(f"Showing {len(exp):,} records")
    display_cols = ["employee_id","first_name","last_name","gender","department",
                    "job_title","salary","age","tenure_years","hire_date","email"]
    st.dataframe(
        exp[display_cols].reset_index(drop=True)
        .style.format({"salary":"${:,.2f}","tenure_years":"{:.1f}"}),
        width='stretch', height=420,
    )

    if len(exp) > 0:
        st.markdown("---")
        st.markdown("<div class='section-header'>Quick Stats on Current View</div>", unsafe_allow_html=True)
        s1,s2,s3,s4 = st.columns(4)
        s1.metric("Employees",  f"{len(exp):,}")
        s2.metric("Avg Salary", f"${exp['salary'].mean():,.0f}")
        s3.metric("Avg Age",    f"{exp['age'].mean():.1f}")
        s4.metric("Avg Tenure", f"{exp['tenure_years'].mean():.1f} yrs")

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            dc = exp["department"].value_counts().reset_index()
            dc.columns = ["Department","Count"]
            fig = px.bar(dc, x="Count", y="Department", orientation="h",
                         color="Count",
                         color_continuous_scale=[[0,"#2C3E70"],[1,BLUE]],
                         title="Dept Breakdown (filtered)")
            theme(fig, height=300, colorscale=True)
            st.plotly_chart(fig, width='stretch')

        with col_v2:
            fig2 = px.histogram(exp, x="salary", nbins=20,
                                color_discrete_sequence=[AMBER],
                                title="Salary Distribution (filtered)")
            theme(fig2, height=300)
            st.plotly_chart(fig2, width='stretch')

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<p style='text-align:center;color:{MUTED};font-size:12px;'>"
    f"🏢 Employee Analytics Dashboard · Built with Streamlit + Plotly · "
    f"Analysing {total:,} employees across {df['department'].nunique()} departments"
    f"</p>",
    unsafe_allow_html=True,
)
