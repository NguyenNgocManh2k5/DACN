import time
import cv2
import os
import numpy as np
import threading
from pathlib import Path
from dotenv import load_dotenv
from inference_sdk import InferenceHTTPClient
from tkinter import messagebox

# Nạp các biến môi trường từ .env
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class ProductDetector:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.client = None
        self.is_running = False
        self.thread = None

        self.cooldowns = {}
        self.cooldown_time = 5.0

        self._init_inference_client()
        self._initialized = True

    def _init_inference_client(self):
        try:
            API_KEY = os.getenv("ROBOFLOW_API_KEY")
            self.model_id = os.getenv("ROBOFLOW_MODEL_ID")
            if not API_KEY or not self.model_id:
                print(f"[Lỗi] Thiếu ROBOFLOW_API_KEY hoặc ROBOFLOW_MODEL_ID trong file .env tại: {env_path}")
                return
            
            self.client = InferenceHTTPClient(
                api_url="https://serverless.roboflow.com",
                api_key=API_KEY
            )
        except Exception as e:
            print(f"[Lỗi] Không thể khởi tạo client Roboflow: {e}")

    def start(self, mode: str, callback=None):
        """Mở cửa sổ camera độc lập để quét sản phẩm dựa trên chế độ ('sales' hoặc 'import')"""
        if self.is_running:
            return
        
        if self.client is None:
            messagebox.showerror("Lỗi", "Chưa khởi tạo được kết nối với hệ thống AI nhận diện sản phẩm!")
            return

        self.is_running = True
        self.cooldowns.clear()

        # Chạy vòng lặp camera trên một Thread riêng biệt để tránh làm đơ giao diện Tkinter
        self.thread = threading.Thread(target=self._run_camera_loop, args=(mode, callback), daemon=True)
        self.thread.start()

    def stop(self):
        """Tắt bộ nhận diện, giải phóng camera và đóng cửa sổ"""
        self.is_running = False
        cv2.destroyAllWindows()

    def _run_camera_loop(self, mode: str, callback):
        cap = cv2.VideoCapture(2)

        if not cap.isOpened():
            messagebox.showerror("Lỗi", "Không thể kết nối với Webcam!")
            self.is_running = False
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        window_name = "Scan product"
        print("Webcam opened — press q to quit.")

        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame = cv2.flip(frame, 1)
            display_frame = frame.copy()
            current_time = time.time()
            detected_items = []

            try:
                result = self.client.infer(
                    frame, 
                    model_id=self.model_id
                )

                for pred in result.get("predictions", []):
                    x = int(pred["x"])
                    y = int(pred["y"])
                    w = int(pred["width"])
                    h = int(pred["height"])
                    conf = float(pred["confidence"])
                    class_name = pred["class"]

                    x1 = int(x - w / 2)
                    y1 = int(y - h / 2)
                    x2 = int(x + w / 2)
                    y2 = int(y + h / 2)

                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                    label = f"{class_name} ({conf:.2f})"
                    cv2.putText(
                        display_frame, label, (x1, max(20, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2
                    )

                    detected_items.append({
                        "product_code": class_name,
                        "confidence": conf,
                        "bbox": [x1, y1, x2, y2]
                    })

                if detected_items and callback:
                    best_match = max(detected_items, key=lambda x: x["confidence"])
                    product_code = best_match["product_code"]
                    
                    last_triggered = self.cooldowns.get(product_code, 0)
                    if current_time - last_triggered >= self.cooldown_time:
                        self.cooldowns[product_code] = current_time
                        callback(mode, product_code)

            except Exception as e:
                pass

            cv2.imshow(window_name, display_frame)

            # Nhấn phím 'q' HOẶC Nhấn vào nút [X] ở góc cửa sổ
            key = cv2.waitKey(1) & 0xFF
            button = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
            if key == ord('q') or button < 1:
                print("Quit requested — stopping.")
                break

        cap.release()
        self.is_running = False
        try:
            cv2.destroyWindow(window_name)
        except Exception:
            cv2.destroyAllWindows()

# Khởi tạo instance dùng chung
product_detector = ProductDetector()