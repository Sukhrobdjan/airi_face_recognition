import face_recognition
import cv2
import numpy as np
import json
from PIL import Image
import io
import base64

class FaceRecognitionSystem:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
    
    def encode_face_from_file(self, image_path):
        """Encode face from image file"""
        try:
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            
            if face_encodings:
                return face_encodings[0]
            return None
        except Exception as e:
            print(f"Error encoding face: {e}")
            return None
    
    def encode_face_from_base64(self, base64_string):
        """Encode face from base64 string"""
        try:
            # Remove data URL prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decode base64 to image
            image_data = base64.b64decode(base64_string)
            image = Image.open(io.BytesIO(image_data))
            image = np.array(image)
            
            # Convert RGB to BGR for face_recognition
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            face_encodings = face_recognition.face_encodings(image)
            
            if face_encodings:
                return face_encodings[0]
            return None
        except Exception as e:
            print(f"Error encoding face from base64: {e}")
            return None
    
    def load_known_faces(self, employees):
        """Load known faces from database"""
        self.known_face_encodings = []
        self.known_face_names = []
        
        for employee in employees:
            if employee.face_encoding:
                try:
                    encoding = np.array(json.loads(employee.face_encoding))
                    self.known_face_encodings.append(encoding)
                    self.known_face_names.append(f"{employee.first_name} {employee.last_name}")
                except Exception as e:
                    print(f"Error loading face encoding for {employee.first_name}: {e}")
    
    def recognize_face(self, base64_string, tolerance=0.6):
        """Recognize face from base64 string"""
        try:
            face_encoding = self.encode_face_from_base64(base64_string)
            
            if face_encoding is None:
                return None, 0.0
            
            if not self.known_face_encodings:
                return None, 0.0
            
            # Compare faces
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            
            if face_distances[best_match_index] <= tolerance:
                confidence = 1 - face_distances[best_match_index]
                return self.known_face_names[best_match_index], confidence
            
            return None, 0.0
        except Exception as e:
            print(f"Error recognizing face: {e}")
            return None, 0.0
    
    def save_face_encoding(self, face_encoding):
        """Save face encoding as JSON string"""
        try:
            return json.dumps(face_encoding.tolist())
        except Exception as e:
            print(f"Error saving face encoding: {e}")
            return None