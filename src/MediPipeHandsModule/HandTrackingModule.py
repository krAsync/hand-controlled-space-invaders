import cv2
import mediapipe as mp
import time
import numpy as np
import os

class hand_detector():
    def __init__(self, mode=False, max_hands=2, detection_con=0.5, track_con=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con

        # New Tasks API
        BaseOptions = mp.tasks.BaseOptions
        HandLandmarker = mp.tasks.vision.HandLandmarker
        HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        # Find model path relative to this file
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(module_dir))
        model_path = os.path.join(project_root, 'models', 'hand_landmarker.task')

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.VIDEO,
            num_hands=self.max_hands,
            min_hand_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con
        )
        self.landmarker = HandLandmarker.create_from_options(options)
        self.results = None
        self.frame_timestamp_ms = 0

        # Hand connections for drawing (same as old mp.solutions.hands.HAND_CONNECTIONS)
        self.HAND_CONNECTIONS = frozenset([
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (0, 9), (9, 10), (10, 11), (11, 12),
            (0, 13), (13, 14), (14, 15), (15, 16),
            (0, 17), (17, 18), (18, 19), (19, 20),
            (5, 9), (9, 13), (13, 17)
        ])

    def find_hands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRGB)

        self.frame_timestamp_ms += 33  # ~30fps increment
        self.results = self.landmarker.detect_for_video(mp_image, self.frame_timestamp_ms)

        if self.results.hand_landmarks:
            h, w, c = img.shape
            for hand_landmarks in self.results.hand_landmarks:
                if draw:
                    self._draw_landmarks(img, hand_landmarks, w, h)
        return img

    def _draw_landmarks(self, img, landmarks, width, height):
        # Draw connections
        for connection in self.HAND_CONNECTIONS:
            start_idx, end_idx = connection
            start = landmarks[start_idx]
            end = landmarks[end_idx]
            start_point = (int(start.x * width), int(start.y * height))
            end_point = (int(end.x * width), int(end.y * height))
            cv2.line(img, start_point, end_point, (0, 255, 0), 2)

        # Draw landmarks
        for landmark in landmarks:
            cx, cy = int(landmark.x * width), int(landmark.y * height)
            cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

    def find_position(self, img, hand_no=0, draw=True):
        """
        Finds the landmarks of a specific hand and returns them in a list.

        Args:
            img: The image to find the landmarks in.
            hand_no: The index of the hand to find the landmarks for.
            draw: Whether to draw the landmarks on the image.

        Returns:
            A list of landmarks for the specified hand.
        """
        lm_list = []
        if self.results and self.results.hand_landmarks:
            if hand_no < len(self.results.hand_landmarks):
                my_hand = self.results.hand_landmarks[hand_no]
                h, w, c = img.shape
                for id, lm in enumerate(my_hand):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, cx, cy])

                if draw:
                    self._draw_landmarks(img, my_hand, w, h)
        return lm_list

    def get_handedness(self):
        handedness_list = []
        if self.results and self.results.hand_landmarks and self.results.handedness:
            for hand_handedness in self.results.handedness:
                # New API returns list of Category objects
                handedness_list.append(hand_handedness[0].category_name)
        return handedness_list

    def get_bbox_location(self, img, hand_no=0, draw=True):

        lm_list = []
        x_list = []
        y_list = []

        bbox = None
        mid = None

        if self.results and self.results.hand_landmarks:
            if hand_no < len(self.results.hand_landmarks):
                my_hand = self.results.hand_landmarks[hand_no]
                h, w, c = img.shape

                for id, lm in enumerate(my_hand):
                    cx, cy = int(lm.x * w), int(lm.y * h)

                    x_list.append(cx)
                    y_list.append(cy)
                    lm_list.append([id, cx, cy])

                #calculate bbox
                x_min, x_max = min(x_list), max(x_list)
                y_min, y_max = min(y_list), max(y_list)

                #add padding
                width = x_max - x_min
                height = y_max - y_min
                buffer_x = int(width * 0.1)  # 10% padding
                buffer_y = int(height * 0.1) # 10% padding
                x_min = max(0, x_min - buffer_x)
                y_min = max(0, y_min - buffer_y)
                x_max = x_max + buffer_x
                y_max = y_max + buffer_y

                x_min_coord = min(x_list)
                x_max_coord = max(x_list)
                y_min_coord = min(y_list)
                y_max_coord = max(y_list)

                lm_min_x = next(lm for lm in lm_list if lm[1] == x_min_coord)
                lm_max_x = next(lm for lm in lm_list if lm[1] == x_max_coord)

                lm_min_y = next(lm for lm in lm_list if lm[2] == y_min_coord)
                lm_max_y = next(lm for lm in lm_list if lm[2] == y_max_coord)

                idd, minxx, minxy = lm_min_x
                idd, minyx, minyy = lm_min_y
                idd, maxxx, maxxy = lm_max_x
                idd, maxyx, maxyy = lm_max_y


                mid = [(x_max - x_min)/2,(y_max - y_min)/2]

                bbox = (x_min, y_min, x_max - x_min, y_max - y_min)
                if draw:
                    cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
                    cv2.line(img, (minxx, minxy), (maxxx, maxxy), (255,0,255), 2)
                    cv2.line(img, (minyx, minyy), (maxyx, maxyy), (255,0,255), 2)

                return lm_list, bbox, mid
        return lm_list, bbox, mid


def main():
    cap = cv2.VideoCapture(0)
    pTime = 0
    cTime = 0
    detector = hand_detector()
    while True:
        success, img = cap.read()
        img = detector.find_hands(img)
        handedness = detector.get_handedness()

        if handedness:
            for i, hand in enumerate(handedness):
                lm_list = detector.find_position(img, hand_no=i)
                if len(lm_list) != 0:
                    print(f'{hand} Hand Landmarks:')
                    print(lm_list[4])

        cv2.imshow("Image", img)
        cv2.waitKey(1)

if __name__ == "__main__":
    main()
