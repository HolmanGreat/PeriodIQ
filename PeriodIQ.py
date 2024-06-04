#Importing libraries
import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime
from github import Github
import io

# Set up your GitHub credentials (Replace with your actual credentials)
header = {"authorization":st.secrets['TOKEN'], "Accept": "application/vnd.github+json"}
REPO_NAME = 'HolmanGreat/PeriodIQ'
FOLDER_NAME = 'Polka'
FILE_NAME = 'symptoms.csv'

# Authenticate to GitHub
g = Github(TOKEN)
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
st.title("PeriodIQ")
user_id = st.text_input("Enter username")
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


def main():
    app = st.sidebar.selectbox("Menu", ["🌞 Landing", "🪐 Home", "📝 Journals", "🧭 Metrics", "🧩 About"])

    # Input PMS variables
    if app == "🌞 Landing":
        st.write(f"🎉 Welcome {user_id}")

    if app == "🪐 Home":
        pms_variables = st.multiselect("Select your 10 most prominent menstrual symptoms",
                                       ["Cramps", "Drowsiness", "Light headedness", "Mastalgia", "Nausea", "Diarrhoea", "Mood swings", "Bloating", "Headaches", "Lethargic", "Vomiting", "Anorexia", "Hot flushes"])

    if app == "📝 Journals":
        st.write("Using the slider below, scale your pre-menstrual/menstrual symptoms")
        st.write("0 = No symptom", "|  10 = Excruciatingly severe")
        st.write("On a scale of 1-10")

        # metrics_data
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
            "ID": user_id,
            "Time": current_time,
            "Symptoms": symptoms,
            "Severity": metrics_data,
            "Start_Date": start_date,
            "End_Date": end_date
        }

        df = pd.DataFrame(data_dict, index=symptoms)
        st.write(df)

        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=True).encode('utf-8')

        csv = convert_df(df)

        if st.button("Save To Journal"):
            upload_status = upload_to_github(FILE_NAME, csv, repo, FOLDER_NAME)
            st.write(upload_status)
        else:
            st.write("Not Saved")

    if app == "🧭 Metrics":
        csv_content = get_csv_content_from_github(repo, FOLDER_NAME, FILE_NAME)
        if csv_content:
            df = pd.read_csv(io.StringIO(csv_content))
            st.success("", icon = "✅")
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

            def symptom_monthly_stats():
                symptom = st.selectbox("Symptom", ["Cramps", "Bloating", "Mastalgia", "Headaches", "Diarrhoea", "Loss of appetite", "Dizziness", "Fatigue", "Vomiting", "Nausea"])
                if st.button("Check Stats"):
                    # Filter data frame based on User_ID, Symptoms & Date range
                    monthly_symptom = df[(df["Symptoms"] == symptom) & (df["ID"] == user_id) & (df["Start_Date"].isin(selected_date))]
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

if __name__ == "__main__":
    main()
