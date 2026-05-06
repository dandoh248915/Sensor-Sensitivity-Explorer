import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Retail Macro Sensitivity Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.main { background-color: #F7F6F2; }

h1, h2, h3 { font-family: 'DM Serif Display', serif; }

.app-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.4rem;
    color: #1C2B4A;
    line-height: 1.2;
    margin-bottom: 0.2rem;
}
.app-subtitle {
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    color: #5C6B82;
    font-weight: 300;
    margin-bottom: 1.5rem;
}
.disclaimer {
    background: #EEF2F7;
    border-left: 3px solid #1C2B4A;
    padding: 0.75rem 1rem;
    border-radius: 0 6px 6px 0;
    font-size: 0.85rem;
    color: #4A5568;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: white;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    margin-bottom: 1rem;
}
.metric-label {
    font-size: 0.78rem;
    color: #8492A6;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-bottom: 0.2rem;
}
.metric-value {
    font-family: 'DM Serif Display', serif;
    font-size: 1.8rem;
    color: #1C2B4A;
    line-height: 1;
}
.metric-delta {
    font-size: 0.85rem;
    font-weight: 500;
    margin-top: 0.25rem;
}
.sector-header {
    font-family: 'DM Serif Display', serif;
    font-size: 1.3rem;
    color: #1C2B4A;
    border-bottom: 2px solid #E2E8F0;
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
}
.electronics-note {
    background: #FFF8ED;
    border-left: 3px solid #F59E0B;
    padding: 0.6rem 1rem;
    border-radius: 0 6px 6px 0;
    font-size: 0.82rem;
    color: #78520A;
    margin-bottom: 1rem;
}
.insight-box {
    background: #EBF4FF;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    font-size: 0.88rem;
    color: #1C2B4A;
    margin-top: 0.5rem;
}
.no-data-box {
    background: #FEF2F2;
    border-radius: 8px;
    padding: 1.2rem;
    text-align: center;
    color: #9B2C2C;
    font-size: 0.9rem;
}
.sidebar-section {
    font-family: 'DM Serif Display', serif;
    font-size: 1rem;
    color: #1C2B4A;
    margin-bottom: 0.5rem;
    margin-top: 1rem;
}
.match-count {
    background: #1C2B4A;
    color: white;
    border-radius: 20px;
    padding: 0.3rem 0.9rem;
    font-size: 0.82rem;
    font-weight: 600;
    display: inline-block;
}
.summary-compare {
    background: white;
    border-radius: 10px;
    padding: 1.4rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, 'retail_macro_data.csv')
    df = pd.read_csv(csv_path, parse_dates=['observation_date'])
    return df

df = load_data()

SECTOR_COLS = {
    'Grocery': 'Grocery_Sales',
    'Clothing': 'Clothing_Sales',
    'Electronics': 'Electronics_Sales'
}
SECTOR_COLORS = {
    'Grocery': '#2E86AB',
    'Clothing': '#A23B72',
    'Electronics': '#F18F01'
}
OVERALL_MEANS = {s: df[col].mean() for s, col in SECTOR_COLS.items()}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Macro Condition Filters")
    st.caption("Select one or more conditions to filter historical periods. Leave all unchecked to view all data.")

    st.markdown("**Inflation Level**")
    inf_low = st.checkbox("Low  (< 2%)", value=False, key="inf_low")
    inf_mod = st.checkbox("Moderate  (2–4%)", value=False, key="inf_mod")
    inf_high = st.checkbox("High  (> 4%)", value=False, key="inf_high")

    st.markdown("**Federal Funds Rate Trend**")
    fed_rising = st.checkbox("Rising", value=False, key="fed_rising")
    fed_stable = st.checkbox("Stable", value=False, key="fed_stable")
    fed_falling = st.checkbox("Falling", value=False, key="fed_falling")

    st.markdown("**Consumer Confidence**")
    conf_low = st.checkbox("Low  (< 70)", value=False, key="conf_low")
    conf_mod = st.checkbox("Moderate  (70–90)", value=False, key="conf_mod")
    conf_high = st.checkbox("High  (> 90)", value=False, key="conf_high")

    st.divider()
    st.caption("📅 Data coverage: 1993–2025 (393 monthly observations)\n\nSource: Federal Reserve Economic Data (FRED)")

# ── Filter logic ──────────────────────────────────────────────────────────────
selected_inf = []
if inf_low: selected_inf.append("Low")
if inf_mod: selected_inf.append("Moderate")
if inf_high: selected_inf.append("High")

selected_fed = []
if fed_rising: selected_fed.append("Rising")
if fed_stable: selected_fed.append("Stable")
if fed_falling: selected_fed.append("Falling")

selected_conf = []
if conf_low: selected_conf.append("Low")
if conf_mod: selected_conf.append("Moderate")
if conf_high: selected_conf.append("High")

mask = pd.Series([True] * len(df))
if selected_inf:
    mask = mask & df['Inflation_Category'].isin(selected_inf)
if selected_fed:
    mask = mask & df['Fed_Category'].isin(selected_fed)
if selected_conf:
    mask = mask & df['Confidence_Category'].isin(selected_conf)

filtered_df = df[mask].copy()
any_filter = bool(selected_inf or selected_fed or selected_conf)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="app-title">Retail Macro Sensitivity Explorer</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Explore how U.S. retail sales across Grocery, Clothing, and Electronics have historically responded to different macroeconomic environments.</div>', unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer">
⚠️ <strong>Descriptive tool only.</strong> This app surfaces historical patterns from 1993–2025 FRED data.
It does not generate forward predictions. All figures represent observed historical averages during matching periods.
</div>
""", unsafe_allow_html=True)

# Match count banner
n_match = len(filtered_df)
n_total = len(df)
if any_filter:
    pct = round(n_match / n_total * 100, 1)
    label = f"{n_match} of {n_total} months match your selected conditions ({pct}% of the historical record)"
else:
    label = f"Showing all {n_total} months — use the sidebar to filter by macro condition"

st.info(f"📅 {label}")

# ── Main content ──────────────────────────────────────────────────────────────
if n_match == 0:
    st.error("⚠️ No historical periods match all selected conditions simultaneously. Try removing one or more filters.")
else:
    # ── Time series charts ────────────────────────────────────────────────────
    st.markdown("### Sales Over Time — Matching Periods Highlighted")
    st.caption("Gray line = full historical record. Colored markers = periods matching your selected conditions.")

    for sector, col in SECTOR_COLS.items():
        color = SECTOR_COLORS[sector]

        fig = go.Figure()

        # Full history line
        fig.add_trace(go.Scatter(
            x=df['observation_date'], y=df[col],
            mode='lines', name='All periods',
            line=dict(color='#D1D5DB', width=1.2),
            hovertemplate='%{x|%b %Y}: $%{y:,.0f}M<extra>All periods</extra>'
        ))

        # Highlighted matching periods
        if any_filter and n_match > 0:
            fig.add_trace(go.Scatter(
                x=filtered_df['observation_date'], y=filtered_df[col],
                mode='markers', name='Matching periods',
                marker=dict(color=color, size=5, opacity=0.85),
                hovertemplate='%{x|%b %Y}: $%{y:,.0f}M<extra>Matching</extra>'
            ))

        # Overall mean line
        fig.add_hline(y=OVERALL_MEANS[sector], line_dash='dot',
                      line_color='#94A3B8', line_width=1.2,
                      annotation_text=f"Overall avg: ${OVERALL_MEANS[sector]:,.0f}M",
                      annotation_position="bottom right",
                      annotation_font_size=10)

        # COVID shading
        fig.add_vrect(x0="2020-01-01", x1="2021-12-31",
                      fillcolor="#FEE2E2", opacity=0.35, line_width=0,
                      annotation_text="COVID", annotation_position="top left",
                      annotation_font_size=9, annotation_font_color="#991B1B")

        fig.update_layout(
            title=dict(text=f"<b>{sector} Sales</b>", font=dict(size=14, color='#1C2B4A')),
            height=260,
            margin=dict(l=10, r=10, t=40, b=30),
            paper_bgcolor='white',
            plot_bgcolor='white',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=10)),
            xaxis=dict(showgrid=False, color='#94A3B8'),
            yaxis=dict(showgrid=True, gridcolor='#F1F5F9', color='#94A3B8',
                       tickprefix='$', ticksuffix='M', tickformat=',.0f'),
            hovermode='x unified'
        )

        if sector == 'Electronics':
            st.warning("⚡ **Electronics note:** This sector showed weak correlation with the macro variables used in this analysis. Patterns here are less consistent and should be interpreted with caution.")

        st.plotly_chart(fig, use_container_width=True)

    # ── Summary Statistics Tables ─────────────────────────────────────────────
    st.markdown("### Summary Statistics — Matching vs. Overall")
    st.caption("How did each sector perform during historically similar macro environments?")

    cols = st.columns(3)
    for i, (sector, col) in enumerate(SECTOR_COLS.items()):
        with cols[i]:
            overall_mean = OVERALL_MEANS[sector]
            if any_filter and n_match > 0:
                match_mean = filtered_df[col].mean()
                match_min = filtered_df[col].min()
                match_max = filtered_df[col].max()
                match_std = filtered_df[col].std()
                delta = ((match_mean - overall_mean) / overall_mean) * 100
            else:
                match_mean = overall_mean
                match_min = df[col].min()
                match_max = df[col].max()
                match_std = df[col].std()
                delta = None

            st.markdown(f"**{sector}**")
            if delta is not None:
                st.metric(
                    label="Avg Sales (Matching)",
                    value=f"${match_mean/1000:.1f}B",
                    delta=f"{delta:+.1f}% vs. overall avg"
                )
            else:
                st.metric(
                    label="Avg Sales (All periods)",
                    value=f"${match_mean/1000:.1f}B"
                )

            c1, c2 = st.columns(2)
            c1.metric("Min", f"${match_min/1000:.1f}B")
            c2.metric("Max", f"${match_max/1000:.1f}B")
            c3, c4 = st.columns(2)
            c3.metric("Std Dev", f"${match_std/1000:.1f}B")
            c4.metric("Months", f"{n_match if any_filter else n_total}")
            st.divider()

    # ── Cross-sector comparison bar chart ─────────────────────────────────────
    if any_filter and n_match > 0:
        st.markdown("### Cross-Sector Comparison")
        st.caption("Average sales during matching periods vs. overall historical average.")

        fig2 = go.Figure()
        sectors_list = list(SECTOR_COLS.keys())
        overall_vals = [OVERALL_MEANS[s]/1000 for s in sectors_list]
        match_vals = [filtered_df[SECTOR_COLS[s]].mean()/1000 for s in sectors_list]
        bar_colors = [SECTOR_COLORS[s] for s in sectors_list]

        fig2.add_trace(go.Bar(
            name='Overall Average', x=sectors_list, y=overall_vals,
            marker_color='#CBD5E1', marker_line_width=0,
            hovertemplate='%{x} Overall Avg: $%{y:.1f}B<extra></extra>'
        ))
        fig2.add_trace(go.Bar(
            name='Matching Periods', x=sectors_list, y=match_vals,
            marker_color=bar_colors, marker_line_width=0,
            hovertemplate='%{x} Matching Avg: $%{y:.1f}B<extra></extra>'
        ))

        fig2.update_layout(
            barmode='group', height=320,
            margin=dict(l=10, r=10, t=20, b=30),
            paper_bgcolor='white', plot_bgcolor='white',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            yaxis=dict(showgrid=True, gridcolor='#F1F5F9', tickprefix='$', ticksuffix='B',
                       tickformat='.1f', color='#94A3B8'),
            xaxis=dict(showgrid=False, color='#94A3B8')
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Plain language interpretation ─────────────────────────────────────────
    st.markdown("### What This Means")

    if not any_filter:
        st.info("""Use the sidebar to select macro conditions — for example, High Inflation and Rising Fed Funds Rate —
to see how each retail sector performed historically during similar environments.
The app will highlight matching periods on the charts and calculate how average sales compared to the long-run historical average.""")
    elif n_match == 0:
        pass
    else:
        insights = []
        for sector, col in [('Grocery', 'Grocery_Sales'), ('Clothing', 'Clothing_Sales')]:
            mean_match = filtered_df[col].mean()
            overall = OVERALL_MEANS[sector]
            delta = ((mean_match - overall) / overall) * 100
            direction = "above" if delta >= 0 else "below"
            insights.append(f"<b>{sector}</b> sales averaged {abs(delta):.1f}% {direction} the long-run mean during these periods.")

        elec_mean = filtered_df['Electronics_Sales'].mean()
        elec_overall = OVERALL_MEANS['Electronics']
        elec_delta = ((elec_mean - elec_overall) / elec_overall) * 100
        elec_dir = "above" if elec_delta >= 0 else "below"
        insights.append(f"<b>Electronics</b> averaged {abs(elec_delta):.1f}% {elec_dir} its long-run mean, though this sector's behavior is less reliably explained by macro conditions alone.")

        condition_desc = []
        if selected_inf: condition_desc.append(f"{' / '.join(selected_inf)} inflation")
        if selected_fed: condition_desc.append(f"{' / '.join(selected_fed)} Fed Funds Rate")
        if selected_conf: condition_desc.append(f"{' / '.join(selected_conf)} consumer confidence")

        insight_text = f"**During periods of {', '.join(condition_desc)} ({n_match} months historically):**\n\n"
        for ins in insights:
            clean = ins.replace('<b>', '**').replace('</b>', '**')
            insight_text += f"- {clean}\n"
        st.info(insight_text)

    # ── Next Steps ────────────────────────────────────────────────────────────
    with st.expander("📌 Research Context & Next Steps"):
        st.markdown("""
        **About this tool**

        This app is based on a Multiple Linear Regression study examining whether macroeconomic
        indicators can predict monthly retail sales across Grocery, Clothing, and Electronics sectors
        using 30 years of FRED data (1993–2025).

        **Key finding**

        The original predictive model produced high training R² scores (0.98+) for Grocery and Clothing,
        but failed on the holdout test set. After diagnosis, the high training R² was found to reflect
        a shared long-term upward trend between CPI and retail sales — not a true predictive relationship.
        This is known as spurious correlation, and it is a common issue when applying regression to
        trending time-series data.

        **What this app does instead**

        Rather than generating unreliable predictions, this tool surfaces historical patterns descriptively.
        It allows retail managers and analysts to contextualize current macro conditions against how
        similar environments have played out historically across the three sectors.

        **Limitations**
        - National aggregate data only — regional and firm-level variation is not captured
        - The 2020–2021 COVID period represents an anomaly that may distort some historical comparisons
        - Electronics showed weak and inconsistent relationships with all macro variables tested
        - This tool does not account for seasonality, promotional events, or firm-specific factors

        **Potential next steps for a more complete solution**
        1. Supplement with sector-specific predictors (food commodity prices for Grocery, wage growth for Clothing)
        2. Apply cointegration or error-correction modeling to properly capture long-run relationships
        3. Incorporate regional data to make the tool more actionable at the store or market level
        4. Build a supervised model trained on first-differenced data with additional predictors
        """)

