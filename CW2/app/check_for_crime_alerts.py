from geopy.distance import geodesic
from flask import current_app

def check_for_crime_alerts():
    from app.models import User, CrimeReport  # Delay imports
    from app import db  # Delay import
    from app.email import send_crime_alert_email  # Delay import

    with current_app.app_context():
        users = User.query.all()
        crimes = CrimeReport.query.all()

        for user in users:
            user_coords = tuple(map(float, user.bookmarked_locations.split(',')))
            for crime in crimes:
                crime_coords = (crime.latitude, crime.longitude)
                distance = geodesic(user_coords, crime_coords).km
                if distance <= user.notification_radius:
                    send_crime_alert_email(
                        user.email,
                        f"{crime.title} reported at {crime.location} on {crime.date_reported.strftime('%Y-%m-%d')}"
                    )