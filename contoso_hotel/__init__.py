from flask import Flask  # Import the Flask class
app = Flask(__name__)    # Create an instance of the class for our use
app.config['MAX_CONTENT_LENGTH'] = 64 * 1000 * 1000




