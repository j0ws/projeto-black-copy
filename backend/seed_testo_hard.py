from app.database import SessionLocal, engine
from app.models import Base
from app.models.product import Product, Benefit, PainPoint, Objection

def seed_db():
    print("Setting up database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    print("Checking if 'Testo Hard' already exists...")
    existing_product = db.query(Product).filter(Product.name == "Testo Hard").first()
    if existing_product:
        print("Testo Hard already seeded. Cleaning up old data to re-seed...")
        db.delete(existing_product)
        db.commit()

    print("Seeding 'Testo Hard' data...")

    # 1. Product Specifications & Features
    testo_hard = Product(
        name="Testo Hard",
        ingredients=[
            "L-Arginine", "Taurine", "Pinus pinaster extract", "Vitamin B3",
            "Vitamin B6", "Vitamin B9", "Vitamin B12", "Vitamin D3",
            "Vitamin E", "Zinc bisglycinate", "Magnesium bisglycinate", "Boron", "Selenium"
        ],
        use_cases=[
            "Gym/Workouts", "Sexual Performance"
        ],
        worst_alternatives=[
            "Tadalafil (Tadala)", "Steroids (\"Bomba\")", "Injectable Testosterone"
        ]
    )

    db.add(testo_hard)
    db.commit()
    db.refresh(testo_hard)

    # Core Benefits
    benefits = [
        "Circulation aid",
        "Proper muscle function",
        "Fatigue reduction",
        "Energy metabolism",
        "Hormonal balance"
    ]
    for b in benefits:
        db.add(Benefit(product_id=testo_hard.id, description=b))

    # 2. Psychological Mapping (Pain Points & LF8 Triggers)
    pain_points = [
        {"desc": "Late on phone at night", "lf8": "Survival and Life Extension (LF1)"},
        {"desc": "Can't sleep", "lf8": "Survival and Life Extension (LF1)"},
        {"desc": "Gaining weight / Getting fat", "lf8": "Sexual Companionship (LF4)"},
        {"desc": "Sexual performance problems", "lf8": "Sexual Companionship (LF4)"},
        {"desc": "Short fuse / Irritability", "lf8": "Sexual Companionship (LF4)"},
        {"desc": "Low testosterone", "lf8": "Sexual Companionship (LF4)"},
        {"desc": "Lack of appetite", "lf8": "Survival and Life Extension (LF1)"},
        {"desc": "Desire to be lean/thin", "lf8": "Sexual Companionship (LF4)"}
    ]
    for pp in pain_points:
        db.add(PainPoint(product_id=testo_hard.id, description=pp["desc"], lf8_trigger=pp["lf8"]))

    # 3. Objections & FAQs (Marketing Angles)
    objections = [
        {
            "type": "Objection",
            "question": "Is it approved by Anvisa (Health Agency)?",
            "answer": "Emphasize that it is tested in a national laboratory."
        },
        {
            "type": "FAQ",
            "question": "How do I know my testo is low?",
            "answer": "Show the common symptoms (fatigue, weight gain)."
        },
        {
            "type": "FAQ",
            "question": "Where is the proof that these ingredients work?",
            "answer": "Show scientific studies."
        },
        {
            "type": "FAQ",
            "question": "Will I become dependent on it to keep testosterone high?",
            "answer": "Explain that the supplement stimulates natural production, it doesn't replace it."
        }
    ]
    for obj in objections:
        db.add(Objection(
            product_id=testo_hard.id,
            type=obj["type"],
            question=obj["question"],
            answer=obj["answer"]
        ))

    db.commit()
    print("✅ Seed script executed successfully! 'Testo Hard' and its intelligence briefing are stored in SQLite.")

if __name__ == "__main__":
    seed_db()
