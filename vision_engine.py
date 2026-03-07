import cv2
import numpy as np
import base64
from ultralytics import YOLO

model = YOLO("yolov8n.pt") 

# Memory tracker for predictive approaching (people, bikes, cars)
tracking_memory = {"name": "", "zone": "", "area": 0, "frames_expanding": 0}

def process_frame_secure(base64_string):
    global tracking_memory
    try:
        encoded_data = base64_string.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        results = model(frame, verbose=False)
        
        frame_height, frame_width = frame.shape[:2]
        frame_area = frame_height * frame_width
        
        detected_objects = []

        for r in results:
            for box in r.boxes:
                # Must be 55% confident to prevent hallucinations
                conf = float(box.conf[0].item())
                if conf < 0.55: 
                    continue
                    
                class_id = int(box.cls[0].item())
                name = model.names[class_id]
                
                # Ignore small floor clutter completely
                if name in ['bottle', 'cell phone', 'cup', 'book', 'mouse', 'remote']: 
                    continue
                    
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                center_x = (x1 + x2) / 2
                box_area = (x2 - x1) * (y2 - y1)
                
                screen_coverage = box_area / frame_area
                floor_proximity = y2 / frame_height
                
                if center_x < frame_width / 3: 
                    zone = "left"
                elif center_x > (frame_width / 3) * 2: 
                    zone = "right"
                else: 
                    zone = "front" # Changed to 'front' for better audio phrasing
                    
                detected_objects.append({
                    "name": name, "zone": zone, 
                    "proximity": floor_proximity, "coverage": screen_coverage, "area": box_area
                })
        
        # SMART SILENCE: Nothing found
        if not detected_objects: 
            tracking_memory = {"name": "", "zone": "", "area": 0, "frames_expanding": 0}
            return "Path clear."
            
        # Find the most dangerous object (closest to feet)
        detected_objects.sort(key=lambda x: x['proximity'], reverse=True)
        primary = detected_objects[0]
        
        name = primary['name'].replace('_', ' ')
        prox = primary['proximity']
        coverage = primary['coverage']
        zone = primary['zone']
        current_area = primary['area']
        
        # 1. WALL/BARRIER DETECTION (Massive Area)
        if coverage > 0.45 and zone == "front":
            return "Wall or barrier ahead. Look for an alternative clear path."
            
        # 2. DISTANCE METRIC / SMART SILENCE
        # If the object is not in the bottom 35% of the screen, it is safely far away. Stay quiet.
        if prox < 0.65: 
            return "Path clear."
            
        # 3. PREDICTIVE APPROACHING (Moving towards user)
        dynamic_objects = ['person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck']
        is_approaching = False
        
        if name in dynamic_objects:
            # If it's the same object as last frame and it got 10% bigger
            if tracking_memory["name"] == name and tracking_memory["zone"] == zone:
                if current_area > (tracking_memory["area"] * 1.10):
                    tracking_memory["frames_expanding"] += 1
                else:
                    tracking_memory["frames_expanding"] = 0
            else:
                tracking_memory["frames_expanding"] = 0
                
            tracking_memory["name"] = name
            tracking_memory["zone"] = zone
            tracking_memory["area"] = current_area
            
            # If it grew for 2 consecutive frames, it is coming right at you
            if tracking_memory["frames_expanding"] >= 2:
                is_approaching = True
        else:
            tracking_memory = {"name": "", "zone": "", "area": 0, "frames_expanding": 0}

        # 4. ACTIONABLE, NON-PASSIVE DESCRIPTIONS
        if is_approaching:
            if zone == "front": return f"{name} approaching from front. Step right to avoid."
            elif zone == "left": return f"{name} approaching from left. Keep right."
            else: return f"{name} approaching from right. Keep left."
            
        # Standard stationary obstacles near feet
        if zone == "front":
            return f"{name} directly ahead. Step right."
        elif zone == "left":
            return f"{name} on left. Step right."
        else: # right
            return f"{name} on right. Step left."

    except Exception as e:
        print(f"Vision Engine Error: {e}")
        return "Path clear."