import pandas as pd
from app import db
from app.models import CrimeReport
from datetime import datetime
import numpy as np
from sklearn.cluster import KMeans


# Function to load crime data from a CSV file into the database
def load_crime_data(file_path):
    data = pd.read_csv(file_path)

    # Iterate each row and create CrimeReport objects to add to the database
    for index, row in data.iterrows():
        # Use 'Last Outcome Category' as the description or set a default value
        description = row['Last Outcome Category'] if pd.notna(row['Last Outcome Category']) else 'No description available'  # noqa

        # Create a new CrimeReport object
        crime_report = CrimeReport(
            title=row['Crime type'],
            description=description,
            location=row['Location'],
            date_reported=datetime.strptime(row['Month'], '%Y-%m'),
            longitude=row['Longitude'],
            latitude=row['Latitude']
        )
        db.session.add(crime_report)

    db.session.commit()


# Function to predict crime hotspots using clustering
def predict_crime_hotspots():
    reports = CrimeReport.query.all()

    # Extract locations from the reports (format is 'latitude,longitude')
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
