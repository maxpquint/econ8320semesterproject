#semester project
import pandas as pd
import requests
from io import BytesIO
from thefuzz import process
import streamlit as st
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

# Check and clean up column names to remove extra spaces (if any)
if df is not None:
    df.columns = df.columns.str.strip()  # Strip spaces from column names

    # Ensure 'Year' column exists; if not, create it from the 'Grant Req Date' column
    if 'Year' not in df.columns and 'Grant Req Date' in df.columns:
        df['Year'] = df['Grant Req Date'].dt.year

    # Verify if 'Year' column exists after cleanup
    if 'Year' not in df.columns:
        st.error("The 'Year' column is missing from the dataset. Please ensure the dataset includes a 'Year' or 'Grant Req Date' column.")
    else:
        # Home page
        page = st.sidebar.selectbox("Select a Page", ["Home", "Demographic Breakout", "Grant Payment Time Difference"])
        
        # Home page
        if page == "Home":
            st.subheader("Home Page")
            st.write("This is the home page for the UNO Service Learning Data Dashboard.")
            st.write("Here you can navigate to various analysis pages using the sidebar.")
            st.write("You can explore data related to demographics, payment timing, and other key metrics.")
            
            # Display the first few rows of the data
            st.write("Preview of the data:")
            st.dataframe(df.head())  # Show the first few rows of the cleaned data

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

        # Demographic Breakout Page
        elif page == "Demographic Breakout":
            st.subheader("Demographic Data Breakdown")

            # Filter by year
            year_filter = st.selectbox("Select Year", sorted(df['Year'].dropna().unique()))

            # Filter data by year
            df_year_filtered = df[df['Year'] == year_filter]

            # Display sums for State, Gender, Income Level, Insurance Type, and other demographic categories
            st.write(f"Data for Year {year_filter}:")

            # State Sum
            state_sum = df_year_filtered.groupby('Pt State')['Amount'].sum().reset_index()
            st.write("Total Amount by State:")
            st.dataframe(state_sum)

            # Gender Sum
            gender_sum = df_year_filtered.groupby('Gender')['Amount'].sum().reset_index()
            st.write("Total Amount by Gender:")
            st.dataframe(gender_sum)

            # Income Level Sum
            income_sum = df_year_filtered.groupby('Income Level')['Amount'].sum().reset_index()
            st.write("Total Amount by Income Level:")
            st.dataframe(income_sum)

            # Insurance Type Sum
            insurance_sum = df_year_filtered.groupby('Insurance Type')['Amount'].sum().reset_index()
            st.write("Total Amount by Insurance Type:")
            st.dataframe(insurance_sum)

        # Grant Payment Time Difference Page
        elif page == "Grant Payment Time Difference":
            # Display the time difference between "Grant Req Date" and "Payment Submitted?"
            if df is not None:
                st.subheader("Grant Payment Time Difference")

                # Ensure that both columns are datetime types (if they're not already)
                if 'Grant Req Date' in df.columns and 'Payment Submitted?' in df.columns:
                    # Filter out rows with missing values in either 'Grant Req Date' or 'Payment Submitted?'
                    df_filtered = df.dropna(subset=['Grant Req Date', 'Payment Submitted?'])

                    # Calculate the difference in days (rounding to the nearest whole number)
                    df_filtered['Time Difference (Days)'] = (df_filtered['Payment Submitted?'] - df_filtered['Grant Req Date']).dt.days

                    # Display the result
                    st.write(f"Showing the time difference (in days) between the 'Grant Req Date' and 'Payment Submitted?' columns:")

                    # Show the table with the time difference
                    st.dataframe(df_filtered[['Grant Req Date', 'Payment Submitted?', 'Time Difference (Days)']])
                else:
                    st.write("Columns 'Grant Req Date' or 'Payment Submitted?' are missing or not formatted correctly.")
            else:
                st.write("Data not available for Grant Payment Time Difference.")
else:
    st.write("Failed to load and clean data.")


