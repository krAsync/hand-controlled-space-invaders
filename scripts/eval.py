import cv2
import time 
import os
import sys
import csv
import joblib
import numpy as np
import pandas as pd

#get path to src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
src_path = os.path.join(project_root, 'src')
data_path = os.path.join(project_root, 'data')


if src_path not in sys.path:
    sys.path.append(src_path)

model = joblib.load('../models/gesture_model.pkl')

try:
    from MediPipeHandsModule.HandTrackingModule import hand_detector
except ImportError as e:
    print(f'error importing HandTrackingModule: {e}')

def normalize_landmarks(lm_list, bbox, handedness):
    normalized_landmarks = []
    if len(lm_list) != 0 and bbox:
        wrist = lm_list[0]  # Wrist is the first landmark
        bbox_width = bbox[2]
        bbox_height = bbox[3]
        for joint in lm_list:
            try:
                # Get relative position to the wrist and scale by bbox dimensions
                normalized_x = (joint[1] - wrist[1]) / bbox_width
                normalized_y = (joint[2] - wrist[2]) / bbox_height
                normalized_landmarks.append((normalized_x, normalized_y))
            except (TypeError, IndexError, ZeroDivisionError) as e:
                print(f"Error processing joint: {joint}, error: {e}")
    return normalized_landmarks
    

def predict_gesture(features, model):
    X_new = np.array(features).reshape(1, -1)
    label = model.predict(X_new)[0]
    return label

def main():
    cap = cv2.VideoCapture(0)
    detector = hand_detector()
    pTime = 0
    # main loop
    while True:
        success, img = cap.read()

        if success:
            img = cv2.flip(img, 1)
            img = detector.find_hands(img)
            handedness = detector.get_handedness()

            if handedness:
                for i, hand in enumerate(handedness):
                    lm_list, bbox, mid = detector.get_bbox_location(img, hand_no=i)
                    if len(lm_list) != 0 and bbox:
                        normalized_landmarks = normalize_landmarks(lm_list, bbox, hand)
                        if normalized_landmarks:
                            landmark_features = [item for sublist in normalized_landmarks for item in sublist]
                            
                            # Encode handedness: left=0, right=1
                            hand_encoded = 0 if hand.lower() == 'left' else 1
                            
                            features = [hand_encoded] + landmark_features

                            if len(features) == 43: # 1 for hand + 42 for landmarks
                                label = predict_gesture(features, model)
                                print(f"Predicted {hand} Label: {label}")
                                img = cv2.putText(img, str(label), (bbox[0] + bbox[2] + 10, bbox[1] + 20),cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,255), 2, cv2.LINE_AA)

            cv2.imshow('hand capture', img)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
