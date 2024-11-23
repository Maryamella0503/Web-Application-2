from flask import Blueprint, jsonify
from app.models import CrimeReport

# Initialize the Blueprint
api = Blueprint('api', __name__)

@api.route('/api/crime-data', methods=['GET'])
def get_crime_data():
    # Fetch all crime reports from the database
    crime_reports = CrimeReport.query.all()
    data = [
        {
            'id': report.id,
            'title': report.title,
            'description': report.description,
            'location': report.location,
            'date_reported': report.date_reported.strftime('%Y-%m'),
            'latitude': report.latitude,
            'longitude': report.longitude
        }
        for report in crime_reports
    ]
    return jsonify(data)