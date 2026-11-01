"""Tab Bộ sưu tập: bộ EzCursor, Bibata, con trỏ của bạn, kho trực tuyến, Yêu thích."""

import webbrowser
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser

import customtkinter as ctk
from PIL import Image

from ..base import MY_DIR
from ..i18n import T
from ..config import my_cursor_files
from ..colors import mix
from ..ombre import apply_ombre, ombre_lut, ombre_tmap
from ..maker import maker_render
from ..curfile import load_cursor_file
from ..theme import ACCENT, BORDER, CARD, CYAN, CYAN_TEXT, FIELD, TEXT, TEXT2
from ..icons import simple_icon, star_icon
from ..bibata import (
    BIBATA_CURSORS, BIBATA_DIR, BIBATA_META, BIBATA_THEMES, OWN_BY_ID, OWN_CURSORS, bibata_colors,
    bibata_image, own_image, own_image_colored)


class LibraryMixin:
    def build_library_tab(self, parent):
        page = ctk.CTkFrame(parent, fg_color="transparent")
        self.page_top(page, "BỘ SƯU TẬP", "Bấm vào con trỏ muốn dùng, bấm ☆ để thêm vào Yêu thích.", (0, 8))
        self.bib_tiles, self.own_tiles, self.fav_tiles, self.fav_stars = {}, {}, {}, {}
        self._fav_sig = self._fav_job = None
        if getattr(self, "lib_view", None) is None:
            self.lib_view = {"Bibata": "bibata", "Ảnh tải lên": "mine"}.get(self.cfg["shape"], "ez")
        has_bib = BIBATA_DIR.exists()

        # Hàng tab: mỗi bộ con trỏ một tab, tab đang xem được gạch chân
        self.view_map = {"ez": T("Bộ EzCursor"), "bibata": "Bibata", "mine": T("Của bạn"),
                         "online": T("Trực tuyến"), "fav": T("★ Yêu thích")}
        if not has_bib:
            del self.view_map["bibata"]
        tabs = ctk.CTkFrame(page, fg_color="transparent")
        tabs.pack(fill="x")
        ctk.CTkFrame(page, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")
        self.view_tabs = {}
        for view, label in self.view_map.items():
            col = ctk.CTkFrame(tabs, fg_color="transparent")
            col.pack(side="left", padx=(0, 14))
            b = ctk.CTkButton(col, text=label, width=10, height=30, corner_radius=6, fg_color="transparent",
                              hover_color=CARD, font=self.F.b(14, strong=True),
                              command=lambda v=view: self.set_lib_view(v))
            b.pack()
            bar = ctk.CTkFrame(col, width=1, height=2, corner_radius=0, fg_color="transparent")
            bar.pack(fill="x")
            self.view_tabs[view] = (b, bar)

        # Thanh công cụ riêng từng tab: chủ đề màu, nút sửa / xóa, làm mới kho...
        tools = ctk.CTkFrame(page, fg_color="transparent")
        tools.pack(fill="x", pady=10)
        self.tool_rows = {view: ctk.CTkFrame(tools, fg_color="transparent") for view in self.view_map}
        self.theme_maps = {"ez": {T("Màu gốc"): "original", T("Tùy chỉnh"): "custom", "Ombre": "ombre"},
                           "bibata": {**{v[0]: k for k, v in BIBATA_THEMES.items()}, T("Tùy chỉnh"): "custom",
                                      "Ombre": "ombre"},
                           "mine": {T("Màu gốc"): "original", T("Tô màu"): "tint", "Ombre": "ombre"}}
        self.theme_segs, self.color_btns = {}, []
        for view, themes in self.theme_maps.items():
            if view not in self.tool_rows:
                continue
            row = self.tool_rows[view]
            self.theme_segs[view] = self.seg(row, list(themes), height=30, command=lambda v, view=view: (
                self.set_lib_theme(view, self.theme_maps[view][v])))
            self.theme_segs[view].pack(side="left")
            # màu cho chủ đề Tùy chỉnh (cũng là màu ở tab Con trỏ); bấm để chọn màu khác
            b = ctk.CTkButton(row, text="", width=30, height=30, corner_radius=15, border_width=2,
                              border_color="#FFFFFF", command=self.pick_bib_color)
            b.pack(side="left", padx=(10, 0))
            self.color_btns.append(b)
        self.mine_del = ctk.CTkButton(self.tool_rows["mine"], text=T("Xóa con trỏ này"), command=self.delete_my_cursor,
                                      height=30, corner_radius=8, border_width=1, border_color="#FF5A5A",
                                      fg_color=mix(CARD, "#FF5A5A", 0.10), hover_color=mix(CARD, "#FF5A5A", 0.22),
                                      text_color="#FF8A8A", font=self.F.b(12, strong=True),
                                      image=ctk.CTkImage(simple_icon("trash", "#FF8A8A", 32), size=(14, 14)))
        self.mine_del.pack(side="right")
        self.mine_edit = ctk.CTkButton(self.tool_rows["mine"], text=T("Sửa con trỏ này"), command=self.edit_made_cursor,
                                       height=30, corner_radius=8, border_width=1, border_color=ACCENT,
                                       fg_color=mix(CARD, ACCENT, 0.10), hover_color=mix(CARD, ACCENT, 0.22),
                                       text_color="#FFFFFF", font=self.F.b(12, strong=True))
        self.mine_edit.pack(side="right", padx=(0, 8))
        self.cyan_button(self.tool_rows["online"], "Làm mới", lambda: self.start_catalog(force=True),
                         ctk.CTkImage(simple_icon("refresh", CYAN_TEXT, 32), size=(16, 16))).pack(side="left")
        self.cat_label = ctk.CTkLabel(self.tool_rows["online"], text="", font=self.F.b(12), text_color=TEXT2,
                                      wraplength=520, justify="left")
        self.cat_label.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(self.tool_rows["fav"], text=T("Ctrl+Alt+R đổi lần lượt giữa các con trỏ yêu thích."),
                     font=self.F.b(12), text_color=TEXT2, height=30).pack(side="left")

        grid = self.card(page)
        grid.pack(fill="both", expand=True)
        cols = 5
        self.lib_grids = {}
        for view in self.view_map:
            if view in ("mine", "online", "fav"):
                inner = ctk.CTkScrollableFrame(grid, fg_color="transparent", scrollbar_button_color=BORDER,
                                               scrollbar_button_hover_color="#3A4152")
            else:
                inner = ctk.CTkFrame(grid, fg_color="transparent")
            for i in range(cols):
                inner.grid_columnconfigure(i, weight=1, uniform="t")
            self.lib_grids[view] = inner
        self.mine_tiles = {}
        self.star_btns = {}
        for shape, label, _f, _h, _g in OWN_CURSORS:
            if own_image(shape) is None:
                continue
            n = len(self.own_tiles)
            b = ctk.CTkButton(self.lib_grids["ez"], text=T(label), compound="top", height=94, width=10,
                              corner_radius=12, border_width=1, font=self.F.b(12, strong=True),
                              command=lambda sh=shape: self.pick_own(sh))
            b.grid(row=n // cols, column=n % cols, sticky="ew", padx=4, pady=4)
            self.own_tiles[shape] = b
            self.add_star(b, shape)
        if has_bib:
            for i, (name, label) in enumerate(BIBATA_CURSORS):
                b = ctk.CTkButton(self.lib_grids["bibata"], text=T(label), compound="top", height=94, width=10,
                                  corner_radius=12, border_width=1, font=self.F.b(12),
                                  command=lambda n=name: self.pick_bibata(n))
                b.grid(row=i // cols, column=i % cols, sticky="ew", padx=4, pady=4)
                self.bib_tiles[name] = b
                self.add_star(b, "bib:" + name)

        # Dưới lưới Bibata: kiểu bo góc, tay thuận và ghi công tác giả
        self.lib_foot = ctk.CTkFrame(page, fg_color="transparent")
        self.style_map = {T("Modern · bo tròn"): "modern", T("Original · góc nhọn"): "original"}
        self.hand_map = {T("Thuận tay phải"): "right", T("Thuận tay trái"): "left"}
        self.style_seg = self.seg(self.lib_foot, list(self.style_map), height=30,
                                  command=lambda v: self.set_bib("bibata_style", self.style_map[v]))
        self.style_seg.pack(side="left")
        self.hand_seg = self.seg(self.lib_foot, list(self.hand_map), height=30,
                                 command=lambda v: self.set_bib("bibata_hand", self.hand_map[v]))
        self.hand_seg.pack(side="left", padx=(8, 0))
        self.style_seg.set({v: k for k, v in self.style_map.items()}.get(self.cfg["bibata_style"], T("Modern · bo tròn")))
        self.hand_seg.set({v: k for k, v in self.hand_map.items()}.get(self.cfg["bibata_hand"], T("Thuận tay phải")))
        link = ctk.CTkLabel(self.lib_foot, text="Bibata © Abdulkaiz Khatri · GPL-3.0", font=self.F.b(12),
                            text_color=CYAN_TEXT, cursor="hand2")
        link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/ful1e5/Bibata_Cursor"))
        link.pack(side="right")
        self._lib_sig = None
        self._own_sig = None
        self.rebuild_mine_tiles()
        self.cat_tiles = {}
        self.build_online_tiles()
        self.show_lib_view()
        return page

    def rebuild_mine_tiles(self):
        """Dựng lại lưới "Của bạn": ô Thêm + mỗi con trỏ đã lưu."""
        self.mine_sig += 1
        grid = getattr(self, "lib_grids", {}).get("mine")
        if grid is None:
            return
        for w in grid.winfo_children():
            w.destroy()
        self.mine_tiles = {}
        self.star_btns = {k: v for k, v in getattr(self, "star_btns", {}).items() if not k.startswith("my:")}
        cols = 5
        make = ctk.CTkButton(grid, text=T("✦ Tạo con trỏ"), compound="top", height=94, width=10, corner_radius=12,
                             border_width=1, border_color=mix(BORDER, ACCENT, 0.6), fg_color=mix(CARD, ACCENT, 0.08),
                             hover_color=mix(CARD, ACCENT, 0.18), text_color="#FFFFFF", font=self.F.b(12, strong=True),
                             image=ctk.CTkImage(maker_render({"fill": "ombre", "in_w": 9, "out_w": 0, "shadow": False},
                                                             64)[0], size=(32, 32)),
                             command=self.open_maker)
        make.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        add = ctk.CTkButton(grid, text=T("+ Thêm con trỏ"), compound="top", height=94, width=10, corner_radius=12,
                            border_width=1, border_color=mix(BORDER, CYAN, 0.5), fg_color=mix(CARD, CYAN, 0.06),
                            hover_color=mix(CARD, CYAN, 0.16), text_color=CYAN_TEXT, font=self.F.b(12, strong=True),
                            image=ctk.CTkImage(simple_icon("upload", CYAN_TEXT, 64), size=(30, 30)),
                            command=self.upload_image)
        add.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        files = my_cursor_files()
        for i, f in enumerate(files, start=2):
            try:
                frames, _hot, _steps = load_cursor_file(str(f))
                th = frames[0].copy()
                th.thumbnail((112, 112), Image.LANCZOS)
                pic = Image.new("RGBA", (112, 112), (0, 0, 0, 0))
                pic.alpha_composite(th, ((112 - th.width) // 2, (112 - th.height) // 2))
            except Exception:
                continue
            name = f.stem if len(f.stem) <= 16 else f.stem[:14] + "…"
            b = ctk.CTkButton(grid, text=name, compound="top", height=94, width=10, corner_radius=12,
                              border_width=1, font=self.F.b(12), image=ctk.CTkImage(pic, size=(56, 56)),
                              command=lambda p=f: self.use_my_cursor(p))
            b.grid(row=i // cols, column=i % cols, sticky="ew", padx=4, pady=4)
            self.mine_tiles[str(f)] = b
            self.add_star(b, "my:" + f.name)
        if not files:
            ctk.CTkLabel(grid, text=T("Chưa có con trỏ nào. Tự tạo một con trỏ, hoặc bấm \"+ Thêm con trỏ\" "
                                      "để thêm ảnh PNG, GIF hay file .cur, .ani."), font=self.F.b(12), text_color=TEXT2,
                         wraplength=360, justify="left").grid(row=0, column=2, columnspan=3, sticky="w", padx=12)
        self.update_library()

    def set_mine_tint(self, on):
        self.cfg["tint_image"] = on
        self.cfg["ombre"] = False
        try:
            self.tint_var.set(on)
        except AttributeError:
            pass
        self.refresh()

    def show_lib_view(self):
        v = self.lib_view
        for view, (b, bar) in self.view_tabs.items():
            b.configure(text_color="#FFFFFF" if view == v else TEXT2)
            bar.configure(fg_color=ACCENT if view == v else "transparent")
        for view, w in list(self.tool_rows.items()) + list(self.lib_grids.items()):
            w.pack_forget()
        self.tool_rows[v].pack(fill="x")
        self.lib_grids[v].pack(fill="both", expand=True, padx=10, pady=10)
        if v == "bibata":
            self.lib_foot.pack(fill="x", pady=(10, 0))
        else:
            self.lib_foot.pack_forget()
        if v == "online" and self.cat_entries is None and not self.cat_busy:
            self.start_catalog()

    def set_lib_view(self, view):
        self.lib_view = view
        self.show_lib_view()
        self.update_library()

    def set_lib_theme(self, view, theme):
        """Nút chủ đề trên thanh công cụ của từng tab."""
        if theme == "ombre":
            self.lib_ombre(view)
        elif view == "ez":
            self.set_own_theme(theme)
        elif view == "bibata":
            self.set_bib("bibata_theme", theme)
        else:
            self.set_mine_tint(theme == "tint")

    def set_own_theme(self, theme):
        self.cfg["own_theme"] = theme
        self.cfg["ombre"] = False
        if self.cfg["shape"] not in OWN_BY_ID:
            self.cfg["shape"] = "EzDrop"
        self.refresh()

    def set_bib_color(self, color):
        self.cfg["color"] = color
        self.cfg["ombre"] = False
        if self.lib_view == "mine":
            self.set_mine_tint(True)
            return
        if self.lib_view == "ez":
            self.cfg["own_theme"] = "custom"
            if self.cfg["shape"] not in OWN_BY_ID:
                self.cfg["shape"] = "EzDrop"
        else:
            self.cfg["bibata_theme"] = "custom"
            if self.cfg["shape"] != "Bibata":
                self.cfg["shape"] = "Bibata"
        self.refresh()

    def pick_bib_color(self):
        res = colorchooser.askcolor(color=self.cfg["color"], parent=self.win, title=T("Chọn màu"))
        if res and res[1]:
            self.set_bib_color(res[1])

    def set_bib(self, key, value):
        self.cfg[key] = value
        if key == "bibata_theme":
            self.cfg["ombre"] = False
        if key == "bibata_theme" and self.cfg["shape"] != "Bibata":
            self.cfg["shape"] = "Bibata"
        self.refresh()

    def add_star(self, tile, fid, store=None):
        if not hasattr(self, "star_imgs"):
            self.star_imgs = {True: ctk.CTkImage(star_icon(True, "#FFC940", 32), size=(15, 15)),
                              False: ctk.CTkImage(star_icon(False, "#6B7488", 32), size=(15, 15))}
        sb = ctk.CTkButton(tile, text="", width=24, height=24, corner_radius=7, fg_color="transparent",
                           hover_color="#2A3040", border_width=0, image=self.star_imgs[False],
                           command=lambda: self.toggle_fav(fid))
        sb.place(relx=1.0, x=-5, y=5, anchor="ne")
        (self.star_btns if store is None else store)[fid] = sb

    def toggle_fav(self, fid):
        favs = list(self.cfg["favorites"])
        if fid in favs:
            favs.remove(fid)
        else:
            favs.append(fid)
        self.cfg["favorites"] = favs
        self.update_library()
        self.save()

    def fav_valid(self, fid):
        if fid.startswith("bib:"):
            return BIBATA_DIR.exists() and fid[4:] in dict(BIBATA_CURSORS)
        if fid.startswith("my:"):
            return (MY_DIR / fid[3:]).is_file()
        return fid in OWN_BY_ID and own_image(fid) is not None

    def fav_label(self, fid):
        if fid.startswith("bib:"):
            return "Bibata · " + T(dict(BIBATA_CURSORS).get(fid[4:], fid[4:]))
        if fid.startswith("my:"):
            return Path(fid[3:]).stem
        return T(OWN_BY_ID[fid][1]) if fid in OWN_BY_ID else T(fid)

    def current_fav_id(self):
        c = self.cfg
        if c["shape"] == "Bibata":
            return "bib:" + c["bibata_cursor"]
        if c["shape"] == "Ảnh tải lên":
            return "my:" + Path(c["image"]).name if c["image"] and Path(c["image"]).parent == MY_DIR else None
        return c["shape"]

    def use_fav(self, fid):
        if not self.fav_valid(fid):
            return
        if fid.startswith("bib:"):
            self.pick_bibata(fid[4:])
        elif fid.startswith("my:"):
            self.use_my_cursor(MY_DIR / fid[3:])
        else:
            self.set_shape(fid)

    def pick_own(self, shape):
        self.cfg["shape"] = shape
        self.refresh()

    def pick_bibata(self, name):
        self.cfg["bibata_cursor"] = name
        self.cfg["shape"] = "Bibata"
        self.refresh()

    def update_library(self):
        self._update_library()
        for sb in list(getattr(self, "star_btns", {}).values()) + list(getattr(self, "fav_stars", {}).values()):
            try:
                col = sb.master.cget("fg_color")
                hov = sb.master.cget("hover_color")
                if getattr(sb, "_bg", None) != col:
                    sb._bg = col
                    sb.configure(fg_color=col, bg_color=col, hover_color=hov)
            except (tk.TclError, ValueError):
                pass

    def _update_library(self):
        if getattr(self, "theme_segs", None) is None:
            return
        c = self.cfg
        current = {"ez": c["own_theme"], "bibata": c["bibata_theme"], "mine": "tint" if c["tint_image"] else "original"}
        for view, seg in self.theme_segs.items():
            key = "ombre" if c["ombre"] else current[view]
            seg.set({k: v for v, k in self.theme_maps[view].items()}.get(key, ""))
        for b in self.color_btns:
            b.configure(fg_color=c["color"], hover_color=c["color"])
        favs = set(c["favorites"])
        for fid, sb in list(self.star_btns.items()) + list(self.fav_stars.items()):
            on = fid in favs
            if getattr(sb, "_fav_on", None) != on:
                sb._fav_on = on
                try:
                    sb.configure(image=self.star_imgs[on])
                except tk.TclError:
                    pass
        mine_sel = c["image"] if c["shape"] == "Ảnh tải lên" else None
        for path, b in self.mine_tiles.items():
            self.tile_style(b, path == mine_sel)
        for cid, b in getattr(self, "cat_tiles", {}).items():
            f = self.cat_file(cid)
            try:
                self.tile_style(b, mine_sel is not None and f is not None and Path(mine_sel) == f)
            except tk.TclError:
                pass
        self.mine_del.configure(state="normal" if mine_sel and mine_sel in self.mine_tiles else "disabled")
        made = mine_sel and mine_sel in self.mine_tiles and Path(mine_sel).name in c["made_cursors"]
        self.mine_edit.configure(state="normal" if made else "disabled")
        # hình trên ô: chỉ vẽ lại khi đổi chủ đề / màu
        oc = tuple(c["ombre_colors"]) if c["ombre"] else None
        osig = (c["own_theme"], c["color"].lower() if c["own_theme"] == "custom" else "", oc)
        if osig != self._own_sig:
            self._own_sig = osig
            for shape, b in self.own_tiles.items():
                if oc:
                    im = own_image(shape).resize((112, 112), Image.LANCZOS)
                    hx, hy = OWN_BY_ID[shape][3]
                    im = apply_ombre(im, ombre_tmap(im, (hx * 112 // 256, hy * 112 // 256)), ombre_lut(oc))
                else:
                    im = own_image_colored(shape, c["color"]) if c["own_theme"] == "custom" else own_image(shape)
                    im = im.resize((112, 112), Image.LANCZOS)
                b.configure(image=ctk.CTkImage(im, size=(56, 56)))
        if self.bib_tiles:
            variant = self.bibata_variant()
            colors = bibata_colors("custom" if oc else c["bibata_theme"], oc[0] if oc else c["color"])
            sig = (variant, colors, oc)
            if sig != self._lib_sig:
                self._lib_sig = sig
                for name, b in self.bib_tiles.items():
                    im = bibata_image(BIBATA_DIR, variant, name, colors).resize((112, 112), Image.LANCZOS)
                    if oc:
                        hx, hy = BIBATA_META["hotspots"].get(f"{variant}/{name}", [128, 128])
                        im = apply_ombre(im, ombre_tmap(im, (hx * 112 // 256, hy * 112 // 256)), ombre_lut(oc))
                    b.configure(image=ctk.CTkImage(im, size=(56, 56)))
        tile_bg = mix(FIELD, "#FFFFFF", 0.05) if c["bibata_theme"] == "classic" else FIELD
        for shape, tile in self.own_tiles.items():
            self.tile_style(tile, c["shape"] == shape, text=TEXT)
        for name, b in self.bib_tiles.items():
            self.tile_style(b, c["shape"] == "Bibata" and name == c["bibata_cursor"], idle=tile_bg)
        # lưới Yêu thích dựng lại sau một nhịp: nút ☆ vừa bấm có thể nằm trong chính lưới đó
        if self._fav_job is None:
            self._fav_job = self.ov.after(150, self.update_favs)

    def update_favs(self):
        """Lưới Yêu thích: ô lấy lại hình của con trỏ gốc, dựng lại khi danh sách hoặc hình đổi."""
        self._fav_job = None
        grid = self.lib_grids.get("fav")
        try:
            if grid is None or not grid.winfo_exists():
                return
        except tk.TclError:
            return
        favs = [f for f in self.cfg["favorites"] if self.fav_valid(f)]
        sig = (tuple(favs), self._own_sig, self._lib_sig, self.mine_sig)
        if sig != self._fav_sig:
            self._fav_sig = sig
            for w in grid.winfo_children():
                w.destroy()
            self.fav_tiles, self.fav_stars = {}, {}
            src = {**self.own_tiles, **{"bib:" + k: b for k, b in self.bib_tiles.items()},
                   **{"my:" + Path(k).name: b for k, b in self.mine_tiles.items()}}
            for i, fid in enumerate(favs):
                name = self.fav_label(fid)
                b = ctk.CTkButton(grid, text=name if len(name) <= 18 else name[:16] + "…", compound="top", height=94,
                                  width=10, corner_radius=12, border_width=1, font=self.F.b(12),
                                  image=src[fid].cget("image") if fid in src else None,
                                  command=lambda f=fid: self.use_fav(f))
                b.grid(row=i // 5, column=i % 5, sticky="ew", padx=4, pady=4)
                self.fav_tiles[fid] = b
                self.add_star(b, fid, self.fav_stars)
            if not favs:
                ctk.CTkLabel(grid, text=T("Chưa có con trỏ yêu thích. Bấm ☆ trên một con trỏ ở các tab khác "
                                          "để thêm vào đây."), font=self.F.b(12), text_color=TEXT2,
                             wraplength=560, justify="left").grid(row=0, column=0, columnspan=5, sticky="w",
                                                                   padx=12, pady=12)
            self.update_library()
        cur = self.current_fav_id()
        for fid, b in self.fav_tiles.items():
            self.tile_style(b, fid == cur)
