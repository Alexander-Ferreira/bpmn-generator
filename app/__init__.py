from flask import Flask, render_template
from dotenv import load_dotenv
import os
from flask_cors import CORS
from app.routes import bp

load_dotenv()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    CORS(app)
    app.config['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY')

    # Registrar blueprints

    app.register_blueprint(bp, url_prefix='/api')

    # Ruta principal para el front
    @app.route('/')
    def index():
        return render_template('index.html')

    return app
