"""
Symbolic Derivative Generator
Week 1 - UI Skeleton with placeholder trail output
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, font
from datetime import datetime
import sys


# ── Colour palette ──────────────────────────────────────────────────────────
BG_DARK   = "#0D0F14"
BG_PANEL  = "#13161E"
BG_INPUT  = "#1A1E2A"
ACCENT    = "#7DF9C2"       # neon mint
ACCENT2   = "#F97DDB"       # neon pink
GOLD      = "#FFD166"
TEXT_PRI  = "#E8EAF0"
TEXT_SEC  = "#8890A6"
BORDER    = "#252B3B"
BTN_COMP  = "#7DF9C2"
BTN_CLR   = "#F97DDB"
BTN_TXT   = "#0D0F14"


class DerivativeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("∂ Symbolic Derivative Generator")
        self.geometry("980x720")
        self.minsize(820, 600)
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

        self._build_fonts()
        self._build_ui()

    # ── Fonts ────────────────────────────────────────────────────────────────
    def _build_fonts(self):
        self.f_title  = font.Font(family="Courier New", size=18, weight="bold")
        self.f_label  = font.Font(family="Courier New", size=10, weight="bold")
        self.f_input  = font.Font(family="Courier New", size=12)
        self.f_trail  = font.Font(family="Courier New", size=10)
        self.f_answer = font.Font(family="Courier New", size=13, weight="bold")
        self.f_sub    = font.Font(family="Courier New", size=9)
        self.f_btn    = font.Font(family="Courier New", size=11, weight="bold")

    # ── Main UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header bar ──────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG_PANEL, height=64)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="∂  SYMBOLIC DERIVATIVE GENERATOR",
            font=self.f_title,
            fg=ACCENT, bg=BG_PANEL
        ).pack(side="left", padx=22, pady=14)

        tk.Label(
            header,
            text="Basic Rules Engine  //  Week 1 Skeleton",
            font=self.f_sub,
            fg=TEXT_SEC, bg=BG_PANEL
        ).pack(side="right", padx=22, pady=20)

        sep = tk.Frame(self, bg=ACCENT, height=2)
        sep.pack(fill="x")

        # ── Body: left input  +  right trail ────────────────────────────────
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        left  = tk.Frame(body, bg=BG_DARK, width=340)
        right = tk.Frame(body, bg=BG_DARK)
        left.pack(side="left", fill="y", padx=(0,10))
        right.pack(side="left", fill="both", expand=True)
        left.pack_propagate(False)

        self._build_left(left)
        self._build_right(right)

    # ── Left panel ───────────────────────────────────────────────────────────
    def _build_left(self, parent):
        # Title
        tk.Label(parent, text="INPUT PANEL", font=self.f_label,
                 fg=ACCENT, bg=BG_DARK).pack(anchor="w", pady=(4,6))

        # Function entry
        self._section_label(parent, "f(x) =")
        self.entry_fx = self._entry(parent)
        self.entry_fx.insert(0, "x**3 + 2*x**2 - 5*x + 1")

        # Variable
        self._section_label(parent, "Variable")
        self.entry_var = self._entry(parent)
        self.entry_var.insert(0, "x")

        # Order
        self._section_label(parent, "Derivative Order (n)")
        self.entry_order = self._entry(parent)
        self.entry_order.insert(0, "1")

        # Eval point
        self._section_label(parent, "Evaluate at x = (optional)")
        self.entry_point = self._entry(parent)
        self.entry_point.insert(0, "")

        # Rule hint
        tk.Label(parent, text="Supported Rules",
                 font=self.f_label, fg=ACCENT2, bg=BG_DARK).pack(anchor="w", pady=(16,4))
        rules_txt = (
            "• Power Rule\n"
            "• Constant Rule\n"
            "• Sum / Difference Rule\n"
            "• Chain Rule (basic)\n"
            "• Product Rule\n"
            "• Quotient Rule"
        )
        tk.Label(parent, text=rules_txt, font=self.f_sub,
                 fg=TEXT_SEC, bg=BG_DARK, justify="left").pack(anchor="w", padx=4)

        # Buttons
        btn_frame = tk.Frame(parent, bg=BG_DARK)
        btn_frame.pack(fill="x", pady=(20,0))

        self.btn_compute = tk.Button(
            btn_frame, text="▶  COMPUTE",
            font=self.f_btn, bg=BTN_COMP, fg=BTN_TXT,
            activebackground=ACCENT, activeforeground=BTN_TXT,
            relief="flat", bd=0, padx=10, pady=8, cursor="hand2",
            command=self._on_compute
        )
        self.btn_compute.pack(fill="x", pady=(0,8))

        self.btn_clear = tk.Button(
            btn_frame, text="✕  CLEAR",
            font=self.f_btn, bg=BTN_CLR, fg=BTN_TXT,
            activebackground=ACCENT2, activeforeground=BTN_TXT,
            relief="flat", bd=0, padx=10, pady=8, cursor="hand2",
            command=self._on_clear
        )
        self.btn_clear.pack(fill="x")

        # Sample problems
        tk.Label(parent, text="Sample Problems",
                 font=self.f_label, fg=GOLD, bg=BG_DARK).pack(anchor="w", pady=(20,4))
        samples = [
            ("1", "x**3 + 2*x**2 - 5*x + 1",  "1", ""),
            ("2", "3*x**4 - 7*x**2 + 2",        "2", ""),
            ("3", "x**5 / 5 + sin(x)",           "1", "0"),
        ]
        for num, fx, order, pt in samples:
            row = tk.Frame(parent, bg=BG_INPUT, pady=4)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"#{num}", font=self.f_sub, fg=ACCENT,
                     bg=BG_INPUT, width=3).pack(side="left", padx=6)
            tk.Label(row, text=f"f(x)={fx}\n  order={order}  pt={pt if pt else '—'}",
                     font=self.f_sub, fg=TEXT_PRI,
                     bg=BG_INPUT, justify="left").pack(side="left")
            tk.Button(row, text="Load", font=self.f_sub,
                      bg=BORDER, fg=ACCENT, relief="flat",
                      cursor="hand2",
                      command=lambda f=fx, o=order, p=pt: self._load_sample(f,o,p)
                      ).pack(side="right", padx=6)

    # ── Right panel ──────────────────────────────────────────────────────────
    def _build_right(self, parent):
        # Final Answer box
        ans_frame = tk.Frame(parent, bg=BG_PANEL, relief="flat")
        ans_frame.pack(fill="x", pady=(4,10))
        tk.Label(ans_frame, text=" FINAL ANSWER ", font=self.f_label,
                 fg=BTN_TXT, bg=ACCENT).pack(side="left")
        self.lbl_answer = tk.Label(
            ans_frame, text="—",
            font=self.f_answer, fg=GOLD, bg=BG_PANEL, padx=10
        )
        self.lbl_answer.pack(side="left", fill="x", expand=True)

        # Solution Trail label
        trail_hdr = tk.Frame(parent, bg=BG_DARK)
        trail_hdr.pack(fill="x")
        tk.Label(trail_hdr, text="SOLUTION TRAIL", font=self.f_label,
                 fg=ACCENT, bg=BG_DARK).pack(side="left")
        tk.Label(trail_hdr, text="(full step-by-step audit log)",
                 font=self.f_sub, fg=TEXT_SEC, bg=BG_DARK).pack(side="left", padx=8)

        # Scrollable trail text area
        trail_container = tk.Frame(parent, bg=BORDER, pady=1, padx=1)
        trail_container.pack(fill="both", expand=True, pady=(6,4))

        self.trail_text = scrolledtext.ScrolledText(
            trail_container,
            font=self.f_trail,
            bg=BG_INPUT, fg=TEXT_PRI,
            insertbackground=ACCENT,
            relief="flat", bd=0,
            wrap="word",
            state="disabled",
            padx=12, pady=10,
        )
        self.trail_text.pack(fill="both", expand=True)

        # Tag colours
        self.trail_text.tag_config("header",   foreground=ACCENT,  font=self.f_label)
        self.trail_text.tag_config("section",  foreground=ACCENT2, font=self.f_label)
        self.trail_text.tag_config("step",     foreground=TEXT_PRI)
        self.trail_text.tag_config("answer",   foreground=GOLD,    font=self.f_answer)
        self.trail_text.tag_config("verify",   foreground="#7DDBF9")
        self.trail_text.tag_config("summary",  foreground=TEXT_SEC, font=self.f_sub)
        self.trail_text.tag_config("dim",      foreground=TEXT_SEC)
        self.trail_text.tag_config("rule",     foreground="#FFD166")

        # Status bar
        self.status_var = tk.StringVar(value="Ready — enter f(x) and click COMPUTE")
        tk.Label(parent, textvariable=self.status_var,
                 font=self.f_sub, fg=TEXT_SEC, bg=BG_DARK,
                 anchor="w").pack(fill="x", pady=(2,0))

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _section_label(self, parent, text):
        tk.Label(parent, text=text, font=self.f_label,
                 fg=TEXT_SEC, bg=BG_DARK).pack(anchor="w", pady=(10,2))

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
        self.entry_fx.delete(0, "end");    self.entry_fx.insert(0, fx)
        self.entry_order.delete(0, "end"); self.entry_order.insert(0, order)
        self.entry_point.delete(0, "end"); self.entry_point.insert(0, pt)
        self.status_var.set(f"Sample loaded: f(x) = {fx}")

    # ── Compute / Clear ───────────────────────────────────────────────────────
    def _on_clear(self):
        for e in (self.entry_fx, self.entry_var, self.entry_order, self.entry_point):
            e.delete(0, "end")
        self.entry_var.insert(0, "x")
        self.entry_order.insert(0, "1")
        self._trail_clear()
        self.lbl_answer.config(text="—")
        self.status_var.set("Cleared — ready for new input")

    def _on_compute(self):
        fx    = self.entry_fx.get().strip()
        var   = self.entry_var.get().strip() or "x"
        order = self.entry_order.get().strip() or "1"
        point = self.entry_point.get().strip()

        if not fx:
            self.status_var.set("⚠  Please enter f(x) first.")
            return

        self._trail_clear()
        self.status_var.set("Computing …")
        self.update_idletasks()

        self._run_placeholder_trail(fx, var, order, point)

    # ── Placeholder Solution Trail (Week 1) ──────────────────────────────────
    def _run_placeholder_trail(self, fx, var, order, pt):
        ts = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

        divider = "─" * 62 + "\n"

        # HEADER
        self._trail_write("╔══════════════════════════════════════════════════════════════╗\n", "header")
        self._trail_write("║   SYMBOLIC DERIVATIVE GENERATOR  —  SOLUTION TRAIL           ║\n", "header")
        self._trail_write("╚══════════════════════════════════════════════════════════════╝\n\n", "header")

        # GIVEN
        self._trail_write("① GIVEN\n", "section")
        self._trail_write(divider, "dim")
        self._trail_write(f"   f({var})       =  {fx}\n", "step")
        self._trail_write(f"   Variable      =  {var}\n", "step")
        self._trail_write(f"   Order (n)     =  {order}\n", "step")
        self._trail_write(f"   Evaluate at   =  {pt if pt else 'Not specified'}\n\n", "step")

        # METHOD
        self._trail_write("② METHOD\n", "section")
        self._trail_write(divider, "dim")
        self._trail_write("   Name          :  Symbolic Differentiation (Basic Rules)\n", "step")
        self._trail_write("   Rules applied :  Power, Constant, Sum/Difference,\n", "step")
        self._trail_write("                    Constant Multiple, Chain, Product, Quotient\n", "step")
        self._trail_write("   Library       :  SymPy (planned — stub in Week 1)\n\n", "step")

        # STEPS
        self._trail_write("③ STEPS  [placeholder — full engine in Week 2]\n", "section")
        self._trail_write(divider, "dim")
        self._trail_write(f"   Step 1  Parse f({var}) into symbolic expression tree\n", "step")
        self._trail_write(f"           → Expression  :  {fx}\n\n", "rule")

        self._trail_write(f"   Step 2  Identify each term and applicable rule\n", "step")
        self._trail_write(f"           → [rule detection will populate here]\n\n", "rule")

        self._trail_write(f"   Step 3  Apply derivative rule term-by-term\n", "step")
        self._trail_write(f"           → d/d{var} [term_1] = ...\n", "rule")
        self._trail_write(f"           → d/d{var} [term_2] = ...\n", "rule")
        self._trail_write(f"           → ...      (n={order} pass(es))\n\n", "rule")

        self._trail_write(f"   Step 4  Simplify / collect like terms\n", "step")
        self._trail_write(f"           → Simplified result will appear here\n\n", "rule")

        if pt:
            self._trail_write(f"   Step 5  Evaluate  f'({pt})\n", "step")
            self._trail_write(f"           → Numeric value will appear here\n\n", "rule")

        # FINAL ANSWER
        self._trail_write("④ FINAL ANSWER\n", "section")
        self._trail_write(divider, "dim")
        placeholder_ans = f"d^{order}/d{var}^{order} [{fx}]  =  [computed in Week 2]"
        self._trail_write(f"   {placeholder_ans}\n\n", "answer")
        self.lbl_answer.config(text="[Computed in Week 2]")

        # VERIFICATION
        self._trail_write("⑤ VERIFICATION\n", "section")
        self._trail_write(divider, "dim")
        self._trail_write("   Method        :  Symbolic back-substitution check\n", "verify")
        self._trail_write("   Check         :  Integrate result → compare to f(x) + C\n", "verify")
        self._trail_write("   Residual      :  [will be computed in Week 2]\n", "verify")
        self._trail_write("   Status        :  ⏳ Pending full engine\n\n", "verify")

        # SUMMARY
        self._trail_write("⑥ SUMMARY\n", "section")
        self._trail_write(divider, "dim")
        self._trail_write(f"   Timestamp     :  {ts}\n", "summary")
        self._trail_write(f"   Python        :  {sys.version.split()[0]}\n", "summary")
        self._trail_write(f"   SymPy         :  [import pending]\n", "summary")
        self._trail_write(f"   Status        :  ✅ UI skeleton complete (Week 1)\n", "summary")
        self._trail_write(f"   Next          :  Full symbolic engine — Week 2\n", "summary")
        self._trail_write("\n" + "═" * 62 + "\n", "dim")

        self.status_var.set(f"✅  Placeholder trail generated  —  {ts}")


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = DerivativeApp()
    app.mainloop()
