#semester project
import pandas as pd
import requests
from io import BytesIO
import streamlit as st
import numpy as np
from thefuzz import process

def import_excel_from_github(sheet_name=0):
    github_raw_url = "https://github.com/maxpquint/econ8320semesterproject/raw/main/UNO%20Service%20Learning%20Data%20Sheet%20De-Identified%20Version.xlsx"
    
    try:
        # Load the data from GitHub
        response = requests.get(github_raw_url)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        df = pd.read_excel(BytesIO(response.content), sheet_name=sheet_name)

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

# Create a navigation sidebar
page = st.sidebar.selectbox("Select a page", ["Home", "Demographic Breakout", "Grant Payment Time Difference"])

# Load the data
df = import_excel_from_github()

# Home page or other pages
if page == "Home":
    st.write("Welcome to the Dashboard!")

elif page == "Demographic Breakout":
    # Year filter for the Demographic Breakout page
    year_filter = st.sidebar.selectbox("Select Year", options=df['Year'].unique())
    filtered_df = df[df['Year'] == year_filter]

    # State sum
    if "Pt State" in filtered_df.columns:
        state_sum = filtered_df.groupby('Pt State')['Amount'].sum().reset_index()
        state_sum = state_sum.sort_values(by="Amount", ascending=False)

        st.subheader(f"Total Amount by State for {year_filter}")
        st.dataframe(state_sum)

    # Gender sum
    if "Gender" in filtered_df.columns:
        gender_sum = filtered_df.groupby('Gender')['Amount'].sum().reset_index()
        gender_sum = gender_sum.sort_values(by="Amount", ascending=False)

        st.subheader(f"Total Amount by Gender for {year_filter}")
        st.dataframe(gender_sum)

    # Income Level sum
    if "Income Level" in filtered_df.columns:
        income_level_sum = filtered_df.groupby('Income Level')['Amount'].sum().reset_index()
        income_level_sum = income_level_sum.sort_values(by="Amount", ascending=False)

        st.subheader(f"Total Amount by Income Level for {year_filter}")
        st.dataframe(income_level_sum)

    # Insurance Type sum
    if "Insurance Type" in filtered_df.columns:
        insurance_sum = filtered_df.groupby('Insurance Type')['Amount'].sum().reset_index()
        insurance_sum = insurance_sum.sort_values(by="Amount", ascending=False)

        st.subheader(f"Total Amount by Insurance Type for {year_filter}")
        st.dataframe(insurance_sum)

    # Marital Status sum
    if "Marital Status" in filtered_df.columns:
        marital_status_sum = filtered_df.groupby('Marital Status')['Amount'].sum().reset_index()
        marital_status_sum = marital_status_sum.sort_values(by="Amount", ascending=False)

        st.subheader(f"Total Amount by Marital Status for {year_filter}")
        st.dataframe(marital_status_sum)

    # Hispanic Latino sum
    if "Hispanic Latino" in filtered_df.columns:
        hispanic_latino_sum = filtered_df.groupby('Hispanic Latino')['Amount'].sum().reset_index()
        hispanic_latino_sum = hispanic_latino_sum.sort_values(by="Amount", ascending=False)

        st.subheader(f"Total Amount by Hispanic Latino for {year_filter}")
        st.dataframe(hispanic_latino_sum)

elif page == "Grant Payment Time Difference":
    # Display the time difference between "Grant Req Date" and "Payment Submitted?"
    if df is not None:
        st.subheader("Grant Payment Time Difference")

        # Ensure that both columns are datetime types (if they're not already)
        if 'Grant Req Date' in df.columns and 'Payment Submitted?' in df.columns:
            # Calculate the difference in days (rounding to the nearest whole number)
            df['Time Difference (Days)'] = (df['Payment Submitted?'] - df['Grant Req Date']).dt.days

            # Display the result
            st.write(f"Time difference (in days) between 'Grant Req Date' and 'Payment Submitted?' calculated for each row.")
            
            # Show the table with the time difference
            st.dataframe(df[['Grant Req Date', 'Payment Submitted?', 'Time Difference (Days)']].dropna(subset=['Time Difference (Days)']))
        else:
            st.write("Columns 'Grant Req Date' or 'Payment Submitted?' are missing or not formatted correctly.")
else:
    st.write("Select a valid page.")

