"""
FixOpenclaw Web Dashboard

Streamlit-based web interface for monitoring and controlling the system.
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# Add project root to path so `from src.xxx` imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.orchestrator import Orchestrator
from src.utils.config_loader import load_config
from src.utils.logger import setup_logger


# Page configuration
st.set_page_config(
    page_title="FixOpenclaw Dashboard",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_orchestrator():
    """Initialize orchestrator (cached)."""
    config = load_config()
    orchestrator = Orchestrator(config)
    orchestrator.start()
    return orchestrator, config


def format_status(status: str) -> str:
    """Format status with color."""
    if status in ["running", "healthy", "success"]:
        return f'<span class="status-success">{status.upper()}</span>'
    elif status in ["error", "failed", "unhealthy"]:
        return f'<span class="status-error">{status.upper()}</span>'
    elif status in ["warning", "degraded"]:
        return f'<span class="status-warning">{status.upper()}</span>'
    else:
        return status.upper()


def main():
    """Main dashboard function."""
    # Initialize orchestrator
    orchestrator, config = initialize_orchestrator()

    # Header
    st.markdown('<div class="main-header">🔧 FixOpenclaw Dashboard</div>', unsafe_allow_html=True)
    st.markdown("**Autonomous OpenClaw Diagnostics & Repair System**")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Control Panel")

        # System status
        status = orchestrator.get_system_status()
        system_status = status["system_state"]["status"]

        st.markdown(f"**System Status:** {format_status(system_status)}", unsafe_allow_html=True)

        st.markdown("---")

        # Actions
        st.subheader("Actions")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔍 Scan Now", use_container_width=True):
                with st.spinner("Scanning..."):
                    result = orchestrator.trigger_monitoring()
                    st.success(f"Found {len(result.get('anomalies', []))} anomalies")

        with col2:
            if st.button("🔄 Full Cycle", use_container_width=True):
                with st.spinner("Running cycle..."):
                    result = orchestrator.run_autonomous_cycle()
                    if result["status"] == "success":
                        st.success("Cycle complete!")
                    else:
                        st.error("Cycle failed")

        st.markdown("---")

        # Configuration
        st.subheader("Configuration")

        # Auto-refresh
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        if auto_refresh:
            refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 10)
            time.sleep(refresh_interval)
            st.rerun()

        # LLM Provider
        current_provider = config.get("llm_provider", {}).get("default", "openai")
        st.text_input("LLM Provider", value=current_provider, disabled=True)

    # Main content
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🔍 Monitoring",
        "🩺 Diagnostics",
        "🔧 Repairs",
        "📈 Metrics"
    ])

    # Tab 1: Overview
    with tab1:
        st.header("System Overview")

        # Metrics
        metrics = orchestrator.get_metrics()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Anomalies Detected",
                metrics["total_anomalies_detected"],
                delta=None
            )

        with col2:
            st.metric(
                "Repairs Attempted",
                metrics["total_repairs_attempted"],
                delta=None
            )

        with col3:
            st.metric(
                "Repairs Successful",
                metrics["total_repairs_successful"],
                delta=None
            )

        with col4:
            success_rate = metrics["success_rate"] * 100
            st.metric(
                "Success Rate",
                f"{success_rate:.1f}%",
                delta=None
            )

        st.markdown("---")

        # Agent Status
        st.subheader("Agent Status")

        agent_cols = st.columns(4)

        for idx, (agent_name, agent_status) in enumerate(status["agents"].items()):
            with agent_cols[idx]:
                st.markdown(f"**{agent_name.title()}**")
                st.markdown(f"Status: {format_status(agent_status['status'])}", unsafe_allow_html=True)
                st.text(f"Task: {agent_status.get('current_task', 'Idle')}")

        st.markdown("---")

        # Recent Activity
        st.subheader("Recent Activity")

        if metrics["last_activity"]:
            st.info(f"Last activity: {metrics['last_activity']}")
        else:
            st.info("No recent activity")

    # Tab 2: Monitoring
    with tab2:
        st.header("Monitoring & Anomaly Detection")

        # Get monitor agent status
        monitor_status = orchestrator.get_agent_status("monitor")

        if monitor_status:
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("Monitored Log Files")
                log_paths = config.get("monitoring", {}).get("log_paths", [])
                for log_path in log_paths:
                    st.text(f"📄 {log_path}")

            with col2:
                st.subheader("Detection Stats")
                st.metric("Total Anomalies", monitor_status.get("metrics", {}).get("anomalies_detected", 0))

            st.markdown("---")

            # Run monitoring
            if st.button("Run Monitoring Scan"):
                with st.spinner("Scanning logs..."):
                    result = orchestrator.trigger_monitoring()

                    if result.get("anomalies"):
                        st.success(f"Found {len(result['anomalies'])} anomalies")

                        # Display anomalies
                        df = pd.DataFrame(result["anomalies"])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No anomalies detected")

    # Tab 3: Diagnostics
    with tab3:
        st.header("Diagnostic Analysis")

        diagnostic_status = orchestrator.get_agent_status("diagnostic")

        if diagnostic_status:
            st.metric(
                "Diagnostics Completed",
                diagnostic_status.get("metrics", {}).get("diagnostics_completed", 0)
            )

            st.markdown("---")

            # Display diagnostic history
            st.subheader("Diagnostic History")

            diagnostic_agent = orchestrator.agents.get("diagnostic")
            if diagnostic_agent and diagnostic_agent.diagnostic_history:
                for diag in diagnostic_agent.diagnostic_history[-10:]:  # Last 10
                    with st.expander(f"🩺 {diag.get('anomaly_type')} - {diag.get('severity')}"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("**Root Cause:**")
                            st.text(diag.get("root_cause", {}).get("summary", "Unknown"))

                        with col2:
                            st.markdown("**Impact:**")
                            st.text(diag.get("impact", {}).get("impact_level", "Unknown"))

                        st.markdown("**Recommendations:**")
                        recommendations = diag.get("recommendations", {})
                        for action in recommendations.get("immediate_actions", []):
                            st.text(f"• {action}")
            else:
                st.info("No diagnostic history available")

    # Tab 4: Repairs
    with tab4:
        st.header("Repair Operations")

        repair_status = orchestrator.get_agent_status("repair")

        if repair_status:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Repairs Generated", len(orchestrator.agents["repair"].repair_history))

            with col2:
                st.metric("Successful", len(orchestrator.agents["repair"].successful_repairs))

            with col3:
                st.metric("Failed", len(orchestrator.agents["repair"].failed_repairs))

            st.markdown("---")

            # Display repair history
            st.subheader("Repair History")

            repair_agent = orchestrator.agents.get("repair")
            if repair_agent and repair_agent.repair_history:
                for repair in repair_agent.repair_history[-10:]:  # Last 10
                    status_icon = "✅" if repair.get("status") == "success" else "❌"
                    with st.expander(f"{status_icon} {repair.get('repair_id')} - {repair.get('status')}"):
                        st.markdown(f"**Applied at:** {repair.get('applied_at', 'N/A')}")
                        st.markdown(f"**Status:** {repair.get('status')}")

                        if repair.get("changes_made"):
                            st.markdown("**Changes:**")
                            for change in repair["changes_made"]:
                                st.text(f"• {change}")

                        if repair.get("validation"):
                            val = repair["validation"]
                            st.markdown(f"**Validation:** {val.get('status')}")
            else:
                st.info("No repair history available")

    # Tab 5: Metrics
    with tab5:
        st.header("System Metrics")

        metrics = orchestrator.get_metrics()

        # Create metrics dataframe
        metrics_data = {
            "Metric": [
                "Total Anomalies Detected",
                "Total Repairs Attempted",
                "Total Repairs Successful",
                "Total Repairs Failed",
                "Success Rate",
                "Active Agents",
            ],
            "Value": [
                metrics["total_anomalies_detected"],
                metrics["total_repairs_attempted"],
                metrics["total_repairs_successful"],
                metrics["total_repairs_failed"],
                f"{metrics['success_rate'] * 100:.1f}%",
                metrics["agent_count"],
            ]
        }

        df = pd.DataFrame(metrics_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Performance metrics
        st.subheader("Performance")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("System Status", metrics["system_status"])

        with col2:
            if metrics["last_activity"]:
                last_activity_time = datetime.fromisoformat(metrics["last_activity"])
                time_since = datetime.now() - last_activity_time
                st.metric("Time Since Last Activity", f"{time_since.seconds}s ago")

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666;">'
        'FixOpenclaw v0.1.0 | Built with ❤️ for autonomous system reliability'
        '</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
