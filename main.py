import streamlit as st
import pandas as pd
import os

# --- 1. DATABASE ENGINE ---
def init_db():
    # Initialize 3 CSV files if they don't exist
    files = {
        "students.csv": ["Name", "Email", "Password", "Branch", "CGPA"],
        "companies.csv": ["Company_Name", "Email", "Password", "Role_Offered", "Package"],
        "apps.csv": ["Student_Email", "Company_Name", "Status"]
    }
    for file, cols in files.items():
        if not os.path.exists(file):
            pd.DataFrame(columns=cols).to_csv(file, index=False)

init_db()

# --- 2. SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None # 'student', 'company', or 'admin'

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
    Welcome to the centralized placement portal. 
    * **Students:** Register, view jobs, and track application status.
    * **Companies:** Post openings and shortlist candidates.
    * **Admin:** Monitor overall placement statistics.
    """)
    st.info("👈 Use the sidebar to log in to your specific zone.")

# --- 5. STUDENT ZONE ---
elif choice == "Student Zone":
    if st.session_state.role != "student":
        st.header("👨‍🎓 Student Access")
        t1, t2 = st.tabs(["Login", "New Registration"])
        with t2:
            with st.form("stu_reg"):
                n = st.text_input("Full Name")
                e = st.text_input("Email (Primary Key)").lower().strip()
                p = st.text_input("Password", type="password")
                b = st.selectbox("Branch", ["CSE", "IT", "ECE", "MECH"])
                c = st.number_input("CGPA", 0.0, 10.0, 7.5)
                if st.form_submit_button("Create Student Account"):
                    df = pd.read_csv("students.csv")
                    if e in df['Email'].values: st.error("Email already registered!")
                    else:
                        pd.concat([df, pd.DataFrame([[n,e,p,b,c]], columns=df.columns)]).to_csv("students.csv", index=False)
                        st.success("Registration Successful! Please Login.")
        with t1:
            le = st.text_input("Student Email").lower().strip()
            lp = st.text_input("Password", type="password")
            if st.button("Login as Student"):
                df = pd.read_csv("students.csv")
                user = df[(df['Email']==le) & (df['Password'].astype(str)==lp)]
                if not user.empty:
                    st.session_state.user, st.session_state.role = le, "student"
                    st.rerun()
                else: st.error("Invalid Credentials")
    else:
        st.header(f"👋 Welcome Back!")
        st.subheader("Your Application Tracking")
        apps = pd.read_csv("apps.csv")
        my_apps = apps[apps['Student_Email'] == st.session_state.user]
        if my_apps.empty: st.info("No applications sent yet.")
        else: st.table(my_apps)

# --- 6. COMPANY ZONE ---
elif choice == "Company Zone":
    if st.session_state.role != "company":
        st.header("🏢 Recruiter Access")
        t1, t2 = st.tabs(["Company Login", "Register Company"])
        with t2:
            with st.form("com_reg"):
                cn = st.text_input("Company Name")
                ce = st.text_input("Work Email").lower().strip()
                cp = st.text_input("Password", type="password")
                cr = st.text_input("Role Offered (e.g. SDE-1)")
                ck = st.text_input("Package (e.g. 12 LPA)")
                if st.form_submit_button("Register Company"):
                    df = pd.read_csv("companies.csv")
                    pd.concat([df, pd.DataFrame([[cn,ce,cp,cr,ck]], columns=df.columns)]).to_csv("companies.csv", index=False)
                    st.success("Company Profile Created!")
        with t1:
            cle = st.text_input("Company Email").lower().strip()
            clp = st.text_input("Password", type="password")
            if st.button("Company Login"):
                df = pd.read_csv("companies.csv")
                comp = df[(df['Email']==cle) & (df['Password'].astype(str)==clp)]
                if not comp.empty:
                    st.session_state.user = comp.iloc[0]['Company_Name']
                    st.session_state.role = "company"
                    st.rerun()
                else: st.error("Company not found.")
    else:
        st.header(f"Recruiter Dashboard: {st.session_state.user}")
        st.subheader("Manage Applicants")
        apps = pd.read_csv("apps.csv")
        my_apps = apps[apps['Company_Name'] == st.session_state.user]
        if my_apps.empty: st.info("No students have applied yet.")
        else:
            for i, row in my_apps.iterrows():
                col1, col2, col3 = st.columns([3,1,1])
                col1.write(f"📧 **{row['Student_Email']}** | Current Status: {row['Status']}")
                if col2.button("Accept", key=f"acc_{i}"):
                    apps.at[i, 'Status'] = "Accepted"
                    apps.to_csv("apps.csv", index=False)
                    st.rerun()
                if col3.button("Reject", key=f"rej_{i}"):
                    apps.at[i, 'Status'] = "Rejected"
                    apps.to_csv("apps.csv", index=False)
                    st.rerun()

# --- 7. JOB BOARD ---
elif choice == "Job Board":
    st.header("💼 Available Opportunities")
    comps = pd.read_csv("companies.csv")
    apps = pd.read_csv("apps.csv")
    if comps.empty: st.warning("No companies are hiring at the moment.")
    else:
        for i, job in comps.iterrows():
            with st.container(border=True):
                st.subheader(job['Company_Name'])
                st.write(f"**Role:** {job['Role_Offered']} | **Salary:** {job['Package']}")
                if st.session_state.role == "student":
                    already = not apps[(apps['Student_Email']==st.session_state.user) & (apps['Company_Name']==job['Company_Name'])].empty
                    if st.button(f"Apply to {job['Company_Name']}", disabled=already, key=f"app_btn_{i}"):
                        new_app = pd.DataFrame([[st.session_state.user, job['Company_Name'], "Pending"]], columns=apps.columns)
                        pd.concat([apps, new_app]).to_csv("apps.csv", index=False)
                        st.success("Application Submitted!")
                        st.rerun()

# --- 8. ADMIN DASHBOARD ---
elif choice == "Admin Dashboard":
    st.header("⚙️ System Administration")
    passwd = st.text_input("Enter Admin Password", type="password")
    if passwd == "admin123":
        s_df, c_df, a_df = pd.read_csv("students.csv"), pd.read_csv("companies.csv"), pd.read_csv("apps.csv")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Students", len(s_df))
        c2.metric("Companies", len(c_df))
        c3.metric("Applications", len(a_df))
        
        st.write("### Global Application View")
        st.dataframe(a_df, use_container_width=True)
        
        if st.button("🚨 Reset All Placement Data", type="primary"):
            for f in ["students.csv", "companies.csv", "apps.csv"]:
                pd.read_csv(f).iloc[0:0].to_csv(f, index=False)
            st.rerun()
    elif passwd: st.error("Wrong password.")