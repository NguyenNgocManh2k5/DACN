import cv2
import sys 
import time

from cvzone.HandTrackingModule import HandDetector
from app.utils.detector_gesture.draw_skeleton import draw_hand_skeleton
from app.utils.detector_gesture.mouse_controller import control_mouse
from app.utils.detector_gesture.sound_controller import check_control_sound

CAP_W = 640
CAP_H = 480
FRAME_R = 120
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open webcam!")
else:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAP_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAP_H)

    hand_detector = HandDetector(detectionCon=0.9, maxHands=2)

    start_time = time.time()
    camera_running = True
    window_name = 'Detection'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    camera_running = True

start_time=time.time()

print("Webcam opened — press q to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Lật ảnh theo chiều ngang
    frame = cv2.flip(frame, 1) 

    # Tính FPS
    end_time=time.time()
    fps = int(1/(end_time - start_time))
    cv2.putText(frame, 
                f"FPS: {fps}",
                (10, 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                (50, 50, 50), 
                2)
    start_time=end_time
    #

    # Nhận diện bàn tay
    hands, frame = hand_detector.findHands(frame, draw=False)

    if hands:
        for hand in hands:
            draw_hand_skeleton(frame, hand["lmList"])
        control_mouse(frame, hands[0], cam_w=CAP_W, cam_h=CAP_H, frame_r=FRAME_R)

    if len(hands) >= 2:
        check_control_sound(frame, hands)

    # Hiển thị
    cv2.imshow(window_name, frame)
    # Nhấn phím 'q' HOẶC Nhấn vào nút [X] ở góc cửa sổ
    key = cv2.waitKey(1) & 0xFF
    button = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
    if key == ord('q') or button < 1:
        print("Quit requested — stopping.")
        break

cap.release()
cv2.destroyAllWindows()