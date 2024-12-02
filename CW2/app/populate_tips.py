from app import create_app, db
from app.models import CrimeType, SafetyTip

app = create_app()

def seed_database():
    """Seed CrimeType and SafetyTip tables."""
    with app.app_context():
        # Seed CrimeType
        sample_types = [
            "Theft", "Assault", "Burglary", "Vehicle Crime", "Shoplifting",
            "Antisocial behaviour", "Arson", "Public Order", "Drugs", "Possession of weapons"
        ]
        for crime_name in sample_types:
            if not CrimeType.query.filter_by(name=crime_name).first():
                db.session.add(CrimeType(name=crime_name))

        # Seed SafetyTip
        tips_data = {
            "Theft": [
                "Keep your belongings secure and avoid displaying valuables.",
                "Be cautious in crowded areas to avoid pickpockets.",
                "Avoid using your phone or other electronics in areas known for theft."
            ],
            "Assault": [
                "Avoid walking alone at night and stay in well-lit areas.",
                "Consider carrying a personal safety alarm.",
                "Plan your route in advance and let someone know where you’re going.",
                "Stay aware of your surroundings and avoid distractions like headphones or phones."
            ],
            "Burglary": [
                "Ensure your doors and windows are locked before leaving.",
                "Install security cameras and motion sensor lights.",
                "Keep valuables out of sight from windows, and avoid leaving spare keys outside.",
                "Use deadbolts and high-quality locks on all exterior doors."
            ],
            "Vehicle Crime": [
                "Always lock your car doors and roll up windows when leaving your vehicle, even for a short time.",
                "Park in well-lit and busy areas, ideally with surveillance cameras.",
                "Avoid leaving valuables visible in the car; store them in the trunk or take them with you.",
                "Use anti-theft devices like steering wheel locks, alarms, or immobilizers.",
                "Never leave your car running unattended, even for quick stops."
            ],
                "Shoplifting": [
                "Ensure proper surveillance in stores with visible CCTV cameras.",
                "Train employees to identify suspicious behavior and politely approach customers if necessary.",
                "Keep valuable items in locked cabinets or behind counters.",
                "Arrange merchandise neatly and check regularly to identify missing items quickly.",
                "Use anti-theft tags and alarms on high-value products."
            ],
                "Antisocial Behaviour": [
                "Avoid engaging with or provoking individuals displaying antisocial behavior.",
                "Stay in well-lit, populated areas if you suspect antisocial activities nearby.",
                "Report disturbances to local authorities immediately rather than trying to intervene.",
                "Encourage community vigilance by organizing neighborhood watch programs.",
                "Install motion-sensing lights and cameras around your property."
            ],
                "Arson": [
                "Ensure your home or business is equipped with functioning smoke detectors and fire alarms.",
                "Keep flammable materials, like paper and chemicals, away from heat sources.",
                "Install security cameras to deter potential arsonists.",
                "Keep outdoor garbage bins or dumpsters far from buildings to reduce fire risks.",
                "Regularly inspect fire extinguishers and sprinkler systems to ensure they are in working order."
            ],
            "Public Order": [
                "Avoid large gatherings or protests if they appear tense or disorganized.",
                "Stay calm and move away from escalating situations to prevent involvement.",
                "Avoid alcohol or substance abuse in public areas to prevent altercations.",
                "Cooperate with law enforcement if present, and follow their instructions.",
                "Keep an emergency number handy in case of a disturbance."
            ],
                "Drugs": [
                "Report suspicious drug activity to local law enforcement anonymously if necessary.",
                "Avoid areas known for drug-related incidents, especially during late hours.",
                "Avoid accepting drinks or substances from strangers to prevent potential drugging.",
                "Support local community initiatives to address and reduce drug-related crimes."
            ]
        }
        for crime_type_name, tips in tips_data.items():
            crime_type = CrimeType.query.filter_by(name=crime_type_name).first()
            if crime_type:
                for tip_content in tips:
                    if not SafetyTip.query.filter_by(content=tip_content, crime_type_id=crime_type.id).first():
                        db.session.add(SafetyTip(content=tip_content, crime_type_id=crime_type.id))
                        print(f"Added Tip: {tip_content} for Crime Type: {crime_type_name}")
        
        db.session.commit()

if __name__ == "__main__":
    seed_database()