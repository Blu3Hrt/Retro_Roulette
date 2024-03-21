# twitch/twitch_flask.py
from PySide6.QtCore import QThread, Signal
from werkzeug.serving import make_server
from flask import Flask, request, jsonify
import logging
import threading

app = Flask(__name__)

class FlaskThread(QThread):
    code_received = Signal(str)
    auth_failed = Signal(str)

    def __init__(self):
        super().__init__()
        self.server = None
        logging.basicConfig(filename='Main.log', encoding='utf-8', level=logging.DEBUG)

    def run(self):
        flask_thread_id = threading.get_ident()
        logging.info(f"FlaskThread is running in thread ID: {flask_thread_id}")        
        global app  # Use the global Flask app instance
        logging.debug("Starting Flask server on localhost:5000")
        self.server = make_server('localhost', 5000, app)
        self.server.serve_forever()

    def stop_server(self):
        if self.server is not None:
            logging.debug("Shutting down Flask server")
            self.server.shutdown()

# Instantiate the FlaskThread
flask_thread = FlaskThread()

@app.route('/oauth/twitch')
def oauth_twitch():
    code = request.args.get('code')
    error = request.args.get('error')
    if code:
        try:
            logging.debug("Emitting code_received signal with code: %s", code)
            flask_thread.code_received.emit(code)
            # Log after emitting the signal
            logging.debug("Signal emitted")
            return "Authentication successful! You can close this window."
        except Exception as e:
            logging.exception("Error handling OAuth code")
            flask_thread.auth_failed.emit(str(e))
            return jsonify({"error": "Internal server error"}), 500
    elif error:
        logging.warning("OAuth error received: %s", error)
        flask_thread.auth_failed.emit(error)
        return jsonify({"error": error}), 400
    else:
        logging.info("No code or error provided by Twitch")
        return "No code or error provided by Twitch."

