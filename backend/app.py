from flask import Flask
from flask_cors import CORS
from api.routes import api_blueprint
from models.database import db
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv(override=False)

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Construir DATABASE_URL desde variables individuales
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_NAME', 'demo_coltanques_db')
    
    safe_password = quote_plus(password) if password else ''
    
    db_uri = f"mysql+mysqlconnector://{user}:{safe_password}@{host}:{port}/{db_name}"
    
    print(f"DEBUG: Usando DB_URI: {db_uri}")
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(api_blueprint, url_prefix='/api')

    @app.route('/')
    def health():
        return {"status": "ok"}, 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=3000)