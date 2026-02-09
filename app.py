import streamlit as st
import pandas as pd

from agents.scout_agent import ScoutAgent
from agents.undercover_agent import UndercoverAgent
from agents.pattern_hunter_agent import PatternHunterAgent
from agents.decision_agent import DecisionAgent

from database.db import init_db, insert_event, get_connection

# Initialize DB
init_db()

st.set_page_config(page_title="FraudHound", layout="wide")

st.title("FraudHound - Gig Scam Detection System")

st.markdown("""
FraudHound is a role-based agentic AI system for detecting gig-economy scams.
It supports Users, Trust & Safety Analysts, and Researchers.
""")

# Sidebar role selection
mode = st.sidebar.radio(
    "Select Role",
    ["User", "Analyst / Developer", "Research / NGO"]
)

if mode == "User":
    st.header("Check a Job / Recruiter Message")
    
    user_message = st.text_area("Paste the message here:", height=180)
    
    if st.button("Check Message"):
        if not user_message.strip():
            st.warning("Paste a message")
        else:
            scout = ScoutAgent()
            fake_job = {"description": user_message}
            score, reasons, suggestion = scout.calculate_risk_score(fake_job)
            
            insert_event(user_message, score, "user")
            
            if score >= 0.7:
                st.error("HIGH SCAM RISK")
            elif score >= 0.4:
                st.warning("Suspicious")
            else:
                st.success("Likely Safe")
            
            st.metric("Risk Score", f"{score:.2f}")
            st.subheader("Reasons")
            st.write(reasons)
            st.subheader("Safety Suggestion")
            st.info(suggestion)

elif mode == "Analyst / Developer":
    st.header("Fraud Analysis Dashboard")
    
    uploaded_file = st.file_uploader(
        "Upload gig job listings CSV",
        type=["csv"]
    )
    
    if uploaded_file is not None:
        try:
            df_uploaded = pd.read_csv(uploaded_file)
            if df_uploaded.empty:
                st.warning("Uploaded file is empty.")
                st.stop()
        except Exception:
            st.error("Invalid CSV file. Please upload a proper CSV.")
            st.stop()
        
        st.subheader("Uploaded Dataset")
        st.dataframe(df_uploaded)
        
        if st.button("Run Full FraudHound Analysis"):
            with st.spinner("Running 4-agent pipeline..."):
                scout = ScoutAgent()
                
                # 1. Scout Agent
                st.subheader("1. Scout Agent Output")
                flagged_jobs = scout.scan_jobs(df=df_uploaded, threshold=0.4)
                
                if flagged_jobs.empty:
                    st.success("No suspicious jobs detected.")
                    st.stop()
                
                st.dataframe(flagged_jobs[["job_id", "job_title", "risk_score", "reasons"]])
                st.info(f"Flagged {len(flagged_jobs)} suspicious jobs out of {len(df_uploaded)} total")
                
                # 2. Undercover Agent
                st.subheader("2. Undercover Agent")
                undercover = UndercoverAgent()
                undercover_results = []
                for _, row in flagged_jobs.iterrows():
                    result = undercover.simulate_conversation(
                        row["job_id"],
                        row.get("description", "")
                    )
                    undercover_results.append(result)
                st.json(undercover_results)
                
                # 3. Pattern Hunter
                st.subheader("3. Pattern Hunter")
                hunter = PatternHunterAgent()
                fraud_rings = hunter.detect_fraud_rings(undercover_results)
                if fraud_rings:
                    st.success(f"Detected {len(fraud_rings)} fraud ring(s)")
                    st.json(fraud_rings)
                else:
                    st.info("No fraud rings detected")
                
                # 4. Decision Agent - PROFESSIONAL DISPLAY (NO EMOJIS)
                st.subheader("4. Decision Agent")
                decision_agent = DecisionAgent()
                
                for ring in fraud_rings:
                    decision = decision_agent.assess_ring(ring)
                    
                    # Professional ring analysis display
                    st.markdown(f"**Ring {ring['ring_id']}**")
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"- **Severity:** {decision['severity']}")
                        st.markdown(f"- **Action:** {decision['action']}")
                        st.markdown(f"- **Jobs Affected:** {len(decision['job_ids'])}")
                    
                    with col2:
                        st.markdown(f"**Status:** {decision['severity']}")
                    
                    st.markdown("**Detailed Analysis:**")
                    for i, reason in enumerate(decision['explanation'], 1):
                        st.markdown(f"  {i}. {reason}")
                    
                    st.markdown("---")
                    
                    # Save to database
                    insert_event(
                        text=f"{ring['ring_id']} ({decision['severity']})",
                        risk_score=1.0 if decision['severity'] in ["HIGH", "CRITICAL"] else 0.5,
                        source="analyst"
                    )
    
elif mode == "Research / NGO":
    st.header("Scam Pattern Insights")
    
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM scam_events ORDER BY timestamp DESC LIMIT 100", conn)
        conn.close()
        
        if df.empty:
            st.info("No data yet. Run User or Analyst mode first.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Records", len(df))
            with col2:
                st.metric("Avg Risk Score", f"{df['risk_score'].mean():.2f}")
            with col3:
                high_risk = len(df[df['risk_score'] >= 0.8])
                st.metric("High Risk Events", high_risk)
            
            st.subheader("Recent Events")
            st.dataframe(df[["text", "risk_score", "source", "timestamp"]])
            
            st.subheader("Risk Score Distribution")
            st.bar_chart(df["risk_score"].value_counts().sort_index())
            
            # Risk breakdown table
            risk_breakdown = df['risk_score'].apply(lambda x: 'HIGH' if x >= 0.8 else 'MEDIUM' if x >= 0.5 else 'LOW').value_counts()
            st.subheader("Risk Categories")
            st.dataframe(risk_breakdown.rename('Count'))
            
    except Exception as e:
        st.error(f"Database error: {str(e)}. Run User/Analyst mode first to populate data.")
