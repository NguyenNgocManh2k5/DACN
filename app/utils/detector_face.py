import cv2
import os
import time
from pathlib import Path
from deepface import DeepFace
from app.database.connection import get_db
from tkinter import messagebox

def verify_face_from_camera(username_input):
    if not username_input:
        return False, "Vui lòng nhập tên đăng nhập trước khi xác thực khuôn mặt!", None

    db = get_db()
    user = db.users.find_one({"username": username_input})
    
    if not user:
        return False, f"Không tìm thấy tài khoản '{username_input}' trong hệ thống!", None

    # Hỗ trợ đa ảnh mẫu (Multi-sample) hoặc fallback về 1 ảnh đơn cũ để tương thích ngược
    stored_paths = user.get("image_paths", [])
    if not stored_paths and user.get("image_path"):
        stored_paths = [user.get("image_path")]

    # Lọc lại các đường dẫn file ảnh mẫu thực sự tồn tại trên ổ cứng
    valid_stored_paths = [p for p in stored_paths if os.path.exists(p)]
    
    if not valid_stored_paths:
        return False, f"Tài khoản '{username_input}' chưa đăng ký ảnh khuôn mặt mẫu nào trong hệ thống!", None

    # 1. Mở Webcam quét liên tục
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return False, "Không thể kết nối với Webcam!", None
    
    messagebox.showinfo("Thông báo", f"Hệ thống quét khuôn mặt đa góc độ (10s) cho: {username_input}.\nHãy nhìn thẳng, xoay nhẹ trái/phải, tìm được khung hình khớp sẽ tự động đăng nhập!")

    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    cascade_path = str(BASE_DIR / "haarcascade_frontalface_default.xml")
    face_cascade = cv2.CascadeClassifier(cascade_path) if os.path.exists(cascade_path) else None

    if not face_cascade:
        cap.release()
        return False, "Không tìm thấy file Haar Cascade để nhận diện mặt!", None

    start_time = time.time()
    TIMEOUT = 10.0    
    CHECK_INTERVAL = 0.7    
    last_check_time = time.time()

    success_result = None
    temp_dir = Path("D:/Image")
    temp_dir.mkdir(parents=True, exist_ok=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()
        
        current_time = time.time()
        elapsed = current_time - start_time
        remaining_time = max(0, int(TIMEOUT - elapsed))

        # Phát hiện mặt để vẽ khung xanh hướng dẫn
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

        if len(faces) > 0:
            for (x, y, w, h) in faces:
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.imshow("Multi-sample Face Login", display_frame)

        if cv2.waitKey(1) & 0xFF == 27:  # Bấm ESC để hủy
            break

        if elapsed >= TIMEOUT:
            break

        # Thực hiện đối chiếu
        if current_time - last_check_time >= CHECK_INTERVAL and len(faces) > 0:
            last_check_time = current_time
            
            try:
                # Cân bằng sáng tự động
                ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
                channels = list(cv2.split(ycrcb))
                channels[0] = cv2.equalizeHist(channels[0])
                balanced_frame = cv2.merge(channels)
                balanced_frame = cv2.cvtColor(balanced_frame, cv2.COLOR_YCrCb2BGR)

                temp_captured_path = str(temp_dir / f"temp_multi_{username_input}.jpg")
                
                # Cắt mặt chuẩn xác
                (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
                padding = int(w * 0.1)
                img_h, img_w, _ = balanced_frame.shape
                x1 = max(0, x - padding)
                y1 = max(0, y - padding)
                x2 = min(img_w, x + w + padding)
                y2 = min(img_h, y + h + padding)
                cropped = balanced_frame[y1:y2, x1:x2]

                if cropped.shape[0] > 50 and cropped.shape[1] > 50:
                    cv2.imwrite(temp_captured_path, cropped)
                else:
                    cv2.imwrite(temp_captured_path, balanced_frame)

                # ĐỐI CHIẾU LẦN LƯỢT VỚI TẤT CẢ CÁC ẢNH MẪU TRONG DANH SÁCH `valid_stored_paths`
                best_distance_for_frame = float('inf')
                for sample_path in valid_stored_paths:
                    try:
                        result = DeepFace.verify(
                            img1_path=sample_path,
                            img2_path=temp_captured_path,
                            model_name="ArcFace",
                            detector_backend="opencv"
                        )
                        dist = result["distance"]
                        if dist < best_distance_for_frame:
                            best_distance_for_frame = dist
                    except:
                        continue

                if os.path.exists(temp_captured_path):
                    os.remove(temp_captured_path)

                CUSTOM_THRESHOLD = 0.28  # Ngưỡng của mô hình ArcFace

                # ĐẠT NGƯỠNG -> ĐĂNG NHẬP 
                if best_distance_for_frame <= CUSTOM_THRESHOLD:
                    similarity_score = max(0, (1 - (best_distance_for_frame / 1.0))) * 100
                    success_result = (True, f"Xác thực đa góc thành công!", user)
                    break

            except Exception:
                pass

    cap.release()
    cv2.destroyAllWindows()

    if success_result:
        return success_result
    else:
        return False, "Hết thời gian quét (10s) hoặc không tìm thấy góc khuôn mặt nào khớp!", None