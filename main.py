import streamlit as st
import pandas as pd
import os

# --- 1. DATABASE INITIALIZATION ---
def init_db():
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
if "login_type" not in st.session_state:
    st.session_state.login_type = None
    st.session_state.user_data = None

st.set_page_config(page_title="Placement Portal", page_icon="🎓")

# --- 3. SIDEBAR NAVIGATION ---
menu = ["Home", "Student Zone", "Company Zone", "Job Board", "Admin Zone"]
choice = st.sidebar.selectbox("Navigation", menu)

# --- 4. STUDENT ZONE ---
if choice == "Student Zone":
    if not st.session_state.user_data:
        st.subheader("👨‍🎓 Student Portal")
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab2:
            with st.form("stu_reg"):
                n, e = st.text_input("Full Name"), st.text_input("Email").lower().strip()
                p, b = st.text_input("Password", type="password"), st.selectbox("Branch", ["CSE", "IT", "ECE", "MECH"])
                c = st.number_input("CGPA", 0.0, 10.0, 7.0)
                if st.form_submit_button("Register"):
                    df = pd.read_csv("students.csv")
                    if e in df['Email'].values: st.error("Email exists!")
                    else:
                        pd.concat([df, pd.DataFrame([[n,e,p,b,c]], columns=df.columns)]).to_csv("students.csv", index=False)
                        st.success("Registered! Go to Login.")
        with tab1:
            le, lp = st.text_input("Email").lower().strip(), st.text_input("Password", type="password")
            if st.button("Student Login"):
                df = pd.read_csv("students.csv")
                user = df[(df['Email']==le) & (df['Password'].astype(str)==lp)]
                if not user.empty:
                    st.session_state.login_type, st.session_state.user_data = "student", user.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Invalid Login")
    else:
        st.header(f"Welcome, {st.session_state.user_data['Name']}")
        apps = pd.read_csv("apps.csv")
        my_apps = apps[apps['Student_Email'] == st.session_state.user_data['Email']]
        st.table(my_apps) if not my_apps.empty else st.info("No apps yet.")
        if st.button("Logout"): st.session_state.user_data = None; st.rerun()

# --- 5. COMPANY ZONE ---
elif choice == "Company Zone":
    if not st.session_state.user_data:
        st.subheader("🏢 Company Portal")
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab2:
            with st.form("com_reg"):
                cn, ce = st.text_input("Company Name"), st.text_input("Email").lower().strip()
                cp, cr = st.text_input("Password", type="password"), st.text_input("Role")
                ck = st.text_input("Package")
                if st.form_submit_button("Register"):
                    df = pd.read_csv("companies.csv")
                    pd.concat([df, pd.DataFrame([[cn,ce,cp,cr,ck]], columns=df.columns)]).to_csv("companies.csv", index=False)
                    st.success("Company Registered!")
        with tab1:
            cle, clp = st.text_input("Email").lower().strip(), st.text_input("Password", type="password")
            if st.button("Company Login"):
                df = pd.read_csv("companies.csv")
                comp = df[(df['Email']==cle) & (df['Password'].astype(str)==clp)]
                if not comp.empty:
                    st.session_state.login_type, st.session_state.user_data = "company", comp.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Invalid credentials")
    else:
        st.header(f"Dashboard: {st.session_state.user_data['Company_Name']}")
        apps = pd.read_csv("apps.csv")
        my_apps = apps[apps['Company_Name'] == st.session_state.user_data['Company_Name']]
        for i, row in my_apps.iterrows():
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"{row['Student_Email']} - {row['Status']}")
            if c2.button("Accept", key=f"a{i}"): apps.at[i, 'Status'] = "Accepted"; apps.to_csv("apps.csv", index=False); st.rerun()
            if c3.button("Reject", key=f"r{i}"): apps.at[i, 'Status'] = "Rejected"; apps.to_csv("apps.csv", index=False); st.rerun()
        if st.button("Logout"): st.session_state.user_data = None; st.rerun()

# --- 6. JOB BOARD ---
elif choice == "Job Board":
    st.header("📢 Hiring Now")
    comps, apps = pd.read_csv("companies.csv"), pd.read_csv("apps.csv")
    for i, job in comps.iterrows():
        with st.container(border=True):
            st.subheader(job['Company_Name'])
            st.write(f"{job['Role_Offered']} | {job['Package']}")
            if st.session_state.login_type == "student":
                already = not apps[(apps['Student_Email']==st.session_state.user_data['Email']) & (apps['Company_Name']==job['Company_Name'])].empty
                if st.button(f"Apply", disabled=already, key=f"ap{i}"):
                    new = pd.DataFrame([[st.session_state.user_data['Email'], job['Company_Name'], "Pending"]], columns=apps.columns)
                    pd.concat([apps, new]).to_csv("apps.csv", index=False); st.rerun()

# --- 7. ADMIN ZONE ---
elif choice == "Admin Zone":
    st.header("⚙️ Administrative Control")
    admin_pass = st.text_input("Admin Password", type="password")
    
    if admin_pass == "admin123":
        s_df, c_df, a_df = pd.read_csv("students.csv"), pd.read_csv("companies.csv"), pd.read_csv("apps.csv")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Students", len(s_df))
        col2.metric("Companies", len(c_df))
        col3.metric("Applications", len(a_df))
        
        with st.expander("View Full Databases"):
            st.write("### Students")
            st.dataframe(s_df)
            st.write("### Companies")
            st.dataframe(c_df)
            st.write("### All Applications")
            st.dataframe(a_df)
            
        if st.button("🚨 Wipe All Databases", type="primary"):
            for f in ["students.csv", "companies.csv", "apps.csv"]:
                if os.path.exists(f): os.remove(f)
            init_db()
            st.success("System Reset Successful!")
            st.rerun()
    elif admin_pass: st.error("Access Denied")

else:
    st.title("🎓 College Placement Portal")
    st.write("Unified platform for students, recruiters, and administrators.")