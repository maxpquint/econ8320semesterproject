import pandas as pd  # Data manipulation
import requests  # HTTP requests
from io import BytesIO  # Handle byte streams for Excel
from thefuzz import process  # Fuzzy string matching
import streamlit as st  # Streamlit web app
import numpy as np  # Numerical operations
import plotly.express as px  # Interactive plotting

# Function to import and clean Excel data from GitHub
@st.cache_data
def import_excel_from_github(sheet_name=0):
    github_raw_url = "https://github.com/maxpquint/econ8320semesterproject/raw/main/UNO%20Service%20Learning%20Data%20Sheet%20De-Identified%20Version.xlsx"
    try:
        response = requests.get(github_raw_url)  # Get the file from GitHub
        response.raise_for_status()
        df = pd.read_excel(BytesIO(response.content), sheet_name=sheet_name)  # Read Excel content into DataFrame
        st.write("Excel file successfully loaded into DataFrame.")

        # Replace 'missing' with NaN for consistency
        df.replace(to_replace=r'(?i)^missing$', value=np.nan, regex=True, inplace=True)

        # Rename certain columns for consistency
        df.rename(columns={
            'State': 'Pt State',
            'Payment Submitted': 'Payment Submitted?',
            'Application Signed': 'Application Signed?'
        }, inplace=True)

        # Normalize 'Request Status' with fuzzy matching
        if 'Request Status' in df.columns:
            request_status_options = ['pending', 'approved', 'denied', 'completed']
            df['Request Status'] = df['Request Status'].astype(str).apply(
                lambda x: process.extractOne(x.lower().strip(), request_status_options)[0]
                if pd.notna(x) and x.lower().strip() != 'nan' else np.nan)

        # Normalize 'Application Signed?' responses
        if 'Application Signed?' in df.columns:
            application_signed_options = ['yes', 'no', 'n/a']
            df['Application Signed?'] = df['Application Signed?'].astype(str).apply(
                lambda x: process.extractOne(x.lower(), application_signed_options)[0] if pd.notna(x) else 'N/A')

        # Convert full state names to postal codes using fuzzy matching
        state_to_postal = {
            "Nebraska": "NE", "Iowa": "IA", "Kansas": "KS", "Missouri": "MO",
            "South Dakota": "SD", "Wyoming": "WY", "Colorado": "CO", "Minnesota": "MN"
        }
        if 'Pt State' in df.columns:
            df['Pt State'] = df['Pt State'].astype(str).apply(
                lambda x: state_to_postal.get(process.extractOne(x, list(state_to_postal.keys()))[0], x)
                if pd.notna(x) and x != 'nan' else x)

        # Clean income data and generate income categories
        if 'Total Household Gross Monthly Income' in df.columns:
            df['Total Household Gross Monthly Income'] = pd.to_numeric(df['Total Household Gross Monthly Income'], errors='coerce')
            df['Annualized Income'] = df['Total Household Gross Monthly Income'] * 12
            df['Income Level'] = df['Annualized Income'].apply(
                lambda x: "$0–$12,000" if x <= 12000 else
                "$12,001–$47,000" if 12000 < x <= 47000 else
                "$47,001–$100,000" if 47000 < x <= 100000 else
                "$100,000+" if x > 100000 else pd.NA)

        # Standardize 'Gender' responses using fuzzy matching
        if 'Gender' in df.columns:
            gender_options = ['male', 'female', 'transgender', 'nonbinary', 'decline to answer', 'other']
            df['Gender'] = df['Gender'].astype(str).apply(
                lambda x: process.extractOne(x, gender_options)[0] if pd.notna(x) and x != 'nan' else x)

        # Standardize 'Race' responses
        if 'Race' in df.columns:
            race_options = [
                'American Indian or Alaska Native', 'Asian', 'Black or African American', 'Middle Eastern or North African',
                'Native Hawaiian or Pacific Islander', 'White', 'decline to answer', 'other', 'two or more']
            df['Race'] = df['Race'].astype(str).apply(
                lambda x: process.extractOne(x, race_options)[0] if pd.notna(x) and x != 'nan' else x)

        # Normalize 'Insurance Type' using fuzzy matching
        if 'Insurance Type' in df.columns:
            insurance_options = [
                'medicare', 'medicaid', 'medicare & medicaid', 'uninsured',
                'private', 'military', 'unknown']
            df['Insurance Type'] = df['Insurance Type'].astype(str).apply(
                lambda x: process.extractOne(x, insurance_options)[0] if pd.notna(x) and x != 'nan' else x)

        # Convert 'Payment Submitted?' column to datetime
        if 'Payment Submitted?' in df.columns:
            df['Payment Submitted?'] = pd.to_datetime(df['Payment Submitted?'], errors='coerce')

        # Parse 'Grant Req Date' and extract year
        if 'Grant Req Date' in df.columns:
            df['Grant Req Date'] = pd.to_datetime(df['Grant Req Date'], errors='coerce')
            df['Year'] = df['Grant Req Date'].dt.year

        # Ensure 'Amount' is numeric
        if 'Amount' in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

        # Standardize 'Marital Status'
        if 'Marital Status' in df.columns:
            marital_options = ['single', 'married', 'widowed', 'divorced', 'domestic partnership', 'separated']
            df['Marital Status'] = df['Marital Status'].astype(str).apply(
                lambda x: process.extractOne(x, marital_options)[0] if pd.notna(x) and x != 'nan' else x)

        # Simplify 'Hispanic/Latino' responses to Yes/No
        if 'Hispanic/Latino' in df.columns:
            df['Hispanic/Latino'] = df['Hispanic/Latino'].apply(
                lambda x: 'No' if 'non' in str(x).lower() else 'Yes' if pd.notna(x) else np.nan)

        # Normalize 'Type of Assistance (CLASS)' values
        if 'Type of Assistance (CLASS)' in df.columns:
            assistance_options = [
                'Medical Supplies/Prescription Co-pay(s)', 'Food/Groceries', 'Gas', 'Other', 'Hotel', 'Housing',
                'Utilities', 'Car Payment', 'Phone/Internet', 'Multiple']
            df['Type of Assistance (CLASS)'] = df['Type of Assistance (CLASS)'].astype(str).apply(
                lambda x: process.extractOne(x.lower(), [i.lower() for i in assistance_options])[0] if pd.notna(x) else x)

        # Compute 'Time to Support' as difference between payment date and request date
        if 'Payment Submitted?' in df.columns and 'Grant Req Date' in df.columns:
            df['Time to Support'] = (df['Payment Submitted?'] - df['Grant Req Date']).dt.days

        return df

    except requests.exceptions.RequestException as e:
        st.write(f"Error: {e}")
        return pd.DataFrame()


# Streamlit App Title
st.title('UNO Service Learning Data Dashboard')

# Load cleaned data
df = import_excel_from_github()

# Sidebar navigation
if df is not None:
    page = st.sidebar.selectbox("Select a Page", [
        "Home",
        "Demographic Breakout",
        "Grant Time Difference",
        "Remaining Balance Analysis",
        "Application Signed",
        "Impact & Progress Summary"
    ])

    # ---------- Home Page ----------
    if page == "Home":
        st.subheader("Welcome to the Home Page!")

        # Display cleaned column names
        st.write("Updated Column names in the dataset:")
        st.write(df.columns)

        # Preview first few rows of cleaned dataset
        st.write("Data cleaned successfully!")
        st.dataframe(df.head(), use_container_width=True)

        # Cache CSV conversion for download
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')

        csv = convert_df(df)

        # Download button for cleaned data
        st.download_button(
            label="Download Cleaned Data",
            data=csv,
            file_name='cleaned_data.csv',
            mime='text/csv'
        )

    # ---------- Demographic Breakout Page ----------
    elif page == "Demographic Breakout":
        st.subheader("Demographic Breakout Analysis")

        # Select year to filter data
        year = st.selectbox("Select Year", df['Year'].unique(), key="year_demo")
        df_year_filtered = df[df['Year'] == year]

        # Helper function to summarize Amount by demographic category
        def render_sum(category, label):
            all_values = sorted(df[category].dropna().unique().tolist())
            group = df_year_filtered.groupby(category)['Amount'].sum(min_count=1).reset_index()
            full = pd.DataFrame(all_values, columns=[category]).merge(group, on=category, how='left')
            st.write(f"Total Amount by {label}:")
            st.dataframe(full)

        # Run summaries for each demographic feature
        render_sum('Pt State', 'State')
        render_sum('Gender', 'Gender')
        render_sum('Income Level', 'Income Level')
        render_sum('Insurance Type', 'Insurance Type')
        render_sum('Marital Status', 'Marital Status')
        render_sum('Hispanic/Latino', 'Hispanic/Latino')

    # ---------- Grant Time Difference Page ----------
    elif page == "Grant Time Difference":
        st.subheader("Time Between Request and Support")

        # Year filter
        year = st.selectbox("Select Year", df['Year'].unique(), key="year_grant_time")
        df_year_filtered = df[df['Year'] == year]

        # Validate required columns exist
        if 'Grant Req Date' in df_year_filtered.columns and 'Payment Submitted?' in df_year_filtered.columns:
            df_year_filtered['Time to Support'] = (df_year_filtered['Payment Submitted?'] - df_year_filtered['Grant Req Date']).dt.days

            # Plot histogram of support delay
            st.write(f"Distribution of Time to Support (in days) for Year: {year}")
            fig = px.histogram(df_year_filtered['Time to Support'].dropna(), nbins=30, title=f"Time to Support (in days) for {year}", 
                                labels={'Time to Support': 'Days'}, opacity=0.75)
            st.plotly_chart(fig)

            # Summary stats
            st.write("Average Time to Support for Year", year, ":", df_year_filtered['Time to Support'].mean())
            st.write("Count for Year", year, ":", df_year_filtered['Time to Support'].count())
        else:
            st.write("Required columns ('Grant Req Date' and 'Payment Submitted?') are missing in the dataset.")

    # ---------- Remaining Balance Analysis Page ----------
    elif page == "Remaining Balance Analysis":
        st.subheader("Remaining Balance Analysis")

        if 'Remaining Balance' in df.columns:
            df['Remaining Balance'] = pd.to_numeric(df['Remaining Balance'], errors='coerce')

            if 'Year' in df.columns:
                year = st.selectbox("Select Year", df['Year'].unique(), key="year_balance")
                df_year_filtered = df[df['Year'] == year]
                df_year_filtered_unique = df_year_filtered.drop_duplicates(subset='Patient ID#')

                # Segment by remaining balance
                df_filtered_zero_or_less = df_year_filtered_unique[df_year_filtered_unique['Remaining Balance'] <= 0]
                df_filtered_greater_than_zero = df_year_filtered_unique[df_year_filtered_unique['Remaining Balance'] > 0]

                # Count unique patients by group
                patient_count_zero_or_less = df_filtered_zero_or_less['Patient ID#'].nunique()
                patient_count_greater_than_zero = df_filtered_greater_than_zero['Patient ID#'].nunique()

                # Display counts and pie chart
                st.write(f"Number of Unique Patients with Remaining Balance <= 0 for Year {year}: {patient_count_zero_or_less}")
                st.write(f"Number of Unique Patients with Remaining Balance > 0 for Year {year}: {patient_count_greater_than_zero}")

                fig = px.pie(
                    names=["<= 0", "> 0"], 
                    values=[patient_count_zero_or_less, patient_count_greater_than_zero], 
                    title="Remaining Balance: Unique Patient Distribution"
                )
                st.plotly_chart(fig)

                # Display detail tables
                st.write("Unique Patients with Remaining Balance <= 0:")
                st.dataframe(df_filtered_zero_or_less[['Patient ID#', 'Remaining Balance']])

                st.write("Unique Patients with Remaining Balance > 0:")
                st.dataframe(df_filtered_greater_than_zero[['Patient ID#', 'Remaining Balance']])

                # Total amount by assistance type
                if 'Type of Assistance (CLASS)' in df.columns:
                    st.write("Total Amount by Type of Assistance (CLASS):")
                    assistance_sum = df_year_filtered.groupby('Type of Assistance (CLASS)')['Amount'].sum(min_count=1).reset_index()

                    fig = px.pie(
                        assistance_sum, 
                        names='Type of Assistance (CLASS)', 
                        values='Amount', 
                        title="Total Amount by Type of Assistance"
                    )
                    st.plotly_chart(fig)
            else:
                st.write("The 'Year' column is missing in the dataset.")
        else:
            st.write("The 'Remaining Balance' column is missing in the dataset.")

    # ---------- Application Signed Page ----------
    elif page == "Application Signed":
        st.subheader("Application Signed Data")

        if 'Request Status' in df.columns:
            df_pending = df[df['Request Status'] == 'pending']
            st.write(f"Displaying records where 'Request Status' is 'pending':")
            st.dataframe(df_pending[['Patient ID#', 'Application Signed?', 'Request Status', 'Year']])
        else:
            st.write("The 'Request Status' column is missing in the dataset.")

    # ---------- Impact & Progress Summary Page ----------
    elif page == "Impact & Progress Summary":
        st.subheader("Impact & Progress Summary")
        required_cols = ['Amount', 'Patient ID#', 'Time to Support', 'Application Signed?', 'Remaining Balance', 'Pt State']
        if all(col in df.columns for col in required_cols):
            year = st.selectbox("Select Year", df['Year'].unique(), key="year_impact")
            df_year_filtered = df[df['Year'] == year]
            
            # Key metrics
            total_amount = df_year_filtered['Amount'].sum()
            patients_served = df_year_filtered['Patient ID#'].nunique()
            avg_support_time = df_year_filtered['Time to Support'].mean()
            signed_apps = df_year_filtered['Application Signed?'].str.lower().eq('yes').sum()
            signed_pct = (signed_apps / len(df_year_filtered)) * 100 if len(df_year_filtered) > 0 else 0
            fully_utilized_pct = (df_year_filtered[df_year_filtered['Remaining Balance'] <= 0]['Patient ID#'].nunique() / patients_served) * 100 if patients_served > 0 else 0

            # Display key stats
            st.markdown("### Key Highlights")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Grants Disbursed", f"${total_amount:,.0f}")
            col2.metric("Patients Served", patients_served)
            col3.metric("Avg. Time to Support", f"{avg_support_time:.1f} days" if not np.isnan(avg_support_time) else "N/A")

            col4, col5 = st.columns(2)
            col4.metric("Application Completion", f"{signed_pct:.1f}%")
            col5.metric("Fully Utilized Grants", f"{fully_utilized_pct:.1f}%")

            st.divider()

            # Grants over time
            if 'Year' in df.columns:
                amount_trend = df.groupby('Year')['Amount'].sum().reset_index()
                fig_trend = px.bar(amount_trend, x='Year', y='Amount', title="Total Grants Over Time")
                st.plotly_chart(fig_trend)

            # Grants by state map
            state_grant_count = df_year_filtered.groupby('Pt State')['Amount'].sum().reset_index()
            fig_map = px.choropleth(
                state_grant_count,
                locations='Pt State',
                locationmode="USA-states",
                color='Amount',
                hover_name='Pt State',
                color_continuous_scale="Viridis",
                title="Grants by State"
            )
            st.plotly_chart(fig_map)

        else:
            st.write("Data is missing some required columns for impact summary.")



















