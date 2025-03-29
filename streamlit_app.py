#semester project
import pandas as pd
import requests
from io import BytesIO
from thefuzz import process
import streamlit as st
import numpy as np
from datetime import datetime

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

        # Step 9: Clean 'Gender' column using fuzzy matching, but skip NaN values
        if 'Gender' in df.columns:
            gender_options = ['male', 'female', 'transgender', 'nonbinary', 'decline to answer', 'other']
            df['Gender'] = df['Gender'].astype(str).apply(lambda x: process.extractOne(x, gender_options)[0] if pd.notna(x) and x != 'nan' else x)

        # Step 10: Clean 'Race' column using fuzzy matching, but skip NaN values
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

        # Step 11: Clean 'Insurance Type' column using fuzzy matching, but skip NaN values
        if 'Insurance Type' in df.columns:
            insurance_options = [
                'medicare', 'medicaid', 'medicare & medicaid', 'uninsured', 
                'private', 'military', 'unknown'
            ]
            df['Insurance Type'] = df['Insurance Type'].astype(str).apply(lambda x: process.extractOne(x, insurance_options)[0] if pd.notna(x) and x != 'nan' else x)

        # Step 12: Clean 'Request Status' column again (just to be sure it's lowercased)
        if 'Request Status' in df.columns:
            df['Request Status'] = df['Request Status'].str.lower().str.strip()  # Ensure it's lowercased

        # Step 13: Clean 'Payment Submitted?' column (convert date strings to NaT or keep them as NaT if empty)
        if 'Payment Submitted?' in df.columns:
            df['Payment Submitted?'] = pd.to_datetime(df['Payment Submitted?'], errors='coerce')

        # Step 14: Clean 'Grant Req Date' column (convert to datetime)
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


# Home page (initial page)
st.title("Welcome to the UNO Service Learning Dashboard")

# For the year filter in demographic breakout page
df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64', errors='ignore')

# Sidebar navigation
pages = ["Home", "Demographic Breakout", "Grant Time Difference"]
page = st.sidebar.radio("Select a page", pages)

# Home page content
if page == "Home":
    st.subheader("Data Overview")
    st.write("Welcome to the UNO Service Learning Data Dashboard. Here you can explore various data and insights related to service learning.")
    st.write("Below is the cleaned data:")
    st.dataframe(df.head())

# Demographic Breakout page
elif page == "Demographic Breakout":
    st.subheader("Demographic Data Breakdown")

    # Ensure the 'Year' column is available for filtering
    if 'Year' not in df.columns:
        st.error("The 'Year' column is missing from the dataset.")
    else:
        # Clean the 'Year' column to ensure all values are consistent and of type 'string'
        df['Year'] = df['Year'].astype(str, errors='ignore')  # Ensure it's treated as a string

        # Check if any non-numeric values exist in the 'Year' column
        try:
            # Try to convert 'Year' to integers for proper sorting
            df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64', errors='ignore')
        except Exception as e:
            st.error(f"Error in 'Year' column conversion: {e}")
        
        # Add Year filter for the page
        year_filter = st.selectbox("Select Year", sorted(df['Year'].dropna().unique()))

        # Filter data by the selected year
        df_year_filtered = df[df['Year'] == year_filter]

        # For 'State' summation
        st.write("Total Amount by State:")
        # Handle NaN values properly and sum up amounts for each state
        state_sum = df_year_filtered.groupby('Pt State')['Amount'].sum(min_count=1).reset_index()
        st.dataframe(state_sum)

        # For 'Gender' summation
        st.write("Total Amount by Gender:")
        gender_sum = df_year_filtered.groupby('Gender')['Amount'].sum(min_count=1).reset_index()
        st.dataframe(gender_sum)

        # For 'Income Level' summation
        st.write("Total Amount by Income Level:")
        income_sum = df_year_filtered.groupby('Income Level')['Amount'].sum(min_count=1).reset_index()
        st.dataframe(income_sum)

        # For 'Insurance Type' summation
        st.write("Total Amount by Insurance Type:")
        insurance_sum = df_year_filtered.groupby('Insurance Type')['Amount'].sum(min_count=1).reset_index()
        st.dataframe(insurance_sum)

# Grant Time Difference page
elif page == "Grant Time Difference":
    st.subheader("Grant Time Difference")

    # Filter the data where both "Grant Req Date" and "Payment Submitted?" columns have values
    df_grant_time = df.dropna(subset=['Grant Req Date', 'Payment Submitted?'])

    # Calculate the time difference between the "Grant Req Date" and "Payment Submitted?" columns
    df_grant_time['Time Difference (Days)'] = (df_grant_time['Payment Submitted?'] - df_grant_time['Grant Req Date']).dt.days

    # Show the data with the calculated time differences
    st.write("Time difference between Grant Req Date and Payment Submitted?")
    st.dataframe(df_grant_time[['Grant Req Date', 'Payment Submitted?', 'Time Difference (Days)']])



