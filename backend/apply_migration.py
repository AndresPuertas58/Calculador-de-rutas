from app import create_app
from models.database import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    alter_statements = [
        "ALTER TABLE conductores ADD COLUMN licencia VARCHAR(10) DEFAULT 'C3'",
        "ALTER TABLE conductores ADD COLUMN vacaciones_inicio DATE",
        "ALTER TABLE conductores ADD COLUMN vacaciones_fin DATE",
        "ALTER TABLE conductores ADD COLUMN incapacidad_inicio DATE",
        "ALTER TABLE conductores ADD COLUMN incapacidad_fin DATE"
    ]
    for statement in alter_statements:
        try:
            db.session.execute(text(statement))
            db.session.commit()
            print(f"Executed: {statement}")
        except Exception as e:
            db.session.rollback()
            print(f"Skipped/Error: {statement} - {e}")

    # Set some dummy data for existing conductors
    try:
        db.session.execute(text("UPDATE conductores SET licencia = 'C3' WHERE licencia IS NULL OR licencia = ''"))
        db.session.commit()
        print("Updated existing conductors with default C3 license.")
    except Exception as e:
        print(f"Error updating dummy data: {e}")
