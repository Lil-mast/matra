"""Matra Admin Dashboard — Streamlit-based analytics and reporting interface.

Provides:
  - Real-time maternal health metrics and aggregated statistics
  - Risk stratification breakdown (high/intermediate/low)
  - Regional referral tracking and case management
  - User activity and clinic performance monitoring
  - Exportable reports for district health managers
"""

import os
import sys
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from models import db, MaternalIntake, User
from config import Config
from app import create_app

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Matra Admin Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .risk-high {
        color: #d32f2f;
        font-weight: bold;
    }
    .risk-intermediate {
        color: #f57c00;
        font-weight: bold;
    }
    .risk-low {
        color: #388e3c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Database Session
# ---------------------------------------------------------------------------

@st.cache_resource
def init_db():
    """Initialize Flask app and database connection."""
    app = create_app(Config)
    with app.app_context():
        db.create_all()
        return app


app = init_db()

def get_db_session():
    """Get a database session within Flask app context."""
    with app.app_context():
        return db.session


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _get_bleeding_level(bleeding_code: int) -> str:
    """
    Safely map bleeding code to description.
    
    Args:
        bleeding_code: 0 = None, 1 = Light, 2 = Severe
    
    Returns:
        Human-readable bleeding level
    """
    bleeding_map = {0: "None", 1: "Light", 2: "Severe"}
    return bleeding_map.get(bleeding_code, "Unknown")


# ---------------------------------------------------------------------------
# Authentication & Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title("🏥 Matra Admin")
st.sidebar.markdown("---")

# Simple auth — in production, use OAuth2 or SAML
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.sidebar.subheader("Admin Login")
    with st.sidebar.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            with app.app_context():
                user = User.query.filter_by(username=username).first()
                if user and user.role in ["hospital", "manager"]:
                    import bcrypt
                    if bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.sidebar.error("Invalid credentials")
                else:
                    st.sidebar.error("Admin access denied")
    st.stop()

# Authenticated user
user = st.session_state.user
st.sidebar.success(f"Logged in as: **{user.username}**")
st.sidebar.markdown(f"Role: `{user.role}` | Clinic: `{user.clinic_name}`")

if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.markdown("---")

# ---------------------------------------------------------------------------
# Main Dashboard
# ---------------------------------------------------------------------------

st.title("📊 Matra Maternal Health Dashboard")

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Risk Analysis", "Referrals", "Users & Activity"])

with tab1:
    st.header("System Overview")
    
    with app.app_context():
        # Fetch metrics
        total_assessments = db.session.query(MaternalIntake).count()
        last_24h = datetime.utcnow() - timedelta(hours=24)
        assessments_today = db.session.query(MaternalIntake).filter(
            MaternalIntake.created_at >= last_24h
        ).count()
        high_risk = db.session.query(MaternalIntake).filter_by(risk_level="high").count()
        intermediate_risk = db.session.query(MaternalIntake).filter_by(risk_level="intermediate").count()
        low_risk = db.session.query(MaternalIntake).filter_by(risk_level="low").count()
        total_users = db.session.query(User).count()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Assessments", total_assessments, f"+{assessments_today} today")
    col2.metric("🔴 High Risk", high_risk, f"{(high_risk/max(total_assessments, 1)*100):.1f}%")
    col3.metric("🟠 Intermediate", intermediate_risk, f"{(intermediate_risk/max(total_assessments, 1)*100):.1f}%")
    col4.metric("🟢 Low Risk", low_risk, f"{(low_risk/max(total_assessments, 1)*100):.1f}%")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Risk Distribution")
        with app.app_context():
            risk_data = pd.DataFrame({
                "Risk Level": ["High", "Intermediate", "Low"],
                "Count": [high_risk, intermediate_risk, low_risk],
                "Color": ["#d32f2f", "#f57c00", "#388e3c"]
            })
        fig = px.pie(risk_data, values="Count", names="Risk Level", color="Risk Level",
                    color_discrete_map={"High": "#d32f2f", "Intermediate": "#f57c00", "Low": "#388e3c"})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Assessments Over Time (Last 30 Days)")
        with app.app_context():
            last_30d = datetime.utcnow() - timedelta(days=30)
            daily_counts = db.session.query(
                db.func.date(MaternalIntake.created_at).label("date"),
                db.func.count(MaternalIntake.id).label("count")
            ).filter(MaternalIntake.created_at >= last_30d).group_by("date").all()
        
        if daily_counts:
            df_daily = pd.DataFrame(daily_counts, columns=["date", "count"])
            fig = px.line(df_daily, x="date", y="count", markers=True, 
                         title="Daily Assessment Trend")
            fig.update_xaxes(title="Date")
            fig.update_yaxes(title="Assessments")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for the last 30 days")

with tab2:
    st.header("Risk Analysis & Patterns")
    
    with app.app_context():
        # Fetch recent high-risk cases
        high_risk_cases = db.session.query(MaternalIntake).filter_by(
            risk_level="high"
        ).order_by(MaternalIntake.created_at.desc()).limit(20).all()
    
    if high_risk_cases:
        st.subheader(f"Recent High-Risk Cases ({len(high_risk_cases)} of last 100)")
        
        case_data = [{
            "ID": case.id,
            "Age": case.age,
            "Parity": case.parity,
            "Systolic BP": case.systolic_bp,
            "Diastolic BP": case.diastolic_bp,
            "Pulse": case.pulse,
            "Bleeding": _get_bleeding_level(case.bleeding),
            "Fever": "Yes" if case.fever else "No",
            "Convulsions": "Yes" if case.convulsions else "No",
            "Action": case.recommended_action,
            "Created": case.created_at.strftime("%Y-%m-%d %H:%M"),
        } for case in high_risk_cases]
        
        df_cases = pd.DataFrame(case_data)
        st.dataframe(df_cases, use_container_width=True, height=400)
        
        # Export option
        csv = df_cases.to_csv(index=False)
        st.download_button("📥 Download as CSV", csv, "high_risk_cases.csv", "text/csv")
    else:
        st.success("✅ No high-risk cases detected")
    
    st.markdown("---")
    
    # Vital sign distributions
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Systolic BP Distribution")
        with app.app_context():
            bps = db.session.query(MaternalIntake.systolic_bp).all()
        if bps:
            df_bp = pd.DataFrame(bps, columns=["Systolic BP"])
            fig = px.histogram(df_bp, x="Systolic BP", nbins=30, title="Distribution of Systolic BP")
            fig.add_vline(x=140, line_dash="dash", line_color="orange", annotation_text="Warning (140)")
            fig.add_vline(x=160, line_dash="dash", line_color="red", annotation_text="Critical (160)")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Pulse Distribution")
        with app.app_context():
            pulses = db.session.query(MaternalIntake.pulse).all()
        if pulses:
            df_pulse = pd.DataFrame(pulses, columns=["Pulse"])
            fig = px.histogram(df_pulse, x="Pulse", nbins=30, title="Distribution of Pulse")
            fig.add_vline(x=100, line_dash="dash", line_color="orange", annotation_text="Elevated (100)")
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Referral Tracking")
    
    with app.app_context():
        referrals = db.session.query(MaternalIntake).filter(
            MaternalIntake.risk_level.in_(["high", "intermediate"])
        ).order_by(MaternalIntake.created_at.desc()).limit(50).all()
    
    if referrals:
        st.metric("Pending Referrals (High + Intermediate)", len(referrals))
        
        referral_data = [{
            "ID": case.id,
            "Risk": case.risk_level.upper(),
            "Clinic": case.user.clinic_name if case.user else "Unknown",
            "Action": case.recommended_action or "Assess further",
            "Reporter": case.user.username if case.user else "System",
            "Date": case.created_at.strftime("%Y-%m-%d %H:%M"),
        } for case in referrals]
        
        df_referrals = pd.DataFrame(referral_data)
        st.dataframe(df_referrals, use_container_width=True, height=400)
        
        csv = df_referrals.to_csv(index=False)
        st.download_button("📥 Export Referrals", csv, "referrals.csv", "text/csv")
    else:
        st.success("✅ No pending referrals")

with tab4:
    st.header("Users & Activity")
    
    with app.app_context():
        # OPTIMIZED: Use single query instead of N+1
        users = db.session.query(User).all()
        
        if users:
            # Fetch all assessment counts in one query
            from sqlalchemy import func
            assessment_counts = db.session.query(
                MaternalIntake.user_id,
                func.count(MaternalIntake.id).label("total")
            ).group_by(MaternalIntake.user_id).all()
            assessment_dict = {uid: count for uid, count in assessment_counts}
            
            # Fetch last activity for each user in one query
            latest_intakes = db.session.query(
                MaternalIntake.user_id,
                func.max(MaternalIntake.created_at).label("last_created")
            ).group_by(MaternalIntake.user_id).all()
            last_activity_dict = {uid: created for uid, created in latest_intakes}
            
            user_stats = []
            for u in users:
                assessments = assessment_dict.get(u.id, 0)
                last_activity = last_activity_dict.get(u.id)
                
                user_stats.append({
                    "Username": u.username,
                    "Role": u.role,
                    "Clinic": u.clinic_name or "—",
                    "Assessments": assessments,
                    "Last Activity": last_activity.strftime("%Y-%m-%d %H:%M") if last_activity else "Never",
                    "Joined": u.created_at.strftime("%Y-%m-%d"),
                })
        
            df_users = pd.DataFrame(user_stats)
            st.dataframe(df_users, use_container_width=True)
            
            # Activity by User (Last 7 Days) - OPTIMIZED
            st.subheader("Activity by User (Last 7 Days)")
            last_7d = datetime.utcnow() - timedelta(days=7)
            
            activity_counts = db.session.query(
                User.username,
                func.count(MaternalIntake.id).label("count")
            ).join(
                MaternalIntake, MaternalIntake.user_id == User.id
            ).filter(
                MaternalIntake.created_at >= last_7d
            ).group_by(User.username).all()
            
            if activity_counts:
                df_activity = pd.DataFrame(
                    [{"User": username, "Assessments (7d)": count} for username, count in activity_counts]
                )
                fig = px.bar(df_activity, x="User", y="Assessments (7d)", title="Active Users (Last 7 Days)")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No users registered yet")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <p>Matra Maternal Health Dashboard | Built with Streamlit & Flask</p>
    <p>© 2026 — Confidential | Health Data Protection Act Compliance</p>
</div>
""", unsafe_allow_html=True)
