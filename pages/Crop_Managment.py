import sqlite3
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
from db import *
from Crop_Analysis import growing_seasons

create_table()

def Crop_Manager():
    st.subheader("Crop Management")
    with st.expander("Manager"):
        crops_name = []
    for x in growing_seasons:
        crops_name.append(x)
    crop_name = st.selectbox("Crop Name", crops_name ,help="Enter the name of the crop you want to register.")
    plant_date_input = st.date_input("Planting Date", help="Select the date when you plan to plant the crop.")
    expected_harvest_date = st.date_input("Expected Harvest Date", value=plant_date_input + timedelta(days=120), help="Estimated date of harvest.")

    # Check if the planting date is in the future
    if st.button("Register Crop"):
        today = datetime.today().date()  # Get today's date

    # Display error if planting date is in the future
        if plant_date_input > expected_harvest_date:
           st.error("The planting date cannot be later than the harvest date.")
        elif expected_harvest_date > today:
            st.error("The harvest date cannot be in the future. Please select a valid date.")
        elif not crop_name:
            st.error("Please enter a valid crop name.")
        else:
            # Register the crop if all validations pass
            register_crop(crop_name, plant_date_input, expected_harvest_date)
            st.success(f"Crop '{crop_name}' registered with planting date {plant_date_input} and expected harvest date {expected_harvest_date}.")
        # Exibir todas as culturas registradas
    st.subheader("Registered Crops")
    if st.button("Show Crops"):
        crops = get_crops()
        if crops:
            crops_df = pd.DataFrame(crops, columns=["ID", "Name", "Plant Date", "Harvest Date"])
            st.write(crops_df)
        else:
            st.write("No crops registered yet.")
    st.subheader("Remove Crops")

    crops = get_crops()
    crop_names = [crop[1] for crop in crops]
    select_crop = st.selectbox("Crops Registred", crop_names)

    if st.button("Remove Crop"):
        remove_crop_by_name(select_crop)
        st.success(f"Crop: {select_crop} removed succesfully")
        st.rerun()



    




Crop_Manager()





