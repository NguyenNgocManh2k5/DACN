"""Hop thoai dang nhap, hien truoc khi vao cua so chinh.

Ket qua nam o self.result: document user neu dang nhap dung,
None neu nguoi dung dong cua so.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from app.services import auth_service
from app.views import theme
from app.utils.detector_face import verify_face_from_camera
from app.utils.remember_username import save_remembered_username, load_remembered_username

class LoginDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.result: dict | None = None

        self.title("Đăng nhập — TechStore")
        self.resizable(False, False)
        self.configure(background=theme.SIDEBAR)
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        body = tk.Frame(
            self,
            bg=theme.SIDEBAR,
            padx=46,
            pady=34
        )
        body.pack(fill="both", expand=True)

        tk.Label(
            body,
            text="TechStore",
            bg=theme.SIDEBAR,
            fg="#ffffff",
            font=(theme.FAMILY, 22, "bold")
        ).pack()

        tk.Label(
            body,
            text="Quản lý bán hàng công nghệ",
            bg=theme.SIDEBAR,
            fg=theme.SIDEBAR_TEXT,
            font=theme.FONT_BASE
        ).pack(pady=(2, 22))

        form = tk.Frame(body, bg=theme.SIDEBAR)
        form.pack()

        tk.Label(
            form,
            text="Tên đăng nhập",
            bg=theme.SIDEBAR,
            fg=theme.SIDEBAR_TEXT,
            font=theme.FONT_SMALL,
            anchor="w"
        ).pack(fill="x")

        self.username = ttk.Entry(
            form,
            width=28,
            font=(theme.FAMILY, 11)
        )
        self.username.pack(
            pady=(2, 10),
            ipady=3
        )

        # ➔ TỰ ĐỘNG ĐIỀN TÊN ĐĂNG NHẬP ĐÃ LƯU TRƯỚC ĐÓ
        saved_user = load_remembered_username()
        if saved_user:
            self.username.insert(0, saved_user)

        tk.Label(
            form,
            text="Mật khẩu",
            bg=theme.SIDEBAR,
            fg=theme.SIDEBAR_TEXT,
            font=theme.FONT_SMALL,
            anchor="w"
        ).pack(fill="x")

        self.password = ttk.Entry(
            form,
            width=28,
            show="●",
            font=(theme.FAMILY, 11)
        )
        self.password.pack(
            pady=(2, 4),
            ipady=3
        )

        self.error = tk.Label(
            body,
            text="",
            bg=theme.SIDEBAR,
            fg="#ff8f8f",
            font=theme.FONT_SMALL
        )
        self.error.pack(pady=(4, 2))

        ttk.Button(
            body,
            text="Đăng nhập",
            style="Big.Accent.TButton",
            command=self._submit
        ).pack(
            fill="x",
            pady=(6, 0)
        )

        face_btn = tk.Button(
            body,
            text="📷  Đăng nhập bằng khuôn mặt",
            bg="#ffffff",
            fg="#0f172a",
            font=("Segoe UI", 10, "bold"),
            relief="solid",
            bd=1,
            cursor="hand2",
            activebackground="#e2e8f0",
            command=self.handle_face_login
        )
        face_btn.pack(
            fill="x",
            ipady=7,
            pady=(8, 0)
        )

        separator_frame = tk.Frame(
            body,
            bg=theme.SIDEBAR
        )
        separator_frame.pack(
            fill="x",
            pady=(14, 10)
        )

        tk.Frame(
            separator_frame,
            bg="#64748b",
            height=1
        ).pack(
            side="left",
            fill="x",
            expand=True,
            pady=7
        )

        tk.Label(
            separator_frame,
            text=" hoặc ",
            bg=theme.SIDEBAR,
            fg=theme.SIDEBAR_TEXT,
            font=theme.FONT_SMALL
        ).pack(side="left")

        tk.Frame(
            separator_frame,
            bg="#64748b",
            height=1
        ).pack(
            side="left",
            fill="x",
            expand=True,
            pady=7
        )

        register_btn = tk.Button(
            body,
            text="📝  Tạo tài khoản mới",
            bg="#e2e8f0",
            fg="#0f172a",
            font=("Segoe UI", 10, "bold"),
            relief="solid",
            bd=1,
            cursor="hand2",
            activebackground="#cbd5e1",
            command=self.open_register
        )
        register_btn.pack(
            fill="x",
            ipady=7
        )

        tk.Label(
            body,
            text="Mặc định: admin / admin123 · nhanvien / 123456",
            bg=theme.SIDEBAR,
            fg=theme.SIDEBAR_TEXT,
            font=theme.FONT_SMALL
        ).pack(pady=(14, 0))

        self.bind(
            "<Return>",
            lambda e: self._submit()
        )

        self.bind(
            "<Escape>",
            lambda e: self._cancel()
        )

        self.update_idletasks()

        x = (
            self.winfo_screenwidth()
            - self.winfo_width()
        ) // 2

        y = (
            self.winfo_screenheight()
            - self.winfo_height()
        ) // 3

        self.geometry(f"+{x}+{y}")

        # Nếu đã có sẵn tên đăng nhập được điền tự động, đẩy focus sang ô mật khẩu cho tiện
        if saved_user:
            self.password.focus_set()
        else:
            self.username.focus_set()
            
        self.grab_set()

    def _submit(self):
        username = self.username.get().strip()
        password = self.password.get()

        if not username or not password:
            self.error.config(text="Vui lòng nhập đầy đủ thông tin.")
            return

        user = auth_service.login(username, password)
        if user:
            # ➔ LƯU LẠI TÊN ĐĂNG NHẬP KHI ĐĂNG NHẬP THÀNH CÔNG
            save_remembered_username(username)
            
            self.result = user
            self.destroy()
            return
        
        self.error.config(text="Sai tên đăng nhập hoặc mật khẩu.")
        self.password.delete(0, "end")
        self.password.focus_set()

    def open_register(self):
        from app.views.register_window import RegisterDialog

        dialog = RegisterDialog(self)

        self.wait_window(dialog)
        if dialog.registered_username:
            self.username.delete(0, "end")
            self.username.insert(0, dialog.registered_username)
            self.password.focus_set()

    def handle_face_login(self):
        user_name = self.username.get().strip()
        success, message, user = verify_face_from_camera(user_name)
        
        if success:
            # Lấy username chuẩn từ user object trả về (hoặc dùng user_name)
            matched_username = user.get("username", user_name) if isinstance(user, dict) else user_name
            
            # ➔ LƯU LẠI TÊN ĐĂNG NHẬP KHI NHẬN DIỆN KHUÔN MẶT THÀNH CÔNG
            save_remembered_username(matched_username)
            
            messagebox.showinfo("Thành công", message)
            self.result = user  # Gán thông tin user để cửa sổ chính nhận diện
            self.destroy()
        else:
            messagebox.showerror("Đăng nhập thất bại", message)

    def _cancel(self):
        self.result = None
        self.destroy()