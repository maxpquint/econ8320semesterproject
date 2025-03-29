import pandas as pd
import requests
from io import BytesIO
from thefuzz import process
import streamlit as st
import numpy as np  # For NaN

# Function to import the Excel file and clean data
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

        # Step 15: Add 'Year' column from the 'Grant Req Date' column
        if 'Grant Req Date' in df.columns:
            df['Year'] = df['Grant Req Date'].dt.year

        # Ensure 'Amount' column is numeric, coerce any errors into NaN
        if 'Amount' in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')  # Coerce errors to NaN

        # Step 16: Clean 'Marital Status' column
        if 'Marital Status' in df.columns:
            marital_options = ['single', 'married', 'widowed', 'divorced', 'domestic partnership', 'separated']
            df['Marital Status'] = df['Marital Status'].astype(str).apply(lambda x: process.extractOne(x, marital_options)[0] if pd.notna(x) and x != 'nan' else x)

        # Step 17: Clean 'Hispanic/Latino' column (correct column name used here)
        if 'Hispanic/Latino' in df.columns:
            df['Hispanic/Latino'] = df['Hispanic/Latino'].apply(
                lambda x: 'Yes' if 'hispanic' in str(x).lower() else ('No' if 'non-hispanic' in str(x).lower() else np.nan)
            )
        else:
            st.write("Error: 'Hispanic/Latino' column not found!")

        return df
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return None


# Streamlit interface
st.title('UNO Service Learning Data Dashboard')

# Load the data globally so it's accessible across pages
df = import_excel_from_github()

# Ensure the DataFrame was successfully loaded
if df is not None:
    # Sidebar navigation
    page = st.sidebar.selectbox("Select a Page", ["Home", "Demographic Breakout", "Grant Time Difference"])

    # Home Page
    if page == "Home":
        st.subheader("Welcome to the Home Page!")

        # Display the updated column names in the DataFrame
        st.write("Updated Column names in the dataset:")
        st.write(df.columns)  # Display the column names in the Streamlit app

        st.write("Data cleaned successfully!")
        st.dataframe(df.head())  # Show the first few rows of the cleaned data

        # Button to download cleaned data
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')

        csv = convert_df(df)
        st.download_button(
            label="Download Cleaned Data",
            data=csv,
            file_name="cleaned_data.csv",
            mime="text/csv",
        )

    # Demographic Breakout Page
    elif page == "Demographic Breakout":
        st.subheader("Demographic Data Breakdown")

        # Ensure the 'Year' column is available for filtering
        if 'Year' not in df.columns:
            st.error("The 'Year' column is missing from the dataset.")
        else:
            # Clean the 'Year' column to ensure all values are consistent and of type 'string'
            df['Year'] = df['Year'].astype(str, errors='ignore')  # Ensure it's treated as a string

            # Add Year filter for the page
            year_filter = st.selectbox("Select Year", sorted(df['Year'].dropna().unique()))

            # Filter data by the selected year
            df_year_filtered = df[df['Year'] == year_filter]

            # Reference lists for all categories
            all_states = [
                'NE', 'IA', 'KS', 'MO', 'SD', 'WY', 'CO', 'MN'
            ]

            all_genders = ['male', 'female', 'transgender', 'nonbinary', 'decline to answer', 'other']
            all_income_levels = [1, 2, 3, 4]  # Example: Adjust to your specific income levels
            all_insurance_types = ['medicare', 'medicaid', 'medicare & medicaid', 'uninsured', 'private', 'military', 'unknown']
            all_marital_status = ['single', 'married', 'widowed', 'divorced', 'domestic partnership', 'separated']
            all_hispanic_latino = ['Yes', 'No']

            # For 'State' summation - ensure all states are included
            st.write("Total Amount by State:")
            state_sum = df_year_filtered.groupby('Pt State')['Amount'].sum(min_count=1).reset_index()
            state_sum = pd.DataFrame(all_states, columns=['Pt State']).merge(state_sum, on='Pt State', how='left')
            st.dataframe(state_sum)

            # For 'Gender' summation - ensure all genders are included
            st.write("Total Amount by Gender:")
            gender_sum = df_year_filtered.groupby('Gender')['Amount'].sum(min_count=1).reset_index()
            gender_sum = pd.DataFrame(all_genders, columns=['Gender']).merge(gender_sum, on='Gender', how='left')
            st.dataframe(gender_sum)

            # For 'Income Level' summation - ensure all income levels are included
            st.write("Total Amount by Income Level:")
            income_sum = df_year_filtered.groupby('Income Level')['Amount'].sum(min_count=1).reset_index()
            income_sum = pd.DataFrame(all_income_levels, columns=['Income Level']).merge(income_sum, on='Income Level', how='left')
            st.dataframe(income_sum)

            # For 'Insurance Type' summation - ensure all insurance types are included
            st.write("Total Amount by Insurance Type:")
            insurance_sum = df_year_filtered.groupby('Insurance Type')['Amount'].sum(min_count=1).reset_index()
            insurance_sum = pd.DataFrame(all_insurance_types, columns=['Insurance Type']).merge(insurance_sum, on='Insurance Type', how='left')
            st.dataframe(insurance_sum)

            # For 'Marital Status' summation - ensure all marital status options are included
            st.write("Total Amount by Marital Status:")
            marital_status_sum = df_year_filtered.groupby('Marital Status')['Amount'].sum(min_count=1).reset_index()
            marital_status_sum = pd.DataFrame(all_marital_status, columns=['Marital Status']).merge(marital_status_sum, on='Marital Status', how='left')
            st.dataframe(marital_status_sum)

            # For 'Hispanic Latino' summation - ensure all options are included
            st.write("Total Amount by Hispanic Latino:")
            hispanic_latino_sum = df_year_filtered.groupby('Hispanic/Latino')['Amount'].sum(min_count=1).reset_index()
            hispanic_latino_sum = pd.DataFrame(all_hispanic_latino, columns=['Hispanic/Latino']).merge(hispanic_latino_sum, on='Hispanic/Latino', how='left')
            st.dataframe(hispanic_latino_sum)

    # Grant Time Difference Page
    elif page == "Grant Time Difference":
        st.subheader("Grant Time Difference Analysis")

        # Filter rows that have both 'Grant Req Date' and 'Payment Submitted?'
        if 'Grant Req Date' in df.columns and 'Payment Submitted?' in df.columns:
            df_filtered = df.dropna(subset=['Grant Req Date', 'Payment Submitted?'])

            # Calculate the time difference between the 'Grant Req Date' and 'Payment Submitted?'
            df_filtered['Time Difference (Days)'] = (df_filtered['Payment Submitted?'] - df_filtered['Grant Req Date']).dt.days

            # Display the filtered DataFrame with time difference
            st.dataframe(df_filtered[['Grant Req Date', 'Payment Submitted?', 'Time Difference (Days)']])
        else:
            st.write("Columns for 'Grant Req Date' and/or 'Payment Submitted?' are missing.")










