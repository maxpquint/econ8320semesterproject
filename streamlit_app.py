#semester project

import pandas as pd
import requests
from io import BytesIO
from thefuzz import process
import streamlit as st

def import_excel_from_github(sheet_name=0):
    github_raw_url = "https://github.com/maxpquint/econ8320semesterproject/raw/main/UNO%20Service%20Learning%20Data%20Sheet%20De-Identified%20Version.xlsx"
    
    try:
        response = requests.get(github_raw_url)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        df = pd.read_excel(BytesIO(response.content), sheet_name=sheet_name)
        st.write("Excel file successfully loaded into DataFrame.")

        # Define state to postal dictionary
        state_to_postal = {
            "Nebraska": "NE",
            "Iowa": "IA",
            "Kansas": "KS",
            "Missouri": "MO",
            "South Dakota": "SD",
            "Wyoming": "WY",
            "Colorado": "CO",
            "Minnesota": "MN"
        }

        # Clean 'State' column
        if 'State' in df.columns:
            df['State'] = df['State'].astype(str).apply(lambda x: state_to_postal.get(process.extractOne(x, list(state_to_postal.keys()))[0], x) if x else x)

        # Ensure 'Total Household Gross Monthly Income' is numeric
        if 'Total Household Gross Monthly Income' in df.columns:
            df['Total Household Gross Monthly Income'] = pd.to_numeric(df['Total Household Gross Monthly Income'], errors='coerce')

        # Add income classification column
        if 'Total Household Gross Monthly Income' in df.columns:
            df['Annualized Income'] = df['Total Household Gross Monthly Income'] * 12
            df['Income Level'] = df['Annualized Income'].apply(
                lambda x: 1 if x <= 12000 else 
                (2 if 12001 <= x <= 47000 else 
                (3 if 47001 <= x <= 100000 else 
                (4 if x > 100000 else pd.NA)))
            )

        # Clean 'gender' column
        if 'gender' in df.columns:
            gender_options = ['male', 'female', 'transgender', 'nonbinary', 'decline to answer', 'other']
            df['gender'] = df['gender'].astype(str).apply(lambda x: process.extractOne(x, gender_options)[0] if x else x)

        # Clean 'race' column
        if 'race' in df.columns:
            race_options = [
                'American Indian or Alaska Native', 
                'Asian', 
                'Black or African American', 
                'Middle Eastern or North African', 
                'Native Hawaiian or Pacific Islander', 
                'White', 
                'decline to answer', 
                'other', 
                'two or more'
            ]
            df['race'] = df['race'].astype(str).apply(lambda x: process.extractOne(x, race_options)[0] if x else x)

        # Clean 'insurance type' column
        if 'insurance type' in df.columns:
            insurance_options = [
                'medicare', 'medicaid', 'medicare & medicaid', 'uninsured', 
                'private', 'military', 'unknown'
            ]
            df['insurance type'] = df['insurance type'].astype(str).apply(lambda x: process.extractOne(x, insurance_options)[0] if x else x)

        # Clean 'request status' column
        if 'request status' in df.columns:
            df['request status'] = df['request status'].astype(str).apply(lambda x: process.extractOne(x, ['pending', 'approved', 'denied'])[0] if x else x)

        # Clean 'payment submitted' column (convert date strings to NaT or keep them as NaT if empty)
        if 'payment submitted' in df.columns:
            df['payment submitted'] = pd.to_datetime(df['payment submitted'], errors='coerce')

        # Clean 'grant req date' column (convert to datetime)
        if 'grant req date' in df.columns:
            df['grant req date'] = pd.to_datetime(df['grant req date'], errors='coerce')

        return df
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return None


# Streamlit interface
st.title('UNO Service Learning Data Dashboard')

# Load the data
df = import_excel_from_github()

# Display the cleaned DataFrame
if df is not None:
    st.write("Data cleaned successfully!")
    st.dataframe(df.head())  # Show the first few rows of the cleaned data

    # Filter by request status (show rows where request status is 'pending')
    st.subheader("Rows where 'Request Status' is 'Pending'")
    pending_df = df[df['request status'] == 'Pending']
    st.dataframe(pending_df)

    # Additional Filtering or Analysis options
    st.subheader("Data Analysis")
    st.write(f"Total number of rows in the dataset: {df.shape[0]}")
    st.write(f"Total number of pending requests: {pending_df.shape[0]}")
else:
    st.write("Failed to load and clean data.")