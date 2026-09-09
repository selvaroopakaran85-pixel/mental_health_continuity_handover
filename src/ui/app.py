"""
Streamlit Web Dashboard for the Consent-Aware Mental Health Continuity Handover System.
Provides interactive role switching, real-time consent toggles, baseline comparisons,
edge case simulations, and live quantitative benchmark visualizations.
"""

import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px

from src.models.data_models import ClientProfile, RoleEnum, ConsentMatrix
from src.engine.summary_engine import SummaryEngine
from src.evaluation.benchmark import HandoverBenchmark


st.set_page_config(
    page_title="Community Mental Health Handover System",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "synthetic_clients.json"
)


@st.cache_data
def load_raw_clients():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_client_objects():
    raw_data = load_raw_clients()
    return [ClientProfile(**item) for item in raw_data]


def main():
    st.title("🤝 Community Mental-Health Service - Continuity & Handover System")
    st.markdown(
        "**Consent-Aware Continuity Summaries for Counsellor & Social Worker Handovers** | "
        "*Eliminating repetitive client history sharing while enforcing privacy consent boundaries.*"
    )

    clients = get_client_objects()
    client_dict = {f"{c.preferred_name} ({c.client_id})": c for c in clients}

    # --- SIDEBAR CONTROLS ---
    st.sidebar.header("⚙️ Care Team & Client Controls")

    selected_client_label = st.sidebar.selectbox(
        "Select Client Profile:", list(client_dict.keys())
    )
    client = client_dict[selected_client_label]

    selected_role_label = st.sidebar.radio(
        "Select Target Handover Role:",
        ["Social Worker 📋", "Counsellor 🧠"],
        help="Select the receiving role for the handover summary."
    )
    target_role = (
        RoleEnum.SOCIAL_WORKER if "Social Worker" in selected_role_label else RoleEnum.COUNSELLOR
    )

    st.sidebar.markdown("---")
    st.sidebar.header("🛡️ Live Client Consent Matrix")
    st.sidebar.info("Modify client consent settings in real-time to observe summary scrubbing:")

    c_trauma = st.sidebar.checkbox(
        "Share Trauma History",
        value=client.consent_matrix.share_trauma_history,
        key="c_trauma",
    )
    c_medical = st.sidebar.checkbox(
        "Share Medical Diagnosis",
        value=client.consent_matrix.share_medical_diagnosis,
        key="c_medical",
    )
    c_social = st.sidebar.checkbox(
        "Share Social Determinants",
        value=client.consent_matrix.share_social_determinants,
        key="c_social",
    )
    c_substance = st.sidebar.checkbox(
        "Share Substance History",
        value=client.consent_matrix.share_substance_history,
        key="c_substance",
    )

    # Apply interactive consent updates
    client.consent_matrix.share_trauma_history = c_trauma
    client.consent_matrix.share_medical_diagnosis = c_medical
    client.consent_matrix.share_social_determinants = c_social
    client.consent_matrix.share_substance_history = c_substance

    # Summary Engine Instance
    summary_engine = SummaryEngine(client)
    proto_summary = summary_engine.generate_prototype_summary(target_role)
    baseline_text = summary_engine.generate_baseline_summary(target_role)

    # --- MAIN DASHBOARD TABS ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Consent-Aware Summary",
        "⚖️ Baseline vs Prototype",
        "🧪 Edge & Failure Cases",
        "📊 Quantitative Benchmark",
    ])

    # --- TAB 1: CONSENT-AWARE SUMMARY ---
    with tab1:
        # Mandatory Operational vs Medical Guardrail Banner
        st.warning(proto_summary.disclaimer_header)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Client Name", client.preferred_name, delta=client.pronouns)
        with col_b:
            st.metric("Receiving Role", target_role.value.upper())
        with col_c:
            st.metric(
                "Active Consent Scopes",
                f"{sum([c_trauma, c_medical, c_social, c_substance])} / 4 Allowed",
            )

        st.markdown("---")

        # Uncertainty / Quality Flags Alert Section
        if proto_summary.uncertainty_flags:
            st.error("⚠️ ATTENTION: Uncertainty & Quality Flags Detected in Client Data")
            for flag in proto_summary.uncertainty_flags:
                st.markdown(
                    f"- **[{flag.severity.upper()}] [{flag.issue_type}]** (Session: `{flag.session_id}`): {flag.description}"
                )
            st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🎯 Active Goals (Continuity Preserved)")
            if proto_summary.active_goals:
                for goal in proto_summary.active_goals:
                    st.markdown(
                        f"- **[{goal.priority.upper()}]** `{goal.title}` | Category: *{goal.category}* | Status: **{goal.status}**"
                    )
            else:
                st.info("No active goals assigned for this role.")

            st.subheader("📌 Pending Care Actions")
            if proto_summary.pending_actions:
                for action in proto_summary.pending_actions:
                    st.markdown(
                        f"- **Due {action.due_date or 'N/A'}** (`{action.assigned_role.value}`): {action.description}"
                    )
            else:
                st.info("No pending actions assigned for this role.")

        with col2:
            st.subheader("🔒 Consented Continuity Notes")
            notes_list = (
                proto_summary.operational_support_notes
                if target_role == RoleEnum.SOCIAL_WORKER
                else proto_summary.psychological_continuity_notes
            )
            if notes_list:
                for note in notes_list:
                    st.success(note)
            else:
                st.info("No consented notes available for this role focus.")

            st.subheader("🛡️ Redacted / Privacy Scrubbed Topics")
            if proto_summary.redacted_sensitive_topics:
                for red in proto_summary.redacted_sensitive_topics:
                    st.warning(f"🚫 {red}")
            else:
                st.caption("All session topics consented under current preferences.")

        with st.expander("🔍 View Consent Engine Audit Log"):
            for audit_item in proto_summary.audit_trail:
                st.code(audit_item)

    # --- TAB 2: BASELINE VS PROTOTYPE ---
    with tab2:
        st.subheader("⚖️ Side-by-Side Comparison: Traditional Baseline vs Consent-Aware Prototype")
        st.markdown(
            "Observe how the baseline simple note dump exposes sensitive traumatic history and lacks operational structure, "
            "whereas the prototype enforces privacy scrubbing, surfaces uncertainty, and organizes role-specific continuity."
        )

        col_base, col_proto = st.columns(2)

        with col_base:
            st.error("❌ BASELINE (Raw Un-redacted Dump)")
            st.text_area("Baseline Handover Output", baseline_text, height=420)
            st.caption("Flaws: No consent enforcement, trauma details leaked, no uncertainty warnings.")

        with col_proto:
            st.success("✅ PROTOTYPE (Consent-Aware Continuity Engine)")
            proto_formatted = (
                f"{proto_summary.disclaimer_header}\n\n"
                f"CLIENT: {proto_summary.client_name} ({proto_summary.client_id})\n"
                f"TARGET ROLE: {proto_summary.target_role.value.upper()}\n\n"
                f"--- CONSENTED NOTES ---\n"
                + "\n".join(notes_list) + "\n\n"
                f"--- PRIVACY REDACTION NOTICES ---\n"
                + "\n".join(proto_summary.redacted_sensitive_topics) + "\n\n"
                f"--- UNCERTAINTY FLAGS ({len(proto_summary.uncertainty_flags)}) ---\n"
                + "\n".join([f"• {f.description}" for f in proto_summary.uncertainty_flags])
            )
            st.text_area("Prototype Handover Output", proto_formatted, height=420)
            st.caption("Benefits: Consent compliant, role-segregated, quality warnings explicit.")

    # --- TAB 3: EDGE & FAILURE CASES ---
    with tab3:
        st.subheader("🧪 Realistic Failure States & Edge Case Simulations")
        st.markdown(
            "Test how the system robustly handles incomplete data, mid-care consent changes, and clinical boundary violations."
        )

        sim_case = st.radio(
            "Select Failure Simulation:",
            [
                "Failure 1: Mid-Care Consent Revocation (Jordan Chen)",
                "Failure 2: Low-Quality / Missing Input Notes (Sam Taylor)",
                "Failure 3: Clinical Boundary Leak Attempt (Morgan Blake)",
                "Failure 4: Conflicting Scopes & Restricted Role (Casey Vance)",
            ]
        )

        if "Failure 1" in sim_case:
            st.markdown("### 🔹 Scenario: Client Revokes Trauma & Substance Consent Mid-Care")
            st.info("Jordan Chen revoked consent for trauma and substance history. Verify that sensitive details are scrubbed while vocational employment goals remain active.")
            sim_c = client_dict["Jordan Chen (MH-102)"]
            sim_eng = SummaryEngine(sim_c)
            s_out = sim_eng.generate_prototype_summary(target_role)
            st.write("**Redaction Result:**", s_out.redacted_sensitive_topics)
            st.write("**Active Goals Preserved:**", [g.title for g in s_out.active_goals])

        elif "Failure 2" in sim_case:
            st.markdown("### 🔹 Scenario: Low Quality & Missing Timestamp Notes")
            st.info("Sam Taylor's file contains missing dates and corrupt text. Verify that explicit Uncertainty Flags alert staff.")
            sim_c = client_dict["Sam Taylor (MH-103)"]
            sim_eng = SummaryEngine(sim_c)
            s_out = sim_eng.generate_prototype_summary(target_role)
            st.error("Uncertainty Flags Raised:")
            for flag in s_out.uncertainty_flags:
                st.write(f"- `{flag.issue_type}`: {flag.description}")

        elif "Failure 3" in sim_case:
            st.markdown("### 🔹 Scenario: Clinical Diagnostic Code Leak to Social Worker")
            st.info("Morgan Blake's file contains DSM-5 Bipolar diagnostic code (F31.1) and quetiapine dosage notes. Verify clinical filter converts this to transport support for Social Worker view.")
            sim_c = client_dict["Morgan Blake (MH-104)"]
            sim_eng = SummaryEngine(sim_c)
            s_out = sim_eng.generate_prototype_summary(RoleEnum.SOCIAL_WORKER)
            st.warning("Clinical Scope Guardrail Flag:")
            for flag in s_out.uncertainty_flags:
                st.write(f"- {flag.description}")

        elif "Failure 4" in sim_case:
            st.markdown("### 🔹 Scenario: Role Access Blocked by Client Matrix")
            st.info("Casey Vance restricted access to Counsellor only. Social Worker view attempts access.")
            sim_c = client_dict["Casey Vance (MH-105)"]
            sim_eng = SummaryEngine(sim_c)
            s_out = sim_eng.generate_prototype_summary(RoleEnum.SOCIAL_WORKER)
            st.error(s_out.redacted_sensitive_topics)

    # --- TAB 4: QUANTITATIVE BENCHMARK ---
    with tab4:
        st.subheader("📊 Quantitative Benchmark Evaluation & Metric Analysis")
        st.markdown(
            "Empirical performance comparison of **Baseline** vs **Prototype** across synthetic test suite."
        )

        bench = HandoverBenchmark(DATA_PATH)
        res = bench.run_benchmark()

        b_metrics = res["summary_metrics"]["baseline"]
        p_metrics = res["summary_metrics"]["prototype"]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Repetition Avoidance Score",
                f"{p_metrics['repetition_avoidance']:.1f}%",
                delta=f"+{p_metrics['repetition_avoidance'] - b_metrics['repetition_avoidance']:.1f}% vs Baseline",
            )
        with col2:
            st.metric(
                "Consent Leakage Rate",
                f"{p_metrics['consent_leakage']:.1f}%",
                delta=f"{p_metrics['consent_leakage'] - b_metrics['consent_leakage']:.1f}% vs Baseline (Lower=Better)",
                delta_color="inverse",
            )
        with col3:
            st.metric(
                "Guardrail Compliance",
                f"{p_metrics['guardrail_compliance']:.1f}%",
                delta=f"+{p_metrics['guardrail_compliance'] - b_metrics['guardrail_compliance']:.1f}%",
            )
        with col4:
            st.metric(
                "Uncertainty Flagging Rate",
                f"{p_metrics['uncertainty_detection']:.1f}%",
                delta=f"+{p_metrics['uncertainty_detection'] - b_metrics['uncertainty_detection']:.1f}%",
            )

        st.markdown("---")

        # Metric Visualizations Chart
        chart_df = pd.DataFrame([
            {"Metric": "Repetition Avoidance (%)", "System": "Baseline", "Score": b_metrics["repetition_avoidance"]},
            {"Metric": "Repetition Avoidance (%)", "System": "Prototype", "Score": p_metrics["repetition_avoidance"]},
            {"Metric": "Consent Leakage (%)", "System": "Baseline", "Score": b_metrics["consent_leakage"]},
            {"Metric": "Consent Leakage (%)", "System": "Prototype", "Score": p_metrics["consent_leakage"]},
            {"Metric": "Guardrail Compliance (%)", "System": "Baseline", "Score": b_metrics["guardrail_compliance"]},
            {"Metric": "Guardrail Compliance (%)", "System": "Prototype", "Score": p_metrics["guardrail_compliance"]},
            {"Metric": "Uncertainty Flagging (%)", "System": "Baseline", "Score": b_metrics["uncertainty_detection"]},
            {"Metric": "Uncertainty Flagging (%)", "System": "Prototype", "Score": p_metrics["uncertainty_detection"]},
        ])

        fig = px.bar(
            chart_df,
            x="Metric",
            y="Score",
            color="System",
            barmode="group",
            title="Baseline vs. Prototype Benchmark Metrics Comparison",
            color_discrete_map={"Baseline": "#EF553B", "Prototype": "#00CC96"},
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📝 Error Analysis & Operational Findings")
        for line in res["error_analysis"]:
            st.markdown(f"- {line}")


if __name__ == "__main__":
    main()
