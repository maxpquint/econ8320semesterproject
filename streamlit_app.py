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

        # Clean column names by stripping any leading or trailing spaces
        df.columns = df.columns.str.strip()

        # Display the cleaned column names to verify
        st.write("Cleaned column names:")
        st.write(df.columns)  # Display the actual column names from the raw data

        # Step 1: Replace all occurrences of "Missing" (case insensitive) with NaN across the entire DataFrame
        df.replace(to_replace=r'(?i)^missing$', value=np.nan, regex=True, inplace=True)

        # Step 2: Rename specific columns to match your desired format
        df.rename(columns={ 
            'State': 'Pt State', 
            'Payment Submitted': 'Payment Submitted?', 
            'Application Signed': 'Application Signed?'
        }, inplace=True)

        # Check if the 'Year' column exists, and if not, create it from 'Grant Req Date'
        if 'Grant Req Date' in df.columns:
            df['Grant Req Date'] = pd.to_datetime(df['Grant Req Date'], errors='coerce')
            df['Year'] = df['Grant Req Date'].dt.year  # Create 'Year' column based on 'Grant Req Date'
        
        # If 'Year' is still missing, create it based on 'Payment Submitted?'
        if 'Year' not in df.columns and 'Payment Submitted?' in df.columns:
            df['Payment Submitted?'] = pd.to_datetime(df['Payment Submitted?'], errors='coerce')
            df['Year'] = df['Payment Submitted?'].dt.year  # Create 'Year' column based on 'Payment Submitted?'
        
        # Check again if 'Year' was successfully created
        if 'Year' not in df.columns:
            st.error("Error: 'Year' column could not be created from the available date columns.")
            return None

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

# Sidebar navigation
pages = ["Home", "Demographic Breakout", "Grant Time Difference"]
page = st.sidebar.radio("Select a page:", pages)

# Load the data
df = import_excel_from_github()

if df is not None:
    if page == "Home":
        # Display basic data and filtering
        st.subheader("Pending Applications")
        
        # Standardizing and filtering 'Request Status' to handle possible variations
        if 'Request Status' in df.columns:
            # Filter the DataFrame to show rows where 'Request Status' ends with 'pending', case insensitive
            pending_df = df[df['Request Status'].str.endswith('pending', na=False)]  # Make case-insensitive check
            
            # Display the rows where request status ends with 'pending'
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
            return df.to_csv(index=False)

        csv = convert_df(df)

        # Provide a download button for the CSV file
        st.download_button(
            label="Download Cleaned Data as CSV",
            data=csv,
            file_name='cleaned_data.csv',
            mime='text/csv'
        )

    elif page == "Demographic Breakout":
        st.subheader("Demographic Data Breakdown")

        # Check if 'Year' column exists
        if 'Year' not in df.columns:
            st.error("The 'Year' column is missing from the dataset.")
        else:
            # Filter by Year (first filter)
            year_filter = st.selectbox("Select Year", sorted(df['Year'].dropna().unique()))

            # Filter data by selected year
            df_year_filtered = df[df['Year'] == year_filter]

            # Display available filters for demographics
            state_filter = st.multiselect("Select State", options=df_year_filtered['Pt State'].dropna().unique(), default=df_year_filtered['Pt State'].dropna().unique())
            gender_filter = st.multiselect("Select Gender", options=df_year_filtered['Gender'].dropna().unique(), default=df_year_filtered['Gender'].dropna().unique())
            income_filter = st.multiselect("Select Income Level", options=df_year_filtered['Income Level'].dropna().unique(), default=df_year_filtered['Income Level'].dropna().unique())
            insurance_filter = st.multiselect("Select Insurance Type", options=df_year_filtered['Insurance Type'].dropna().unique(), default=df_year_filtered['Insurance Type'].dropna().unique())

            # Apply filters on the filtered year data
            df_filtered = df_year_filtered[
                df_year_filtered['Pt State'].isin(state_filter) &
                df_year_filtered['Gender'].isin(gender_filter) &
                df_year_filtered['Income Level'].isin(income_filter) &
                df_year_filtered['Insurance Type'].isin(insurance_filter)
            ]

            # Remove rows with NaN in the 'Amount' column before summing
            df_filtered_cleaned = df_filtered.dropna(subset=['Amount'])

            # Display sums for each demographic category

            # State Sum
            state_sum = df_filtered_cleaned.groupby('Pt State')['Amount'].sum().reset_index()
            st.write("Total Amount by State:")
            st.dataframe(state_sum)

            # Gender Sum
            gender_sum = df_filtered_cleaned.groupby('Gender')['Amount'].sum().reset_index()
            st.write("Total Amount by Gender:")
            st.dataframe(gender_sum)

            # Income Level Sum
            income_sum = df_filtered_cleaned.groupby('Income Level')['Amount'].sum().reset_index()
            st.write("Total Amount by Income Level:")
            st.dataframe(income_sum)

            # Insurance Type Sum
            insurance_sum = df_filtered_cleaned.groupby('Insurance Type')['Amount'].sum().reset_index()
            st.write("Total Amount by Insurance Type:")
            st.dataframe(insurance_sum)

    elif page == "Grant Time Difference":
        st.subheader("Time Difference Between Grant Request Date and Payment Submitted")

        # Filter rows with valid Grant Req Date and Payment Submitted? date values
        df_grant_time_filtered = df.dropna(subset=['Grant Req Date', 'Payment Submitted?'])

        # Calculate time difference in days between 'Grant Req Date' and 'Payment Submitted?'
        df_grant_time_filtered['Grant Time Difference (days)'] = (df_grant_time_filtered['Payment Submitted?'] - df_grant_time_filtered['Grant Req Date']).dt.days

        # Display the time differences
        st.write("Time Difference (in days) between Grant Request Date and Payment Submitted?")
        st.dataframe(df_grant_time_filtered[['Grant Req Date', 'Payment Submitted?', 'Grant Time Difference (days)']])



