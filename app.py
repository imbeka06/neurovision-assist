import time
from flask import Flask, render_template
from flask_socketio import SocketIO
import vision_engine

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

last_frame_time = 0
last_alert_time = 0
last_alert_message = "Path clear."

@app.route('/camera')
def camera():
    return render_template('camera.html')

@app.route('/user')
def user():
    return render_template('user.html')

@socketio.on('video_frame')
def handle_frame(data):
    global last_frame_time, last_alert_time, last_alert_message
    current_time = time.time()
    
    # Process 1 frame every 0.4 seconds (Fast but prevents lag)
    if current_time - last_frame_time < 0.4:
        return 
    last_frame_time = current_time
        
    ai_response = vision_engine.process_frame_secure(data)
    
    # --- SMART SILENCE & CLEAR PATH CONFIRMATION ---
    if ai_response == "Path clear.":
        # If the last thing we saw was a barrier, and now it's clear, tell the user!
        if "barrier" in last_alert_message:
            if current_time - last_alert_time > 4.5:
                socketio.emit('navigation_alert', {'message': "Alternative path is clear. Proceed."})
                last_alert_message = "Path clear."
                last_alert_time = current_time
        return # Otherwise, stay in total silence.

    # --- STRICT ANTI-STUTTER COOLDOWN ---
    # We force the system to wait 4.5 seconds before speaking again so the sentence finishes.
    if current_time - last_alert_time > 4.5:
        # Only speak if it's a new threat OR enough time has passed
        if ai_response != last_alert_message or (current_time - last_alert_time > 6.0):
            socketio.emit('navigation_alert', {'message': ai_response})
            last_alert_message = ai_response
            last_alert_time = current_time

if __name__ == '__main__':
    print("==========================================")
    print("🏆 FINAL PRODUCTION SERVER RUNNING.")
    print("==========================================")
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)