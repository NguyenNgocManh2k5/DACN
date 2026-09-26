"""Cua so chinh: thanh dieu huong ben trai, vung noi dung ben phai.

Cac man hinh deu duoc grid vao cung mot o (0, 0) roi xep chong len nhau;
chuyen man hinh bang tkraise().

Toan bo giao dien duoc dung trong _build_ui() de co the DUNG LAI:
doi che do sang/toi hoac dang xuat -> _reset_ui() pha het widget cu,
ap style moi roi dung lai tu dau. Cac view doc mau tu theme.* tai thoi
diem khoi tao nen dung lai la du de mau moi co hieu luc.
"""
import tkinter as tk
import cv2
from PIL import Image, ImageTk
from tkinter import messagebox, ttk

from app.config import APP_TITLE, WINDOW_SIZE, load_settings, save_setting
from app.database import bootstrap
from app.database.connection import check_connection, ensure_indexes
from app.models import product as product_model
from app.services import audit_service
from app.services.auth_service import ROLES
from app.views import theme
from app.views.audit_view import AuditView
from app.views.category_view import CategoryView
from app.views.chat_view import ChatView
from app.views.customer_view import CustomerView
from app.views.dashboard_view import DashboardView
from app.views.inventory_view import InventoryView
from app.views.login_window import LoginDialog
from app.views.order_view import OrderView
from app.views.product_view import ProductView
from app.views.purchase_view import PurchaseView
from app.views.sales_view import SalesView
from app.views.settings_view import SettingsView
from app.views.supplier_view import SupplierView
from app.views.profile_dialog import ProfileDialog

# (khoa, nhan, icon, cac vai tro duoc thay)
MENU = [
    ("sales", "Bán hàng", "🛒", ("admin", "staff")),
    ("products", "Sản phẩm", "📦", ("admin",)),
    ("categories", "Danh mục", "🏷", ("admin",)),
    ("inventory", "Tồn kho", "📊", ("admin",)),
    ("purchases", "Nhập hàng", "📥", ("admin",)),
    ("suppliers", "Nhà cung cấp", "🚚", ("admin",)),
    ("orders", "Hóa đơn", "🧾", ("admin", "staff")),
    ("customers", "Khách hàng", "👥", ("admin", "staff")),
    ("dashboard", "Thống kê", "📈", ("admin",)),
    ("audit", "Nhật ký", "📜", ("admin",)),
    ("settings", "Cài đặt", "⚙", ("admin",)),
    ("chat", "Trợ lý AI", "🤖", ("admin", "staff")),
]

VIEWS = {
    "sales": SalesView,
    "products": ProductView,
    "categories": CategoryView,
    "inventory": InventoryView,
    "purchases": PurchaseView,
    "suppliers": SupplierView,
    "orders": OrderView,
    "customers": CustomerView,
    "dashboard": DashboardView,
    "audit": AuditView,
    "settings": SettingsView,
    "chat": ChatView,
}


class MainWindow(tk.Tk):
    def __init__(self, user: dict | None = None):
        """user: truyen san de bo qua man dang nhap (dung cho kiem thu)."""
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(1180, 700)
        try:
            # mo phong to san: nhieu bang co kha nhieu cot, o kich thuoc
            # WINDOW_SIZE mac dinh se bi cat mat cot ben phai. 'zoomed' chi
            # co tren Windows; he dieu hanh khac bo qua loi nay va giu
            # nguyen WINDOW_SIZE (van dung duoc, chi khong phong to).
            self.state("zoomed")
        except tk.TclError:
            pass

        ok, message = check_connection()
        if not ok:
            messagebox.showerror("Lỗi kết nối", message)
            self.destroy()
            return
        ensure_indexes()
        bootstrap.migrate()

        theme.set_mode(load_settings().get("theme", "light"))
        theme.apply_theme(self)

        self.user = user
        if self.user is None and not self._ask_login():
            return
        audit_service.set_user(self.user)   # cover ca duong test truyen san user=...

        self._badge_job = None

        self.cap = None
        self.hand_detector = None
        self.camera_widget = None
        self.is_camera_active = False
        self._build_ui()
        self._schedule_badge_refresh()

    # ---------- dang nhap / dang xuat ----------

    def _ask_login(self) -> bool:
        """Hien hop thoai dang nhap. Tra ve False neu nguoi dung thoat."""
        self.withdraw()
        dialog = LoginDialog(self)
        self.wait_window(dialog)
        if not dialog.result:
            self.destroy()
            return False
        self.user = dialog.result
        audit_service.set_user(self.user)
        audit_service.log("Đăng nhập")
        self.deiconify()
        return True

    def logout(self):
        if not messagebox.askyesno("Đăng xuất",
                                   "Đăng xuất khỏi tài khoản hiện tại?"):
            return
        audit_service.log("Đăng xuất")
        if self._ask_login():
            self._reset_ui()   # dung lai menu theo vai tro cua nguoi moi

    # ---------- bo cuc ----------

    def _allowed_menu(self):
        role = self.user.get("role", "staff")
        return [(k, l, i) for k, l, i, roles in MENU if role in roles]

    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.frames: dict[str, ttk.Frame] = {}
        self.buttons: dict[str, tk.Label] = {}
        self.current = None

        self._build_sidebar()

        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        self.container = right

        for key, _label, _icon in self._allowed_menu():
            frame = VIEWS[key](self.container, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[key] = frame

        self.camera_widget = tk.Label(self, bg="black")
        self.camera_widget.place(relx=1.0, x=-25, y=25, anchor="ne", width=240, height=180)
        self.camera_widget.lower()
        self.camera_widget.place_forget()

        self.show(self._allowed_menu()[0][0])

    def _reset_ui(self):
        """Pha het giao dien va dung lai — dung khi doi theme / doi tai khoan."""
        for child in self.winfo_children():
            child.destroy()
        theme.apply_theme(self)
        self._build_ui()
        self.refresh_stock_badge()

    def _build_sidebar(self):
        sidebar = tk.Frame(self, bg=theme.SIDEBAR, width=210)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        brand = tk.Frame(sidebar, bg=theme.SIDEBAR)
        brand.pack(fill="x", pady=(22, 6), padx=18)
        tk.Label(brand, text="TechStore", bg=theme.SIDEBAR, fg="#ffffff",
                 font=theme.FONT_BRAND).pack(anchor="w")
        tk.Label(brand, text="Quản lý bán hàng", bg=theme.SIDEBAR,
                 fg=theme.SIDEBAR_TEXT, font=theme.FONT_SMALL).pack(anchor="w")

        tk.Frame(sidebar, bg=theme.SIDEBAR_HOVER, height=1).pack(
            fill="x", padx=18, pady=(14, 10))

        for key, label, icon in self._allowed_menu():
            self.buttons[key] = self._nav_button(sidebar, key, label, icon)

        # ---- chan sidebar: nguoi dung + canh bao ton kho + tien ich ----
        foot = tk.Frame(sidebar, bg=theme.SIDEBAR)
        foot.pack(side="bottom", fill="x", pady=14, padx=14)

        role_name = ROLES.get(self.user.get("role"), "Nhân viên")

        # 1. Tạo các Label hiển thị tên và vai trò
        lbl_user_name = tk.Label(foot, text=f"👤 {self.user.get('display_name', '')}",
                                 bg=theme.SIDEBAR, fg="#ffffff", font=theme.FONT_BOLD,
                                 anchor="w", cursor="hand2") # Thêm cursor tay chỉ
        lbl_user_name.pack(fill="x")
        
        lbl_role_name = tk.Label(foot, text=role_name, bg=theme.SIDEBAR,
                                 fg=theme.SIDEBAR_TEXT, font=theme.FONT_SMALL,
                                 anchor="w", cursor="hand2") # Thêm cursor tay chỉ
        lbl_role_name.pack(fill="x")

        # 2. Định nghĩa hàm mở bảng ProfileDialog khi click vào
        def open_profile(e=None):
            # self chính là cửa sổ MainWindow hiện tại
            dialog = ProfileDialog(self, self.user)
            self.wait_window(dialog) # Đợi khi dialog đóng thì có thể load lại thông tin nếu cần
            # (Tùy chọn) Cập nhật lại tên hiển thị ở sidebar nếu user vừa đổi tên xong:
            lbl_user_name.config(text=f"👤 {self.user.get('display_name', '')}")

        # 3. Gắn sự kiện click chuột trái vào tên, vai trò và cả khung chứa (foot hoặc tạo một sub-frame riêng nếu muốn)
        lbl_user_name.bind("<Button-1>", open_profile)
        lbl_role_name.bind("<Button-1>", open_profile)

        badge_row = tk.Frame(foot, bg=theme.SIDEBAR)
        badge_row.pack(fill="x", pady=(8, 10))
        self.badge_dot = tk.Label(badge_row, text="●", bg=theme.SIDEBAR,
                                  fg=theme.SUCCESS, font=(theme.FAMILY, 11))
        self.badge_dot.pack(side="left", padx=(0, 6))
        self.badge = tk.Label(badge_row, text="", bg=theme.SIDEBAR,
                              fg=theme.SIDEBAR_TEXT, font=theme.FONT_SMALL,
                              wraplength=140, justify="left", anchor="w")
        self.badge.pack(side="left", fill="x")
        if self.user.get("role") == "admin":
            # bam vao canh bao la nhay thang sang man Ton kho
            for widget in (self.badge, self.badge_dot):
                widget.configure(cursor="hand2")
                widget.bind("<Button-1>", lambda e: self.show("inventory"))

        dark = theme.MODE == "dark"
        self._link(foot, ("☀  Giao diện sáng" if dark else "🌙  Giao diện tối"),
                   self.toggle_theme)
        self._link(foot, "⏻  Đăng xuất", self.logout)

    def _link(self, parent, text: str, command) -> tk.Label:
        """Dong chu bam duoc o chan sidebar (nhe nhang hon nut)."""
        link = tk.Label(parent, text=text, bg=theme.SIDEBAR,
                        fg=theme.SIDEBAR_TEXT, font=theme.FONT_SMALL,
                        anchor="w", cursor="hand2")
        link.pack(fill="x", pady=1)
        link.bind("<Button-1>", lambda e: command())
        link.bind("<Enter>", lambda e: link.configure(fg="#ffffff"))
        link.bind("<Leave>", lambda e: link.configure(fg=theme.SIDEBAR_TEXT))
        return link

    def _nav_button(self, parent, key: str, label: str, icon: str) -> tk.Label:
        """Dung tk.Label chu khong dung ttk.Button: can doi mau nen theo
        trang thai hover / dang chon, ma ttk.Button khong cho to nen tu do."""
        item = tk.Label(parent, text=f"  {icon}   {label}", bg=theme.SIDEBAR,
                        fg=theme.SIDEBAR_TEXT, font=theme.FONT_BASE,
                        anchor="w", padx=10, pady=9, cursor="hand2")
        item.pack(fill="x", padx=10, pady=1)

        item.bind("<Button-1>", lambda e, k=key: self.show(k))
        item.bind("<Enter>", lambda e, w=item, k=key: self._hover(w, k, True))
        item.bind("<Leave>", lambda e, w=item, k=key: self._hover(w, k, False))
        return item

    def _hover(self, widget, key: str, entering: bool):
        if key == self.current:
            return
        widget.configure(bg=theme.SIDEBAR_HOVER if entering else theme.SIDEBAR)

    # ---------- che do sang / toi ----------

    def toggle_theme(self):
        mode = "light" if theme.MODE == "dark" else "dark"
        theme.set_mode(mode)
        save_setting("theme", mode)
        self._reset_ui()

    # ---------- dieu huong ----------

    def show(self, key: str):
        if key not in self.frames:
            return
        for other, button in self.buttons.items():
            active = other == key
            button.configure(
                bg=theme.PRIMARY if active else theme.SIDEBAR,
                fg=theme.SIDEBAR_ACTIVE_TEXT if active else theme.SIDEBAR_TEXT,
                font=theme.FONT_BOLD if active else theme.FONT_BASE,
            )
        self.current = key

        frame = self.frames[key]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()

        if self.is_camera_active and self.camera_widget:
            self.camera_widget.lift()

    # ---------- canh bao ton kho ----------

    def refresh_stock_badge(self):
        if not hasattr(self, "badge") or not self.badge.winfo_exists():
            return
        try:
            count = product_model.low_stock_count()
        except Exception:
            return
        self.badge.config(
            text=f"{count} sản phẩm sắp hết hàng" if count else "Tồn kho ổn định")
        self.badge_dot.config(fg=theme.DANGER if count else theme.SUCCESS)

    def _schedule_badge_refresh(self):
        """Cap nhat dinh ky. Dung root.after chu khong dung time.sleep,
        vi sleep se lam dong bang toan bo giao dien."""
        self.refresh_stock_badge()
        self._badge_job = self.after(60_000, self._schedule_badge_refresh)

    def toggle_gesture_camera(self, activate: bool):
        """Bật hoặc tắt hiển thị camera cử chỉ nổi trên giao diện"""
        if activate:
            if not self.is_camera_active:
                try:
                    from cvzone.HandTrackingModule import HandDetector
                    # Mở webcam (thử index 0, nếu lỗi thử 1)
                    self.cap = cv2.VideoCapture(0)
                    if not self.cap.isOpened():
                        self.cap = cv2.VideoCapture(1)
                    
                    if self.cap.isOpened():
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        # Khởi tạo detector với cấu hình chuẩn
                        self.hand_detector = HandDetector(detectionCon=0.8, maxHands=2)
                        self.is_camera_active = True
                        
                        # Hiển thị và đưa lên lớp trên cùng (không bị che bởi các trang khác)
                        self.camera_widget.place(relx=1.0, x=-25, y=25, anchor="ne", width=240, height=180)
                        self.camera_widget.lift()
                        
                        self._update_camera_frame()
                    else:
                        messagebox.showerror("Lỗi", "Không thể mở webcam!", parent=self)
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không khởi động được cử chỉ: {e}", parent=self)
        else:
            self.is_camera_active = False
            if self.cap:
                self.cap.release()
                self.cap = None
            if self.camera_widget:
                self.camera_widget.place_forget()

    def _update_camera_frame(self):
        """Vòng lặp xử lý khung hình camera mượt mà không làm đơ giao diện"""
        if not self.is_camera_active or not self.cap:
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            
            # --- THÊM ĐOẠN NÀY ĐỂ PYTHON NHẬN DIỆN ĐƯỢC CÁC MODULE TRONG THƯ MỤC GESTURE ---
            import sys
            import os
            gesture_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "utils", "detector_gesture")
            if gesture_dir not in sys.path:
                sys.path.append(gesture_dir)
            # --------------------------------------------------------------------------

            # Xử lý nhận diện bàn tay và điều khiển cử chỉ
            try:
                from draw_skeleton import draw_hand_skeleton
                from mouse_controller import control_mouse
                from sound_controller import check_control_sound
                
                hands_data = self.hand_detector.findHands(frame, draw=False)
                if isinstance(hands_data, tuple):
                    hands, frame = hands_data
                else:
                    hands = hands_data

                if hands:
                    for hand in hands:
                        draw_hand_skeleton(frame, hand["lmList"])
                    control_mouse(frame, hands[0], cam_w=640, cam_h=480, frame_r=120)
                if len(hands) >= 2:
                    check_control_sound(frame, hands)
            except Exception as e:
                print(f"Lỗi xử lý cử chỉ khung hình: {e}")

            # Đổi hệ màu BGR sang RGB để hiển thị lên Tkinter Label qua PIL
            cv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(cv_img).resize((240, 180))
            imgtk = ImageTk.PhotoImage(image=pil_img)
            
            self.camera_widget.imgtk = imgtk  
            self.camera_widget.configure(image=imgtk)
            self.camera_widget.lift()

        if self.is_camera_active:
            self.after(30, self._update_camera_frame)