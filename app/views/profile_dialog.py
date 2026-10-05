import tkinter as tk
from tkinter import messagebox, filedialog
import cv2
import os
from pathlib import Path
import bcrypt
from app.database.connection import get_db

class ProfileDialog(tk.Toplevel):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.parent = parent
        self.current_user = current_user
        self.db = get_db()

        self.title("Thông tin cá nhân & Cài đặt tài khoản")
        self.geometry("450x650")
        self.config(bg="#f8f9fa")
        self.resizable(False, False)
        
        # Đặt cửa sổ hiển thị ở giữa màn hình và nằm trên cùng (Modal)
        self.transient(parent)
        self.grab_set()

        # Lấy danh sách ảnh mẫu hiện tại (Hỗ trợ tương thích ngược nếu DB cũ dùng image_path)
        existing_paths = self.current_user.get("image_paths", [])
        if not existing_paths and self.current_user.get("image_path"):
            existing_paths = [self.current_user.get("image_path")]
        
        # Biến lưu danh sách đường dẫn ảnh mẫu (Nhiều ảnh)
        self.image_paths = existing_paths

        self.create_widgets()

    def create_widgets(self):
        # Tiêu đề
        title_lbl = tk.Label(self, text="HỒ SƠ CÁ NHÂN & ĐẠI DIỆN AI", font=("Arial", 14, "bold"), bg="#f8f9fa", fg="#333")
        title_lbl.pack(pady=15)

        # Frame chứa form nhập liệu
        form_frame = tk.Frame(self, bg="#f8f9fa")
        form_frame.pack(padx=30, pady=5, fill="both", expand=True)

        # 1. Tên đăng nhập
        tk.Label(form_frame, text="Tên đăng nhập:", font=("Arial", 10, "bold"), bg="#f8f9fa").pack(anchor="w", pady=(5, 0))
        self.ent_username = tk.Entry(form_frame, font=("Arial", 11), bg="#e9ecef", relief="solid", bd=1)
        self.ent_username.pack(fill="x", pady=(0, 10), ipady=4)
        self.ent_username.insert(0, self.current_user.get("username", ""))
        self.ent_username.config(state="readonly")

        # 2. Tên hiển thị / Họ tên
        tk.Label(form_frame, text="Họ tên hiển thị:", font=("Arial", 10, "bold"), bg="#f8f9fa").pack(anchor="w", pady=(5, 0))
        self.ent_display_name = tk.Entry(form_frame, font=("Arial", 11), relief="solid", bd=1)
        self.ent_display_name.pack(fill="x", pady=(0, 10), ipady=4)
        self.ent_display_name.insert(0, self.current_user.get("display_name", self.current_user.get("full_name", "")))

        # 3. Mật khẩu mới
        tk.Label(form_frame, text="Mật khẩu mới (Bỏ trống nếu không đổi):", font=("Arial", 10, "bold"), bg="#f8f9fa").pack(anchor="w", pady=(5, 0))
        self.ent_password = tk.Entry(form_frame, font=("Arial", 11), show="*", relief="solid", bd=1)
        self.ent_password.pack(fill="x", pady=(0, 10), ipady=4)

        # 4. Quản lý Ảnh khuôn mặt AI (Đa ảnh mẫu)
        tk.Label(form_frame, text="Danh sách ảnh nhận diện AI (Đa góc độ):", font=("Arial", 10, "bold"), bg="#f8f9fa").pack(anchor="w", pady=(5, 0))
        
        # Listbox hiển thị danh sách các file ảnh đang có
        self.listbox_paths = tk.Listbox(form_frame, font=("Arial", 9), height=5, relief="solid", bd=1)
        self.listbox_paths.pack(fill="x", pady=(0, 5))
        self.refresh_listbox()

        # Frame chứa các nút thao tác ảnh
        btn_img_action_frame = tk.Frame(form_frame, bg="#f8f9fa")
        btn_img_action_frame.pack(fill="x", pady=2)

        btn_choose_file = tk.Button(btn_img_action_frame, text="📁 Thêm từ tệp", font=("Arial", 9, "bold"), bg="#6c757d", fg="white", cursor="hand2", command=self.choose_image_files)
        btn_choose_file.pack(side="left", expand=True, fill="x", padx=(0, 3), ipady=4)

        btn_capture = tk.Button(btn_img_action_frame, text="📷 Chụp thêm góc", font=("Arial", 9, "bold"), bg="#17a2b8", fg="white", cursor="hand2", command=self.capture_from_webcam)
        btn_capture.pack(side="left", expand=True, fill="x", padx=3, ipady=4)

        btn_remove = tk.Button(btn_img_action_frame, text="❌ Xóa ảnh chọn", font=("Arial", 9, "bold"), bg="#dc3545", fg="white", cursor="hand2", command=self.remove_selected_image)
        btn_remove.pack(side="right", expand=True, fill="x", padx=(3, 0), ipady=4)

        # Nút Lưu thay đổi
        btn_save = tk.Button(self, text="LƯU THAY ĐỔI", font=("Arial", 11, "bold"), bg="#28a745", fg="white", cursor="hand2", command=self.save_profile)
        btn_save.pack(pady=15, ipadx=20, ipady=5)

    def refresh_listbox(self):
        """Cập nhật lại giao diện Listbox hiển thị danh sách đường dẫn ảnh"""
        self.listbox_paths.delete(0, tk.END)
        for path in self.image_paths:
            self.listbox_paths.insert(tk.END, path)

    def choose_image_files(self):
        """Cho phép chọn nhiều file ảnh cùng lúc từ máy tính"""
        file_paths = filedialog.askopenfilenames(
            title="Chọn các ảnh khuôn mặt mẫu",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
        )
        if file_paths:
            for path in file_paths:
                if path not in self.image_paths:
                    self.image_paths.append(path)
            self.refresh_listbox()

    def capture_from_webcam(self):
        """Mở webcam chụp ảnh trực tiếp bổ sung góc độ mới"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Lỗi", "Không thể kết nối với Webcam!")
            return

        messagebox.showinfo("Hướng dẫn", "Nhìn vào camera (có thể xoay nhẹ trái/phải) và nhấn [SPACEBAR] để chụp thêm góc mẫu!")

        captured_frame = None
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        cascade_path = str(BASE_DIR / "haarcascade_frontalface_default.xml")
        face_cascade = cv2.CascadeClassifier(cascade_path)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            display_frame = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5)
            for (x, y, w, h) in faces:
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            cv2.imshow("Chup anh bo sung - Nhan SPACE de luu", display_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 32:  # Phím Space
                captured_frame = frame
                break
            elif key == 27:  # Phím ESC hủy
                break

        cap.release()
        cv2.destroyAllWindows()

        if captured_frame is not None:
            save_dir = Path("D:/Image")
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Đặt tên file tự động dựa theo thời gian để tránh trùng lặp các góc chụp
            import time
            timestamp = int(time.time())
            save_path = str(save_dir / f"{self.current_user.get('username')}_face_{timestamp}.jpg")
            cv2.imwrite(save_path, captured_frame)
            
            self.image_paths.append(save_path)
            self.refresh_listbox()
            messagebox.showinfo("Thành công", f"Đã thêm góc chụp mới:\n{save_path}")

    def remove_selected_image(self):
        """Xóa ảnh đang chọn khỏi danh sách mẫu"""
        selected_indices = self.listbox_paths.curselection()
        if not selected_indices:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một dòng ảnh trong danh sách để xóa!")
            return
        
        idx = selected_indices[0]
        removed_path = self.image_paths.pop(idx)
        self.refresh_listbox()

    def save_profile(self):
        """Cập nhật thông tin và danh sách mảng ảnh vào MongoDB"""
        new_display_name = self.ent_display_name.get().strip()
        new_password = self.ent_password.get().strip()

        if not new_display_name:
            messagebox.showwarning("Cảnh báo", "Họ tên hiển thị không được để trống!")
            return

        if not self.image_paths:
            messagebox.showwarning("Cảnh báo", "Tài khoản phải có ít nhất một ảnh khuôn mặt mẫu để nhận diện AI!")
            return

        update_data = {
            "display_name": new_display_name,
            "full_name": new_display_name,
            "image_paths": self.image_paths # Lưu dạng mảng danh sách nhiều ảnh
        }

        # Nếu đổi mật khẩu mới thì mã hóa bcrypt
        if new_password:
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            update_data["password_hash"] = hashed_password
            update_data["password"] = hashed_password

        try:
            self.db.users.update_one(
                {"username": self.current_user.get("username")},
                {"$set": update_data}
            )
            messagebox.showinfo("Thành công", "Cập nhật hồ sơ và danh sách ảnh AI thành công!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi cơ sở dữ liệu", f"Không thể cập nhật:\n{str(e)}")