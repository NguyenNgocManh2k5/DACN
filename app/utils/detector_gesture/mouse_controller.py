import cv2
import numpy as np
import pyautogui
import time

from app.utils.detector_gesture.math_processor import get_distance, camera_to_screen, smooth_coordinates

# Tắt cơ chế an toàn để di chuyển mượt ở 4 góc màn hình
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# Lấy kích thước màn hình máy tính
SCREEN_W, SCREEN_H = pyautogui.size()

# Biến trạng thái toàn cục
prev_x, prev_y = 0, 0
pinch_active = False
right_pinch_active = False
is_dragging = False            # Trạng thái đang kéo rê

pinch_start_time = 0
pinch_hold_time = 0.2         # Giữ chụm > 0.2s để kích hoạt Dragging
last_release_time = 0         # Thời điểm nhả chụm tay lần trước
double_click_interval = 0.35  # Khoảng thời gian giữa 2 lần nhả tay để tính Double Click

def control_mouse(frame, hand, cam_w=640, cam_h=480, frame_r=120, pinch_threshold=35):
    global prev_x, prev_y, pinch_active, right_pinch_active, is_dragging
    global pinch_start_time, last_release_time

    lmList = hand["lmList"]

    x_wrist, y_wrist = lmList[0][0], lmList[0][1]      # Cổ tay (0)
    x_thumb, y_thumb = lmList[4][0], lmList[4][1]      # Ngón cái (4)
    x_index, y_index = lmList[8][0], lmList[8][1]      # Đầu ngón trỏ (8)
    x_middle, y_middle = lmList[12][0], lmList[12][1]  # Đầu ngón giữa (12)
    x_ring, y_ring = lmList[16][0], lmList[16][1]      # Đầu ngón áp út (16)
    x_pinky, y_pinky = lmList[20][0], lmList[20][1]    # Đầu ngón út (20)

    x_target, y_target = camera_to_screen(x_index, y_index, cam_w, cam_h, SCREEN_W, SCREEN_H, frame_r)
    curr_x, curr_y = smooth_coordinates(prev_x, prev_y, x_target, y_target)
    prev_x, prev_y = curr_x, curr_y
    prev_x, prev_y = curr_x, curr_y

    # ================= XỬ LÝ CỬ CHỈ =================
    # Tính khoảng cách các đầu ngón tay đến cổ tay
    ring_wrist = get_distance(x_ring, x_wrist, y_ring, y_wrist)
    pinky_wrist = get_distance(x_pinky, x_wrist, y_pinky, y_wrist)
    index_wrist = get_distance(x_index, x_wrist, y_index, y_wrist)
    middle_wrist = get_distance(x_middle, x_wrist, y_middle, y_wrist)

    # Tính khoảng cách chụm ngón
    len_thumb_index = get_distance(x_thumb, x_index, y_thumb, y_index)
    len_thumb_middle = get_distance(x_thumb, x_middle, y_thumb, y_middle)

    # 1. CHUỘT PHẢI (Ngón cái + Ngón giữa)
    if len_thumb_middle < pinch_threshold and len_thumb_index >= pinch_threshold:
        cv2.circle(frame, (x_middle, y_middle), 8, (255,0,0), cv2.FILLED)
        if not right_pinch_active:
            pyautogui.rightClick()
            right_pinch_active = True
    else:
        right_pinch_active = False

    # 2. CHUỘT TRÁI, DOUBLE CLICK & DRAG (Ngón cái + Ngón trỏ)
    if len_thumb_index < pinch_threshold and not right_pinch_active:
        cv2.circle(frame, (x_index, y_index), 8, (0, 255, 0), cv2.FILLED)
        curr_time = time.time()

        if not pinch_active:
            # Bắt đầu chụm ngón tay
            pinch_active = True
            pinch_start_time = curr_time
        else:
            # Nếu chụm ngón tay giữ lâu -> Bắt đầu giữ chuột để kéo rê (Drag)
            if (curr_time - pinch_start_time > pinch_hold_time) and not is_dragging:
                pyautogui.mouseDown()
                is_dragging = True
    else:
        # Khi xòe tay ra -> Nhả chuột
        if pinch_active:
            curr_time = time.time()

            if is_dragging:
                # Nếu trước đó đang kéo rê -> Thả chuột ra
                pyautogui.mouseUp()
                is_dragging = False
            else:
                # Nếu xòe tay ra nhanh (dưới 0.2s) -> Tính là Click hoặc Double Click
                if curr_time - last_release_time < double_click_interval:
                    pyautogui.doubleClick()
                    last_release_time = 0
                else:
                    pyautogui.click()
                    last_release_time = curr_time

            pinch_active = False

    if not right_pinch_active and (not pinch_active or is_dragging):
        pyautogui.moveTo(curr_x, curr_y)