"""Tab Tùy chọn: ngôn ngữ, khởi động, độ trễ, đặt lại cài đặt."""

import ctypes
import subprocess
import sys
import tkinter as tk
from ctypes import wintypes
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from .. import i18n
from ..base import APP_DIR, APP_NAME, APP_VERSION, ENTRY_SCRIPT
from ..winapi import show_real_cursor, user32
from ..syscursor import REAL_CURSOR_MODE
from ..startup import is_startup_enabled, set_startup
from ..i18n import LANGUAGES, T
from ..config import ProfileCfg, default_cfg, my_cursor_files
from ..colors import mix
from ..display import monitor_scale
from ..theme import ACCENT, CARD, CYAN, CYAN_TEXT, FIELD, LINE, MUTED, TEXT2


class OptionsMixin:
    def build_options_tab(self, parent):
        page = ctk.CTkFrame(parent, fg_color="transparent")
        self.header(page, "TÙY CHỌN", "Cài đặt chung, cập nhật và phím tắt.").pack(anchor="w", pady=(0, 8))
        box = self.card(page)
        box.pack(fill="x")

        def section(title):
            """Nhóm cài đặt: tiêu đề nhỏ + lưới hai cột."""
            self.caps(box, title).pack(anchor="w", padx=18, pady=(8, 0))
            grid = ctk.CTkFrame(box, fg_color="transparent")
            grid.pack(fill="x", padx=18)
            grid.grid_columnconfigure((0, 1), weight=1, uniform="o")
            return grid

        def place(grid, i, row):
            row.grid(row=i // 2, column=i % 2, sticky="ew", padx=(0, 28) if i % 2 == 0 else 0, pady=3)

        def toggles(grid, items, start=0):
            for i, (title, sub, var, cmd) in enumerate(items, start):
                place(grid, i, self.option_row(grid, title, sub, var, cmd, size=13)[0])

        self.hide_var = tk.BooleanVar(value=self.cfg["hide_real"])
        self.lock_var = tk.BooleanVar(value=self.cfg["lock_cursor"])
        self.taskbar_var = tk.BooleanVar(value=self.cfg["keep_taskbar"])
        self.predict_var = tk.BooleanVar(value=self.cfg["predict"])
        self.shake_var = tk.BooleanVar(value=self.cfg["find_shake"])
        self.startup_var = tk.BooleanVar(value=is_startup_enabled())
        self.auto_upd_var = tk.BooleanVar(value=self.cfg["auto_check_update"])
        self.splash_var = tk.BooleanVar(value=self.cfg["splash"])
        self.stream_var = tk.BooleanVar(value=self.stream is not None)

        game = section("TRONG GAME")
        if REAL_CURSOR_MODE:
            row, self.mode_sub = self.option_row(game, "Chế độ con trỏ", "", size=13)
            row.grid(row=9, column=0, columnspan=2, sticky="ew", pady=3)
            self.mode_map = {T("Lớp phủ"): "overlay", T("Con trỏ thật"): "system"}
            self.mode_seg = self.seg(row, list(self.mode_map), lambda v: self.set_cursor_mode(self.mode_map[v]),
                                     height=28)
            self.mode_seg.pack(side="right")
            self.update_mode_ui()
        toggles(game, [("Ẩn con trỏ thật của game", "Chỉ hiện con trỏ EzCursor trong game.",
                        self.hide_var, self.set_hide),
                       ("Giữ chuột trong cửa sổ game", "Không lỡ click sang màn hình khác.",
                        self.lock_var, self.set_lock_cursor),
                       ("Giữ con trỏ trên thanh taskbar", "Vẫn dùng con trỏ EzCursor trên taskbar.",
                        self.taskbar_var, self.set_keep_taskbar),
                       ("Đoán trước vị trí con trỏ", "Bù nửa khung hình khi rê nhanh.",
                        self.predict_var, self.set_predict),
                       ("Lắc chuột để tìm", "Lắc nhanh là con trỏ phóng to, dễ thấy.",
                        self.shake_var, self.set_find_shake)])

        app = section("ỨNG DỤNG")
        row, _ = self.option_row(app, "Ngôn ngữ", size=13)
        place(app, 0, row)
        self.lang_map = {name: code for code, name in LANGUAGES}
        self.lang_seg = self.seg(row, list(self.lang_map), lambda v: self.set_language(self.lang_map[v]), height=28)
        self.lang_seg.set(dict(LANGUAGES)[self.cfg["language"]])
        self.lang_seg.pack(side="right")
        toggles(app, [("Khởi động cùng Windows", "Chạy ngầm dưới khay khi bật máy.",
                       self.startup_var, self.set_startup_opt),
                      ("Tự động kiểm tra cập nhật", "Báo khi có phiên bản mới trên GitHub.",
                       self.auto_upd_var, self.set_auto_update),
                      ("Màn hình chào khi mở", "Logo động khoảng 2 giây.", self.splash_var, self.set_splash)], start=1)

        # Chế độ stream (OBS): link + nút sao chép chỉ hiện khi đang bật
        self.caps(box, "STREAM").pack(anchor="w", padx=18, pady=(8, 0))
        row, self.stream_sub = self.option_row(box, "Hiện con trỏ trên stream (OBS)", "", self.stream_var,
                                               self.set_stream, size=13)
        row.pack(fill="x", padx=18, pady=(3, 10))
        self.stream_copy = ctk.CTkButton(row, text=T("Sao chép link"), command=self.copy_stream_link, width=10,
                                         height=28, corner_radius=8, border_width=1, border_color=CYAN,
                                         fg_color=mix(CARD, CYAN, 0.10), hover_color=mix(CARD, CYAN, 0.22),
                                         text_color=CYAN_TEXT, font=self.F.b(12, strong=True))
        self.update_stream_ui()

        hk = self.card(page)
        hk.pack(fill="x", pady=(8, 0))
        head = ctk.CTkFrame(hk, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(10, 4))
        self.caps(head, "PHÍM TẮT").pack(side="left")
        ctk.CTkButton(head, text=T("Mặc định"), command=self.reset_hotkeys, width=10, height=24, corner_radius=6,
                      fg_color="transparent", hover_color="#1A1E29", text_color=MUTED,
                      font=self.F.b(12)).pack(side="right")
        ctk.CTkLabel(head, text=T("Bấm vào một ô để đổi phím"), font=self.F.b(12),
                     text_color=MUTED).pack(side="right", padx=8)
        grid = ctk.CTkFrame(hk, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 12))
        grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="h")
        self.hotkey_caps = {}
        keys = [("toggle", "Bật / tắt"), ("shape", "Đổi hình dạng"), ("color", "Đổi màu"), ("find", "Tìm con trỏ"),
                ("lock", "Giữ / thả chuột"), ("quit", "Thoát")]
        for i, (act, desc) in enumerate(keys):
            cell = ctk.CTkFrame(grid, fg_color=FIELD, border_color=LINE, border_width=1, corner_radius=10,
                                cursor="hand2")
            cell.grid(row=i // 3, column=i % 3, sticky="ew", padx=4, pady=4)
            lbl = ctk.CTkLabel(cell, text=T(desc), font=self.F.b(13), text_color="#C9CFDB")
            lbl.pack(side="left", padx=(12, 4), pady=10)
            caps = ctk.CTkFrame(cell, fg_color="transparent")
            caps.pack(side="right", padx=(0, 8))
            self.hotkey_caps[act] = caps
            for w in (cell, lbl, caps):
                w.bind("<Button-1>", lambda e, a=act: self.capture_hotkey(a))
                w.bind("<Enter>", lambda e, c=cell: c.configure(border_color=ACCENT))
                w.bind("<Leave>", lambda e, c=cell: c.configure(border_color=LINE))
        self.update_hotkey_ui()

        # Chân trang: phiên bản, cập nhật, log; khôi phục cài đặt gốc để nhỏ, tách riêng
        foot = ctk.CTkFrame(page, fg_color="transparent")
        foot.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(foot, text=T("Phiên bản "), font=self.F.b(12), text_color=TEXT2).pack(side="left", padx=(6, 0))
        ctk.CTkLabel(foot, text=APP_VERSION, font=self.F.m(12), text_color=ACCENT).pack(side="left")
        self.upd_label = ctk.CTkLabel(foot, text="", font=self.F.b(12), text_color=TEXT2)
        self.upd_label.pack(side="left", padx=(10, 0))
        for text, cmd, color in (("Khôi phục cài đặt gốc…", self.reset_settings, "#FF8A8A"),
                                 ("Mở thư mục log", self.open_log_folder, CYAN_TEXT),
                                 ("Kiểm tra cập nhật", lambda: self.check_update(manual=True), CYAN_TEXT)):
            ctk.CTkButton(foot, text=T(text), command=cmd, width=10, height=26, corner_radius=6,
                          fg_color="transparent", hover_color="#1A1E29", text_color=color,
                          font=self.F.b(12, strong=True)).pack(side="right")
        return page

    def set_find_shake(self):
        self.cfg["find_shake"] = bool(self.shake_var.get())
        self.sh_rev = []
        self.save()

    def set_dpi_scale(self):
        self.cfg["dpi_scale"] = bool(self.dpi_var.get())
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        self.cur_scale = monitor_scale(pt.x, pt.y)
        self.refresh()

    def check_monitor(self):
        """Đổi kích thước con trỏ khi chuột sang màn hình có tỉ lệ khác (nếu bật)."""
        if not self.cfg["dpi_scale"]:
            return
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        sc = monitor_scale(pt.x, pt.y)
        if abs(sc - self.cur_scale) > 0.01:
            self.cur_scale = sc
            self.rebuild_overlay()
            self.update_preview()
            if self.active:
                self.move_overlay()

    def update_mode_ui(self):
        try:
            sysm = self.system_mode()
            self.mode_seg.set({v: k for k, v in self.mode_map.items()}[self.cfg["cursor_mode"]])
            self.mode_sub.configure(text=T("Không độ trễ, chạy cả Fullscreen. Không có lấp lánh, ombre chuyển động.")
                                    if sysm else T("Đủ hiệu ứng. Game cần chạy Borderless hoặc Windowed."))
        except (AttributeError, tk.TclError):
            pass

    def set_hide(self):
        self.cfg["hide_real"] = bool(self.hide_var.get())
        show_real_cursor(not (self.active and self.cfg["hide_real"]))
        self.save()

    def set_startup_opt(self):
        try:
            set_startup(self.startup_var.get())
        except Exception as e:
            messagebox.showerror(T("Lỗi"), T("Không thay đổi được cài đặt khởi động:") + f"\n{e}", parent=self.win)
            self.startup_var.set(is_startup_enabled())

    def reset_settings(self):
        if not messagebox.askyesno(APP_NAME, T("Khôi phục toàn bộ cài đặt về mặc định?\n\n"
                                     "Danh sách game, con trỏ, hiệu ứng và ảnh đã tải lên sẽ bị xóa. "
                                     "EzCursor sẽ tự khởi động lại."), parent=self.win):
            return
        for f in list(APP_DIR.glob("custom*.*")) + list(my_cursor_files()):
            try:
                f.unlink()
            except OSError:
                pass
        self.cfg = ProfileCfg(default_cfg())
        self.enabled = True
        self.save()
        if getattr(sys, "frozen", False):
            args = f'"{sys.executable}"'
        else:
            pyw = Path(sys.executable).with_name("pythonw.exe")
            args = f'"{pyw if pyw.exists() else sys.executable}" "{ENTRY_SCRIPT}"'
        # đợi bản hiện tại thoát hẳn rồi mới mở lại
        subprocess.Popen(f'cmd /c timeout /t 2 /nobreak >nul & start "" {args}',
                         shell=True, creationflags=0x08000000)
        self.quit()

    def set_language(self, code):
        """Đổi ngôn ngữ giao diện và dựng lại toàn bộ giao diện ngay, không cần khởi động lại."""
        if code == self.cfg["language"]:
            return
        self.cfg["language"] = code
        i18n.LANG = code
        self.save()
        self.win.after(20, self.rebuild_ui)

    def rebuild_ui(self):
        tab = self.tab
        for w in self.win.winfo_children():
            w.destroy()
        self.profile_menus = []
        self.build_ui()
        self.refresh_apps()
        self.refresh()
        self.show_tab(tab)
        try:
            self.icon.update_menu()
        except Exception:
            pass

    def set_predict(self):
        self.cfg["predict"] = bool(self.predict_var.get())
        self.save()
        self.move_overlay()

    def set_keep_taskbar(self):
        self.cfg["keep_taskbar"] = bool(self.taskbar_var.get())
        self.save()

    def set_lock_cursor(self):
        self.cfg["lock_cursor"] = bool(self.lock_var.get())
        self.save()

    def set_splash(self):
        self.cfg["splash"] = bool(self.splash_var.get())
        self.save()
