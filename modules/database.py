# modules/database.py
import streamlit as st
import pandas as pd
import os

PATIENTS_FILE = "patients.txt"


def load_patients_db():
    """Loads patients directly from patients.txt into session state."""
    if "patients_db" not in st.session_state:
        if os.path.exists(PATIENTS_FILE):
            try:
                # Read pipe-separated file
                df = pd.read_csv(PATIENTS_FILE, sep="|")
                # Ensure all column values are strings/properly formatted to prevent type conversion issues
                st.session_state.patients_db = df
            except Exception as e:
                st.error(f"Error loading {PATIENTS_FILE}: {e}")
                st.session_state.patients_db = _get_empty_patients_df()
        else:
            # Initialize empty dataframe with correct headers if file doesn't exist
            df = _get_empty_patients_df()
            save_patients_db(df)
            st.session_state.patients_db = df

    return st.session_state.patients_db


def save_patients_db(df):
    """Saves the current pandas DataFrame back to patients.txt using pipe separation and forces disk write."""
    try:
        # Write to csv using pipe separator
        df.to_csv(PATIENTS_FILE, sep="|", index=False)
        st.session_state.patients_db = df
    except Exception as e:
        st.error(f"Error saving to {PATIENTS_FILE}: {e}")


def _get_empty_patients_df():
    """Returns an empty DataFrame with the required patient schema headers."""
    headers = [
        "UID", "Full_Name", "DOB", "Gender", "Contact_Number",
        "Email", "Address", "Emergency_Contact", "Allergies",
        "Pre_existing_Conditions", "Registration_Date"
    ]
    return pd.DataFrame(columns=headers)