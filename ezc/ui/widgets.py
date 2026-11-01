"""Khối giao diện dùng chung (thẻ, công tắc, nút, tiêu đề trang)."""

import customtkinter as ctk

from ..i18n import T
from ..colors import mix
from ..theme import ACCENT, BORDER, CARD, CYAN, CYAN_TEXT, FIELD, MUTED, TEXT, TEXT2
from ..icons import simple_icon


class WidgetsMixin:
    def caps(self, parent, text, color=MUTED):
        return ctk.CTkLabel(parent, text=T(text), font=self.F.h(11, bold=False), text_color=color)

    def card(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color=CARD, border_color=BORDER, border_width=1, corner_radius=14, **kw)

    def switch(self, parent, var, command):
        return ctk.CTkSwitch(parent, text="", variable=var, command=command, width=50,
                             switch_width=46, switch_height=24, progress_color=ACCENT, fg_color="#1A1E29",
                             button_color="#FFFFFF", button_hover_color="#FFFFFF", border_color="#3A4152")

    def cyan_button(self, parent, text, command, icon=None):
        return ctk.CTkButton(parent, text=T(text), command=command, image=icon, compound="left",
                             height=40, corner_radius=10, border_width=1, border_color=CYAN,
                             fg_color=mix(CARD, CYAN, 0.10), hover_color=mix(CARD, CYAN, 0.22),
                             text_color=CYAN_TEXT, font=self.F.b(13, strong=True))

    def header(self, parent, title, sub):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(f, text=T(title), font=self.F.h(24), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(f, text=T(sub), font=self.F.b(13), text_color=TEXT2).pack(anchor="w")
        return f

    def page_top(self, page, title, sub, pady):
        """Tiêu đề tab kèm ô chọn hồ sơ đang chỉnh."""
        top = ctk.CTkFrame(page, fg_color="transparent")
        top.pack(fill="x", pady=pady)
        self.header(top, title, sub).pack(side="left", anchor="w")
        box = ctk.CTkFrame(top, fg_color="transparent")
        box.pack(side="right", anchor="s")
        ctk.CTkLabel(box, text=T("Đang chỉnh"), font=self.F.b(11), text_color=MUTED, height=14).pack(anchor="w")
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(anchor="w")
        menu = ctk.CTkOptionMenu(row, values=[""], command=self.pick_profile, width=210, height=32,
                                 corner_radius=8, fg_color=FIELD, button_color=mix(CARD, ACCENT, 0.35),
                                 button_hover_color=mix(CARD, ACCENT, 0.5), text_color=TEXT,
                                 dropdown_fg_color=CARD, dropdown_hover_color=mix(CARD, ACCENT, 0.2),
                                 dropdown_text_color=TEXT, font=self.F.b(12, strong=True),
                                 dropdown_font=self.F.b(12), dynamic_resizing=False)
        menu.pack(side="left")
        rm = ctk.CTkButton(row, text="", width=32, height=32, corner_radius=8, fg_color="transparent",
                           hover_color=mix(CARD, "#FF5A5A", 0.22), border_width=1, border_color=BORDER,
                           image=ctk.CTkImage(simple_icon("trash", "#FF8A8A", 32), size=(14, 14)),
                           command=self.delete_profile)
        self.profile_menus.append((menu, rm))
        return top

    def seg(self, parent, values, command, height=32, size=12, strong=True):
        """Nút chọn một trong nhiều lựa chọn, cùng kiểu trên mọi tab."""
        return ctk.CTkSegmentedButton(parent, values=values, command=command, height=height,
                                      font=self.F.b(size, strong=strong), fg_color=FIELD, unselected_color=FIELD,
                                      unselected_hover_color="#1A1E29", selected_color=mix(CARD, ACCENT, 0.35),
                                      selected_hover_color=mix(CARD, ACCENT, 0.45), text_color=TEXT)

    @staticmethod
    def tile_style(b, on, idle=FIELD, text=TEXT2):
        """Ô chọn (con trỏ, hiệu ứng...): nền và viền nổi lên khi đang chọn."""
        b.configure(fg_color=mix(CARD, ACCENT, 0.16) if on else idle,
                    hover_color=mix(CARD, ACCENT, 0.24) if on else "#161A23",
                    border_color=ACCENT if on else BORDER, text_color="#FFFFFF" if on else text)

    def option_row(self, parent, title, sub=None, var=None, command=None, size=14):
        """Hàng cài đặt: tiêu đề (+ mô tả) bên trái, công tắc bên phải nếu có var.
        Trả về (hàng, nhãn mô tả) để đặt thêm nút hoặc đổi mô tả về sau."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        text = ctk.CTkFrame(row, fg_color="transparent")
        text.pack(side="left")
        ctk.CTkLabel(text, text=T(title), font=self.F.b(size, strong=size >= 14), text_color=TEXT,
                     height=20).pack(anchor="w")
        sub_lbl = None
        if sub is not None:
            sub_lbl = ctk.CTkLabel(text, text=T(sub) if sub else "", font=self.F.b(11), text_color=TEXT2, height=16)
            sub_lbl.pack(anchor="w")
        if var is not None:
            self.switch(row, var, command).pack(side="right")
        return row, sub_lbl
