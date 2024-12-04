from app import create_app, db
from app.models import CrimeType, SafetyTip

app = create_app()


def seed_database():
    """Seed CrimeType and SafetyTip tables."""
    with app.app_context():
        # Seed CrimeType
        sample_types = [
            "Theft", "Assault", "Burglary", "Vehicle Crime", "Shoplifting",
            "Antisocial behaviour", "Arson", "Public Order", "Drugs",
            "Possession of weapons"
        ]
        for crime_name in sample_types:
            if not CrimeType.query.filter_by(name=crime_name).first():
                db.session.add(CrimeType(name=crime_name))

        # Seed the SafetyTip table with tips for each crime category
        tips_data = {
            "Theft": [
                "Keep your belongings secure and avoid displaying valuables.",
                "Be cautious in crowded areas to avoid pickpockets.",
                "Avoid using your phone or other electronics in areas known for theft." # noqa
            ],
            "Assault": [
                "Avoid walking alone at night and stay in well-lit areas.",
                "Consider carrying a personal safety alarm.",
                "Plan your route in advance and let someone know where you’re going.", # noqa
                "Stay aware of your surroundings and avoid distractions like headphones or phones." # noqa
            ],
            "Burglary": [
                "Ensure your doors and windows are locked before leaving.",
                "Install security cameras and motion sensor lights.",
                "Keep valuables out of sight from windows, and avoid leaving spare keys outside.", # noqa
                "Use deadbolts and high-quality locks on all exterior doors."
            ],
            "Vehicle Crime": [
                "Always lock your car doors and roll up windows when leaving your vehicle, even for a short time.", # noqa
                "Park in well-lit and busy areas, ideally with surveillance cameras.", # noqa
                "Avoid leaving valuables visible in the car; store them in the trunk or take them with you.", # noqa
                "Use anti-theft devices like steering wheel locks, alarms, or immobilizers.", # noqa
                "Never leave your car running unattended, even for quick stops." # noqa
            ],
            "Shoplifting": [
                "Ensure proper surveillance in stores with visible CCTV cameras.", # noqa
                "Train employees to identify suspicious behavior and politely approach customers if necessary.", # noqa
                "Keep valuable items in locked cabinets or behind counters.",
                "Arrange merchandise neatly and check regularly to identify missing items quickly.", # noqa
                "Use anti-theft tags and alarms on high-value products."
            ],
            "Antisocial Behaviour": [
                "Avoid engaging with or provoking individuals displaying antisocial behavior.", # noqa
                "Stay in well-lit, populated areas if you suspect antisocial activities nearby.", # noqa
                "Report disturbances to local authorities immediately rather than trying to intervene.", # noqa
                "Encourage community vigilance by organizing neighborhood watch programs.", # noqa
                "Install motion-sensing lights and cameras around your property." # noqa
            ],
            "Arson": [
                "Ensure your home or business is equipped with functioning smoke detectors and fire alarms.", # noqa
                "Keep flammable materials, like paper and chemicals, away from heat sources.", # noqa
                "Install security cameras to deter potential arsonists.",
                "Keep outdoor garbage bins or dumpsters far from buildings to reduce fire risks.", # noqa
                "Regularly inspect fire extinguishers and sprinkler systems to ensure they are in working order." # noqa
            ],
            "Public Order": [
                "Avoid large gatherings or protests if they appear tense or disorganized.", # noqa
                "Stay calm and move away from escalating situations to prevent involvement.", # noqa
                "Avoid alcohol or substance abuse in public areas to prevent altercations.", # noqa
                "Cooperate with law enforcement if present, and follow their instructions.", # noqa
                "Keep an emergency number handy in case of a disturbance."
            ],
            "Drugs": [
                "Report suspicious drug activity to local law enforcement anonymously if necessary.", # noqa
                "Avoid areas known for drug-related incidents, especially during late hours.", # noqa
                "Avoid accepting drinks or substances from strangers to prevent potential drugging.", # noqa
                "Support local community initiatives to address and reduce drug-related crimes." # noqa
            ]
        }
        for crime_type_name, tips in tips_data.items():
            crime_type = CrimeType.query.filter_by(name=crime_type_name).first() # noqa
            if crime_type:
                for tip_content in tips:
                    if not SafetyTip.query.filter_by(content=tip_content, crime_type_id=crime_type.id).first(): # noqa
                        db.session.add(SafetyTip(content=tip_content, crime_type_id=crime_type.id)) # noqa
                        print(f"Added Tip: {tip_content} for Crime Type: {crime_type_name}") # noqa
        db.session.commit()


# Run the seeding script if executed directly
if __name__ == "__main__":
    seed_database()
