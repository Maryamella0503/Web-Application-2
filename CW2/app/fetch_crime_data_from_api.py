import requests
from app import db
from app.models import CrimeReport
from datetime import datetime

def fetch_crime_data_from_api():
    """Function to fetch data from the crime data API and load it into the database."""
    try:
        # Example API URL - replace with the correct one
        api_url = "https://data.police.uk/api/crimes-street/all-crime?lat=53.8008&lng=-1.5491"
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
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
            description = outcome_status.get('category', 'No description available')

            # Create a new CrimeReport object
            new_report = CrimeReport(
                title=category,
                description=description,
                location=None,  # Update if you have a valid location
                date_reported=date_reported,
                latitude=latitude,
                longitude=longitude
            )
            db.session.add(new_report)

        # Commit the changes to the database
        db.session.commit()
        print("Data imported successfully from the API!")
        return True

    except Exception as e:
        print(f"Failed to fetch data from API: {e}")
        return False