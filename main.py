"""
Symbolic Derivative Generator  —  SD Solver
Week 2: Input Validation + Error Messaging
"""

import tkinter as tk
from tkinter import scrolledtext, font
from datetime import datetime
import sys

from engine import DerivativeEngine

# ── Colour palette ────────────────────────────────────────────────────────────
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


class DerivativeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("∂ SD Solver  —  Week 2")
        self.geometry("980x740")
        self.minsize(820, 600)
        self.configure(bg=BG_DARK)
        self.resizable(True, True)
        self.engine = DerivativeEngine()
        self._build_fonts()
        self._build_ui()

    # ── Fonts ─────────────────────────────────────────────────────────────────
    def _build_fonts(self):
        self.f_title  = font.Font(family="Courier New", size=18, weight="bold")
        self.f_label  = font.Font(family="Courier New", size=10, weight="bold")
        self.f_input  = font.Font(family="Courier New", size=12)
        self.f_trail  = font.Font(family="Courier New", size=10)
        self.f_answer = font.Font(family="Courier New", size=13, weight="bold")
        self.f_sub    = font.Font(family="Courier New", size=9)
        self.f_btn    = font.Font(family="Courier New", size=11, weight="bold")

    # ── Main UI ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG_PANEL, height=64)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(header, text="∂  SD SOLVER  —  SYMBOLIC DERIVATIVE GENERATOR",
                 font=self.f_title, fg=ACCENT, bg=BG_PANEL
                 ).pack(side="left", padx=22, pady=14)
        tk.Label(header, text="Basic Rules Engine  //  Week 2",
                 font=self.f_sub, fg=TEXT_SEC, bg=BG_PANEL
                 ).pack(side="right", padx=22, pady=20)

        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

        # Body
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=16, pady=12)
        left  = tk.Frame(body, bg=BG_DARK, width=340)
        right = tk.Frame(body, bg=BG_DARK)
        left.pack(side="left",  fill="y",    padx=(0, 10))
        right.pack(side="left", fill="both", expand=True)
        left.pack_propagate(False)
        self._build_left(left)
        self._build_right(right)

    # ── Left panel ────────────────────────────────────────────────────────────
    def _build_left(self, parent):
        tk.Label(parent, text="INPUT PANEL", font=self.f_label,
                 fg=ACCENT, bg=BG_DARK).pack(anchor="w", pady=(4, 6))

        # f(x)
        self._section_label(parent, "f(x) =")
        self.entry_fx = self._entry(parent)
        self.err_fx = self._error_label(parent)
        self._add_placeholder(self.entry_fx, "x**3 + 2*x**2 - 5*x + 1")

        # Variable
        self._section_label(parent, "Variable")
        self.entry_var = self._entry(parent)
        self.err_var = self._error_label(parent)
        self._add_placeholder(self.entry_var, "x")

        # Order
        self._section_label(parent, "Derivative Order (n)")
        self.entry_order = self._entry(parent)
        self.err_order = self._error_label(parent)
        self._add_placeholder(self.entry_order, "1")

        # Eval point
        self._section_label(parent, "Evaluate at x = (optional)")
        self.entry_point = self._entry(parent)
        self.err_point = self._error_label(parent)
        self._add_placeholder(self.entry_point, "2.5   (leave blank to skip)")

        # Supported rules hint
        tk.Label(parent, text="Supported Rules", font=self.f_label,
                 fg=ACCENT2, bg=BG_DARK).pack(anchor="w", pady=(12, 4))
        tk.Label(parent,
                 text=("• Power Rule\n• Constant Rule\n"
                       "• Sum / Difference Rule\n• Chain Rule (basic)\n"
                       "• Product Rule\n• Quotient Rule"),
                 font=self.f_sub, fg=TEXT_SEC, bg=BG_DARK, justify="left"
                 ).pack(anchor="w", padx=4)

        # Buttons
        btn_frame = tk.Frame(parent, bg=BG_DARK)
        btn_frame.pack(fill="x", pady=(16, 0))
        tk.Button(btn_frame, text="▶  COMPUTE", font=self.f_btn,
                  bg=ACCENT, fg=BG_DARK,
                  activebackground="#5ADBA8", activeforeground=BG_DARK,
                  relief="flat", bd=0, padx=10, pady=8, cursor="hand2",
                  command=self._on_compute
                  ).pack(fill="x", pady=(0, 8))
        tk.Button(btn_frame, text="✕  CLEAR", font=self.f_btn,
                  bg=ACCENT2, fg=BG_DARK,
                  activebackground="#D96BB8", activeforeground=BG_DARK,
                  relief="flat", bd=0, padx=10, pady=8, cursor="hand2",
                  command=self._on_clear
                  ).pack(fill="x")

        # Sample problems
        tk.Label(parent, text="Sample Problems", font=self.f_label,
                 fg=GOLD, bg=BG_DARK).pack(anchor="w", pady=(18, 4))
        samples = [
            ("1", "x**3 + 2*x**2 - 5*x + 1", "1", ""),
            ("2", "3*x**4 - 7*x**2 + 2",      "2", ""),
            ("3", "x**2 * sin(x)",             "1", "0"),
        ]
        for num, fx, order, pt in samples:
            row = tk.Frame(parent, bg=BG_INPUT, pady=4)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"#{num}", font=self.f_sub, fg=ACCENT,
                     bg=BG_INPUT, width=3).pack(side="left", padx=6)
            tk.Label(row,
                     text=f"f(x)={fx}\n  order={order}  pt={pt if pt else '—'}",
                     font=self.f_sub, fg=TEXT_PRI, bg=BG_INPUT, justify="left"
                     ).pack(side="left")
            tk.Button(row, text="Load", font=self.f_sub,
                      bg=BORDER, fg=ACCENT, relief="flat", cursor="hand2",
                      command=lambda f=fx, o=order, p=pt: self._load_sample(f, o, p)
                      ).pack(side="right", padx=6)

    # ── Right panel ───────────────────────────────────────────────────────────
    def _build_right(self, parent):
        # Final answer bar
        ans_frame = tk.Frame(parent, bg=BG_PANEL, relief="flat")
        ans_frame.pack(fill="x", pady=(4, 10))
        tk.Label(ans_frame, text=" FINAL ANSWER ", font=self.f_label,
                 fg=BG_DARK, bg=ACCENT).pack(side="left")
        self.lbl_answer = tk.Label(ans_frame, text="—",
                                   font=self.f_answer, fg=GOLD, bg=BG_PANEL, padx=10)
        self.lbl_answer.pack(side="left", fill="x", expand=True)

        # Trail header
        trail_hdr = tk.Frame(parent, bg=BG_DARK)
        trail_hdr.pack(fill="x")
        tk.Label(trail_hdr, text="SOLUTION TRAIL", font=self.f_label,
                 fg=ACCENT, bg=BG_DARK).pack(side="left")
        tk.Label(trail_hdr, text="(full step-by-step audit log)",
                 font=self.f_sub, fg=TEXT_SEC, bg=BG_DARK).pack(side="left", padx=8)

        # Trail text area
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

        # Text tags
        self.trail_text.tag_config("header",  foreground=ACCENT,   font=self.f_label)
        self.trail_text.tag_config("section", foreground=ACCENT2,  font=self.f_label)
        self.trail_text.tag_config("step",    foreground=TEXT_PRI)
        self.trail_text.tag_config("answer",  foreground=GOLD,     font=self.f_answer)
        self.trail_text.tag_config("verify",  foreground="#7DDBF9")
        self.trail_text.tag_config("summary", foreground=TEXT_SEC, font=self.f_sub)
        self.trail_text.tag_config("dim",     foreground=TEXT_SEC)
        self.trail_text.tag_config("rule",    foreground=GOLD)
        self.trail_text.tag_config("pass",    foreground=OK_GRN)
        self.trail_text.tag_config("fail",    foreground=ERR_RED)
        self.trail_text.tag_config("warn",    foreground=WARN_YEL)

        # Status bar
        self.status_var = tk.StringVar(value="Ready — enter f(x) and click COMPUTE")
        tk.Label(parent, textvariable=self.status_var,
                 font=self.f_sub, fg=TEXT_SEC, bg=BG_DARK, anchor="w"
                 ).pack(fill="x", pady=(2, 0))

    # ── Helpers ───────────────────────────────────────────────────────────────
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

    def _trail_write(self, text, tag="step"):
        self.trail_text.configure(state="normal")
        self.trail_text.insert("end", text, tag)
        self.trail_text.configure(state="disabled")
        self.trail_text.see("end")

    def _trail_clear(self):
        self.trail_text.configure(state="normal")
        self.trail_text.delete("1.0", "end")
        self.trail_text.configure(state="disabled")

    def _load_sample(self, fx, order, pt):
        self._clear_all_errors()
        for entry, val in [
            (self.entry_fx,    fx),
            (self.entry_var,   "x"),
            (self.entry_order, order),
            (self.entry_point, pt),
        ]:
            self._remove_placeholder(entry)
            entry.delete(0, "end")
            if val:
                entry.insert(0, val)
                entry.config(fg=TEXT_PRI)
        self.status_var.set(f"Sample loaded: f(x) = {fx}")

    # ── Placeholder helpers ───────────────────────────────────────────────────
    def _add_placeholder(self, entry, text):
        """Show greyed-out hint text; disappears on focus."""
        entry._placeholder = text
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
        """Forcibly clear placeholder state (called before inserting real values)."""
        if getattr(entry, "_has_placeholder", False):
            entry.delete(0, "end")
            entry.config(fg=TEXT_PRI)
            entry._has_placeholder = False

    def _real_value(self, entry):
        """Return the entry value, or '' if it currently shows placeholder text."""
        if getattr(entry, "_has_placeholder", False):
            return ""
        return entry.get().strip()

    # ── Clear ─────────────────────────────────────────────────────────────────
    def _on_clear(self):
        self._clear_all_errors()
        self._trail_clear()
        self.lbl_answer.config(text="—", fg=GOLD)
        self.status_var.set("Cleared — ready for new input")
        for entry, ph in [
            (self.entry_fx,    "x**3 + 2*x**2 - 5*x + 1"),
            (self.entry_var,   "x"),
            (self.entry_order, "1"),
            (self.entry_point, "2.5   (leave blank to skip)"),
        ]:
            entry.delete(0, "end")
            self._add_placeholder(entry, ph)

    # ── Compute ───────────────────────────────────────────────────────────────
    def _on_compute(self):
        self._clear_all_errors()

        # Strip placeholder text so empty fields read as ""
        raw_fx    = self._real_value(self.entry_fx)
        raw_var   = self._real_value(self.entry_var)
        raw_order = self._real_value(self.entry_order)
        raw_point = self._real_value(self.entry_point)

        self._trail_clear()
        self.lbl_answer.config(text="…", fg=TEXT_SEC)
        self.status_var.set("Validating inputs …")
        self.update_idletasks()

        # ── Run validation through engine ─────────────────────────────────
        result = self.engine.validate_and_compute(raw_fx, raw_var, raw_order, raw_point)

        # ── Write trail ───────────────────────────────────────────────────
        self._write_trail(result)

        # ── Update answer label ───────────────────────────────────────────
        if result["ok"]:
            self.lbl_answer.config(text=result["answer"], fg=GOLD)
            self.status_var.set(f"✅  Done  —  {result['timestamp']}")
        else:
            self.lbl_answer.config(text="Error — see trail", fg=ERR_RED)
            self.status_var.set(f"⚠  Validation failed  —  check highlighted fields")
            # Highlight offending fields in UI
            for field, msg in result["field_errors"].items():
                if field == "fx":
                    self._set_field_error(self.entry_fx, self.err_fx, msg)
                elif field == "var":
                    self._set_field_error(self.entry_var, self.err_var, msg)
                elif field == "order":
                    self._set_field_error(self.entry_order, self.err_order, msg)
                elif field == "point":
                    self._set_field_error(self.entry_point, self.err_point, msg)

    # ── Trail renderer ────────────────────────────────────────────────────────
    def _write_trail(self, r):
        DIV = "─" * 62 + "\n"

        self._trail_write("╔══════════════════════════════════════════════════════════════╗\n", "header")
        self._trail_write("║   SD SOLVER  —  SOLUTION TRAIL                               ║\n", "header")
        self._trail_write("╚══════════════════════════════════════════════════════════════╝\n\n", "header")

        # ① GIVEN
        self._trail_write("① GIVEN\n", "section")
        self._trail_write(DIV, "dim")
        self._trail_write(f"   f({r['var']})           =  {r['raw_fx']}\n", "step")
        self._trail_write(f"   Variable        =  {r['raw_var']}\n", "step")
        self._trail_write(f"   Order (n)       =  {r['raw_order']}\n", "step")
        self._trail_write(f"   Evaluate at     =  {r['raw_point'] if r['raw_point'] else 'Not specified'}\n\n", "step")

        # ② VALIDATION
        self._trail_write("② VALIDATION\n", "section")
        self._trail_write(DIV, "dim")
        for check in r["validation_steps"]:
            num   = check["num"]
            label = check["label"]
            status = check["status"]   # "PASS" | "FAIL" | "SKIP" | "WARN"
            detail = check.get("detail", "")

            tag = {"PASS": "pass", "FAIL": "fail", "WARN": "warn", "SKIP": "dim"}.get(status, "step")
            icon = {"PASS": "✔", "FAIL": "✘", "WARN": "⚠", "SKIP": "○"}.get(status, " ")

            self._trail_write(f"   Step {num}  {label}\n", "step")
            self._trail_write(f"           {icon}  {status}", tag)
            if detail:
                self._trail_write(f"  —  {detail}", tag)
            self._trail_write("\n\n", "step")

        if not r["ok"]:
            self._trail_write("   ✘  Computation aborted — correct the errors above and retry.\n", "fail")
            self._trail_write("\n" + "═" * 62 + "\n", "dim")
            return

        self._trail_write("   ✔  All checks passed — proceeding to computation.\n\n", "pass")

        # ③ METHOD
        self._trail_write("③ METHOD\n", "section")
        self._trail_write(DIV, "dim")
        self._trail_write(f"   Name            :  Symbolic Differentiation (Basic Rules)\n", "step")
        self._trail_write(f"   Rules applied   :  Power, Constant, Sum/Difference,\n", "step")
        self._trail_write(f"                      Constant Multiple, Chain, Product, Quotient\n", "step")
        self._trail_write(f"   Library         :  SymPy {r['sympy_version']}\n\n", "step")

        # ④ STEPS  (placeholder — full engine Week 4)
        self._trail_write("④ STEPS  [placeholder — full rule engine in Week 4]\n", "section")
        self._trail_write(DIV, "dim")
        var = r["var"]
        fx  = r["raw_fx"]
        n   = r["order"]
        self._trail_write(f"   Step 1  Parse f({var}) into symbolic expression tree\n", "step")
        self._trail_write(f"           → Expression  :  {fx}\n\n", "rule")
        self._trail_write(f"   Step 2  Identify each term and applicable rule\n", "step")
        self._trail_write(f"           → [rule detection will populate in Week 4]\n\n", "rule")
        self._trail_write(f"   Step 3  Apply derivative rule term-by-term  (n={n} pass(es))\n", "step")
        self._trail_write(f"           → d/d{var} [terms] = ...\n\n", "rule")
        self._trail_write(f"   Step 4  Simplify / collect like terms\n", "step")
        self._trail_write(f"           → {r['answer']}\n\n", "rule")

        if r.get("point_value") is not None:
            self._trail_write(f"   Step 5  Evaluate  f'({r['raw_point']})\n", "step")
            self._trail_write(f"           → f'({r['raw_point']})  =  {r['point_value']}\n\n", "rule")

        # ⑤ FINAL ANSWER
        self._trail_write("⑤ FINAL ANSWER\n", "section")
        self._trail_write(DIV, "dim")
        self._trail_write(f"   d^{n}/d{var}^{n} [{fx}]  =  {r['answer']}\n\n", "answer")

        # ⑥ VERIFICATION
        self._trail_write("⑥ VERIFICATION\n", "section")
        self._trail_write(DIV, "dim")
        self._trail_write("   Method          :  Symbolic back-substitution check\n", "verify")
        self._trail_write("   Check           :  Integrate result → compare to f(x) + C\n", "verify")
        self._trail_write("   Residual        :  [will be computed in Week 9]\n", "verify")
        self._trail_write("   Status          :  ⏳ Pending full verification engine\n\n", "verify")

        # ⑦ SUMMARY
        self._trail_write("⑦ SUMMARY\n", "section")
        self._trail_write(DIV, "dim")
        self._trail_write(f"   Timestamp       :  {r['timestamp']}\n", "summary")
        self._trail_write(f"   Python          :  {r['python_version']}\n", "summary")
        self._trail_write(f"   SymPy           :  {r['sympy_version']}\n", "summary")
        self._trail_write(f"   Status          :  ✅ Validation complete (Week 2)\n", "summary")
        self._trail_write(f"   Next            :  Solution Trail logger — Week 3\n", "summary")
        self._trail_write("\n" + "═" * 62 + "\n", "dim")


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = DerivativeApp()
    app.mainloop()