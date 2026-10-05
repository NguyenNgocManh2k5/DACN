"""Man hinh dang ky tai khoan cho TechStore."""

import tkinter as tk
from tkinter import ttk, messagebox

from app.services import auth_service
from app.views import theme


class RegisterDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.registered_username = None

        self.title("Tạo tài khoản — TechStore")
        self.resizable(False, False)
        self.configure(background=theme.SIDEBAR)

        self.protocol(
            "WM_DELETE_WINDOW",
            self._cancel
        )

        # =========================
        # Khung chính
        # =========================
        body = tk.Frame(
            self,
            bg=theme.SIDEBAR,
            padx=46,
            pady=30
        )
        body.pack(
            fill="both",
            expand=True
        )

        # =========================
        # Tiêu đề
        # =========================
        tk.Label(
            body,
            text="Tạo tài khoản",
            bg=theme.SIDEBAR,
            fg="#ffffff",
            font=(theme.FAMILY, 22, "bold")
        ).pack()

        tk.Label(
            body,
            text="Đăng ký tài khoản nhân viên TechStore",
            bg=theme.SIDEBAR,
            fg=theme.SIDEBAR_TEXT,
            font=theme.FONT_BASE
        ).pack(
            pady=(4, 20)
        )

        # =========================
        # Form
        # =========================
        form = tk.Frame(
            body,
            bg=theme.SIDEBAR
        )
        form.pack()

        # =========================
        # Họ và tên
        # =========================
        tk.Label(
            form,
            text="Họ và tên",
            bg=theme.SIDEBAR,
            fg=theme.SIDEBAR_TEXT,
            font=theme.FONT_SMALL,
            anchor="w"
        ).pack(fill="x")

        self.display_name = ttk.Entry(
            form,
            width=28,
            font=(theme.FAMILY, 11)
        )
        self.display_name.pack(
            pady=(2, 10),
            ipady=3
        )

        # =========================
        # Tên đăng nhập
        # =========================
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

        # =========================
        # Mật khẩu
        # =========================
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
            pady=(2, 10),
            ipady=3
        )

        # =========================
        # Nhập lại mật khẩu
        # =========================
        tk.Label(
            form,
            text="Nhập lại mật khẩu",
            bg=theme.SIDEBAR,
            fg=theme.SIDEBAR_TEXT,
            font=theme.FONT_SMALL,
            anchor="w"
        ).pack(fill="x")

        self.confirm_password = ttk.Entry(
            form,
            width=28,
            show="●",
            font=(theme.FAMILY, 11)
        )
        self.confirm_password.pack(
            pady=(2, 4),
            ipady=3
        )

        # =========================
        # Thông báo lỗi
        # =========================
        self.error = tk.Label(
            body,
            text="",
            bg=theme.SIDEBAR,
            fg="#ff8f8f",
            font=theme.FONT_SMALL,
            wraplength=300
        )
        self.error.pack(
            pady=(5, 5)
        )

        # =========================
        # Nút tạo tài khoản
        # =========================
        ttk.Button(
            body,
            text="Tạo tài khoản",
            style="Big.Accent.TButton",
            command=self._create_account
        ).pack(
            fill="x",
            pady=(4, 8)
        )

        # =========================
        # Nút quay lại đăng nhập
        # =========================
        back_btn = tk.Button(
            body,
            text="← Quay lại đăng nhập",
            bg="#e2e8f0",
            fg="#0f172a",
            font=("Segoe UI", 10, "bold"),
            relief="solid",
            bd=1,
            cursor="hand2",
            activebackground="#cbd5e1",
            command=self._cancel
        )

        back_btn.pack(
            fill="x",
            ipady=7
        )

        # =========================
        # Ghi chú
        # =========================
        tk.Label(
            body,
            text="Tài khoản đăng ký mới có vai trò Nhân viên.",
            bg=theme.SIDEBAR,
            fg=theme.SIDEBAR_TEXT,
            font=theme.FONT_SMALL
        ).pack(
            pady=(14, 0)
        )

        # =========================
        # Phím tắt
        # =========================
        self.bind(
            "<Return>",
            lambda e: self._create_account()
        )

        self.bind(
            "<Escape>",
            lambda e: self._cancel()
        )

        # =========================
        # Canh giữa màn hình
        # =========================
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

        self.display_name.focus_set()
        self.grab_set()

    # =====================================================
    # Tạo tài khoản
    # =====================================================
    def _create_account(self):
        display_name = self.display_name.get().strip()
        username = self.username.get().strip().lower()
        password = self.password.get()
        confirm_password = self.confirm_password.get()

        # =========================
        # Kiểm tra họ tên
        # =========================
        if not display_name:
            self._show_error(
                "Vui lòng nhập họ và tên."
            )
            self.display_name.focus_set()
            return

        # =========================
        # Kiểm tra tên đăng nhập
        # =========================
        if not username:
            self._show_error(
                "Vui lòng nhập tên đăng nhập."
            )
            self.username.focus_set()
            return

        if len(username) < 3:
            self._show_error(
                "Tên đăng nhập phải có ít nhất 3 ký tự."
            )
            self.username.focus_set()
            return

        # =========================
        # Kiểm tra mật khẩu
        # =========================
        if not password:
            self._show_error(
                "Vui lòng nhập mật khẩu."
            )
            self.password.focus_set()
            return

        if len(password) < 6:
            self._show_error(
                "Mật khẩu phải có ít nhất 6 ký tự."
            )
            self.password.focus_set()
            return

        # =========================
        # Kiểm tra nhập lại mật khẩu
        # =========================
        if password != confirm_password:
            self._show_error(
                "Mật khẩu nhập lại không khớp."
            )

            self.confirm_password.delete(
                0,
                "end"
            )

            self.confirm_password.focus_set()
            return

        # =========================
        # Tạo tài khoản trong MongoDB
        # =========================
        try:
            auth_service.create_user(
                username=username,
                password=password,
                display_name=display_name,
                role="staff",
                image_path=""
            )

        except ValueError as e:
            self._show_error(
                str(e)
            )
            return

        except Exception as e:
            self._show_error(
                f"Không thể tạo tài khoản: {e}"
            )
            return

        # =========================
        # Đăng ký thành công
        # =========================
        self.registered_username = username

        messagebox.showinfo(
            "Đăng ký thành công",
            "Tài khoản đã được tạo thành công!\n\n"
            f"Tên đăng nhập: {username}\n"
            "Vai trò: Nhân viên",
            parent=self
        )

        self.destroy()

    # =====================================================
    # Hiển thị lỗi
    # =====================================================
    def _show_error(self, message):
        self.error.config(
            text=message
        )

    # =====================================================
    # Đóng cửa sổ
    # =====================================================
    def _cancel(self):
        self.registered_username = None
        self.destroy()
