#semester project

import pandas as pd
import requests
from io import BytesIO
from thefuzz import process
import streamlit as st

# Function to import and clean the Excel file
def import_excel_from_github(sheet_name=0):
    github_raw_url = "https://github.com/maxpquint/econ8320semesterproject/raw/main/UNO%20Service%20Learning%20Data%20Sheet%20De-Identified%20Version.xlsx"
    
    try:
        # Fetch and read the Excel file from GitHub
        response = requests.get(github_raw_url)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        df = pd.read_excel(BytesIO(response.content), sheet_name=sheet_name)
        
        # Standardizing all column names to lowercase and replacing spaces with underscores
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Dictionaries for cleaning the columns
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

        gender_options = ['male', 'female', 'transgender', 'nonbinary', 'decline to answer', 'other']
        
        race_options = [
            'american_indian_or_alaska_native', 
            'asian', 
            'black_or_african_american', 
            'middle_eastern_or_north_african', 
            'native_hawaiian_or_pacific_islander', 
            'white', 
            'decline_to_answer', 
            'other', 
            'two_or_more'
        ]

        insurance_options = [
            'medicare', 'medicaid', 'medicare_&_medicaid', 'uninsured', 
            'private', 'military', 'unknown'
        ]
        
        # Clean 'request_status' column
        df['request_status'] = df['request_status'].str.lower().str.strip()

        # Clean 'gender' column
        if 'gender' in df.columns:
            df['gender'] = df['gender'].astype(str).apply(lambda x: process.extractOne(x, gender_options)[0] if x else x)

        # Clean 'race' column
        if 'race' in df.columns:
            df['race'] = df['race'].astype(str).apply(lambda x: process.extractOne(x, race_options)[0] if x else x)

        # Clean 'insurance_type' column
        if 'insurance_type' in df.columns:
            df['insurance_type'] = df['insurance_type'].astype(str).apply(lambda x: process.extractOne(x, insurance_options)[0] if x else x)

        # Clean 'state' column using the state_to_postal dictionary
        if 'state' in df.columns:
            df['state'] = df['state'].astype(str).apply(lambda x: state_to_postal.get(process.extractOne(x, list(state_to_postal.keys()))[0], x) if x else x)

        # Ensure 'total_household_gross_monthly_income' is numeric
        df['total_household_gross_monthly_income'] = pd.to_numeric(df['total_household_gross_monthly_income'], errors='coerce')

        # Add income classification column based on the annualized income
        df['annualized_income'] = df['total_household_gross_monthly_income'] * 12
        df['income_level'] = df['annualized_income'].apply(
            lambda x: 1 if x <= 12000 else 
            (2 if 12001 <= x <= 47000 else 
            (3 if 47001 <= x <= 100000 else 
            (4 if x > 100000 else pd.NA)))
        )

        # Clean 'payment_submitted' column (convert date strings to NaT or keep them as NaT if empty)
        df['payment_submitted'] = pd.to_datetime(df['payment_submitted'], errors='coerce')

        # Clean 'grant_req_date' column (convert to datetime)
        df['grant_req_date'] = pd.to_datetime(df['grant_req_date'], errors='coerce')

        return df
    
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return None

# Streamlit app code starts here
# Load and clean the data
df = import_excel_from_github()

if df is not None:
    # Show the cleaned data
    st.write("Cleaned DataFrame:", df.head())
    
    # Filter and show only the rows where 'request_status' is 'pending'
    pending_df = df[df['request_status'] == 'pending']
    st.write(f"Total number of pending requests: {pending_df.shape[0]}")
    st.write("Pending Requests:", pending_df)

    # Allow user to download the cleaned data as a CSV
    st.download_button(
        label="Download Cleaned Data as CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='cleaned_data.csv',
        mime='text/csv'
    )

else:
    st.write("Failed to load and clean data.")

