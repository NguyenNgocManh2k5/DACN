"""Man cai dat: sao luu / khoi phuc du lieu, quan ly tai khoan dang nhap.

Chi danh cho Quan ly (menu da loc theo vai tro o main_window). Restore la
thao tac PHA HUY: ghi de toan bo du lieu hien tai, nen doi hoi go dung chu
"XAC NHAN" thay vi mot cai click Yes/No de tranh bam nham.
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from app.config import EXPORTS_DIR
from app.models import user as user_model
from app.services import audit_service, auth_service, backup_service
from app.services.auth_service import ROLES
from app.utils.validators import ValidationError, require_text
from app.utils.detector_product import product_detector
from app.views import theme, widgets
from app.views.base_frame import BaseFrame, make_title
from app.utils.formatters import money

USER_COLUMNS = [
    ("username", "Tên đăng nhập", 160),
    ("display_name", "Họ tên hiển thị", 220),
    ("role", "Vai trò", 120),
]


class SettingsView(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)

        make_title(self, "Cài đặt", "")

        # --- Điều khiển qua cử chỉ, Nhập hàng
        # , Bán hàng ---
        gesture_container = ttk.Frame(self)
        gesture_container.pack(fill="x")

        # --- Khởi tạo các biến trạng thái bật/tắt (BooleanVar) cho cử chỉ ---
        self.var_gesture_main = tk.BooleanVar(value=False)
        self.var_gesture_import = tk.BooleanVar(value=False)
        self.var_gesture_sales = tk.BooleanVar(value=False)

        # --- 3 Dòng Điều khiển qua cử chỉ, Nhập hàng, Bán hàng (Click được vào cả Nhãn & Nút) ---
        gesture_container = ttk.Frame(self)
        gesture_container.pack(fill="x", pady=(0, 16))

        # 1. Điều khiển qua cử chỉ
        self._create_toggle_row(
            gesture_container, 
            text="Điều khiển qua cử chỉ", 
            variable=self.var_gesture_main,
            command=lambda: self._on_toggle_changed("main", self.var_gesture_main.get())
        )

        # --- Khung chứa các nút quét sản phẩm AI (Bán hàng / Nhập hàng) ---
        scan_frame = ttk.LabelFrame(self, text="Nhận diện sản phẩm bằng AI (Webcam)", padding=16)
        scan_frame.pack(fill="x", pady=(0, 16))

        ttk.Label(
            scan_frame, 
            text="Bấm vào các nút bên dưới để mở cửa sổ camera quét sản phẩm. Hệ thống sẽ tự động nhận diện và thêm vào giỏ hàng hoặc phiếu nhập.",
            style="Muted.TLabel", wraplength=640, justify="left"
        ).pack(anchor="w", pady=(0, 12))

        btn_box = ttk.Frame(scan_frame)
        btn_box.pack(anchor="w")

        # Nút quét Bán hàng
        ttk.Button(
            btn_box, 
            text="📷 Quét sản phẩm Bán hàng", 
            style="Accent.TButton",
            command=lambda: self.run_scanner("sales")
        ).pack(side="left", padx=(0, 10))

        # Nút quét Nhập hàng
        ttk.Button(
            btn_box, 
            text="📷 Quét sản phẩm Nhập hàng", 
            style="Accent.TButton",
            command=lambda: self.run_scanner("import")
        ).pack(side="left")

        # Sao luu
        section = ttk.LabelFrame(self, text="Sao lưu & khôi phục dữ liệu",
                                 padding=16)
        section.pack(fill="x", pady=(12, 12))

        ttk.Label(section,
                  text="Sao lưu xuất toàn bộ dữ liệu (sản phẩm, hóa đơn, khách "
                       "hàng, tài khoản...) ra một file JSON trong thư mục "
                       "exports/. Khôi phục sẽ GHI ĐÈ toàn bộ dữ liệu hiện tại "
                       "bằng nội dung file đã chọn — nhớ chọn đúng file.",
                  style="Muted.TLabel", wraplength=640, justify="left").pack(
            anchor="w", pady=(0, 12))

        buttons = ttk.Frame(section)
        buttons.pack(anchor="w")
        ttk.Button(buttons, text="Sao lưu ngay", style="Accent.TButton",
                   command=self.do_backup).pack(side="left")
        ttk.Button(buttons, text="Khôi phục từ file...", style="Danger.TButton",
                   command=self.do_restore).pack(side="left", padx=8)

        self.last_label = ttk.Label(section, text="", style="Muted.TLabel")
        self.last_label.pack(anchor="w", pady=(10, 0))

        self._build_users_section()

    def _create_toggle_row(self, parent, text, variable, command):
        """Hàm phụ trợ tạo một hàng gồm Nhãn và Nút Toggle đồng bộ trạng thái khi click"""
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)

        def _update_button_style(is_active):
            if is_active:
                # Trạng thái Bật: Đổi sang màu Xanh (Accent)
                btn.config(text="Bật", style="Accent.TButton")
            else:
                # Trạng thái Tắt: Đổi sang màu Đỏ/Cảnh báo (Danger)
                btn.config(text="Tắt", style="Danger.TButton")

        # Hàm xử lý đảo trạng thái khi click vào nhãn hoặc nút
        def toggle_action(event=None):
            new_val = not variable.get()
            variable.set(new_val)
            _update_button_style(new_val)
            # Cập nhật chữ hiển thị trên nút dựa vào trạng thái mới
            btn.config(text="Bật" if new_val else "Tắt")
            if command:
                command()

        # Nhãn văn bản (gắn sự kiện click chuột trái <Button-1>)
        label_font = getattr(theme, 'FONT_BOLD', ('Arial', 10, 'bold'))
        lbl = ttk.Label(row, text=text, width=22, font=label_font, anchor="w", cursor="hand2")
        lbl.pack(side="left")
        lbl.bind("<Button-1>", toggle_action)

        # Nút bấm dạng Toggle (khởi tạo ban đầu theo giá trị của biến)
        initial_val = variable.get()
        btn = ttk.Button(row, width=10, command=toggle_action)
        _update_button_style(initial_val)  # Thiết lập màu sắc ban đầu cho đúng với biến
        btn.pack(side="left")
        
        # Lưu lại reference của button để nếu cần đồng bộ từ bên ngoài
        return btn

    def _handle_detected_product(self, mode, product_label):
        """Hàm callback xử lý khi AI nhận diện được sản phẩm qua camera độc lập"""
        try:
            import winsound
            winsound.Beep(2500, 300)
        except Exception:
            print("\a")

        product = None
        clean_label = str(product_label).strip().lower()

        try:
            from app.database.connection import get_db
            db = get_db()
            if db is not None:
                import re
                safe_pattern = re.compile(r"^\s*" + re.escape(clean_label) + r"\s*$", re.IGNORECASE)
                product = db.products.find_one({"label": safe_pattern})
        except Exception as e:
            print(f"[Lỗi] Truy vấn CSDL thất bại: {e}")

        if product:
            product_name = product.get("name", clean_label)

            def update_ui_cart():
                try:
                    if mode == "sales":
                        # Lấy SalesView từ từ điển self.frames của MainWindow
                        sales_v = self.app.frames.get("sales")
                        if sales_v and hasattr(sales_v, "cart"):
                            sales_v.cart.add(product, quantity=1)
                            if hasattr(sales_v, "refresh_cart"):
                                sales_v.refresh_cart()
                            widgets.toast(self, f"Đã thêm sản phẩm {product_name} vào giỏ hàng.")
                            print(f"[Giỏ hàng] Đã thêm {product_name} vào giỏ hàng.")

                    elif mode == "import":
                        # Lấy PurchaseView từ từ điển self.frames của MainWindow
                        purchase_v = self.app.frames.get("purchases")
                        if purchase_v and hasattr(purchase_v, "cart"):
                            unit_cost = product.get("cost", 0) or product.get("price", 0)
                            purchase_v.cart.add(product, quantity=1, unit_cost=unit_cost)
                            if hasattr(purchase_v, "refresh_receipt"):
                                purchase_v.refresh_receipt()
                            widgets.toast(self, f"Đã thêm sản phẩm {product_name} vào phiếu nhập.")
                            print(f"[Phiếu nhập] Đã thêm {product_name} vào phiếu nhập.")
                except Exception as ex:
                    print(f"[Lỗi cập nhật giỏ hàng]: {ex}")

            # Gọi an toàn trên luồng chính bằng self.app.after
            self.app.after(0, update_ui_cart)
        else:
            widgets.toast(self, f"Nhận diện được '{product_label}' nhưng chưa gán nhãn trong CSDL.")

    def run_scanner(self, mode: str):
        """Mở trực tiếp camera quét sản phẩm theo chế độ ('sales' hoặc 'import')"""
        try:
            product_detector.start(mode=mode, callback=self._handle_detected_product)
        except Exception as exc:
            messagebox.showerror("Lỗi", f"Không thể mở camera quét:\n{exc}", parent=self)

    def _on_toggle_changed(self, feature_type, is_active):
        """Xử lý logic khi bật/tắt tính năng cử chỉ"""
        if feature_type == "main":
            if hasattr(self.app, "toggle_gesture_camera"):
                self.app.toggle_gesture_camera(is_active)
            if is_active:
                widgets.toast(self, "Đã bật điều khiển qua cử chỉ")
            else:
                widgets.toast(self, "Đã tắt điều khiển qua cử chỉ")

    def _build_users_section(self):
        section = ttk.LabelFrame(self, text="Tài khoản đăng nhập", padding=16)
        section.pack(fill="both", expand=True)

        ttk.Label(section,
                  text="Tạo tài khoản mới cho nhân viên hoặc quản lý khác. "
                       "Mật khẩu được băm PBKDF2, không ai xem lại được kể "
                       "cả admin.",
                  style="Muted.TLabel", wraplength=640, justify="left").pack(
            anchor="w", pady=(0, 10))

        table = ttk.Frame(section)
        table.pack(fill="both", expand=True)

        self.user_tree = ttk.Treeview(
            table, columns=[c[0] for c in USER_COLUMNS], show="headings",
            height=6)
        for key, title, width in USER_COLUMNS:
            self.user_tree.heading(key, text=title)
            self.user_tree.column(key, width=width, anchor="w")

        scroll = ttk.Scrollbar(table, orient="vertical",
                               command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=scroll.set)
        self.user_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        widgets.add_grid_lines(self.user_tree, stretch_column="display_name")

        theme.configure_stripes(self.user_tree)

        ttk.Button(section, text="Tạo tài khoản mới", style="Accent.TButton",
                   command=self.create_user).pack(anchor="w", pady=(10, 0))

    def on_show(self):
        self._refresh_last_backup()
        self._reload_users()

    def _reload_users(self):
        self.user_tree.delete(*self.user_tree.get_children())
        for user in user_model.list_all():
            self.user_tree.insert(
                "", "end", iid=user["username"],
                values=(user["username"], user.get("display_name", ""),
                        ROLES.get(user.get("role"), user.get("role", ""))),
            )
        theme.stripe_rows(self.user_tree)

    def create_user(self):
        dialog = CreateUserDialog(self)
        self.wait_window(dialog)
        if dialog.created_username:
            audit_service.log("Tạo tài khoản",
                              f"{dialog.created_username} "
                              f"({ROLES.get(dialog.created_role, '')})")
            widgets.toast(self, f"Đã tạo tài khoản \"{dialog.created_username}\"")
            self._reload_users()

    def _refresh_last_backup(self):
        files = sorted(EXPORTS_DIR.glob("backup_*.json"),
                       key=lambda p: p.stat().st_mtime, reverse=True) \
                if EXPORTS_DIR.exists() else []
        self.last_label.config(
            text=f"Lần sao lưu gần nhất: {files[0].name}" if files
                 else "Chưa có bản sao lưu nào.")

    def do_backup(self):
        try:
            path = backup_service.backup()
        except Exception as exc:
            messagebox.showerror("Lỗi", f"Không sao lưu được:\n{exc}")
            return

        self._refresh_last_backup()
        open_it = messagebox.askyesno(
            "Đã sao lưu", f"Đã lưu vào:\n{path}\n\nMở thư mục chứa file?")
        if open_it:
            try:
                os.startfile(path.parent)
            except OSError as exc:
                messagebox.showwarning("Không mở được", str(exc))

    def do_restore(self):
        path = filedialog.askopenfilename(
            title="Chọn file backup",
            initialdir=str(EXPORTS_DIR),
            filetypes=[("Backup JSON", "*.json")],
        )
        if not path:
            return

        warn = messagebox.askyesno(
            "CẢNH BÁO — Ghi đè dữ liệu",
            "Khôi phục sẽ XÓA TOÀN BỘ dữ liệu hiện tại và thay bằng nội dung "
            f"file:\n{path}\n\n"
            "Ứng dụng sẽ tự sao lưu dữ liệu hiện tại trước khi ghi đè, "
            "nhưng thao tác này vẫn nên cân nhắc kỹ.\n\nTiếp tục?",
            icon="warning",
        )
        if not warn:
            return

        confirm = simpledialog.askstring(
            "Xác nhận lần cuối",
            "Gõ chính xác XAC NHAN (không dấu, chữ hoa) để khôi phục:",
            parent=self)
        if confirm != "XAC NHAN":
            messagebox.showinfo("Đã hủy", "Không khớp — đã hủy khôi phục.")
            return

        try:
            counts = backup_service.restore(path)
        except Exception as exc:
            messagebox.showerror("Lỗi", f"Không khôi phục được:\n{exc}")
            return

        self._refresh_last_backup()
        detail = "\n".join(f"  {name}: {n}" for name, n in counts.items() if n)
        messagebox.showinfo(
            "Đã khôi phục",
            f"Khôi phục thành công.\n\n{detail}\n\n"
            "Hãy khởi động lại ứng dụng để tải lại toàn bộ giao diện.")


class CreateUserDialog(tk.Toplevel):
    """Tao tai khoan dang nhap moi (nhan vien hoac quan ly). Chi Quan ly moi
    mo duoc man Cai dat nen khong can kiem tra quyen lai o day."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Tạo tài khoản mới")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.configure(background=theme.BG)
        self.created_username = None
        self.created_role = None

        body = ttk.Frame(self, padding=18)
        body.pack(fill="both", expand=True)

        self.fields = {}
        for key, label in [("username", "Tên đăng nhập"),
                           ("display_name", "Họ tên hiển thị"),
                           ("password", "Mật khẩu")]:
            ttk.Label(body, text=label).pack(anchor="w", pady=(4, 0))
            entry = ttk.Entry(body, width=32,
                              show="*" if key == "password" else "")
            entry.pack(fill="x")
            self.fields[key] = entry

        ttk.Label(body, text="Vai trò").pack(anchor="w", pady=(4, 0))
        self.role_box = ttk.Combobox(body, width=29, state="readonly",
                                     values=list(ROLES.values()))
        self.role_box.set(ROLES["staff"])
        self.role_box.pack(fill="x", pady=(0, 10))

        buttons = ttk.Frame(body)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Tạo tài khoản", style="Accent.TButton",
                   command=self._save).pack(side="left", expand=True,
                                            fill="x", padx=(0, 4))
        ttk.Button(buttons, text="Hủy", command=self.destroy).pack(
            side="left", expand=True, fill="x")

        self.bind("<Escape>", lambda e: self.destroy())
        self.fields["username"].focus_set()
        self.grab_set()

    def _save(self):
        try:
            username = require_text(self.fields["username"].get(),
                                    "Tên đăng nhập", max_len=40)
            display_name = require_text(self.fields["display_name"].get(),
                                        "Họ tên hiển thị")
            password = self.fields["password"].get()
            if len(password) < 4:
                raise ValidationError("Mật khẩu phải có ít nhất 4 ký tự.")
        except ValidationError as exc:
            messagebox.showwarning("Dữ liệu không hợp lệ", str(exc), parent=self)
            return

        role = next((k for k, v in ROLES.items() if v == self.role_box.get()),
                   "staff")

        try:
            auth_service.create_user(username, password, display_name, role)
        except ValueError as exc:
            messagebox.showwarning("Không tạo được", str(exc), parent=self)
            return

        self.created_username = username.strip().lower()
        self.created_role = role
        self.destroy()
