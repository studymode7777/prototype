import streamlit as st
import pandas as pd
import os

# --- 1. SELF-HEALING DATABASE ENGINE ---
def init_db():
    schema = {
        "students.csv": ["Name", "Email", "Password", "Branch", "CGPA"],
        "companies.csv": ["Company_Name", "Email", "Password", "Role_Offered", "Package"],
        "apps.csv": ["Student_Email", "Company_Name", "Status"]
    }
    for file, required_cols in schema.items():
        if not os.path.exists(file):
            pd.DataFrame(columns=required_cols).to_csv(file, index=False)
        else:
            df = pd.read_csv(file)
            if list(df.columns) != required_cols:
                # This fixes the ValueError by updating old CSV files automatically
                pd.DataFrame(columns=required_cols).to_csv(file, index=False)

init_db()

# --- 2. SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None 

st.set_page_config(page_title="Placement Portal", page_icon="🎓", layout="wide")

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("🚀 Career Hub")
if st.session_state.user:
    st.sidebar.success(f"Logged in: {st.session_state.user}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()

menu = ["Home", "Student Zone", "Company Zone", "Job Board", "Admin Dashboard"]
choice = st.sidebar.selectbox("Navigate To", menu)

# --- 4. HOME PAGE ---
if choice == "Home":
    st.title("🎓 College Placement Management System")
    st.markdown("""
    Welcome to the centralized portal for campus recruitment. 
    * **Students:** Register and apply for your dream roles.
    * **Recruiters:** Post openings and manage talent.
    * **Admins:** Oversee the entire placement lifecycle.
    """)
    st.info("👈 Select a zone from the sidebar to begin.")

# --- 5. STUDENT ZONE ---
elif choice == "Student Zone":
    if st.session_state.role != "student":
        st.header("👨‍🎓 Student Access")
        t1, t2 = st.tabs(["Login", "Register"])
        with t2:
            with st.form("stu_reg"):
                n, e = st.text_input("Full Name"), st.text_input("Email").lower().strip()
                p, b = st.text_input("Password", type="password"), st.selectbox("Branch", ["CSE", "IT", "ECE", "MECH"])
                c = st.number_input("CGPA", 0.0, 10.0, 7.5)
                if st.form_submit_button("Create Account"):
                    df = pd.read_csv("students.csv")
                    if e in df['Email'].values: st.error("Email exists!")
                    else:
                        new_stu = pd.DataFrame([[n, e, p, b, c]], columns=df.columns)
                        pd.concat([df, new_stu]).to_csv("students.csv", index=False)
                        st.success("Registered! You can now login.")
        with t1:
            le, lp = st.text_input("Email").lower().strip(), st.text_input("Password", type="password")
            if st.button("Student Login"):
                df = pd.read_csv("students.csv")
                user = df[(df['Email']==le) & (df['Password'].astype(str)==lp)]
                if not user.empty:
                    st.session_state.user, st.session_state.role = le, "student"
                    st.rerun()
                else: st.error("Invalid Credentials")
    else:
        st.header(f"Welcome Student!")
        apps = pd.read_csv("apps.csv")
        my_apps = apps[apps['Student_Email'] == st.session_state.user]
        st.subheader("My Application Status")
        if not my_apps.empty:
            st.dataframe(my_apps, use_container_width=True, hide_index=True)
        else:
            st.info("No applications yet. Visit the Job Board!")

# --- 6. COMPANY ZONE ---
elif choice == "Company Zone":
    if st.session_state.role != "company":
        st.header("🏢 Recruiter Access")
        t1, t2 = st.tabs(["Login", "Register"])
        with t2:
            with st.form("com_reg"):
                cn, ce = st.text_input("Company Name"), st.text_input("Work Email").lower().strip()
                cp, cr = st.text_input("Password", type="password"), st.text_input("Role")
                ck = st.text_input("Package (e.g. 12 LPA)")
                if st.form_submit_button("Register Company"):
                    df = pd.read_csv("companies.csv")
                    new_comp = pd.DataFrame([[cn, ce, cp, cr, ck]], columns=df.columns)
                    pd.concat([df, new_comp]).to_csv("companies.csv", index=False)
                    st.success("Company Profile Created!")
        with t1:
            cle, clp = st.text_input("Email").lower().strip(), st.text_input("Password", type="password")
            if st.button("Company Login"):
                df = pd.read_csv("companies.csv")
                comp = df[(df['Email']==cle) & (df['Password'].astype(str)==clp)]
                if not comp.empty:
                    st.session_state.user, st.session_state.role = comp.iloc[0]['Company_Name'], "company"
                    st.rerun()
                else: st.error("Invalid Credentials")
    else:
        st.header(f"Dashboard: {st.session_state.user}")
        apps = pd.read_csv("apps.csv")
        my_apps = apps[apps['Company_Name'] == st.session_state.user]
        if my_apps.empty: st.info("No applicants yet.")
        else:
            for i, row in my_apps.iterrows():
                with st.expander(f"Applicant: {row['Student_Email']}"):
                    st.write(f"Current Status: **{row['Status']}**")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Accept", key=f"acc_{i}"):
                        apps.at[i, 'Status'] = "Accepted"
                        apps.to_csv("apps.csv", index=False)
                        st.rerun()
                    if c2.button("❌ Reject", key=f"rej_{i}"):
                        apps.at[i, 'Status'] = "Rejected"
                        apps.to_csv("apps.csv", index=False)
                        st.rerun()

# --- 7. JOB BOARD (With Search) ---
elif choice == "Job Board":
    st.header("💼 Available Jobs")
    comps, apps = pd.read_csv("companies.csv"), pd.read_csv("apps.csv")
    
    search = st.text_input("🔍 Search by Company or Role").lower()
    
    if comps.empty: st.warning("No jobs posted yet.")
    else:
        # Filter matching rows
        filtered = comps[comps['Company_Name'].str.lower().str.contains(search) | 
                         comps['Role_Offered'].str.lower().str.contains(search)]
        
        for i, job in filtered.iterrows():
            with st.container(border=True):
                st.subheader(job['Company_Name'])
                st.write(f"**Role:** {job['Role_Offered']} | **Salary:** {job['Package']}")
                if st.session_state.role == "student":
                    already = not apps[(apps['Student_Email']==st.session_state.user) & (apps['Company_Name']==job['Company_Name'])].empty
                    if st.button(f"Apply Now", disabled=already, key=f"ap_{i}"):
                        new_app = pd.DataFrame([[st.session_state.user, job['Company_Name'], "Pending"]], columns=apps.columns)
                        pd.concat([apps, new_app]).to_csv("apps.csv", index=False)
                        st.success("Applied!")
                        st.rerun()

# --- 8. ADMIN DASHBOARD (With Status Filter) ---
elif choice == "Admin Dashboard":
    st.header("⚙️ Admin Control Panel")
    pw = st.text_input("Password", type="password")
    if pw == "admin123":
        s_df, c_df, a_df = pd.read_csv("students.csv"), pd.read_csv("companies.csv"), pd.read_csv("apps.csv")
        
        status_filter = st.selectbox("Filter Applications by Status", ["All", "Pending", "Accepted", "Rejected"])
        
        display_df = a_df if status_filter == "All" else a_df[a_df['Status'] == status_filter]
        
        st.metric("Total Shown", len(display_df))
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        if st.button("🚨 Reset All Data", type="primary"):
            for f in ["students.csv", "companies.csv", "apps.csv"]:
                if os.path.exists(f): os.remove(f)
            init_db()
            st.rerun()