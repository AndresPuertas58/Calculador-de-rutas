from flask import Flask
from flask_cors import CORS
from api.routes import api_blueprint
from models.database import db
import os
from dotenv import load_dotenv

# override=False: las variables del docker-compose.yml siempre ganan sobre el .env local
load_dotenv(override=False)

def create_app():
    app = Flask(__name__)
    CORS(app)

    # DB Configuration
    db_uri = os.getenv('DATABASE_URL')
    print(f"DEBUG: Usando DB_URI: {db_uri}")
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(api_blueprint, url_prefix='/api')

    @app.route('/health')
    def health():
        return {"status": "ok"}, 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=8000)
