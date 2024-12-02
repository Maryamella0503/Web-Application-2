import pandas as pd
from app import db
from app.models import CrimeReport
from datetime import datetime
import numpy as np
from sklearn.cluster import KMeans

def load_crime_data(file_path):
    """Function to load crime data from a CSV file into the database."""
    # Load the CSV file using pandas
    data = pd.read_csv(file_path)

    # Iterate over each row and create CrimeReport objects to add to the database
    for index, row in data.iterrows():
        # Use 'Last Outcome Category' as the description or set a default value
        description = row['Last Outcome Category'] if pd.notna(row['Last Outcome Category']) else 'No description available'

        # Create a new CrimeReport object
        crime_report = CrimeReport(
            title=row['Crime type'],  # Ensure 'Crime_Type' is a valid column in your CSV
            description=description,
            location=row['Location'],  # Ensure 'Location' is a valid column in your CSV
            date_reported=datetime.strptime(row['Month'], '%Y-%m'),  # Adjust the date format if needed
            longitude=row['Longitude'],  # Ensure 'Longitude' is a valid column
            latitude=row['Latitude']  # Ensure 'Latitude' is a valid column
        )
        db.session.add(crime_report)

    # Commit all changes to the database
    db.session.commit()

def predict_crime_hotspots():
    """Function to predict crime hotspots using clustering."""
    # Fetch all crime reports from the database
    reports = CrimeReport.query.all()

    # Extract locations from the reports (Assuming location format is 'latitude,longitude')
    coordinates = []
    for report in reports:
        try:
            lat, lon = map(float, report.location.split(","))
            coordinates.append([lat, lon])
        except ValueError:
            continue  # Skip if the location is not in the expected format

    if not coordinates:
        print("No valid location data found for clustering.")
        return

    # Convert the list of coordinates to a numpy array
    coordinates_np = np.array(coordinates)

    # Use KMeans clustering to identify hotspots
    kmeans = KMeans(n_clusters=5)
    kmeans.fit(coordinates_np)
    hotspots = kmeans.cluster_centers_

    return hotspots