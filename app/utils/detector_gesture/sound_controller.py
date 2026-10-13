import cv2
import numpy as np
import time
from pycaw.pycaw import AudioUtilities
from app.utils.detector_gesture.math_processor import get_distance

device = AudioUtilities.GetSpeakers()
volume = device.EndpointVolume   # type: ignore

start_time = 0
connection_timeout = 2.0
is_connecting = False
is_audio_controlling = False
flag = False    # Đánh dấu Tay 1 nhả ra

def check_control_sound(frame, hands):
    global start_time, connection_timeout, is_connecting, is_audio_controlling, flag
    if len(hands) < 2:
        return

    lmList1 = hands[0]["lmList"] 
    lmList2 = hands[1]["lmList"] 

    # Tay 1: ngón trỏ (8) + ngón cái (4)
    x_index1, y_index1 = lmList1[8][0], lmList1[8][1]   
    x_thumb1, y_thumb1 = lmList1[4][0], lmList1[4][1]   
    cx1, cy1 = (x_index1 + x_thumb1)//2, (y_index1 + y_thumb1)//2     

    # Tay 2: ngón trỏ (8) + ngón cái (4)
    x_index2, y_index2 = lmList2[8][0], lmList2[8][1]
    x_thumb2, y_thumb2 = lmList2[4][0], lmList2[4][1]

    # CÁC KHOẢNG CÁCH KIỂM TRA ĐIỀU KIỆN
    index_thumb1 = get_distance(x_index1, x_thumb1, y_index1, y_thumb1)    # Tay 1 tự chụm (dùng để Click/Trigger)
    thumb2_to_1 = get_distance(cx1, x_thumb2, cy1, y_thumb2)    # Tay 1 chụm chạm vào Ngón Cái Tay 2
    index2_to_1 = get_distance(cx1, x_index2, cy1, y_index2)    # Tay 1 chụm chạm vào Ngón Trỏ Tay 2

    current_time = time.time()

    # --- BƯỚC 1: KÍCH HOẠT KÉO DÂY ---
    # Tay 1 chụm ngón (<30px) VÀ chạm sát vào ngón cái Tay 2 (<35px)
    if not is_connecting and not is_audio_controlling:
        if index_thumb1 < 25 and thumb2_to_1 < 35:
            is_connecting = True
            start_time = current_time
            print("Connecting to speaker...")

    # --- BƯỚC 2: XỬ LÝ TRẠNG THÁI ĐANG KÉO DÂY ---
    if is_connecting:
        end_time = time.time()
        # Kiểm tra quá thời gian (Timeout)
        if end_time - start_time > connection_timeout:
            is_connecting = False   # Hủy kết nối
            print("[status] Failure!")
        else:
            cv2.line(frame, (cx1, cy1), (x_thumb2, y_thumb2), (0, 100, 255), 2)
            if index2_to_1 < 35:
                is_connecting = False
                is_audio_controlling = True
                flag = False
                print("[status] Success! Setting volume... ")
    # --- BƯỚC 3: ĐIỀU KHUYỂN ÂM THANH & KẾT THÚC ---
    if is_audio_controlling:
        cv2.line(frame, (x_thumb2, y_thumb2), (x_index2, y_index2), (255, 0 ,255), 2)
        control_sound(frame, hands[1])
        
        if index_thumb1 > 40:
            flag = True

        if index_thumb1 < 25 and flag:
            is_audio_controlling = False
            flag = False
            vol_per = int(volume.GetMasterVolumeLevelScalar() * 100)
            print(f"[finished] Volume: {vol_per}%")


def control_sound(frame, hand):
    lmList = hand["lmList"]
    x1, y1 = lmList[4][0], lmList[4][1]
    x2, y2 = lmList[8][0], lmList[8][1]
    cv2.circle(frame, (x1, y1), 8, (255, 0, 255), -1)
    cv2.circle(frame, (x2, y2), 8, (255, 0, 255), -1)
    cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)

    # Khoảng cách Euclidean giữa ngón cái và ngón trỏ
    length = get_distance(x1, x2, y1, y2)

    h, w, _ = frame.shape
    bar_x1, bar_x2 = 40, 60          # Chiều rộng cố định 20px
    bar_y2 = h - 60                  # Cách mép dưới 60px
    bar_y1 = bar_y2 - 200            # Chiều cao cố định 200px

    # Chuyển đổi length sang tọa độ Y trên màn hình
    vol_bar = np.interp(length, [25, 250], [bar_y2, bar_y1])
    vol_bar = np.clip(vol_bar, bar_y1, bar_y2)

    # Chuyển đổi length thành tỉ lệ 0% đến 100%
    vol_scalar = np.interp(length, [25, 250], [0.0, 1.0])
    vol_scalar = np.clip(vol_scalar, 0.0, 1.0)

    # Đặt âm lượng hệ thống
    volume.SetMasterVolumeLevelScalar(vol_scalar, None)
    vol_per = vol_scalar * 100

    if length < 25:
        cx, cy = (x1+x2)//2, (y1+y2)//2
        cv2.circle(frame, (cx, cy), 8, (0, 255, 0), -1)

    cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x2, bar_y2), (128, 128, 128), 2)
    cv2.rectangle(frame, (bar_x1, int(vol_bar)), (bar_x2, bar_y2), (192, 192, 192), -1)
    cv2.putText(frame, f'{int(vol_per)} %', (bar_x2, bar_y2-5), 
                cv2.FONT_HERSHEY_PLAIN, 0.6, (0, 0, 0), 1)