import pandas as pd
from app import db
from app.models import CrimeReport
from datetime import datetime


# Function to load crime data from a CSV file into the database
def load_crime_data(file_path, from_api=False):

    # Load the CSV file using pandas
    data = pd.read_csv(file_path)

    # Clear existing data to avoid duplicates
    CrimeReport.query.delete()

    # Iterate each row and create CrimeReport objects to add to the database
    for index, row in data.iterrows():
        # Use 'Last Outcome Category' as the description or set a default value
        description = row['Last outcome category'] if pd.notna(row['Last outcome category']) else 'No description available' # noqa

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
