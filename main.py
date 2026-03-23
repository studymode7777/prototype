import streamlit as st
import pandas as pd
import os

# --- 1. SELF-HEALING DATABASE ENGINE ---
def init_db():
    # Define the exact required structure
    schema = {
        "students.csv": ["Name", "Email", "Password", "Branch", "CGPA"],
        "companies.csv": ["Company_Name", "Email", "Password", "Role_Offered", "Package"],
        "apps.csv": ["Student_Email", "Company_Name", "Status"]
    }
    
    for file, required_cols in schema.items():
        if not os.path.exists(file):
            # Create fresh if missing
            pd.DataFrame(columns=required_cols).to_csv(file, index=False)
        else:
            # CHECK FOR COLUMN MISMATCH (The cause of your ValueError)
            df = pd.read_csv(file)
            if list(df.columns) != required_cols:
                # Force reset the file to the correct headers
                pd.DataFrame(columns=required_cols).to_csv(file, index=False)
                st.sidebar.warning(f"Re-indexed {file} to fix column mismatch.")

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
    st.write("Streamlined portal for Students, Recruiters, and Admins.")
    

# --- 5. STUDENT ZONE ---
elif choice == "Student Zone":
    if st.session_state.role != "student":
        st.header("👨‍🎓 Student Access")
        t1, t2 = st.tabs(["Login", "Register"])
        with t2:
            with st.form("stu_reg"):
                n = st.text_input("Full Name")
                e = st.text_input("Email").lower().strip()
                p = st.text_input("Password", type="password")
                b = st.selectbox("Branch", ["CSE", "IT", "ECE", "MECH"])
                c = st.number_input("CGPA", 0.0, 10.0, 7.5)
                if st.form_submit_button("Register"):
                    df = pd.read_csv("students.csv")
                    if e in df['Email'].values: st.error("Email exists!")
                    else:
                        new_stu = pd.DataFrame([[n, e, p, b, c]], columns=df.columns)
                        pd.concat([df, new_stu]).to_csv("students.csv", index=False)
                        st.success("Registered! Login now.")
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
        st.subheader("My Applications")
        st.dataframe(my_apps, use_container_width=True) if not my_apps.empty else st.info("No applications yet.")

# --- 6. COMPANY ZONE ---
elif choice == "Company Zone":
    if st.session_state.role != "company":
        st.header("🏢 Recruiter Access")
        t1, t2 = st.tabs(["Login", "Register"])
        with t2:
            with st.form("com_reg"):
                cn = st.text_input("Company Name")
                ce = st.text_input("Work Email").lower().strip()
                cp = st.text_input("Password", type="password")
                cr = st.text_input("Role (e.g. Developer)")
                ck = st.text_input("Package (e.g. 12 LPA)")
                if st.form_submit_button("Register Company"):
                    df = pd.read_csv("companies.csv")
                    # Fixed 5-item list for 5-column CSV
                    new_comp = pd.DataFrame([[cn, ce, cp, cr, ck]], columns=df.columns)
                    pd.concat([df, new_comp]).to_csv("companies.csv", index=False)
                    st.success("Company Registered!")
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
                col1, col2, col3 = st.columns([2,1,1])
                col1.write(f"📧 {row['Student_Email']} | Status: **{row['Status']}**")
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
    st.header("💼 Available Jobs")
    comps, apps = pd.read_csv("companies.csv"), pd.read_csv("apps.csv")
    if comps.empty: st.warning("No jobs posted yet.")
    else:
        for i, job in comps.iterrows():
            with st.container(border=True):
                st.subheader(job['Company_Name'])
                st.write(f"**Role:** {job['Role_Offered']} | **Salary:** {job['Package']}")
                if st.session_state.role == "student":
                    already = not apps[(apps['Student_Email']==st.session_state.user) & (apps['Company_Name']==job['Company_Name'])].empty
                    if st.button(f"Apply", disabled=already, key=f"ap_{i}"):
                        new_app = pd.DataFrame([[st.session_state.user, job['Company_Name'], "Pending"]], columns=apps.columns)
                        pd.concat([apps, new_app]).to_csv("apps.csv", index=False)
                        st.success("Applied!")
                        st.rerun()

# --- 8. ADMIN DASHBOARD ---
elif choice == "Admin Dashboard":
    st.header("⚙️ Admin Control Panel")
    pw = st.text_input("Password", type="password")
    if pw == "admin123":
        s_df, c_df, a_df = pd.read_csv("students.csv"), pd.read_csv("companies.csv"), pd.read_csv("apps.csv")
        st.metric("Total Applications", len(a_df))
        st.write("### Live Application Log")
        st.dataframe(a_df, use_container_width=True)
        if st.button("🚨 Wipe All Databases", type="primary"):
            for f in ["students.csv", "companies.csv", "apps.csv"]:
                os.remove(f) if os.path.exists(f) else None
            init_db()
            st.rerun()