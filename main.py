import streamlit as st
import pandas as pd
import os
import time
from io import BytesIO

# --- PDF Generation Setup ---
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# --- Page Config ---
st.set_page_config(page_title="Placement Portal", layout="wide", page_icon="🎓")

# ==========================================
# DATABASE & HELPER FUNCTIONS
# ==========================================

DB_FILES = {
    "students": "database.csv",
    "companies": "companies.csv",
    "allocations": "allocations.csv",
    "applications": "applications.csv"
}

def init_db():
    """Initializes CSV files with headers if they don't exist."""
    if not os.path.exists(DB_FILES["students"]):
        pd.DataFrame(columns=["Name", "Email", "Password", "CGPA", "Branch", "Boosted"]).to_csv(DB_FILES["students"], index=False)
    if not os.path.exists(DB_FILES["companies"]):
        pd.DataFrame(columns=["Company", "Email", "Address", "Password", "Package", "Criteria"]).to_csv(DB_FILES["companies"], index=False)
    if not os.path.exists(DB_FILES["allocations"]):
        pd.DataFrame(columns=["Student_Email", "Company", "Package", "Date"]).to_csv(DB_FILES["allocations"], index=False)
    if not os.path.exists(DB_FILES["applications"]):
        pd.DataFrame(columns=["Student_Email", "Company_Name", "Status"]).to_csv(DB_FILES["applications"], index=False)

def safe_read_csv(filename):
    """Reads CSV and ensures columns exist for backward compatibility."""
    try:
        df = pd.read_csv(filename)
        if filename == DB_FILES["students"] and "Boosted" not in df.columns:
            df["Boosted"] = "False"
        if filename == DB_FILES["applications"] and "Status" not in df.columns:
            df["Status"] = "Pending"
        return df.fillna("")
    except Exception:
        return pd.DataFrame()

def append_to_csv(filename, data_dict):
    """Appends a single row to a CSV safely."""
    df = safe_read_csv(filename)
    new_row = pd.DataFrame([data_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(filename, index=False)

init_db()

# ==========================================
# SESSION STATE MANAGEMENT
# ==========================================
if "student_logged_in" not in st.session_state:
    st.session_state.student_logged_in = False
    st.session_state.user = None

if "company_logged_in" not in st.session_state:
    st.session_state.company_logged_in = False
    st.session_state.company = None

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("Navigation")
menu = ["Home", "Student Zone", "Company Zone", "Job Board", "Admin Dashboard"]
choice = st.sidebar.radio("Go to", menu)

# ==========================================
# 1. HOME PAGE
# ==========================================
if choice == "Home":
    st.title("🎓 College Placement Portal")
    st.markdown("""
    Welcome to the **Unified Placement Cell**. This platform bridges the gap between talented students and top-tier recruiters.
    
    * **Students:** Build resumes, apply to jobs, and track applications.
    * **Companies:** Post job drives and manage your candidate pipeline.
    * **Admin:** Overlook the entire placement statistics.
    """)
    

# ==========================================
# 2. STUDENT ZONE (Registration, Login, Resume)
# ==========================================
elif choice == "Student Zone":
    if not st.session_state.student_logged_in:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab2:
            st.subheader("Student Registration")
            with st.form("student_reg"):
                name = st.text_input("Name")
                email = st.text_input("College Email").lower().strip()
                pwd = st.text_input("Password", type="password")
                cgpa = st.number_input("CGPA", 0.0, 10.0, 7.0)
                branch = st.selectbox("Branch", ["CSE", "IT", "ECE", "Mechanical", "Civil"])
                if st.form_submit_button("Register"):
                    df = safe_read_csv(DB_FILES["students"])
                    if email in df['Email'].values:
                        st.error("Email already registered.")
                    else:
                        append_to_csv(DB_FILES["students"], {"Name": name, "Email": email, "Password": pwd, "CGPA": cgpa, "Branch": branch, "Boosted": "False"})
                        st.success("Registration successful! Go to Login tab.")

        with tab1:
            st.subheader("Student Login")
            l_email = st.text_input("Email").lower().strip()
            l_pwd = st.text_input("Password", type="password")
            if st.button("Login"):
                df = safe_read_csv(DB_FILES["students"])
                user = df[(df['Email'] == l_email) & (df['Password'].astype(str) == l_pwd)]
                if not user.empty:
                    st.session_state.student_logged_in = True
                    st.session_state.user = user.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
    else:
        # LOGGED IN STUDENT VIEW
        st.header(f"Welcome, {st.session_state.user['Name']}!")
        
        # Profile Boost Section
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Branch:** {st.session_state.user['Branch']} | **CGPA:** {st.session_state.user['CGPA']}")
            with col2:
                if str(st.session_state.user.get('Boosted')) == "True":
                    st.markdown("✅ **Boosted Profile**")
                else:
                    if st.button("🚀 Boost Profile (₹300)"):
                        df = safe_read_csv(DB_FILES["students"])
                        df.loc[df['Email'] == st.session_state.user['Email'], 'Boosted'] = "True"
                        df.to_csv(DB_FILES["students"], index=False)
                        st.session_state.user['Boosted'] = "True"
                        st.success("Profile Boosted!")
                        st.rerun()

        # Application Status
        st.subheader("My Applications")
        apps = safe_read_csv(DB_FILES["applications"])
        my_apps = apps[apps['Student_Email'] == st.session_state.user['Email']]
        if my_apps.empty:
            st.info("No applications yet. Visit the Job Board!")
        else:
            st.table(my_apps)

        if st.button("Logout"):
            st.session_state.student_logged_in = False
            st.rerun()

# ==========================================
# 3. JOB BOARD
# ==========================================
elif choice == "Job Board":
    st.title("📢 Active Job Openings")
    df_jobs = safe_read_csv(DB_FILES["companies"])
    
    if df_jobs.empty:
        st.info("No companies are hiring at the moment.")
    else:
        for idx, job in df_jobs.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(job['Company'])
                    st.write(f"💰 **Package:** {job['Package']} | 📍 **Location:** {job['Address']}")
                    st.write(f"🎯 **Criteria:** {job['Criteria']}")
                with col2:
                    if st.session_state.student_logged_in:
                        apps = safe_read_csv(DB_FILES["applications"])
                        already_applied = not apps[(apps['Student_Email'] == st.session_state.user['Email']) & (apps['Company_Name'] == job['Company'])].empty
                        
                        if already_applied:
                            st.button("Applied", disabled=True, key=f"btn_{idx}")
                        else:
                            if st.button("Apply Now", key=f"btn_{idx}"):
                                append_to_csv(DB_FILES["applications"], {"Student_Email": st.session_state.user['Email'], "Company_Name": job['Company'], "Status": "Pending"})
                                st.success("Applied!")
                                st.rerun()
                    else:
                        st.warning("Login to apply")

# ==========================================
# 4. ADMIN DASHBOARD
# ==========================================
elif choice == "Admin Dashboard":
    st.title("⚙️ Admin Portal")
    pwd = st.text_input("Enter Admin Password", type="password")
    
    if pwd == "admin123":
        df_students = safe_read_csv(DB_FILES["students"])
        df_apps = safe_read_csv(DB_FILES["applications"])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Students", len(df_students))
        col2.metric("Applications", len(df_apps))
        
        st.subheader("Student Database")
        st.dataframe(df_students)
        
        if st.button("Clear All Data", type="primary"):
            for f in DB_FILES.values():
                if os.path.exists(f): os.remove(f)
            init_db()
            st.rerun()
    elif pwd:
        st.error("Access Denied")

# Footer
st.sidebar.markdown("---")
st.sidebar.write("Developed for College Placement Cell 2026")