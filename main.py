import tkinter as tk
from tkinter import scrolledtext, font
from datetime import datetime
import sys
import threading

from engine import DerivativeEngine
from numerical_engine import NumericalEngine
from trail_logger import TrailLogger

BG_DARK  = "#0D0F14"
BG_PANEL = "#13161E"
BG_INPUT = "#1A1E2A"
ACCENT   = "#7DF9C2"
ACCENT2  = "#F97DDB"
GOLD     = "#FFD166"
TEXT_PRI = "#E8EAF0"
TEXT_SEC = "#8890A6"
BORDER   = "#252B3B"
ERR_RED  = "#FF6B6B"
WARN_YEL = "#FFD166"
OK_GRN   = "#7DF9C2"
ACCENT3  = "#7DB9F9"


class DerivativeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("∂ SD Solver")
        self.geometry("1060x860")
        self.minsize(900, 720)
        self.configure(bg=BG_DARK)
        self.resizable(True, True)
        self.sym_engine   = DerivativeEngine()
        self.num_engine   = NumericalEngine()
        self._generating  = False
        self._last_result = None
        self._method_var  = tk.StringVar(value="symbolic")
        self._scheme_var  = tk.StringVar(value="central")
        self._build_fonts()
        self._build_ui()

    def _build_fonts(self):
        self.f_title  = font.Font(family="Courier New", size=18, weight="bold")
        self.f_label  = font.Font(family="Courier New", size=10, weight="bold")
        self.f_input  = font.Font(family="Courier New", size=12)
        self.f_trail  = font.Font(family="Courier New", size=10)
        self.f_answer = font.Font(family="Courier New", size=13, weight="bold")
        self.f_sub    = font.Font(family="Courier New", size=9)
        self.f_btn    = font.Font(family="Courier New", size=11, weight="bold")

    def _build_ui(self):
        header = tk.Frame(self, bg=BG_PANEL, height=64)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(header, text="∂  SD SOLVER  —  SYMBOLIC DERIVATIVE GENERATOR",
                 font=self.f_title, fg=ACCENT, bg=BG_PANEL
                 ).pack(side="left", padx=22, pady=14)
        tk.Label(header, text="Basic Rules Engine",
                 font=self.f_sub, fg=TEXT_SEC, bg=BG_PANEL
                 ).pack(side="right", padx=22, pady=20)

        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        left_outer = tk.Frame(body, bg=BG_DARK, width=380)
        left_outer.pack(side="left", fill="y", padx=(0, 10))
        left_outer.pack_propagate(False)

        left_canvas = tk.Canvas(left_outer, bg=BG_DARK, highlightthickness=0)
        left_scroll = tk.Scrollbar(left_outer, orient="vertical", command=left_canvas.yview)
        left_canvas.configure(yscrollcommand=left_scroll.set)
        left_scroll.pack(side="right", fill="y")
        left_canvas.pack(side="left", fill="both", expand=True)

        left = tk.Frame(left_canvas, bg=BG_DARK)
        left_canvas_window = left_canvas.create_window((0, 0), window=left, anchor="nw")

        def _on_left_configure(e):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))
            left_canvas.itemconfig(left_canvas_window, width=left_canvas.winfo_width())

        left.bind("<Configure>", _on_left_configure)
        left_canvas.bind("<Configure>", lambda e: left_canvas.itemconfig(
            left_canvas_window, width=e.width))

        def _on_mousewheel(e):
            left_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        left_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        right = tk.Frame(body, bg=BG_DARK)
        right.pack(side="left", fill="both", expand=True)

        self._build_left(left)
        self._build_right(right)
        self.logger = TrailLogger(self.trail_text)

    def _build_left(self, parent):
        tk.Label(parent, text="INPUT PANEL", font=self.f_label,
                 fg=ACCENT, bg=BG_DARK).pack(anchor="w", pady=(4, 6))

        self._section_label(parent, "f(x) =")
        self.entry_fx = self._entry(parent)
        self.err_fx   = self._error_label(parent)
        self._add_placeholder(self.entry_fx, "x^3 + 2x^2 - 5x + 1")

        self._section_label(parent, "Variable")
        self.entry_var = self._entry(parent)
        self.err_var   = self._error_label(parent)
        self._add_placeholder(self.entry_var, "x")

        self._section_label(parent, "Derivative Order (n)")
        self.entry_order = self._entry(parent)
        self.err_order   = self._error_label(parent)
        self._add_placeholder(self.entry_order, "1")

        self.lbl_point = tk.Label(parent, text="Evaluate at x = (optional)",
                                  font=self.f_label, fg=TEXT_SEC, bg=BG_DARK)
        self.lbl_point.pack(anchor="w", pady=(10, 2))
        self.entry_point = self._entry(parent)
        self.err_point   = self._error_label(parent)
        self._add_placeholder(self.entry_point, "2.5   (leave blank to skip)")

        tk.Label(parent, text="Supported Rules", font=self.f_label,
                 fg=ACCENT2, bg=BG_DARK).pack(anchor="w", pady=(12, 4))
        self.lbl_rules = tk.Label(
            parent,
            text=("• Power Rule\n• Constant Rule\n"
                  "• Sum / Difference Rule\n• Chain Rule (basic)\n"
                  "• Product Rule\n• Quotient Rule"),
            font=self.f_sub, fg=TEXT_SEC, bg=BG_DARK, justify="left",
        )
        self.lbl_rules.pack(anchor="w", padx=4)

        btn_frame = tk.Frame(parent, bg=BG_DARK)
        btn_frame.pack(fill="x", pady=(16, 0))

        tk.Button(btn_frame, text="▶  COMPUTE", font=self.f_btn,
                  bg=ACCENT, fg=BG_DARK,
                  activebackground="#5ADBA8", activeforeground=BG_DARK,
                  relief="flat", bd=0, padx=10, pady=8, cursor="hand2",
                  command=self._on_compute
                  ).pack(fill="x", pady=(0, 8))

        self.btn_clear = tk.Button(
            btn_frame, text="✕  CLEAR", font=self.f_btn,
            bg=ACCENT2, fg=BG_DARK,
            activebackground="#D96BB8", activeforeground=BG_DARK,
            relief="flat", bd=0, padx=10, pady=8, cursor="hand2",
            command=self._on_clear_or_stop,
        )
        self.btn_clear.pack(fill="x")

    def _build_right(self, parent):
        ans_frame = tk.Frame(parent, bg=BG_PANEL, relief="flat")
        ans_frame.pack(fill="x", pady=(4, 10))
        tk.Label(ans_frame, text=" FINAL ANSWER ", font=self.f_label,
                 fg=BG_DARK, bg=ACCENT).pack(side="left")
        self.lbl_answer = tk.Label(ans_frame, text="—",
                                   font=self.f_answer, fg=GOLD, bg=BG_PANEL, padx=10)
        self.lbl_answer.pack(side="left", fill="x", expand=True)

        self.lbl_method_badge = tk.Label(
            ans_frame,
            text="—",
            font=self.f_sub, fg=BG_DARK, bg=TEXT_SEC,
            padx=6, pady=2,
        )
        self.lbl_method_badge.pack(side="right", padx=6)

        trail_hdr = tk.Frame(parent, bg=BG_DARK)
        trail_hdr.pack(fill="x")
        tk.Label(trail_hdr, text="SOLUTION TRAIL", font=self.f_label,
                 fg=ACCENT, bg=BG_DARK).pack(side="left")
        tk.Label(trail_hdr, text="(step-by-step audit log)",
                 font=self.f_sub, fg=TEXT_SEC, bg=BG_DARK).pack(side="left", padx=8)

        trail_container = tk.Frame(parent, bg=BORDER, pady=1, padx=1)
        trail_container.pack(fill="both", expand=True, pady=(6, 4))
        self.trail_text = scrolledtext.ScrolledText(
            trail_container,
            font=self.f_trail,
            bg=BG_INPUT, fg=TEXT_PRI,
            insertbackground=ACCENT,
            relief="flat", bd=0,
            wrap="word", state="disabled",
            padx=12, pady=10,
        )
        self.trail_text.pack(fill="both", expand=True)

        self.trail_text.tag_config("header",  foreground=ACCENT,  font=self.f_label)
        self.trail_text.tag_config("section", foreground=ACCENT2, font=self.f_label)
        self.trail_text.tag_config("step",    foreground=TEXT_PRI)
        self.trail_text.tag_config("answer",  foreground=GOLD,    font=self.f_answer)
        self.trail_text.tag_config("verify",  foreground="#7DDBF9")
        self.trail_text.tag_config("summary", foreground=TEXT_SEC, font=self.f_sub)
        self.trail_text.tag_config("dim",     foreground=TEXT_SEC)
        self.trail_text.tag_config("rule",    foreground=GOLD)
        self.trail_text.tag_config("pass",    foreground=OK_GRN)
        self.trail_text.tag_config("fail",    foreground=ERR_RED)
        self.trail_text.tag_config("warn",    foreground=WARN_YEL)

        self.status_var = tk.StringVar(value="Ready — enter f(x) and click COMPUTE")
        self.lbl_status = tk.Label(parent, textvariable=self.status_var,
                                   font=self.f_sub, fg=TEXT_SEC, bg=BG_DARK, anchor="w")
        self.lbl_status.pack(fill="x", pady=(2, 0))

    # ── method selection popup ────────────────────────────────────────────────
    def _show_method_popup(self, on_confirm):
        popup = tk.Toplevel(self)
        popup.title("Select Method")
        popup.configure(bg=BG_PANEL)
        popup.resizable(False, False)
        popup.grab_set()

        popup_method = tk.StringVar(value=self._method_var.get())
        popup_scheme = tk.StringVar(value=self._scheme_var.get())

        # top accent bar
        tk.Frame(popup, bg=ACCENT, height=4).pack(fill="x")

        # title
        title_frame = tk.Frame(popup, bg=BG_PANEL, padx=28, pady=16)
        title_frame.pack(fill="x")
        tk.Label(title_frame,
                 text="SELECT DIFFERENTIATION METHOD",
                 font=font.Font(family="Courier New", size=11, weight="bold"),
                 fg=ACCENT, bg=BG_PANEL).pack(anchor="w")
        tk.Label(title_frame,
                 text="Choose how the derivative will be computed.",
                 font=font.Font(family="Courier New", size=9),
                 fg=TEXT_SEC, bg=BG_PANEL).pack(anchor="w", pady=(2, 0))

        tk.Frame(popup, bg=BORDER, height=1).pack(fill="x", padx=20)

        content = tk.Frame(popup, bg=BG_PANEL, padx=28, pady=18)
        content.pack(fill="x")

        # Symbolic card
        sym_card = tk.Frame(content, bg=BG_INPUT, pady=10, padx=14)
        sym_card.pack(fill="x", pady=(0, 10))

        rb_sym = tk.Radiobutton(
            sym_card,
            text="  Symbolic  —  Exact Derivative",
            variable=popup_method, value="symbolic",
            font=font.Font(family="Courier New", size=10, weight="bold"),
            fg=ACCENT, bg=BG_INPUT,
            activebackground=BG_INPUT, activeforeground=ACCENT,
            selectcolor=BG_DARK,
            relief="flat", cursor="hand2",
        )
        rb_sym.pack(anchor="w")
        tk.Label(sym_card,
                 text="     Uses algebraic rules (Power, Product, Chain…)\n"
                      "     Returns an exact symbolic expression.",
                 font=font.Font(family="Courier New", size=8),
                 fg=TEXT_SEC, bg=BG_INPUT, justify="left").pack(anchor="w", pady=(2, 0))

        # Numerical card
        num_card = tk.Frame(content, bg=BG_INPUT, pady=10, padx=14)
        num_card.pack(fill="x", pady=(0, 6))

        rb_num = tk.Radiobutton(
            num_card,
            text="  Numerical  —  Finite Difference Approximation",
            variable=popup_method, value="numerical",
            font=font.Font(family="Courier New", size=10, weight="bold"),
            fg=ACCENT3, bg=BG_INPUT,
            activebackground=BG_INPUT, activeforeground=ACCENT3,
            selectcolor=BG_DARK,
            relief="flat", cursor="hand2",
        )
        rb_num.pack(anchor="w")
        tk.Label(num_card,
                 text="     Approximates via finite difference formula.\n"
                      "     Requires an evaluation point x = value.",
                 font=font.Font(family="Courier New", size=8),
                 fg=TEXT_SEC, bg=BG_INPUT, justify="left").pack(anchor="w", pady=(2, 0))

        # Scheme sub-selector inside numerical card
        scheme_frame = tk.Frame(num_card, bg=BG_INPUT)
        tk.Label(scheme_frame,
                 text="     Scheme:",
                 font=font.Font(family="Courier New", size=9, weight="bold"),
                 fg=TEXT_SEC, bg=BG_INPUT).pack(anchor="w", pady=(6, 2))
        for val, lbl in [
            ("central",  "Central    O(h²) — recommended"),
            ("forward",  "Forward    O(h)"),
            ("backward", "Backward   O(h)"),
        ]:
            tk.Radiobutton(
                scheme_frame,
                text=f"       {lbl}",
                variable=popup_scheme, value=val,
                font=font.Font(family="Courier New", size=9),
                fg=ACCENT3, bg=BG_INPUT,
                activebackground=BG_INPUT, activeforeground=ACCENT3,
                selectcolor=BG_DARK,
                relief="flat", cursor="hand2",
            ).pack(anchor="w", pady=1)

        def show_scheme():
            scheme_frame.pack(fill="x", pady=(8, 0))

        def hide_scheme():
            scheme_frame.pack_forget()

        rb_sym.config(command=hide_scheme)
        rb_num.config(command=show_scheme)

        # show scheme if numerical already selected
        if popup_method.get() == "numerical":
            show_scheme()

        tk.Frame(popup, bg=BORDER, height=1).pack(fill="x", padx=20)

        # buttons
        btn_frame = tk.Frame(popup, bg=BG_PANEL, padx=28, pady=14)
        btn_frame.pack(fill="x")

        def on_proceed():
            chosen_method = popup_method.get()
            chosen_scheme = popup_scheme.get()
            self._method_var.set(chosen_method)
            self._scheme_var.set(chosen_scheme)
            if chosen_method == "numerical":
                self.lbl_point.config(
                    text="Evaluate at x = (REQUIRED for numerical)", fg=ERR_RED)
            else:
                self.lbl_point.config(
                    text="Evaluate at x = (optional)", fg=TEXT_SEC)
            popup.destroy()
            on_confirm(chosen_method, chosen_scheme)

        tk.Button(btn_frame, text="▶  PROCEED",
                  font=font.Font(family="Courier New", size=10, weight="bold"),
                  bg=ACCENT, fg=BG_DARK,
                  activebackground="#5ADBA8", activeforeground=BG_DARK,
                  relief="flat", bd=0, padx=14, pady=7, cursor="hand2",
                  command=on_proceed).pack(side="right", padx=(8, 0))

        tk.Button(btn_frame, text="  CANCEL  ",
                  font=font.Font(family="Courier New", size=10, weight="bold"),
                  bg=BORDER, fg=TEXT_SEC,
                  activebackground=BG_INPUT, activeforeground=TEXT_PRI,
                  relief="flat", bd=0, padx=14, pady=7, cursor="hand2",
                  command=popup.destroy).pack(side="right")

        # center over main window
        self.update_idletasks()
        popup.update_idletasks()
        mx = self.winfo_x() + (self.winfo_width()  // 2) - (popup.winfo_width()  // 2)
        my = self.winfo_y() + (self.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{mx}+{my}")

    # ── helpers ───────────────────────────────────────────────────────────────
    def _section_label(self, parent, text):
        tk.Label(parent, text=text, font=self.f_label,
                 fg=TEXT_SEC, bg=BG_DARK).pack(anchor="w", pady=(10, 2))

    def _entry(self, parent):
        e = tk.Entry(parent, font=self.f_input,
                     bg=BG_INPUT, fg=TEXT_PRI,
                     insertbackground=ACCENT,
                     relief="flat", bd=0,
                     highlightthickness=1,
                     highlightcolor=ACCENT,
                     highlightbackground=BORDER)
        e.pack(fill="x", ipady=5, padx=2)
        return e

    def _error_label(self, parent):
        lbl = tk.Label(parent, text="", font=self.f_sub,
                       fg=ERR_RED, bg=BG_DARK, anchor="w")
        lbl.pack(fill="x", padx=4)
        return lbl

    def _set_field_error(self, entry, err_lbl, msg):
        entry.config(highlightcolor=ERR_RED, highlightbackground=ERR_RED,
                     highlightthickness=1)
        err_lbl.config(text=f"  ⚠  {msg}")

    def _clear_field_error(self, entry, err_lbl):
        entry.config(highlightcolor=ACCENT, highlightbackground=BORDER,
                     highlightthickness=1)
        err_lbl.config(text="")

    def _clear_all_errors(self):
        for entry, lbl in [
            (self.entry_fx,    self.err_fx),
            (self.entry_var,   self.err_var),
            (self.entry_order, self.err_order),
            (self.entry_point, self.err_point),
        ]:
            self._clear_field_error(entry, lbl)

    def _add_placeholder(self, entry, text):
        entry._placeholder     = text
        entry._has_placeholder = False

        def _show(e=None):
            if not entry.get():
                entry.insert(0, text)
                entry.config(fg=TEXT_SEC)
                entry._has_placeholder = True

        def _hide(e=None):
            if entry._has_placeholder:
                entry.delete(0, "end")
                entry.config(fg=TEXT_PRI)
                entry._has_placeholder = False

        entry.bind("<FocusIn>",  _hide)
        entry.bind("<FocusOut>", _show)
        _show()

    def _remove_placeholder(self, entry):
        if getattr(entry, "_has_placeholder", False):
            entry.delete(0, "end")
            entry.config(fg=TEXT_PRI)
            entry._has_placeholder = False

    def _real_value(self, entry):
        if getattr(entry, "_has_placeholder", False):
            return ""
        return entry.get().strip()

    def _set_generating(self, state: bool):
        self._generating = state
        if state:
            self.btn_clear.config(text="⏹  STOP", bg=ERR_RED,
                                  activebackground="#CC4444")
        else:
            self.btn_clear.config(text="✕  CLEAR", bg=ACCENT2,
                                  activebackground="#D96BB8")

    def _on_clear_or_stop(self):
        if self._generating:
            self.logger.stop()
        else:
            self._do_clear()

    def _do_clear(self):
        self._clear_all_errors()
        self.logger.clear()
        self.lbl_answer.config(text="—", fg=GOLD)
        self.lbl_method_badge.config(text="—", bg=TEXT_SEC)
        self.lbl_status.config(fg=TEXT_SEC)
        self.status_var.set("Cleared — ready for new input")
        self.lbl_point.config(text="Evaluate at x = (optional)", fg=TEXT_SEC)
        for entry, ph in [
            (self.entry_fx,    "x^3 + 2x^2 - 5x + 1"),
            (self.entry_var,   "x"),
            (self.entry_order, "1"),
            (self.entry_point, "2.5   (leave blank to skip)"),
        ]:
            entry.delete(0, "end")
            self._add_placeholder(entry, ph)

    def _show_stop_popup(self, reason: str, outcome: str):
        popup = tk.Toplevel(self)
        popup.title("Completion / Stopping Condition")
        popup.configure(bg=BG_PANEL)
        popup.resizable(False, False)

        if outcome == "manual":
            accent_col = ERR_RED
            icon_text  = "⏹  MANUALLY STOPPED"
        elif outcome == "validation":
            accent_col = WARN_YEL
            icon_text  = "⚠  COMPUTATION STOPPED"
        else:
            accent_col = OK_GRN
            icon_text  = "✔  COMPUTATION COMPLETE"

        tk.Frame(popup, bg=accent_col, height=6).pack(fill="x")

        title_frame = tk.Frame(popup, bg=BG_PANEL, padx=24, pady=14)
        title_frame.pack(fill="x")
        tk.Label(title_frame,
                 text="🛑  COMPLETION / STOPPING CONDITION",
                 font=font.Font(family="Courier New", size=11, weight="bold"),
                 fg=accent_col, bg=BG_PANEL).pack(anchor="w")
        tk.Label(title_frame,
                 text=icon_text,
                 font=font.Font(family="Courier New", size=9),
                 fg=TEXT_SEC, bg=BG_PANEL).pack(anchor="w", pady=(2, 0))

        tk.Frame(popup, bg=BORDER, height=1).pack(fill="x", padx=24)

        msg_frame = tk.Frame(popup, bg=BG_PANEL, padx=24, pady=16)
        msg_frame.pack(fill="x")
        tk.Label(msg_frame,
                 text=reason,
                 font=font.Font(family="Courier New", size=10),
                 fg=TEXT_PRI, bg=BG_PANEL,
                 wraplength=380, justify="left").pack(anchor="w")

        tk.Frame(popup, bg=BORDER, height=1).pack(fill="x", padx=24)

        btn_frame2 = tk.Frame(popup, bg=BG_PANEL, padx=24, pady=12)
        btn_frame2.pack(fill="x")
        tk.Button(btn_frame2, text="  OK  ",
                  font=font.Font(family="Courier New", size=10, weight="bold"),
                  bg=accent_col, fg=BG_DARK,
                  activebackground=BG_INPUT, activeforeground=accent_col,
                  relief="flat", bd=0, padx=16, pady=6, cursor="hand2",
                  command=popup.destroy).pack(side="right")

        self.update_idletasks()
        popup.update_idletasks()
        mx = self.winfo_x() + (self.winfo_width()  // 2) - (popup.winfo_width()  // 2)
        my = self.winfo_y() + (self.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{mx}+{my}")

    # ── compute ───────────────────────────────────────────────────────────────
    def _on_compute(self):
        if self._generating:
            return
        self._show_method_popup(self._do_compute)

    def _do_compute(self, method: str, scheme: str):
        self._clear_all_errors()
        raw_fx    = self._real_value(self.entry_fx)
        raw_var   = self._real_value(self.entry_var)
        raw_order = self._real_value(self.entry_order)
        raw_point = self._real_value(self.entry_point)

        self.logger.clear()
        self.lbl_answer.config(text="…", fg=TEXT_SEC)
        self.lbl_status.config(fg=TEXT_SEC)
        self.status_var.set("Computing …")
        self.update_idletasks()

        if method == "numerical":
            self.lbl_method_badge.config(text="NUMERICAL", bg=ACCENT3, fg=BG_DARK)
        else:
            self.lbl_method_badge.config(text="SYMBOLIC", bg=ACCENT, fg=BG_DARK)

        if method == "numerical":
            result = self.num_engine.validate_and_compute(
                raw_fx, raw_var, raw_order, raw_point, scheme=scheme
            )
        else:
            result = self.sym_engine.validate_and_compute(
                raw_fx, raw_var, raw_order, raw_point
            )

        full_log = result.get("log", [])

        if not result["ok"]:
            self.lbl_answer.config(text="Error — see trail", fg=ERR_RED)
            self.lbl_status.config(fg=ERR_RED)
            self.status_var.set("⚠  Validation failed  —  check highlighted fields")
            for field, msg in result["field_errors"].items():
                if field == "fx":
                    self._set_field_error(self.entry_fx,    self.err_fx,    msg)
                elif field == "var":
                    self._set_field_error(self.entry_var,   self.err_var,   msg)
                elif field == "order":
                    self._set_field_error(self.entry_order, self.err_order, msg)
                elif field == "point":
                    self._set_field_error(self.entry_point, self.err_point, msg)

            reason = "  \n".join(result["field_errors"].values())
            self.logger.animate(
                full_log, delay_ms=38,
                on_done=lambda _: self._show_stop_popup(reason, "validation")
            )
            return

        self._set_generating(True)

        def on_animation_done(outcome):
            self._set_generating(False)
            if outcome == "stopped":
                self.lbl_answer.config(text="—", fg=GOLD)
                self.lbl_status.config(fg=TEXT_SEC)
                self.status_var.set("Stopped — no result")
                self._show_stop_popup("User pressed Stop.", "manual")
            else:
                self.lbl_answer.config(text=result["answer"], fg=GOLD)
                self.lbl_status.config(fg=TEXT_SEC)
                self.status_var.set(
                    f"Done  [{method.capitalize()}]  —  {result['timestamp']}"
                )
                self._show_stop_popup("Computation Complete", "done")

        self.logger.animate(full_log, delay_ms=38, on_done=on_animation_done)

    def _on_clear(self):
        if not self._generating:
            self._do_clear()


if __name__ == "__main__":
    app = DerivativeApp()
    app.mainloop()
