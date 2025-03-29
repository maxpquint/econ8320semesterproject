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

        # Step 1: Replace all occurrences of "Missing" (case insensitive) with NaN across the entire DataFrame
        df.replace(to_replace=r'(?i)^missing$', value=np.nan, regex=True, inplace=True)

        # Step 2: Rename specific columns to match your desired format
        df.rename(columns={ 
            'State': 'Pt State', 
            'Payment Submitted': 'Payment Submitted?', 
            'Application Signed': 'Application Signed?'
        }, inplace=True)

        # Step 3: Standardizing the 'Request Status' column to lowercase immediately after loading the data
        if 'Request Status' in df.columns:
            df['Request Status'] = df['Request Status'].str.lower().str.strip()

        # Step 4: Clean 'Application Signed?' column (standardizing values to "Yes", "No", or "N/A")
        if 'Application Signed?' in df.columns:
            application_signed_options = ['yes', 'no', 'n/a']
            df['Application Signed?'] = df['Application Signed?'].astype(str).apply(
                lambda x: process.extractOne(x.lower(), application_signed_options)[0] if pd.notna(x) else 'N/A'
            )

        # Step 5: Define state to postal dictionary
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

        # Step 6: Clean 'Pt State' column (was 'State' before) using fuzzy matching, but skip NaN values
        if 'Pt State' in df.columns:
            df['Pt State'] = df['Pt State'].astype(str).apply(
                lambda x: state_to_postal.get(process.extractOne(x, list(state_to_postal.keys()))[0], x) if pd.notna(x) and x != 'nan' else x)

        # Step 7: Ensure 'Total Household Gross Monthly Income' is numeric
        if 'Total Household Gross Monthly Income' in df.columns:
            df['Total Household Gross Monthly Income'] = pd.to_numeric(df['Total Household Gross Monthly Income'], errors='coerce')

        # Step 8: Add income classification column
        if 'Total Household Gross Monthly Income' in df.columns:
            df['Annualized Income'] = df['Total Household Gross Monthly Income'] * 12
            df['Income Level'] = df['Annualized Income'].apply(
                lambda x: 1 if x <= 12000 else 
                (2 if 12001 <= x <= 47000 else 
                (3 if 47001 <= x <= 100000 else 
                (4 if x > 100000 else pd.NA)))
            )

        # Step 9: Add Age Grouping column based on the individual's age
        if 'Age' in df.columns:
            df['Age Group'] = df['Age'].apply(lambda x: 'Children/Adolescents' if x < 15 else 
                                              ('Working-Age Adults' if 15 <= x <= 64 else 'The Elderly') 
                                              if pd.notna(x) else pd.NA)

        # Step 10: Clean 'Gender' column using fuzzy matching, but skip NaN values
        if 'Gender' in df.columns:
            gender_options = ['male', 'female', 'transgender', 'nonbinary', 'decline to answer', 'other']
            df['Gender'] = df['Gender'].astype(str).apply(lambda x: process.extractOne(x, gender_options)[0] if pd.notna(x) and x != 'nan' else x)

        # Step 11: Clean 'Race' column using fuzzy matching, but skip NaN values
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
            df['Race'] = df['Race'].astype(str).apply(lambda x: process.extractOne(x, race_options)[0] if pd.notna(x) and x != 'nan' else x)

        # Step 12: Clean 'Insurance Type' column using fuzzy matching, but skip NaN values
        if 'Insurance Type' in df.columns:
            insurance_options = [
                'medicare', 'medicaid', 'medicare & medicaid', 'uninsured', 
                'private', 'military', 'unknown'
            ]
            df['Insurance Type'] = df['Insurance Type'].astype(str).apply(lambda x: process.extractOne(x, insurance_options)[0] if pd.notna(x) and x != 'nan' else x)

        # Step 13: Clean 'Request Status' column again (just to be sure it's lowercased)
        if 'Request Status' in df.columns:
            df['Request Status'] = df['Request Status'].str.lower().str.strip()  # Ensure it's lowercased

        # Step 14: Clean 'Payment Submitted?' column (convert date strings to NaT or keep them as NaT if empty)
        if 'Payment Submitted?' in df.columns:
            df['Payment Submitted?'] = pd.to_datetime(df['Payment Submitted?'], errors='coerce')

        # Step 15: Clean 'Grant Req Date' column (convert to datetime)
        if 'Grant Req Date' in df.columns:
            df['Grant Req Date'] = pd.to_datetime(df['Grant Req Date'], errors='coerce')

        # Ensure 'Amount' is numeric and handle any non-numeric values by converting to NaN
        if 'Amount' in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

        # Clean 'Marital Status' column
        if 'Marital Status' in df.columns:
            marital_status_options = ['single', 'married', 'widowed', 'divorced', 'domestic partnership', 'separated']
            df['Marital Status'] = df['Marital Status'].astype(str).apply(lambda x: process.extractOne(x.lower(), marital_status_options)[0] if pd.notna(x) and x != 'nan' else x)

        # Clean 'Hispanic Latino' column
        if 'Hispanic Latino' in df.columns:
            hispanic_latino_options = ['hispanic-latino', 'non-hispanic latino']
            df['Hispanic Latino'] = df['Hispanic Latino'].astype(str).apply(lambda x: 'yes' if 'hispanic' in x.lower() else 'no' if 'non-hispanic' in x.lower() else x)

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

    # Add functionality to filter by Application Signed?
    application_signed_options = ['yes', 'no', 'n/a']
    application_signed_filter = st.selectbox(
        "Filter by 'Application Signed?'",
        options=application_signed_options
    )
    
    # Filter the data based on the selection
    filtered_df = df[df['Application Signed?'] == application_signed_filter]

    st.write(f"Filtered data based on 'Application Signed?' = {application_signed_filter}:")
    st.dataframe(filtered_df)

    # Demographic Breakout page (Summation by State, Gender, Income Level, Insurance Type, Marital Status, and Hispanic Latino)
    st.sidebar.subheader("Demographic Breakout")
    
    # Sum the "Amount" by "State"
    if "Pt State" in df.columns:
        state_sum = df.groupby('Pt State')['Amount'].sum().reset_index()
        state_sum = state_sum.sort_values(by="Amount", ascending=False)

        st.subheader("Total Amount by State")
        st.dataframe(state_sum)

    # Sum the "Amount" by "Gender"
    if "Gender" in df.columns:
        gender_sum = df.groupby('Gender')['Amount'].sum().reset_index()
        gender_sum = gender_sum.sort_values(by="Amount", ascending=False)

        st.subheader("Total Amount by Gender")
        st.dataframe(gender_sum)

    # Sum the "Amount" by "Income Level"
    if "Income Level" in df.columns:
        income_level_sum = df.groupby('Income Level')['Amount'].sum().reset_index()
        income_level_sum = income_level_sum.sort_values(by="Amount", ascending=False)

        st.subheader("Total Amount by Income Level")
        st.dataframe(income_level_sum)

    # Sum the "Amount" by "Insurance Type"
    if "Insurance Type" in df.columns:
        insurance_sum = df.groupby('Insurance Type')['Amount'].sum().reset_index()
        insurance_sum = insurance_sum.sort_values(by="Amount", ascending=False)

        st.subheader("Total Amount by Insurance Type")
        st.dataframe(insurance_sum)

    # Sum the "Amount" by "Marital Status"
    if "Marital Status" in df.columns:
        marital_status_sum = df.groupby('Marital Status')['Amount'].sum().reset_index()
        marital_status_sum = marital_status_sum.sort_values(by="Amount", ascending=False)

        st.subheader("Total Amount by Marital Status")
        st.dataframe(marital_status_sum)

    # Sum the "Amount" by "Hispanic Latino"
    if "Hispanic Latino" in df.columns:
        hispanic_latino_sum = df.groupby('Hispanic Latino')['Amount'].sum().reset_index()
        hispanic_latino_sum = hispanic_latino_sum.sort_values(by="Amount", ascending=False)

        st.subheader("Total Amount by Hispanic Latino")
        st.dataframe(hispanic_latino_sum)

else:
    st.write("Failed to load and clean data.")
