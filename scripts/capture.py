import cv2
import time 
import os
import sys
import csv

#get path to src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
src_path = os.path.join(project_root, 'src')
data_path = os.path.join(project_root, 'data')


if src_path not in sys.path:
    sys.path.append(src_path)

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
    
def write_data(data, hand, number):
    with open (data_path+'/numbers/gestures.csv', 'a') as f:
        wr = csv.writer(f)
        wr.writerow([number, hand.lower()] + [item for sublist in data for item in sublist])

def main():
    cap = cv2.VideoCapture(0)
    detector = hand_detector()
    pTime = 0
    landmarks_to_save = []
    hand_to_save = None

    # main loop
    while True:
        success, img = cap.read()

        if success:
            img = cv2.flip(img, 1)
            img = detector.find_hands(img)
            handedness = detector.get_handedness()

            landmarks_to_save = []
            hand_to_save = None

            if handedness:
                # Only process the first detected hand
                hand = handedness[0]
                lm_list, bbox, mid = detector.get_bbox_location(img, hand_no=0)
                if len(lm_list) != 0 and bbox:
                    img = cv2.putText(img, hand, (bbox[0] + bbox[2] + 10, bbox[1] + 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                    normalized_landmarks = normalize_landmarks(lm_list, bbox, hand)
                    if normalized_landmarks:
                        landmarks_to_save = normalized_landmarks
                        hand_to_save = hand

            cv2.imshow('hand capture', img)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            
            if ord('0') <= key <= ord('9'):
                num = int(chr(key))
                if num == 0:
                    num = 10
                if landmarks_to_save and hand_to_save:
                    write_data(landmarks_to_save, hand_to_save, num)
                    print(f"Saved {hand_to_save} hand data for number {num}")
                else:
                    print('no landmarks to save')

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()