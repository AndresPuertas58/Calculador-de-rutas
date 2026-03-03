from flask import Flask
from flask_cors import CORS
from api.routes import api_blueprint
from models.database import db
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # DB Configuration
    db_uri = os.getenv('DATABASE_URL')
    print(f"DEBUG: Usando DB_URI: {db_uri}")
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # Test connection
    with app.app_context():
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            print("--------------------------------------------------")
            print("✅ CONEXIÓN A BASE DE DATOS EXITOSA")
            print("--------------------------------------------------")
        except Exception as e:
            print("--------------------------------------------------")
            print(f"❌ ERROR DE CONEXIÓN A DB: {e}")
            print("--------------------------------------------------")
    
    # Configure static folder to point to frontend
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app.static_folder = os.path.join(base_dir, '..', 'frontend')
    app.static_url_path = ''
    
    # Register Blueprints
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    @app.route('/')
    def index():
        from flask import send_from_directory
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        from flask import send_from_directory
        return send_from_directory(app.static_folder, path)

    @app.route('/health')
    def health():
        return {"status": "ok"}, 200
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
