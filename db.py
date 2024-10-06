import sqlite3
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta

# Função para conectar ao banco de dados SQLite
def create_connection():
    conn = sqlite3.connect('crop_management.db')
    return conn

# Função para criar a tabela de culturas
def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            plant_date DATE NOT NULL,
            harvest_date DATE NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Função para registrar uma nova cultura
def register_crop(name, plant_date, harvest_date):
    conn = create_connection()
    cursor = conn.cursor()

    # Check if the crop with the same name already exists
    cursor.execute('''
        SELECT COUNT(*) FROM crops WHERE name LIKE ?
    ''', (name + '%',))
    
    count = cursor.fetchone()[0]

    # If the crop name already exists, append a number
    if count > 0:
        new_name = f"{name}{count + 1}"  # Append the next available number
    else:
        new_name = name  # Use the original name if no duplicates

    # Insert the crop into the database
    cursor.execute('''
        INSERT INTO crops (name, plant_date, harvest_date)
        VALUES (?, ?, ?)
    ''', (new_name, plant_date, harvest_date))

    conn.commit()
    conn.close()

    return new_name  # Optionally return the registered crop name


# Função para obter todas as culturas registradas
def get_crops():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM crops')
    crops = cursor.fetchall()
    conn.close()
    return crops

def remove_crop_by_name(crop_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM crops WHERE name='{crop_name}';")
    conn.commit()
    conn.close()

# Cria a tabela no banco de dados
create_table()