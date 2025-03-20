#semester project

import pandas as pd
import requests
from io import BytesIO
from thefuzz import process
import streamlit as st
import io
import numpy as np  # For NaN

def import_excel_from_github(sheet_name=0):
    github_raw_url = "https://github.com/maxpquint/econ8320semesterproject/raw/main/UNO%20Service%20Learning%20Data%20Sheet%20De-Identified%20Version.xlsx"
    
    try:
        # Load the data from GitHub
        response = requests.get(github_raw_url)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        df = pd.read_excel(BytesIO(response.content), sheet_name=sheet_name)
        st.write("Excel file successfully loaded into DataFrame.")

        # Display the raw column names to verify
        st.write("Raw column names:")
        st.write(df.columns)  # Display the actual column names from the raw data

        # Replace "Missing" with NaN in selected columns that are likely to have "Missing" values
        columns_with_missing_values = [
            'State', 'Gender', 'Race', 'Insurance Type', 'Request Status', 'Application Signed?', 'Pt State'
        ]
        
        # Replace "Missing" with NaN in these columns only
        for column in columns_with_missing_values:
            if column in df.columns:
                df[column] = df[column].replace("Missing", np.nan)

        # Rename specific columns to match your desired format
        df.rename(columns={ 
            'State': 'Pt State', 
            'Payment Submitted': 'Payment Submitted?', 
            'Application Signed': 'Application Signed?'
        }, inplace=True)

        # Standardizing the 'Request Status' column to lowercase immediately after loading the data
        if 'Request Status' in df.columns:
            df['Request Status'] = df['Request Status'].str.lower().str.strip()

        # Clean 'Application Signed?' column (standardizing values to "Yes", "No", or "N/A")
        if 'Application Signed?' in df.columns:
            application_signed_options = ['yes', 'no', 'n/a']
            df['Application Signed?'] = df['Application Signed?'].astype(str).apply(
                lambda x: process.extractOne(x.lower(), application_signed_options)[0] if x else 'N/A'
            )

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

        # Clean 'Pt State' column (was 'State' before)
        if 'Pt State' in df.columns:
            df['Pt State'] = df['Pt State'].astype(str).apply(lambda x: state_to_postal.get(process.extractOne(x, list(state_to_postal.keys()))[0], x) if x else x)

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

        # Clean 'Gender' column
        if 'Gender' in df.columns:
            gender_options = ['male', 'female', 'transgender', 'nonbinary', 'decline to answer', 'other']
            df['Gender'] = df['Gender'].astype(str).apply(lambda x: process.extractOne(x, gender_options)[0] if x else x)

        # Clean 'Race' column
        if 'Race' in df.columns:
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
            df['Race'] = df['Race'].astype(str).apply(lambda x: process.extractOne(x, race_options)[0] if x else x)

        # Clean 'Insurance Type' column
        if 'Insurance Type' in df.columns:
            insurance_options = [
                'medicare', 'medicaid', 'medicare & medicaid', 'uninsured', 
                'private', 'military', 'unknown'
            ]
            df['Insurance Type'] = df['Insurance Type'].astype(str).apply(lambda x: process.extractOne(x, insurance_options)[0] if x else x)

        # Clean 'Request Status' column again (just to be sure it's lowercased)
        if 'Request Status' in df.columns:
            df['Request Status'] = df['Request Status'].str.lower().str.strip()  # Ensure it's lowercased

        # Clean 'Payment Submitted?' column (convert date strings to NaT or keep them as NaT if empty)
        if 'Payment Submitted?' in df.columns:
            df['Payment Submitted?'] = pd.to_datetime(df['Payment Submitted?'], errors='coerce')

        # Clean 'Grant Req Date' column (convert to datetime)
        if 'Grant Req Date' in df.columns:
            df['Grant Req Date'] = pd.to_datetime(df['Grant Req Date'], errors='coerce')

        return df
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return None


# Streamlit interface
st.title('UNO Service Learning Data Dashboard')

# Load the data
df = import_excel_from_github()

# Display the updated column names in the DataFrame
if df is not None:
    st.write("Updated Column names in the dataset:")
    st.write(df.columns)  # Display the column names in the Streamlit app

    st.write("Data cleaned successfully!")
    st.dataframe(df.head())  # Show the first few rows of the cleaned data

    # Standardizing and filtering 'Request Status' to handle possible variations
    if 'Request Status' in df.columns:
        # Filter the DataFrame to show rows where 'Request Status' ends with 'pending', case insensitive
        pending_df = df[df['Request Status'].str.endswith('pending', na=False)]  # Make case-insensitive check
        
        # Display the rows where request status ends with 'pending' in the same way
        st.subheader("Rows where 'Request Status' ends with 'Pending'")

        if pending_df.empty:
            st.write("No pending requests found.")
        else:
            st.dataframe(pending_df)  # Display the filtered rows like the raw data

    # Additional Filtering or Analysis options
    st.subheader("Data Analysis")
    st.write(f"Total number of rows in the dataset: {df.shape[0]}")

    # Add functionality to download the cleaned data as a CSV
    @st.cache_data
    def convert_df(df):
        # Cache the conversion to avoid re-running on every interaction
        return df.to_csv(index=False)

    csv = convert_df(df)

    # Provide a download button for the CSV file
    st.download_button(
        label="Download Cleaned Data as CSV",
        data=csv,
        file_name='cleaned_data.csv',
        mime='text/csv'
    )
else:
    st.write("Failed to load and clean data.")

