# pylint: disable=E0611
"""This script contains the queries for recent and historical data."""

from os import environ as ENV
import pandas as pd
from pyodbc import connect
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    '''Returns a connection to the RDS database'''
    return connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                   f"SERVER={ENV['DB_HOST']},{ENV['DB_PORT']};"
                   f"DATABASE={ENV['DB_NAME']};"
                   f"UID={ENV['DB_USER']};"
                   f"PWD={ENV['DB_PASSWORD']}")


def get_plants_dict():
    """Returns a dictionary of species id and name."""
    q = '''SELECT plant_species_id, common_name FROM gamma.plant_species;'''

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(q)
            result = cur.fetchall()
            species_dict = {
                row.common_name: row.plant_species_id for row in result}

    return species_dict


def get_today_data(selected_plant, metric):
    """Fetches today's data for the selected plant."""
    # Use a direct query for a single plant ID
    query = f"""
    SELECT time_taken AS time, {metric}, plant_id
    FROM gamma.recordings
    WHERE time_taken >= CAST(GETDATE() AS DATE)
      AND plant_id = {selected_plant}
    ORDER BY time_taken;
    """

    with get_connection() as conn:
        df = pd.read_sql(query, conn)

    return df


def get_plant_ids():
    """Gets stored plant names."""
    query = "SELECT plant_id FROM gamma.plants;"
    with get_connection() as conn:
        df = pd.read_sql(query, conn)
    return df['plant_id'].tolist()


def fetch_plant_species_data(selected_plant_id):
    """Fetches plant species data based on selected plant ID."""
    query = """
    SELECT TOP 1 p.plant_id, sp.plant_species_id, sp.common_name, sp.scientific_name, r.last_watering 
    FROM gamma.plants AS p
    JOIN gamma.plant_species AS sp ON sp.plant_species_id = p.plant_species_id
    JOIN gamma.recordings AS r ON p.plant_id = r.plant_id
    WHERE p.plant_id = ?
    ORDER BY r.last_watering DESC
    """
    with get_connection() as conn:
        return pd.read_sql(query, conn, params=(selected_plant_id,))
