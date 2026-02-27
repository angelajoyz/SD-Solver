"""
Symbolic Derivative Generator  —  SD Solver
Week 2: Input Validation + Error Messaging
UI: CustomTkinter — playful-formal light theme, Nunito + Space Mono vibes
"""

import customtkinter as ctk
import tkinter as tk
import os

from engine import DerivativeEngine


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ── Palette (light, airy, blue-lavender) ──────────────────────────────────────
BG          = "#f0f4ff"
BG2         = "#e4eaff"
SURFACE     = "#ffffff"
SURFACE2    = "#f7f9ff"
BORDER      = "#d0d8f5"
BORDER2     = "#c2ccf0"
ACCENT      = "#5c6ef8"
ACCENT2     = "#8b5cf6"
GOLD        = "#f59e0b"
GREEN       = "#10b981"
RED         = "#ef4444"
BLUE_V      = "#3b82f6"
TXT         = "#1e2150"
TXT2        = "#5a608a"
TXT3        = "#9ba3cc"
TAG_BG      = "#eef0ff"

# ── Fonts — defined as CTkFont objects inside _load_fonts() ──────────────────
F_TOPBAR  = ("Nunito ExtraBold", 19)
F_SECTION = ("Nunito ExtraBold", 15)
F_LABEL   = ("Nunito ExtraBold", 15)
F_MONO    = ("Consolas",    13)
F_TAG     = ("Consolas",    12, "bold")
F_BTN     = ("Nunito ExtraBold", 17)
F_SMALL   = ("Nunito ExtraBold", 12)
F_ERR     = ("Nunito",      12)
F_ANSWER  = ("Consolas",    26, "bold")
F_STATUS  = ("Nunito ExtraBold", 17)
F_CHIP    = ("Nunito ExtraBold", 15)


class DerivativeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._load_fonts()
        self.title("∂ SD Solver — Symbolic Derivative Generator")
        self.geometry("920x680")
        self.minsize(720, 520)
        self.configure(fg_color=BG)
        self.resizable(True, True)
        self.engine = DerivativeEngine()
        self._typing = False
        self._build_ui()

    # ── Font loader ──────────────────────────────────────────────────────────
    def _load_fonts(self):
        """Override module-level font tuples with CTkFont objects.
        Must run after super().__init__() so Tk exists."""
        global F_TOPBAR, F_SECTION, F_LABEL, F_MONO, F_TAG
        global F_BTN, F_SMALL, F_ERR, F_ANSWER, F_STATUS, F_CHIP

        F_TOPBAR  = ctk.CTkFont(family="Nunito ExtraBold", size=18)
        F_SECTION = ctk.CTkFont(family="Nunito ExtraBold", size=13)
        F_LABEL   = ctk.CTkFont(family="Nunito SemiBold",  size=13)
        F_MONO    = ctk.CTkFont(family="Consolas",         size=13)
        F_TAG     = ctk.CTkFont(family="Consolas",         size=12, weight="bold")
        F_BTN     = ctk.CTkFont(family="Nunito ExtraBold", size=14)
        F_SMALL   = ctk.CTkFont(family="Nunito SemiBold",  size=11)
        F_ERR     = ctk.CTkFont(family="Nunito",           size=11)
        F_ANSWER  = ctk.CTkFont(family="Consolas",         size=26, weight="bold")
        F_STATUS  = ctk.CTkFont(family="Nunito ExtraBold", size=16)
        F_CHIP    = ctk.CTkFont(family="Nunito SemiBold",  size=13)


    # ── Main UI ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_topbar()
        self.main_scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG, corner_radius=0,
            scrollbar_button_color=BORDER2,
            scrollbar_button_hover_color=ACCENT)
        self.main_scroll.pack(fill="both", expand=True)

        self.col = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.col.pack(fill="x", padx=56, pady=(32, 48))

        self._build_input_panel()
        self._build_rules_section()
        self._build_trail_section()   # built but hidden until compute

    # ── Topbar ────────────────────────────────────────────────────────────────
    def _build_topbar(self):
        bar = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0,
                           height=58, border_width=2, border_color=BORDER)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        ctk.CTkLabel(bar, text="∂", font=ctk.CTkFont(family="Nunito ExtraBold", size=22),
                     fg_color=ACCENT, text_color="white",
                     corner_radius=12, width=40, height=40
                     ).pack(side="left", padx=(18, 0), pady=9)

        ctk.CTkLabel(bar, text=" SD ", font=F_TOPBAR,
                     fg_color="transparent", text_color=ACCENT
                     ).pack(side="left")
        ctk.CTkLabel(bar, text="Solver — Symbolic Derivative Generator",
                     font=F_TOPBAR, fg_color="transparent", text_color=TXT
                     ).pack(side="left")

        ctk.CTkFrame(bar, fg_color=BORDER2, width=1, height=22,
                     corner_radius=0).pack(side="left", padx=14, pady=18)

        ctk.CTkLabel(bar, text="  Basic Rules Engine  ",
                     font=F_SMALL, fg_color=TAG_BG,
                     text_color=TXT2, corner_radius=20
                     ).pack(side="left")

        self.st_dot = ctk.CTkLabel(bar, text="●", font=F_SMALL,
                                   text_color=GREEN, fg_color="transparent")
        self.st_dot.pack(side="right", padx=(4, 18))
        self.status_lbl = ctk.CTkLabel(bar, text="Ready",
                                       font=F_SMALL, text_color=TXT3,
                                       fg_color="transparent")
        self.status_lbl.pack(side="right")

    # ── Section label with trailing line ─────────────────────────────────────
    def _section_label(self, parent, text, pady_top=0):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(pady_top, 10))
        ctk.CTkLabel(row, text=text.upper(), font=F_SECTION,
                     fg_color="transparent", text_color=ACCENT,
                     anchor="w").pack(side="left")
        ctk.CTkFrame(row, fg_color=BORDER, height=2,
                     corner_radius=2).pack(side="left", fill="x",
                                           expand=True, padx=(10, 0), pady=6)

    # ── Input panel ───────────────────────────────────────────────────────────
    def _build_input_panel(self):
        self._section_label(self.col, "Input Panel")

        panel = ctk.CTkFrame(self.col, fg_color=SURFACE, corner_radius=20,
                             border_width=2, border_color=BORDER)
        panel.pack(fill="x")

        inner = ctk.CTkFrame(panel, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)

        # Row 1 — f(x) alone, full width
        fx_block = self._field(inner, "f(x) =", "f(x)", "x**3 + 2*x**2 - 5*x + 1")
        fx_block.pack(fill="x", pady=(0, 10))
        self.entry_fx   = fx_block._entry
        self.wrap_fx    = fx_block._wrap
        self.err_fx     = fx_block._err

        # Row 2 — var, order, eval point side by side
        fields_row = ctk.CTkFrame(inner, fg_color="transparent")
        fields_row.pack(fill="x")
        fields_row.columnconfigure(0, weight=1)
        fields_row.columnconfigure(1, weight=1)
        fields_row.columnconfigure(2, weight=2)

        var_block = self._field(fields_row, "Variable", "var", "x")
        var_block.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.entry_var  = var_block._entry
        self.wrap_var   = var_block._wrap
        self.err_var    = var_block._err

        order_block = self._field(fields_row, "Order (n)", "n =", "1")
        order_block.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.entry_order = order_block._entry
        self.wrap_order  = order_block._wrap
        self.err_order   = order_block._err

        point_block = self._field(fields_row, "Eval at x =", "x =", "e.g. 2.5", optional=True)
        point_block.grid(row=0, column=2, sticky="ew")
        self.entry_point = point_block._entry
        self.wrap_point  = point_block._wrap
        self.err_point   = point_block._err

        # Buttons — right-aligned, fixed width
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(14, 0))

        ctk.CTkButton(btn_row, text="✕  Clear", font=F_BTN,
                      fg_color=SURFACE, hover_color=BG2,
                      text_color=TXT2, corner_radius=12, height=42,
                      width=120, border_width=2, border_color=BORDER2,
                      command=self._on_clear
                      ).pack(side="right")

        ctk.CTkButton(btn_row, text="▶   COMPUTE", font=F_BTN,
                      fg_color=ACCENT, hover_color=ACCENT2,
                      text_color="white", corner_radius=12, height=42,
                      width=154, command=self._on_compute
                      ).pack(side="right", padx=(0, 8))

    # ── Field widget ──────────────────────────────────────────────────────────
    def _field(self, parent, label_text, tag_text, placeholder, optional=False):
        outer = ctk.CTkFrame(parent, fg_color="transparent")

        lbl_row = ctk.CTkFrame(outer, fg_color="transparent")
        lbl_row.pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(lbl_row, text=label_text, font=F_LABEL,
                     fg_color="transparent", text_color=TXT2).pack(side="left")
        if optional:
            ctk.CTkLabel(lbl_row, text=" opt ", font=ctk.CTkFont(family="Nunito ExtraBold", size=13),
                         fg_color=BG2, text_color=TXT3,
                         corner_radius=6).pack(side="left", padx=(5, 0))

        wrap = ctk.CTkFrame(outer, fg_color=SURFACE2, corner_radius=12,
                            border_width=2, border_color=BORDER)
        wrap.pack(fill="x")

        ctk.CTkLabel(wrap, text=f" {tag_text} ", font=F_TAG,
                     fg_color=TAG_BG, text_color=ACCENT,
                     corner_radius=8, height=36
                     ).pack(side="left", padx=(3, 0), pady=3)

        entry = ctk.CTkEntry(wrap, font=F_MONO,
                             fg_color="transparent", bg_color="transparent",
                             text_color=TXT,
                             placeholder_text=placeholder,
                             placeholder_text_color=TXT3,
                             border_width=0, corner_radius=0, height=36)
        entry.pack(side="left", fill="x", expand=True, padx=(8, 6), pady=3)

        err = ctk.CTkLabel(outer, text="", font=F_ERR,
                           text_color=RED, fg_color="transparent", anchor="w")
        err._outer = outer

        outer._entry = entry
        outer._wrap  = wrap
        outer._err   = err
        return outer

    # ── Error helpers ─────────────────────────────────────────────────────────
    def _set_err(self, wrap, err, msg):
        wrap.configure(border_color=RED)
        err.configure(text=f"⚠  {msg}")
        err.pack(anchor="w", pady=(3, 0), in_=err._outer)

    def _clr_err(self, wrap, err):
        wrap.configure(border_color=BORDER)
        err.configure(text="")
        err.pack_forget()

    def _clear_all_errors(self):
        for w, e in [(self.wrap_fx, self.err_fx), (self.wrap_var, self.err_var),
                     (self.wrap_order, self.err_order), (self.wrap_point, self.err_point)]:
            self._clr_err(w, e)

    # ── Supported rules ───────────────────────────────────────────────────────
    def _build_rules_section(self):
        self._section_label(self.col, "Supported Rules", pady_top=22)

        panel = ctk.CTkFrame(self.col, fg_color=SURFACE, corner_radius=20,
                             border_width=2, border_color=BORDER)
        panel.pack(fill="x")

        inner = ctk.CTkFrame(panel, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        grid = ctk.CTkFrame(inner, fg_color="transparent")
        grid.pack(fill="x")
        for i in range(3):
            grid.columnconfigure(i, weight=1)

        rules = ["Power Rule", "Constant Rule", "Sum / Difference",
                 "Chain Rule (basic)", "Product Rule", "Quotient Rule"]

        for i, rule in enumerate(rules):
            c, r = i % 3, i // 3
            ctk.CTkLabel(grid, text=f"✦  {rule}",
                         font=F_CHIP, text_color=TXT2,
                         fg_color="transparent", anchor="w"
                         ).grid(row=r, column=c,
                                padx=(0, 8) if c < 2 else 0,
                                pady=5, sticky="w")

    # ── Trail section (hidden until compute) ──────────────────────────────────
    def _build_trail_section(self):
        self.trail_outer = ctk.CTkFrame(self.col, fg_color="transparent")
        # NOT packed here — shown only after compute

        self._section_label(self.trail_outer, "Solution Trail", pady_top=22)

        trail_card = ctk.CTkFrame(self.trail_outer, fg_color=SURFACE,
                                  corner_radius=20, border_width=2,
                                  border_color=BORDER)
        trail_card.pack(fill="x")

        # Answer pill
        ans_bar = ctk.CTkFrame(trail_card, fg_color=SURFACE2,
                               corner_radius=0, border_width=0)
        ans_bar.pack(fill="x")
        ans_inner = ctk.CTkFrame(ans_bar, fg_color="transparent")
        ans_inner.pack(fill="x", padx=20, pady=16)

        ans_left = ctk.CTkFrame(ans_inner, fg_color="transparent")
        ans_left.pack(side="left")
        ctk.CTkLabel(ans_left, text="FINAL ANSWER", font=F_SMALL,
                     text_color=TXT3, fg_color="transparent").pack(anchor="w")
        self.lbl_answer = ctk.CTkLabel(ans_left, text="—", font=F_ANSWER,
                                       text_color=GOLD, fg_color="transparent")
        self.lbl_answer.pack(anchor="w")

        ans_right = ctk.CTkFrame(ans_inner, fg_color="transparent")
        ans_right.pack(side="right")
        self.status_pill = ctk.CTkFrame(ans_right, fg_color=TAG_BG,
                                        corner_radius=14, border_width=2,
                                        border_color=BORDER2)
        self.status_pill.pack()
        self.ab_dot = ctk.CTkLabel(self.status_pill, text="●",
                                   font=ctk.CTkFont(family="Nunito ExtraBold", size=15), text_color=TXT3,
                                   fg_color="transparent")
        self.ab_dot.pack(side="left", padx=(12, 4), pady=10)
        self.ab_status_lbl = ctk.CTkLabel(self.status_pill, text="READY",
                                          font=F_STATUS, text_color=TXT3,
                                          fg_color="transparent")
        self.ab_status_lbl.pack(side="left", padx=(0, 14), pady=10)

        ctk.CTkFrame(trail_card, fg_color=BORDER, height=2,
                     corner_radius=0).pack(fill="x")

        # Trail header
        trail_hdr = ctk.CTkFrame(trail_card, fg_color=BG2,
                                 corner_radius=0, height=38)
        trail_hdr.pack(fill="x")
        trail_hdr.pack_propagate(False)

        ctk.CTkLabel(trail_hdr, text="SOLUTION TRAIL", font=F_SECTION,
                     text_color=TXT, fg_color="transparent"
                     ).pack(side="left", padx=18, pady=10)
        ctk.CTkLabel(trail_hdr, text="step-by-step audit log",
                     font=ctk.CTkFont(family="Nunito",      size=12), text_color=TXT3,
                     fg_color="transparent").pack(side="left")
        self.trail_tag_lbl = ctk.CTkLabel(trail_hdr, text="Awaiting input",
                                          font=ctk.CTkFont(family="Nunito ExtraBold", size=18),
                                          text_color=ACCENT2,
                                          fg_color=SURFACE, corner_radius=20)
        self.trail_tag_lbl.pack(side="right", padx=14, pady=8)

        ctk.CTkFrame(trail_card, fg_color=BORDER, height=2,
                     corner_radius=0).pack(fill="x")

        # Trail text box
        self.trail_text = tk.Text(
            trail_card, font=("Nunito SemiBold", 13),
            bg=SURFACE, fg=TXT,
            insertbackground=ACCENT,
            relief="flat", bd=0,
            wrap="word", state="disabled",
            padx=20, pady=16,
            height=4, cursor="arrow",
            selectbackground=BG2,
            selectforeground=TXT)
        self.trail_text.pack(fill="x", expand=False)

        for tag, fg_, fnt in [
            ("section", ACCENT2,  ("Nunito ExtraBold", 13)),   # ① GIVEN, ② VALIDATION etc
            ("step",    TXT,      ("Nunito SemiBold",  13)),   # Step 1, Step 2...
            ("answer",  GOLD,     ("Nunito ExtraBold", 20)),   # FINAL ANSWER line — big
            ("verify",  BLUE_V,   ("Nunito",           13)),
            ("summary", TXT2,     ("Nunito",           13)),
            ("dim",     TXT3,     ("Consolas",         12)),   # separator lines
            ("rule",    GOLD,     ("Consolas",         13)),   # → math results
            ("pass",    GREEN,    ("Nunito SemiBold",  13)),
            ("fail",    RED,      ("Nunito SemiBold",  13)),
            ("warn",    GOLD,     ("Nunito SemiBold",  13)),
        ]:
            self.trail_text.tag_config(tag, foreground=fg_, font=fnt)

        # Solve another footer
        ctk.CTkFrame(trail_card, fg_color=BORDER, height=2,
                     corner_radius=0).pack(fill="x")
        solve_foot = ctk.CTkFrame(trail_card, fg_color=SURFACE2,
                                  corner_radius=0)
        solve_foot.pack(fill="x")

        self.solve_another_btn = ctk.CTkButton(
            solve_foot, text="↺   Solve Another", font=F_BTN,
            fg_color=SURFACE, hover_color=ACCENT,
            text_color=ACCENT, corner_radius=12, height=44,
            border_width=2, border_color=ACCENT,
            command=self._solve_another)
        # packed dynamically after typing done

    # ── Status helpers ────────────────────────────────────────────────────────
    def _set_pill(self, text, color, bg):
        self.status_pill.configure(fg_color=bg, border_color=color)
        self.ab_dot.configure(text_color=color)
        self.ab_status_lbl.configure(text=text, text_color=color)

    def _set_status(self, msg, dot_color=None):
        self.status_lbl.configure(text=msg)
        if dot_color:
            self.st_dot.configure(text_color=dot_color)

    # ── Trail helpers ─────────────────────────────────────────────────────────
    def _tc(self):
        self.trail_text.configure(state="normal")
        self.trail_text.delete("1.0", "end")
        self.trail_text.configure(state="disabled")

    def _show_trail(self):
        self.trail_outer.pack(fill="x")

    def _hide_trail(self):
        self.trail_outer.pack_forget()
        self.solve_another_btn.pack_forget()

    def _real_value(self, entry):
        return entry.get().strip()

    # ── Typing animation ──────────────────────────────────────────────────────
    def _type_trail(self, segments):
        self._typing = True
        flat = [(ch, tag) for text, tag in segments for ch in text]

        def write_char(idx):
            if idx >= len(flat):
                self._typing = False
                self.after(0, self._on_typing_done)
                return
            ch, tag = flat[idx]
            self.trail_text.configure(state="normal")
            self.trail_text.insert("end", ch, tag)
            # grow height to fit all content
            line_count = int(self.trail_text.index("end-1c").split(".")[0])
            self.trail_text.configure(state="disabled", height=max(4, line_count))
            self.trail_text.see("end")
            self.main_scroll._parent_canvas.yview_moveto(1.0)
            delay = 1 if tag == "dim" else 6
            self.after(delay, write_char, idx + 1)

        write_char(0)

    def _on_typing_done(self):
        self.solve_another_btn.pack(fill="x", padx=16, pady=12)
        self.after(100, lambda: self.main_scroll._parent_canvas.yview_moveto(1.0))

    # ── Clear ─────────────────────────────────────────────────────────────────
    def _on_clear(self):
        self._clear_all_errors()
        for entry, ph in [
            (self.entry_fx,    "x**3 + 2*x**2 - 5*x + 1"),
            (self.entry_var,   "x"),
            (self.entry_order, "1"),
            (self.entry_point, "e.g. 2.5"),
        ]:
            entry.delete(0, "end")
            entry.configure(placeholder_text=ph, text_color=TXT)
        self._set_status("Cleared", GREEN)

    # ── Solve another ─────────────────────────────────────────────────────────
    def _solve_another(self):
        self._typing = False
        self._hide_trail()
        self._on_clear()
        self._tc()
        self.lbl_answer.configure(text="—", text_color=GOLD)
        self._set_pill("READY", TXT3, TAG_BG)
        self.trail_tag_lbl.configure(text="Awaiting input")
        self._set_status("Ready", GREEN)
        self.main_scroll._parent_canvas.yview_moveto(0.0)

    # ── Compute ───────────────────────────────────────────────────────────────
    def _on_compute(self):
        if self._typing:
            return
        self._clear_all_errors()
        self._hide_trail()

        raw_fx    = self._real_value(self.entry_fx)
        raw_var   = self._real_value(self.entry_var)
        raw_order = self._real_value(self.entry_order)
        raw_point = self._real_value(self.entry_point)

        self._set_status("Computing…", ACCENT)
        self.update_idletasks()

        result = self.engine.validate_and_compute(raw_fx, raw_var, raw_order, raw_point)

        self._tc()
        self._show_trail()

        if result["ok"]:
            self.lbl_answer.configure(text=result["answer"], text_color=GOLD)
            self._set_pill("SOLVED", GREEN, "#f0fdf8")
            self.trail_tag_lbl.configure(text="✔  All checks passed")
            self._set_status(f"Done  —  {result['timestamp']}", GREEN)
        else:
            self.lbl_answer.configure(text="Error — see trail", text_color=RED)
            self._set_pill("ERROR", RED, "#fff5f5")
            self.trail_tag_lbl.configure(text="⚠  Validation failed")
            self._set_status("Validation failed", RED)
            for field, msg in result["field_errors"].items():
                pairs = {"fx":    (self.wrap_fx,    self.err_fx),
                         "var":   (self.wrap_var,   self.err_var),
                         "order": (self.wrap_order, self.err_order),
                         "point": (self.wrap_point, self.err_point)}
                if field in pairs:
                    self._set_err(*pairs[field], msg)

        segments = self._build_segments(result)
        self.after(120, lambda: self.main_scroll._parent_canvas.yview_moveto(1.0))
        self.after(200, lambda: self._type_trail(segments))

    # ── Build trail segments ──────────────────────────────────────────────────
    def _build_segments(self, r):
        DIV = "─" * 58 + "\n"
        segs = []

        def s(text, tag="step"):
            segs.append((text, tag))

        s("① GIVEN\n", "section");      s(DIV, "dim")
        s(f"   f({r['var']})           =  {r['raw_fx']}\n")
        s(f"   Variable        =  {r['raw_var']}\n")
        s(f"   Order (n)       =  {r['raw_order']}\n")
        s(f"   Evaluate at     =  {r['raw_point'] or 'Not specified'}\n\n")

        s("② VALIDATION\n", "section"); s(DIV, "dim")
        for chk in r["validation_steps"]:
            status = chk["status"]
            tag  = {"PASS":"pass","FAIL":"fail","WARN":"warn","SKIP":"dim"}.get(status,"step")
            icon = {"PASS":"✔","FAIL":"✘","WARN":"⚠","SKIP":"○"}.get(status," ")
            s(f"   Step {chk['num']}  {chk['label']}\n")
            s(f"           {icon}  {status}", tag)
            if chk.get("detail"):
                s(f"  —  {chk['detail']}", tag)
            s("\n\n")

        if not r["ok"]:
            s("   ✘  Computation aborted — correct the errors above and retry.\n", "fail")
            s("\n" + "═" * 58 + "\n", "dim")
            return segs

        s("   ✔  All checks passed — proceeding to computation.\n\n", "pass")

        s("③ METHOD\n", "section");     s(DIV, "dim")
        s(f"   Name            :  Symbolic Differentiation (Basic Rules)\n")
        s(f"   Rules applied   :  Power, Constant, Sum/Difference,\n")
        s(f"                      Constant Multiple, Chain, Product, Quotient\n")
        s(f"   Library         :  SymPy {r['sympy_version']}\n\n")

        s("④ STEPS  [placeholder — full rule engine in Week 4]\n", "section")
        s(DIV, "dim")
        var, fx, n = r["var"], r["raw_fx"], r["order"]
        s(f"   Step 1  Parse f({var}) into symbolic expression tree\n")
        s(f"           → Expression  :  {fx}\n\n", "rule")
        s(f"   Step 2  Identify each term and applicable rule\n")
        s(f"           → [rule detection will populate in Week 4]\n\n", "rule")
        s(f"   Step 3  Apply derivative rule term-by-term  (n={n} pass(es))\n")
        s(f"           → d/d{var} [terms] = ...\n\n", "rule")
        s(f"   Step 4  Simplify / collect like terms\n")
        s(f"           → {r['answer']}\n\n", "rule")

        if r.get("point_value") is not None:
            s(f"   Step 5  Evaluate  f'({r['raw_point']})\n")
            s(f"           → f'({r['raw_point']})  =  {r['point_value']}\n\n", "rule")

        s("⑤ FINAL ANSWER\n", "section"); s(DIV, "dim")
        s(f"   d^{n}/d{var}^{n} [{fx}]  =  {r['answer']}\n\n", "answer")

        s("⑥ VERIFICATION\n", "section"); s(DIV, "dim")
        s("   Method          :  Symbolic back-substitution check\n", "verify")
        s("   Check           :  Integrate result → compare to f(x) + C\n", "verify")
        s("   Residual        :  [will be computed in Week 9]\n", "verify")
        s("   Status          :  ⏳ Pending full verification engine\n\n", "verify")

        s("⑦ SUMMARY\n", "section");    s(DIV, "dim")
        s(f"   Timestamp       :  {r['timestamp']}\n", "summary")
        s(f"   Python          :  {r['python_version']}\n", "summary")
        s(f"   SymPy           :  {r['sympy_version']}\n", "summary")
        s(f"   Status          :  ✅ Validation complete\n", "summary")
        s("\n" + "═" * 58 + "\n", "dim")

        return segs


if __name__ == "__main__":
    app = DerivativeApp()
    app.mainloop()
