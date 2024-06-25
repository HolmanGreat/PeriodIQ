#Importing dependencies

%%writefile pilot.py

import streamlit as st
import altair as alt
import firebase_admin
from firebase_admin import credentials, auth
import pandas as pd
from datetime import datetime
from github import Github
import io
import random




#Github Acces
GITHUB_TOKEN = st.secrets.database.GITHUB_TOKEN

REPO_NAME = 'HolmanGreat/PeriodIQ'
FOLDER_NAME = 'Polka'
FILE_NAME = 'symptoms.csv'
FILE_NAME_2 = 'pharma.csv'
FILE_NAME_3 = 'token.csv'




# Authenticate to GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)



def upload_to_github(file_name, new_content, repo, folder_name):
    path = f"{folder_name}/{file_name}"
    try:
        contents = repo.get_contents(path)
        existing_content = contents.decoded_content.decode('utf-8')
        existing_df = pd.read_csv(io.StringIO(existing_content))
        new_df = pd.read_csv(io.StringIO(new_content.decode('utf-8')))
        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        updated_content = updated_df.to_csv(index=False).encode('utf-8')
        repo.update_file(contents.path, "Updating file with new data", updated_content, contents.sha)
        return "File updated with new data"
    except Exception as e:
        repo.create_file(path, "Creating new file", new_content)
        return "File created"

symptoms = ["Cramps", "Bloating", "Mastalgia", "Headaches", "Diarrhoea", "Loss of appetite", "Dizziness", "Fatigue", "Vomiting", "Nausea"]





#Retrieve file
def get_csv_content_from_github(repo, folder_name, file_name):
    path = f"{folder_name}/{file_name}"
    try:
        contents = repo.get_contents(path)
        csv_content = contents.decoded_content.decode('utf-8')
        return csv_content
    except Exception as e:
        st.error(f"Error: {e}")
        return None




# Function to generate QAuth
def generate_password():
    alphabets = "abcdefghijklmnopqrstuvwxyz"
    numbers = "0123456789"
    capital_letters = alphabets.upper()
    symbols = "&$_@+()-+_/?!;:'~|•√π÷∆©%=][}{§×£¢€¥°®><✓™#,"
    scrambled_password = f"{alphabets}{numbers}{capital_letters}{symbols}"
    password_length = 12
    password = "".join(random.sample(scrambled_password, password_length))
    return password



def authenticate(user_id, qauth):
    token_csv_content = get_csv_content_from_github(repo, FOLDER_NAME, FILE_NAME_3)
    if token_csv_content:
        token_df = pd.read_csv(io.StringIO(token_csv_content))
        user_token = token_df[(token_df["ID"] == user_id)]
        if not user_token.empty:
            return qauth == user_token.iloc[-1]["sets"]
    return False



def create_symptom_chart(metrics_df, symptom):
    chart = alt.Chart(metrics_df).mark_bar().encode(
        x=alt.X('Start_Date:T', title='Date', axis=alt.Axis(labelAngle=90)),
        y=alt.Y('Severity:Q', title='Severity')
    ).properties(
        title=f"Metrics of {symptom}",
        width=600,
        height=400
    )
    return chart







# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate("/content/periodiq_3A.json")
    firebase_admin.initialize_app(cred)






def login(email, password):
    try:
        user = auth.get_user_by_email(email)
        st.success("Login Successful")
        st.session_state.username = user.uid
        st.session_state.useremail = user.email
        st.session_state.authenticated = True
    except:
        st.warning("Login Failed")

def logout():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.useremail = ""
    st.experimental_rerun()

def create_account(email, password, username):
    try:
        user = auth.create_user(email=email, password=password, uid=username)
        st.success("Account Created")
        st.markdown("Please login using your credentials")
        st.balloons()
    except Exception as e:
        st.error(f"Error creating account: {e}")










def main():
    tab1, tab2 = st.tabs(["Login/Sign-Up", "💕My Partner"])

    if "username" not in st.session_state:
        st.session_state.username = ""
    if "useremail" not in st.session_state:
        st.session_state.useremail = ""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    landing_page = None  # Initialize landing_page

    with tab1:


        if not st.session_state.authenticated:
            landing_page = st.selectbox("Login/Sign-Up", ["Login", "Sign-Up"])

        if landing_page == "Login":
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                login(email, password)

        elif landing_page == "Sign-Up":
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            username = st.text_input("Enter Username")
            if st.button("Create Account"):
                create_account(email, password, username)
        else:
            app = st.sidebar.selectbox("Menu", ["🪐 Home", "📝 Journals", "🧭 Metrics", "💊 Drug Tab", "🔒 QAuth Token", "❌ Log Out"])

            if app == "🪐 Home":
                st.title("PeriodIQ")
                st.write(f"Welcome, {st.session_state.username}!")
                st.divider()
                pms_variables = st.multiselect("Select your 10 most prominent menstrual symptoms",
                    ["Cramps", "Drowsiness", "Light headedness", "Mastalgia", "Nausea", "Diarrhoea", "Mood swings", "Bloating", "Headaches", "Lethargic", "Vomiting", "Anorexia", "Hot flushes"])

            elif app == "📝 Journals":
                st.title("📝 Journals")
                st.divider()
                st.write("Using the slider below, scale your pre-menstrual/menstrual symptoms")
                st.write("0 = No symptom", "|  10 = Excruciatingly severe")
                st.write("On a scale of 1-10")

                # metrics_data
                username = f"{st.session_state.username}"
                metrics_data = []
                start_date = st.date_input("Start of period", value=None)
                end_date = st.date_input("End of period", value=None)
                current_time = datetime.now().strftime("%H:%M:%S")

                pms_var1 = st.slider("Cramps", 0, 10, 0)
                metrics_data.append(pms_var1)

                pms_var2 = st.slider("Bloating", 0, 10, 0)
                metrics_data.append(pms_var2)

                pms_var3 = st.slider("Mastalgia", 0, 10, 0)
                metrics_data.append(pms_var3)

                pms_var4 = st.slider("Headaches", 0, 10, 0)
                metrics_data.append(pms_var4)

                pms_var5 = st.slider("Diarrhoea", 0, 10, 0)
                metrics_data.append(pms_var5)

                pms_var6 = st.slider("Loss of appetite", 0, 10, 0)
                metrics_data.append(pms_var6)

                pms_var7 = st.slider("Dizziness", 0, 10, 0)
                metrics_data.append(pms_var7)

                pms_var8 = st.slider("Fatigue", 0, 10, 0)
                metrics_data.append(pms_var8)

                pms_var9 = st.slider("Vomiting", 0, 10, 0)
                metrics_data.append(pms_var9)

                pms_var10 = st.slider("Nausea", 0, 10, 0)
                metrics_data.append(pms_var10)

                data_dict = {
                    "ID": username,
                    "Time": current_time,
                    "Symptoms": ["Cramps", "Bloating", "Mastalgia", "Headaches", "Diarrhoea", "Loss of appetite", "Dizziness", "Fatigue", "Vomiting", "Nausea"],
                    "Severity": metrics_data,
                    "Start_Date": start_date,
                    "End_Date": end_date
                }

                df = pd.DataFrame(data_dict)


                @st.cache_data
                def convert_df(df):
                    return df.to_csv(index=True).encode('utf-8')

                csv = convert_df(df)

                if st.button("Save To Journal"):
                    upload_status = upload_to_github("journal.csv", csv, "repo_name", "folder_name")
                    st.write(upload_status)
                else:
                    st.write("Not Saved")

            elif app == "🧭 Metrics":
                st.title("🧭 Metrics")
                st.divider()
                st.image("/content/calc.png")
                csv_content = get_csv_content_from_github(repo, FOLDER_NAME, FILE_NAME)
                if csv_content:
                    df = pd.read_csv(io.StringIO(csv_content))
                    st.success("", icon="✅")
                else:
                    st.error("Failed to retrieve content.")

                # Date inputs for start and end of period
                start_date = st.date_input("Period Starts")
                end_date = st.date_input("Period Ends")

                if csv_content and start_date and end_date:
                    df["Start_Date"] = pd.to_datetime(df["Start_Date"], errors='coerce')
                    df["End_Date"] = pd.to_datetime(df["End_Date"], errors='coerce')
                    # Filter dates
                    selected_date = pd.date_range(start=start_date, end=end_date).tolist()
                    username = f"{st.session_state.username}"

                    def symptom_monthly_stats():
                        symptom = st.selectbox("Symptom", ["Cramps", "Bloating", "Mastalgia", "Headaches", "Diarrhoea", "Loss of appetite", "Dizziness", "Fatigue", "Vomiting", "Nausea"])
                        if st.button("Check Stats"):
                            # Filter data frame based on User_ID, Symptoms & Date range
                            monthly_symptom = df[(df["Symptoms"] == symptom) & (df["ID"] == username) & (df["Start_Date"].isin(selected_date))]
                            if not monthly_symptom.empty:
                                metrics_df = monthly_symptom[["Start_Date", "Severity"]]

                                chart = alt.Chart(metrics_df).mark_bar().encode(
                                    x=alt.X('Start_Date:T', title='Date', axis=alt.Axis(labelAngle=90)),
                                    y=alt.Y('Severity:Q', title='Severity')
                                ).properties(
                                    title=f"Metrics of {symptom}"
                                )
                                st.altair_chart(chart, use_container_width=True)
                            else:
                                st.write("No data found for the selected filters.")
                        else:
                            st.write("Click the button to check stats")

                    symptom_monthly_stats()

                else:
                    st.write("✨")

            elif app == "💊 Drug Tab":
                st.write("")
                st.image("/content/drug tab(pink).jpeg", caption="Keep tabs with period pills")
                st.write("")
                drug_name = st.text_input("Drug Name")
                date = st.date_input("Enter date")
                username = f"{st.session_state.username}"
                drug_dict = {"ID": [username], "Date": [date], "Pill": [drug_name]}
                drug_df = pd.DataFrame(drug_dict)

                @st.cache_data
                def convert_df(df):
                    return df.to_csv(index=True).encode('utf-8')
                pharma = convert_df(drug_df)

                if st.button("Update Tab"):
                    upload_to_github("drugs.csv", pharma, "repo_name", "folder_name")

                pharma_csv_content = ""
                if st.button("View Tab"):
                    pharma_csv_content = get_csv_content_from_github(repo, FOLDER_NAME, FILE_NAME_2)

                if pharma_csv_content:
                    df = pd.read_csv(io.StringIO(pharma_csv_content))
                    st.success("", icon="✅")
                    st.write(df)
                else:
                    st.warning("No content available or failed to load content")

            elif app == "🔒 QAuth Token":
                st.title("🔒 QAuth Token")
                st.image("/content/QAuth.jpg", caption= "©image: Designed by Freepik")

                if st.button("Generate Token"):
                    token = generate_password()
                    user_id = f"{st.session_state.username}"
                    token_dict = {"ID":[user_id], "sets":[token]}
                    token_df = pd.DataFrame(token_dict)
                    @st.cache_data
                    def convert_df(df):
                        return df.to_csv(index=True).encode('utf-8')
                    token_csv = convert_df(token_df)
                    upload_token = upload_to_github(FILE_NAME_3,token_csv,repo,FOLDER_NAME)
                    get_token = get_csv_content_from_github(repo, FOLDER_NAME, FILE_NAME_3)
                    df_token = pd.read_csv(io.StringIO(get_token))
                    generated_token = df_token[(df_token["ID"] == user_id) & (df_token["sets"])]
                    user_token = generated_token.iloc[-1]["sets"]
                    #Qtoken = user_token
                    st.markdown(user_token)

                    st.success("Token generated")
                st.divider()
                st.caption(":octagonal_sign: _Share period metrics with your partner by generating a QAuth Token to enable them access. Remember to copy and save the generated token, as leaving this pages will make the token no longer visible_")


            elif app == "❌ Log Out":
                logout()

    with tab2:
        st.title("💕 Partner Console")
        if "authenticate" not in st.session_state:
            st.session_state.authenticate = False

        if not st.session_state.authenticate:
            user_id = st.text_input("Partner's ID")
            qauth = st.text_input("Enter QAuth Token", type="password")

            st.divider()
            st.caption(":warning: _If you encounter issues gaining access kindly ask your partner for a valid QAuth Token to enable access_")

            if st.button("Access Metrics"):
                if authenticate(user_id, qauth):
                    st.session_state.authenticate = True
                    st.session_state.user_id = user_id
                    st.success("Authentication successful!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid Partner's ID or QAuth Token")

        else:
            st.write("Open Partner Console")
            console_data = get_csv_content_from_github(repo, FOLDER_NAME, FILE_NAME)
            if console_data:
                console_df = pd.read_csv(io.StringIO(console_data))

                # Date inputs for start and end of period
                start_date = st.date_input("Period Starts")
                end_date = st.date_input("Period Ends")

                if console_data and start_date and end_date:
                    console_df["Start_Date"] = pd.to_datetime(console_df["Start_Date"], errors='coerce')
                    console_df["End_Date"] = pd.to_datetime(console_df["End_Date"], errors='coerce')

                    # Filter dates
                    mask = (console_df["Start_Date"] >= pd.Timestamp(start_date)) & (console_df["Start_Date"] <= pd.Timestamp(end_date))

                    selected_symptoms = st.selectbox("Select Symptom", ["Cramps", "Bloating", "Mastalgia", "Headaches", "Diarrhoea", "Loss of appetite", "Dizziness", "Fatigue", "Vomiting", "Nausea"])

                    if st.button("View Stats"):
                        if selected_symptoms:
                            # Filter data frame based on User_ID, Symptoms & Date range
                            monthly_symptom = console_df[mask & (console_df["Symptoms"] == selected_symptoms) & (console_df["ID"] == st.session_state.user_id)]
                            if not monthly_symptom.empty:
                                metrics_df = monthly_symptom[["Start_Date", "Severity"]]
                                chart = create_symptom_chart(metrics_df, selected_symptoms)
                                st.altair_chart(chart, use_container_width=True)

                            else:
                                st.write(f"No data found for {selected_symptoms}")

                        else:
                            st.write("Please select at least one symptom")
                else:
                    st.write("Please select a start and end date.")
            else:
                st.write("Failed to load data from GitHub.")

            if st.button("❌Sign-Out"):
                st.session_state.authenticate = False
                st.experimental_rerun()

if __name__ == "__main__":
    main()
