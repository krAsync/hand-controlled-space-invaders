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
    if hand == 'left':
        with open (data_path+'/numbers/left.csv', 'a') as f:
            wr = csv.writer(f)
            wr.writerow([number] + [item for sublist in data for item in sublist])
    if hand == 'right':
        with open (data_path+'/numbers/right.csv', 'a') as f:
            wr = csv.writer(f)
            wr.writerow([number] + [item for sublist in data for item in sublist])

def main():
    cap = cv2.VideoCapture(0)
    detector = hand_detector()
    pTime = 0
    dump_right = []
    dump_left = []
    # main loop
    while True:
        success, img = cap.read()

        if success:
            img = detector.find_hands(img)
            handedness = detector.get_handedness()

            if handedness:
                dump_left = []
                dump_right = []
                for i, hand in enumerate(handedness):
                    lm_list, bbox = detector.get_bbox_location(img, hand_no=i)
                    if len(lm_list) != 0 and bbox:
                        normalized_landmarks = normalize_landmarks(lm_list, bbox, hand)
                        if normalized_landmarks:
                            for landmark_n in normalized_landmarks:
                                if hand:
                                    if hand.lower() == 'left':
                                        dump_left.append(landmark_n)
                                    else:
                                        dump_right.append(landmark_n)

            img = cv2.flip(img, 1)
            cv2.imshow('hand capture', img)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            
            if ord('0') <= key <= ord('9'):
                num = int(chr(key))
                if num == 0:
                    num = 10
                if len(dump_left) != 0:
                    write_data(dump_left, 'left', num)
                    print(f"Saved left hand data for number {num}")
                elif len(dump_right) != 0:
                    write_data(dump_right, 'right', num)
                    print(f"Saved right hand data for number {num}")
                else:
                    print('no landmarks to save')

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
