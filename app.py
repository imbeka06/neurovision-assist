import logging
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from vision_engine import process_frame_secure

# Clean up the console output so it doesn't spam you with web logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'neurovision_hackathon_secret'

# Enable CORS so the phones aren't blocked from connecting
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/camera')
def camera_ui():
    """Serves the frontend for Phone 1 (The Eyes)"""
    return render_template('camera.html')

@app.route('/user')
def user_ui():
    """Serves the frontend for Phone 2 (The Audio Interface)"""
    return render_template('user.html')

@socketio.on('video_frame')
def handle_frame(base64_image):
    """Receives frames from Phone 1, runs AI, sends alerts to Phone 2"""
    # 1. Pass the incoming image directly to your Phase 1 AI engine
    command = process_frame_secure(base64_image)
    
    # 2. If the AI detects an obstacle, broadcast the warning to Phone 2
    if command != "Path clear.":
        emit('navigation_alert', {'message': command}, broadcast=True)

if __name__ == '__main__':
    print("==================================================")
    print("🧠 NeuroVision Offline Edge Server is RUNNING.")
    print("🔗 Connect Phone 1 (Camera) to: http://<YOUR_IPV4_ADDRESS>:5000/camera")
    print("🔗 Connect Phone 2 (Audio) to:  http://<YOUR_IPV4_ADDRESS>:5000/user")
    print("==================================================")
    
    # host='0.0.0.0' is critical: it allows external devices on the Wi-Fi to connect
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)