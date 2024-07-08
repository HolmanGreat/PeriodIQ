#Importing dependencies



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








