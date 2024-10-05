from flask import Flask  # Import the Flask class
from flask_cors import CORS  # Import the CORS class

app = Flask(__name__)  # Create an instance of the class for our use
CORS(app, origins="*")  # Enable CORS for all origins

app.config['MAX_CONTENT_LENGTH'] = 64 * 1000 * 1000
