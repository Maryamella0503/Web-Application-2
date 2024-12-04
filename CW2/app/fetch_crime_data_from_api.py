import requests
from app import db
from app.models import CrimeReport
from datetime import datetime


def fetch_crime_data_from_api():
    # Function to fetch data from the crime data API
    # and load it into the database
    try:
        api_url = "https://data.police.uk/api/crimes-street/all-crime?lat=53.8008&lng=-1.5491" # noqa
        response = requests.get(api_url)
        response.raise_for_status()
        crimes = response.json()

        # Clear existing data to avoid duplicates
        CrimeReport.query.delete()

        # Add each crime report to the database
        for crime in crimes:
            # Safely get values with default fallbacks
            date_reported_str = crime.get('month', '2024-09')
            date_reported = datetime.strptime(date_reported_str, '%Y-%m')

            latitude = float(crime.get('location', {}).get('latitude', 0.0))
            longitude = float(crime.get('location', {}).get('longitude', 0.0))
            category = crime.get('category', 'Unknown Crime Type')
            outcome_status = crime.get('outcome_status', {})
            description = outcome_status.get('category', 'No description available') # noqa

            # Create a new CrimeReport object
            new_report = CrimeReport(
                title=category,
                description=description,
                location=None,
                date_reported=date_reported,
                latitude=latitude,
                longitude=longitude
            )
            db.session.add(new_report)

        db.session.commit()
        return True

    except Exception as e: # noqa
        return False
