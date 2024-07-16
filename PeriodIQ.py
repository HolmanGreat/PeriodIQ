#Importing dependencies
import altair as alt
import io
import pandas as pd
import pymongo
import re
import random
import streamlit as st

from datetime import datetime
from github import Github
from pymongo import MongoClient



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


# MongoDB access
db_access = st.secrets.mongo_db_key.conn_str

# Instantiate client
client =  MongoClient(db_access)
                
# Create DB
db = client["DB"]

# Create Collections (Data Table | Symptom_Variables)
collection = db["Data_Table"]
symptom_collection = db["Symptom_Variables"]




# Initialize session state for symptoms_list and metrics_data
if 'symptoms_list' not in st.session_state:
    st.session_state.symptoms_list = []
if 'metrics_data' not in st.session_state:
    st.session_state.metrics_data = {}
if 'username' not in st.session_state:
    st.session_state.username = ""




def top_symptoms():
    """
    10 prominent menstrual symptoms
    """
    st.title("PeriodIQ")
    st.write(f"Welcome, {st.session_state.username}!")
    st.divider()
    st.image("checklist.jpeg")
    st.write("Enter your 10 prominent menstrual symptoms")
    symptoms = st.text_input(label="E.g: Cramps, Nausea, Fatigue...")
    if st.button("Save"):
        symptoms_add = [symptom.strip() for symptom in symptoms.split(",")]
        if len(symptoms_add) <= 10:
            st.session_state.symptoms_list = symptoms_add
            period_symptoms = {"ID": st.session_state.username, "Period Symptoms": symptoms_add}
            symptom_collection.insert_one(period_symptoms)
            st.success("Saved")
            st.session_state.need_to_enter_symptoms = False  # Update the state
            st.rerun()  # Redirect to landing page
        else:
            st.error("Please enter only 10 symptoms")





def metrics():
    """
    Generates a slider to enable user to grade period symptoms
    """
    for symptom in st.session_state.symptoms_list:
        period_symptom_var = st.slider(symptom, 0, 10, 0, key=symptom)
        st.session_state.metrics_data[symptom] = period_symptom_var


def check_mongodb():
    # Query DB for user symptoms using user ID
    document = symptom_collection.find_one({"ID": st.session_state.username})

    if document:
        symptom_array = document.get('Period Symptoms')
        if symptom_array:
            #st.write(symptom_array)
            landing_page()
        else:
            st.write("Symptoms not found")
    else:
        st.write("Please enter your 10 prominent period symptoms.")
        top_symptoms()



def authenticate(user_id, qauth):
    """
    Authenticate QAuth Token
    """
    token_csv_content = get_csv_content_from_github(repo, FOLDER_NAME, FILE_NAME_3)
    if token_csv_content:
        token_df = pd.read_csv(io.StringIO(token_csv_content))
        user_token = token_df[(token_df["ID"] == user_id)]
        if not user_token.empty:
            return qauth == user_token.iloc[-1]["sets"]
    return False



def create_symptom_chart(metrics_df, symptom):
    """
    Display plot of selected period symptom
    """
    chart = alt.Chart(metrics_df).mark_bar().encode(
        x=alt.X('Start_Date:T', title='Date', axis=alt.Axis(labelAngle=90)),
        y=alt.Y('Severity:Q', title='Severity')
    ).properties(
        title=f"Metrics of {symptom}",
        width=600,
        height=400
    )
    return chart










def upload_to_github(file_name, new_content, repo, folder_name):
    """
    Upload file
    """
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

#symptoms = ["Cramps", "Bloating", "Mastalgia", "Headaches", "Diarrhoea", "Loss of appetite", "Dizziness", "Fatigue", "Vomiting", "Nausea"]




#Retrieve file
def get_csv_content_from_github(repo, folder_name, file_name):
    """
    Retrieve csv file
    """
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
    """
    Generate QAuth Tokens
    """
    alphabets = "abcdefghijklmnopqrstuvwxyz"
    numbers = "0123456789"
    capital_letters = alphabets.upper()
    symbols = "&$_@+()-+_/?!;:'~|•√π÷∆©%=][}{§×£¢€¥°®><✓™#,"
    scrambled_password = f"{alphabets}{numbers}{capital_letters}{symbols}"
    password_length = 12
    password = "".join(random.sample(scrambled_password, password_length))
    return password







def validate_username(username):
    """
    Checks validity of the username.

    Returns True if the username is valid, else False.
    """
    pattern = r'^[a-zA-Z0-9]*$'

    if re.match(pattern, username):
        return True
    return False



def validate_email(email):
    """
    Checks the validity of the email.

    Returns True if the email is valid, else False.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if re.match(pattern, email):
        return True
    return False


def login_signup_page():
    tab1, tab2, tab3 = st.tabs(["Login", "Sign-Up", "💕 Partner Console"])

    with tab1:
        with st.form(key="Login", clear_on_submit=True):
            st.subheader(":violet[Login]")
            user = st.text_input("Username")
            passkey = st.text_input("Password", type="password")

            if st.form_submit_button("Login"):
                if not user or not passkey:
                    st.error("Enter both username and password")
                else:
                    user_details = collection.find_one({"Name": user, "Password": passkey})
                    if not user_details:
                        st.error("Invalid Username/Password")
                    else:
                        st.success("Login successful!")
                        st.session_state.logged_in = True
                        st.session_state.username = user
                        st.session_state.need_to_enter_symptoms = False  # Reset state
                        st.rerun()

    with tab2:
        with st.form(key="Sign Up", clear_on_submit=True):
            st.subheader(":violet[Sign-Up]")
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")

            if st.form_submit_button("Create Account"):
                if not username or not email or not password:
                    st.error("Please fill in all fields.")
                elif not validate_username(username):
                    st.error("Username can only contain letters and numbers.")
                elif not validate_email(email):
                    st.error("Please enter a valid email address.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    if collection.find_one({"$or": [{"Name": username}, {"Email": email}]}):
                        st.error("Username or Email already exists.")
                    else:
                        data = {"Name": username, "Email": email, "Password": password}
                        added_doc = collection.insert_one(data)
                        st.success("Account Created")
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.need_to_enter_symptoms = True  # Set state to enter symptoms
                        st.rerun()






    with tab3:
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
            st.write("Partner Console")
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
                st.experimental_rerun







def landing_page():
    app = st.sidebar.selectbox("Menu",["📝 Journals","🧭 Metrics", "💊 Drug Tab","🔒 QAuth Token","❌ Log Out"])


    if app == "📝 Journals":
        st.title("📝 Journals")
        st.divider()
        st.image("calendar_blue.jpeg")
        st.caption(":octagonal_sign: _Using the slider below, scale your pre-menstrual/menstrual symptoms_")
        st.caption("0 = No symptom  ||  10 = Excruciatingly severe")
        st.caption("On a scale of 1-10")

        username = st.session_state.username

        start_date = st.date_input("Period begins", value=None)
        end_date = st.date_input("Period ends", value=None)
        current_time = datetime.now().strftime("%H:%M:%S")

        symptom_db = symptom_collection.find_one({"ID": username})

        if symptom_db:
            period_symptoms = symptom_db.get('Period Symptoms', [])

        else:
            st.error("Please enter your 10 prominent period symptoms")
            period_symptoms = []

        if 'metrics_data' not in st.session_state:
            st.session_state.metrics_data = {}

        for symptom in period_symptoms:
            period_symptom_var = st.slider(symptom, 0, 10, 0, key=symptom)
            st.session_state.metrics_data[symptom] = period_symptom_var

        data_dict = {
            "ID": username,
            "Time": current_time,
            "Symptoms": period_symptoms,
            "Severity": list(st.session_state.metrics_data.values()),
            "Start_Date": start_date,
            "End_Date": end_date
        }






        df = pd.DataFrame(data_dict, index=st.session_state.metrics_data)


        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=True).encode('utf-8')

        csv = convert_df(df)

        if st.button("Save To Journal"):
            upload_status = upload_to_github(FILE_NAME, csv, repo, FOLDER_NAME)
            st.write(upload_status)
        else:
            st.write("Not Saved")



    elif app == "🧭 Metrics":
        st.title("🧭 Metrics")
        st.divider()
        st.image("chart.jpeg", caption = "Your period metrics at a glance")
        csv_content = get_csv_content_from_github(repo, FOLDER_NAME, FILE_NAME)
        if csv_content:
            df = pd.read_csv(io.StringIO(csv_content))
            st.success("")
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
                        st.image("File not found.jpg", caption = "©image:Designed by Freepik")
                        st.write("No data found for the selected filters.")
                else:
                    st.write("Click the button to check stats")

            symptom_monthly_stats()

        else:
            st.write("✨")

    elif app == "💊 Drug Tab":
        st.title("💊 Drug Tab")
        st.divider()
        st.image("drug tab(pink).jpeg", caption = "Keep tabs with period pills")
        st.write("")
        drug_name  = st.text_input("Period Pills")
        date = st.date_input("Date used")
        username = f"{st.session_state.username}"
        drug_dict = {"ID":[username],"Date":[date],"Pill":[drug_name]}
        drug_df = pd.DataFrame(drug_dict)


        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=True).encode('utf-8')
        pharma = convert_df(drug_df)

        if st.button("Update Tab"):
            upload_to_github(FILE_NAME_2,pharma, repo, FOLDER_NAME)

        pharma_csv_content = ""
        if st.button("View Tab"):
            pharma_csv_content = get_csv_content_from_github(repo, FOLDER_NAME, FILE_NAME_2)


        if pharma_csv_content:
            df = pd.read_csv(io.StringIO(pharma_csv_content))
            st.success("", icon = "✅")
            st.write(df)

        else:
            st.warning("No period pill(s) have been added to your drug tab")

    elif app == "🔒 QAuth Token":
        st.title("QAuth Token")
        st.divider()
        st.image("lock.jpeg")

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
            Qtoken = user_token
            st.markdown(user_token)

            st.success("Token generated")
        st.divider()
        st.caption(":octagonal_sign: _Share period metrics with your partner by generating a QAuth Token to enable them access_")
        st.write("")
        st.caption(":warning: Remember to copy and save the generated token, as leaving this page will make the token no longer visible")

    elif app == "❌ Log Out":
        st.session_state.logged_in = False
        st.experimental_rerun()

def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'need_to_enter_symptoms' not in st.session_state:
        st.session_state.need_to_enter_symptoms = False

    if not st.session_state.logged_in:
        login_signup_page()
    elif st.session_state.need_to_enter_symptoms:
        top_symptoms()
    else:
        landing_page()

if __name__ == "__main__":
    main()







