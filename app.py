
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.storage import get_connection
from config import REPORTS_DIR


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="ClaimShield | Insurance Fraud Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# THEME AND GLOBAL STYLING
# ============================================================

st.markdown(
    """
    <style>
    :root {
        --cs-bg: #0b1220;
        --cs-panel: #111c2e;
        --cs-border: #263750;
        --cs-text: #e8eef8;
        --cs-muted: #9aabc2;
    }

    .stApp {
        background:
            radial-gradient(circle at 12% 0%, rgba(42,105,180,.16), transparent 30%),
            linear-gradient(135deg,#0b1220 0%,#0e1728 55%,#101b2e 100%);
        color: var(--cs-text);
    }

    [data-testid="stHeader"] {
        background: rgba(11,18,32,.88);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,#0d1728 0%,#101d31 100%);
        border-right: 1px solid var(--cs-border);
    }

    [data-testid="stSidebar"] * {
        color: var(--cs-text);
    }

    h1,h2,h3 {
        color: #f4f7fc !important;
        letter-spacing: -.02em;
    }

    h1 { font-weight: 800 !important; }

    p,li,label,.stCaption {
        color: var(--cs-muted);
    }

    [data-testid="stMetric"] {
        background: linear-gradient(145deg,#172943 0%,#122137 100%);
        border: 1px solid #2a4262;
        border-radius: 15px;
        padding: 18px 20px;
        box-shadow: 0 8px 22px rgba(0,0,0,.18);
        min-height: 112px;
    }

    [data-testid="stMetricLabel"] {
        color: #b8c8dc !important;
        font-size: .88rem !important;
        font-weight: 650 !important;
    }

    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.9rem !important;
        font-weight: 800 !important;
    }

    [data-testid="stMetricDelta"] {
        color: #8fd8bd !important;
    }

    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
        border: 1px solid var(--cs-border);
        border-radius: 12px;
        overflow: hidden;
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    div[data-testid="stPlotlyChart"] {
        background: rgba(17,28,46,.72);
        border: 1px solid var(--cs-border);
        border-radius: 14px;
        padding: 8px;
    }

    hr {
        border-color: var(--cs-border) !important;
    }

    .cs-eyebrow {
        color: #72baff;
        text-transform: uppercase;
        letter-spacing: .13em;
        font-size: .72rem;
        font-weight: 800;
        margin-bottom: .25rem;
    }

    .cs-subtitle {
        color: #a9bad0;
        font-size: .96rem;
        margin-top: -.45rem;
        margin-bottom: 1.2rem;
    }

    .cs-footer {
        color: #8294ad;
        text-align: center;
        font-size: .78rem;
        padding: 12px 0 4px;
    }

    .cs-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: #1b3554;
        color: #bfe0ff;
        border: 1px solid #31577e;
        font-size: .76rem;
        font-weight: 700;
    }

    .stButton > button {
        border-radius: 10px;
        border: 1px solid #3479b8;
        background: #1769aa;
        color: white;
        font-weight: 700;
    }

    .stButton > button:hover {
        background: #2385d1;
        border-color: #62b6ff;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATA ACCESS
# ============================================================

@st.cache_data(ttl=60, show_spinner=False)
def load_data(query: str) -> pd.DataFrame:
    """Run a read-only query and return its rows."""
    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        return pd.DataFrame(cursor.fetchall())
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def get_scalar(query: str) -> int:
    dataframe = load_data(query)

    if dataframe.empty:
        return 0

    value = dataframe.iloc[0, 0]
    return int(value) if value is not None else 0


def show_page_header(title: str, subtitle: str) -> None:
    st.markdown(
        '<div class="cs-eyebrow">ClaimShield | Insurance intelligence</div>',
        unsafe_allow_html=True,
    )
    st.title(title)
    st.markdown(
        f'<div class="cs-subtitle">{subtitle}</div>',
        unsafe_allow_html=True,
    )


def style_figure(fig, height: int = 360):
    fig.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dce7f5", family="Arial", size=12),
        title_font=dict(color="#f4f7fc", size=16),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=24, r=24, t=55, b=35),
    )

    fig.update_xaxes(
        gridcolor="rgba(143,165,194,.13)",
        tickfont=dict(color="#b8c8dc"),
    )

    fig.update_yaxes(
        gridcolor="rgba(143,165,194,.13)",
        tickfont=dict(color="#b8c8dc"),
    )

    return fig


def show_empty_state(message: str) -> None:
    st.info(message)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:
    st.markdown("## 🛡️ ClaimShield")
    st.caption("INSURANCE FRAUD INTELLIGENCE PLATFORM")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Dashboard Overview",
            "Fraud Analytics",
            "Investigation Management",
            "Evidence Management",
            "Graph Analytics",
            "Data Quality",
        ],
        label_visibility="visible",
    )

    st.divider()

    st.markdown(
        '<span class="cs-pill">LIVE DATABASE</span>',
        unsafe_allow_html=True,
    )

    st.caption("Python · MySQL · Streamlit · Plotly")

    if st.button("Refresh dashboard data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ============================================================
# DASHBOARD OVERVIEW
# ============================================================

if page == "Dashboard Overview":

    show_page_header(
        "Insurance Fraud Detection Dashboard",
        "A consolidated view of claims, risk signals, investigations and evidence.",
    )

    try:
        total_claims = get_scalar(
            "SELECT COUNT(*) FROM claims"
        )

        total_claimants = get_scalar(
            "SELECT COUNT(*) FROM claimants"
        )

        total_providers = get_scalar(
            "SELECT COUNT(*) FROM providers"
        )

        total_investigations = get_scalar(
            "SELECT COUNT(*) FROM investigations"
        )

        total_indicators = get_scalar(
            "SELECT COUNT(*) FROM fraud_indicators"
        )

        open_investigations = get_scalar(
            """
            SELECT COUNT(*)
            FROM investigations
            WHERE investigation_status = 'OPEN'
            """
        )

        high_critical_claims = get_scalar(
            """
            SELECT COUNT(*)
            FROM claim_risk_scores
            WHERE risk_category IN ('HIGH','CRITICAL')
            """
        )

        st.subheader("Operational snapshot")

        k1, k2, k3, k4 = st.columns(4)

        k1.metric("Total Claims", f"{total_claims:,}")
        k2.metric("Claimants", f"{total_claimants:,}")
        k3.metric("Providers", f"{total_providers:,}")
        k4.metric("Investigations", f"{total_investigations:,}")

        k5, k6, k7 = st.columns(3)

        k5.metric("Fraud Indicators", f"{total_indicators:,}")
        k6.metric("Open Investigations", f"{open_investigations:,}")
        k7.metric("High / Critical Claims", f"{high_critical_claims:,}")

        st.divider()

        left, right = st.columns(2)

        with left:
            st.subheader("Claims by risk category")

            risk_data = load_data(
                """
                SELECT risk_category, COUNT(*) AS total
                FROM claim_risk_scores
                GROUP BY risk_category
                ORDER BY total DESC
                """
            )

            if not risk_data.empty:
                fig = px.pie(
                    risk_data,
                    names="risk_category",
                    values="total",
                    hole=0.58,
                    color="risk_category",
                    color_discrete_map={
                        "LOW": "#35c98b",
                        "MEDIUM": "#f4b942",
                        "HIGH": "#ff914d",
                        "CRITICAL": "#ff5964",
                    },
                )

                fig.update_traces(
                    textposition="inside",
                    textinfo="percent+label",
                    marker=dict(
                        line=dict(color="#101b2e", width=3)
                    ),
                )

                style_figure(fig, 370)
                st.plotly_chart(fig, use_container_width=True)
            else:
                show_empty_state("No claim risk scores are available.")

        with right:
            st.subheader("Investigation status")

            investigation_data = load_data(
                """
                SELECT investigation_status, COUNT(*) AS total
                FROM investigations
                GROUP BY investigation_status
                ORDER BY total DESC
                """
            )

            if not investigation_data.empty:
                fig = px.bar(
                    investigation_data,
                    x="investigation_status",
                    y="total",
                    text="total",
                    color="investigation_status",
                    color_discrete_sequence=[
                        "#48a6ff",
                        "#35c98b",
                        "#f4b942",
                    ],
                )

                fig.update_traces(
                    textposition="outside",
                    marker_line_width=0,
                    cliponaxis=False,
                )

                style_figure(fig, 370)
                st.plotly_chart(fig, use_container_width=True)
            else:
                show_empty_state("No investigation records are available.")

        st.subheader("Latest high-risk claims")

        high_risk = load_data(
            """
            SELECT claim_id, total_risk_score, risk_category,
                   indicator_count, risk_explanation
            FROM claim_risk_scores
            WHERE risk_category IN ('HIGH','CRITICAL')
            ORDER BY total_risk_score DESC
            LIMIT 10
            """
        )

        if not high_risk.empty:
            st.dataframe(
                high_risk,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success(
                "No HIGH or CRITICAL claims are currently recorded."
            )

    except Exception as error:
        st.error(f"Dashboard loading failed: {error}")


# ============================================================
# FRAUD ANALYTICS
# ============================================================

elif page == "Fraud Analytics":

    show_page_header(
        "Fraud Analytics",
        "Explore indicator patterns, claim-level risk and cases requiring attention.",
    )

    try:
        risk_data = load_data(
            """
            SELECT risk_category,
                   COUNT(*) AS total_claims,
                   ROUND(AVG(total_risk_score),2) AS average_score
            FROM claim_risk_scores
            GROUP BY risk_category
            ORDER BY FIELD(risk_category,'CRITICAL','HIGH','MEDIUM','LOW')
            """
        )

        st.subheader("Risk category summary")

        if not risk_data.empty:
            counts = {
                str(row["risk_category"]): int(row["total_claims"])
                for _, row in risk_data.iterrows()
            }

            r1, r2, r3, r4 = st.columns(4)

            r1.metric("Critical", f'{counts.get("CRITICAL", 0):,}')
            r2.metric("High", f'{counts.get("HIGH", 0):,}')
            r3.metric("Medium", f'{counts.get("MEDIUM", 0):,}')
            r4.metric("Low", f'{counts.get("LOW", 0):,}')

            st.dataframe(
                risk_data,
                use_container_width=True,
                hide_index=True,
            )
        else:
            show_empty_state("No risk scoring data is available.")

        indicator_data = load_data(
            """
            SELECT indicator_type, severity, COUNT(*) AS total
            FROM fraud_indicators
            GROUP BY indicator_type, severity
            ORDER BY total DESC
            """
        )

        st.divider()
        st.subheader("Fraud indicator analysis")

        if not indicator_data.empty:
            fig = px.bar(
                indicator_data,
                x="indicator_type",
                y="total",
                color="severity",
                barmode="group",
                text="total",
                color_discrete_map={
                    "MEDIUM": "#f4b942",
                    "HIGH": "#ff914d",
                    "CRITICAL": "#ff5964",
                },
            )

            fig.update_traces(
                textposition="outside",
                cliponaxis=False,
            )

            fig.update_layout(
                xaxis_title="Indicator type",
                yaxis_title="Findings",
            )

            style_figure(fig, 410)
            st.plotly_chart(fig, use_container_width=True)
        else:
            show_empty_state("No fraud indicators are currently recorded.")

        st.subheader("High-risk claims")

        high_risk = load_data(
            """
            SELECT claim_id, total_risk_score, risk_category,
                   indicator_count, risk_explanation
            FROM claim_risk_scores
            WHERE risk_category IN ('HIGH','CRITICAL')
            ORDER BY total_risk_score DESC
            """
        )

        if not high_risk.empty:
            st.dataframe(
                high_risk,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success(
                "No HIGH or CRITICAL claims are currently recorded."
            )

        st.caption(
            "Risk indicators identify claims for review; "
            "they are not proof of fraud."
        )

    except Exception as error:
        st.error(f"Fraud analytics failed: {error}")


# ============================================================
# INVESTIGATION MANAGEMENT
# ============================================================

elif page == "Investigation Management":

    show_page_header(
        "Investigation Management",
        "Monitor assigned investigations, priorities and current workflow status.",
    )

    try:
        investigations = load_data(
            """
            SELECT investigation_id, claim_id, assigned_investigator,
                   investigation_status, priority, risk_score, opened_at
            FROM investigations
            ORDER BY risk_score DESC, opened_at DESC
            """
        )

        summary = load_data(
            """
            SELECT investigation_status, priority, COUNT(*) AS total
            FROM investigations
            GROUP BY investigation_status, priority
            ORDER BY investigation_status, priority
            """
        )

        total_inv = len(investigations)

        open_inv = int(
            (investigations["investigation_status"] == "OPEN").sum()
        ) if not investigations.empty else 0

        in_progress = int(
            (
                investigations["investigation_status"]
                == "IN_PROGRESS"
            ).sum()
        ) if not investigations.empty else 0

        on_hold = int(
            (
                investigations["investigation_status"]
                == "ON_HOLD"
            ).sum()
        ) if not investigations.empty else 0

        a, b, c, d = st.columns(4)

        a.metric("Total investigations", f"{total_inv:,}")
        b.metric("Open", f"{open_inv:,}")
        c.metric("In progress", f"{in_progress:,}")
        d.metric("On hold", f"{on_hold:,}")

        st.subheader("Investigation register")

        if not investigations.empty:
            st.dataframe(
                investigations,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "risk_score": st.column_config.NumberColumn(
                        "Risk score",
                        format="%.1f",
                    ),
                    "opened_at": st.column_config.DatetimeColumn(
                        "Opened at",
                        format="YYYY-MM-DD HH:mm",
                    ),
                },
            )
        else:
            show_empty_state(
                "No investigations have been created yet."
            )

        st.divider()
        st.subheader(
            "Investigation summary by status and priority"
        )

        if not summary.empty:
            fig = px.bar(
                summary,
                x="investigation_status",
                y="total",
                color="priority",
                barmode="stack",
                text="total",
                color_discrete_map={
                    "LOW": "#35c98b",
                    "MEDIUM": "#f4b942",
                    "HIGH": "#ff914d",
                    "CRITICAL": "#ff5964",
                },
            )

            fig.update_traces(textposition="inside")

            fig.update_layout(
                xaxis_title="Status",
                yaxis_title="Investigations",
            )

            style_figure(fig, 350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            show_empty_state(
                "No investigation summary is available."
            )

    except Exception as error:
        st.error(f"Investigation loading failed: {error}")


# ============================================================
# EVIDENCE MANAGEMENT
# ============================================================

elif page == "Evidence Management":

    show_page_header(
        "Evidence Management",
        "Review evidence registered against investigations and monitor evidence status.",
    )

    try:
        evidence = load_data(
            """
            SELECT evidence_id, investigation_id, evidence_type,
                   evidence_reference, evidence_description,
                   collected_by, collected_at, evidence_status
            FROM investigation_evidence
            ORDER BY collected_at DESC
            """
        )

        evidence_total = len(evidence)

        status_counts = (
            evidence["evidence_status"].value_counts()
            if not evidence.empty
            else pd.Series(dtype="int64")
        )

        e1, e2, e3, e4 = st.columns(4)

        e1.metric("Total evidence", f"{evidence_total:,}")
        e2.metric(
            "Available",
            f"{int(status_counts.get('AVAILABLE', 0)):,}",
        )
        e3.metric(
            "Under review",
            f"{int(status_counts.get('UNDER_REVIEW', 0)):,}",
        )
        e4.metric(
            "Verified",
            f"{int(status_counts.get('VERIFIED', 0)):,}",
        )

        st.subheader("Evidence register")

        if not evidence.empty:
            st.dataframe(
                evidence,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "collected_at": st.column_config.DatetimeColumn(
                        "Collected at",
                        format="YYYY-MM-DD HH:mm",
                    )
                },
            )
        else:
            show_empty_state(
                "No evidence has been registered yet."
            )

        if not evidence.empty:
            st.divider()
            st.subheader("Evidence status distribution")

            status_summary = (
                evidence.groupby("evidence_status")
                .size()
                .reset_index(name="total")
            )

            fig = px.bar(
                status_summary,
                x="evidence_status",
                y="total",
                text="total",
                color="evidence_status",
                color_discrete_sequence=[
                    "#48a6ff",
                    "#f4b942",
                    "#35c98b",
                    "#ff6b75",
                ],
            )

            fig.update_traces(
                textposition="outside",
                cliponaxis=False,
            )

            fig.update_layout(
                xaxis_title="Evidence status",
                yaxis_title="Records",
            )

            style_figure(fig, 340)
            st.plotly_chart(fig, use_container_width=True)

    except Exception as error:
        st.error(f"Evidence loading failed: {error}")


# ============================================================
# GRAPH ANALYTICS
# ============================================================

elif page == "Graph Analytics":

    show_page_header(
        "Relationship Graph Analytics",
        "Understand entity connectivity using the generated relationship analysis report.",
    )

    try:
        total_nodes = get_scalar(
            """
            SELECT COUNT(*)
            FROM (
                SELECT source_entity_type, source_entity_id
                FROM relationship_edges

                UNION

                SELECT target_entity_type, target_entity_id
                FROM relationship_edges
            ) entities
            """
        )

        total_edges = get_scalar(
            "SELECT COUNT(*) FROM relationship_edges"
        )

        node_report_path = (
            Path(REPORTS_DIR) / "graph_node_analysis.csv"
        )

        g1, g2 = st.columns(2)

        g1.metric("Unique graph entities", f"{total_nodes:,}")
        g2.metric("Relationship edges", f"{total_edges:,}")

        if not node_report_path.exists():
            st.warning(
                "Graph analysis report not found. "
                "Run `python -m src.graph_analysis` to generate it."
            )

        else:
            node_data = pd.read_csv(node_report_path)

            required_columns = {"entity", "degree"}

            if not required_columns.issubset(node_data.columns):
                st.error(
                    "The graph report does not contain the expected "
                    "'entity' and 'degree' columns."
                )

            elif node_data.empty:
                show_empty_state(
                    "The graph analysis report contains no entities."
                )

            else:
                node_data["degree"] = pd.to_numeric(
                    node_data["degree"],
                    errors="coerce",
                ).fillna(0)

                node_data = node_data.sort_values(
                    "degree",
                    ascending=False,
                ).head(20)

                st.divider()
                st.subheader("Top connected entities")

                st.dataframe(
                    node_data,
                    use_container_width=True,
                    hide_index=True,
                )

                fig = px.bar(
                    node_data.sort_values(
                        "degree",
                        ascending=True,
                    ),
                    x="degree",
                    y="entity",
                    orientation="h",
                    text="degree",
                    title="Top 20 entities by degree",
                    color="degree",
                    color_continuous_scale=[
                        "#245b91",
                        "#48a6ff",
                        "#36d1dc",
                    ],
                )

                fig.update_traces(
                    textposition="outside",
                    cliponaxis=False,
                )

                fig.update_layout(
                    xaxis_title="Number of connections",
                    yaxis_title="Entity",
                    coloraxis_showscale=False,
                )

                style_figure(fig, 560)
                st.plotly_chart(fig, use_container_width=True)

                if "degree_centrality" in node_data.columns:
                    st.subheader("Degree centrality")

                    centrality = node_data.sort_values(
                        "degree_centrality",
                        ascending=False,
                    ).head(10)

                    st.dataframe(
                        centrality[
                            [
                                "entity",
                                "degree",
                                "degree_centrality",
                            ]
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )

        st.caption(
            "Graph connectivity highlights structural relationships; "
            "a highly connected entity is not automatically fraudulent."
        )

    except Exception as error:
        st.error(f"Graph analytics failed: {error}")


# ============================================================
# DATA QUALITY
# ============================================================

elif page == "Data Quality":

    show_page_header(
        "Data Quality Monitoring",
        "Review database record volumes and recorded data-quality exceptions.",
    )

    try:
        tables = [
            "claimants",
            "policies",
            "incidents",
            "providers",
            "claims",
            "invoices",
            "payments",
            "relationship_edges",
            "fraud_indicators",
            "claim_risk_scores",
            "investigations",
            "investigation_events",
            "audit_logs",
            "data_quality_issues",
            "investigation_evidence",
        ]

        results = []

        for table in tables:
            count = get_scalar(
                f"SELECT COUNT(*) FROM `{table}`"
            )

            results.append(
                {
                    "Table Name": table,
                    "Record Count": count,
                }
            )

        quality_data = pd.DataFrame(results)

        total_records = int(
            quality_data["Record Count"].sum()
        )

        issue_count = get_scalar(
            "SELECT COUNT(*) FROM data_quality_issues"
        )

        open_issue_count = get_scalar(
            """
            SELECT COUNT(*)
            FROM data_quality_issues
            WHERE resolution_status = 'OPEN'
            """
        )

        q1, q2, q3 = st.columns(3)

        q1.metric("Database tables", f"{len(tables):,}")
        q2.metric("Total table records", f"{total_records:,}")
        q3.metric("Recorded quality issues", f"{issue_count:,}")

        st.subheader("Database record summary")

        st.dataframe(
            quality_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Record Count": st.column_config.NumberColumn(
                    "Record count",
                    format="%d",
                )
            },
        )

        fig = px.bar(
            quality_data.sort_values(
                "Record Count",
                ascending=True,
            ),
            x="Record Count",
            y="Table Name",
            orientation="h",
            text="Record Count",
            color="Record Count",
            color_continuous_scale=[
                "#245b91",
                "#48a6ff",
                "#36d1dc",
            ],
        )

        fig.update_traces(
            textposition="outside",
            cliponaxis=False,
        )

        fig.update_layout(
            xaxis_title="Records",
            yaxis_title="Database table",
            coloraxis_showscale=False,
        )

        style_figure(fig, 520)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("Recorded data quality issues")

        issues = load_data(
            """
            SELECT issue_id, entity_type, entity_id, field_name,
                   invalid_value, issue_type, issue_description,
                   detected_at, resolution_status
            FROM data_quality_issues
            ORDER BY detected_at DESC
            """
        )

        if not issues.empty:
            st.warning(
                f"{open_issue_count:,} issue(s) currently have OPEN status. "
                "Some records in this project are intentionally injected test anomalies."
            )

            st.dataframe(
                issues,
                use_container_width=True,
                hide_index=True,
            )

        else:
            st.success(
                "No data quality issues are currently recorded."
            )

    except Exception as error:
        st.error(f"Data quality loading failed: {error}")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    '<div class="cs-footer">'
    '🛡️ <b>ClaimShield</b> · Insurance Fraud Detection & Investigation System'
    '<br>Risk indicators support investigation and do not independently establish fraud.'
    '</div>',
    unsafe_allow_html=True,
)
