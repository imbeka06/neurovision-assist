import base64
from vision_engine import process_frame_secure

# 1. Provide the name of a test image on your laptop
# (Download a picture of a person or a chair and save it in this folder as 'test.jpg')
IMAGE_PATH = "test.jpg" 

try:
    # 2. Read the image and convert it to Base64 (simulating the phone's web browser)
    with open(IMAGE_PATH, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Simulate the exact string format the HTML canvas will send
    simulated_payload = f"data:image/jpeg;base64,{encoded_string}"

    print("Running secure AI inference...")
    
    # 3. Feed it to your Phase 1 engine
    command = process_frame_secure(simulated_payload)
    
    print("====================================")
    print(f"AI OUTPUT: {command}")
    print("====================================")

except FileNotFoundError:
    print(f"Error: Could not find '{IMAGE_PATH}'. Please put a test photo in the folder!")