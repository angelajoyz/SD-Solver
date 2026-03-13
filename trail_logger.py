DIV  = "─" * 62
HDIV = "═" * 62

SECTIONS = [
    "GIVEN", "METHOD", "STEPS",
    "FINAL ANSWER", "VERIFICATION", "SUMMARY"
]

SECTION_ICONS = {
    "GIVEN":        "①",
    "METHOD":       "②",
    "STEPS":        "③",
    "FINAL ANSWER": "④",
    "VERIFICATION": "⑤",
    "SUMMARY":      "⑥",
}


class TrailLogger:
    """Writes to a Tkinter ScrolledText widget; auto-numbers STEPS."""

    def __init__(self, widget):
        self._widget       = widget
        self._step_counter = 0
        self._in_steps     = False
        self._log          = []   # list of (text, tag) for future export

    # ── Public API ────────────────────────────────────────────────────────────

    def clear(self):
        """Wipe trail panel and reset counter."""
        self._step_counter = 0
        self._in_steps     = False
        self._log.clear()
        self._widget.configure(state="normal")
        self._widget.delete("1.0", "end")
        self._widget.configure(state="disabled")

    def write_header(self):
        """Print the top banner (called once per computation)."""
        self._write("╔" + "═" * 62 + "╗\n", "header")
        self._write("║   SD SOLVER  —  SOLUTION TRAIL" + " " * 30 + "║\n", "header")
        self._write("╚" + "═" * 62 + "╝\n\n", "header")

    def open_section(self, name: str):
        """Print a standard section heading with divider."""
        icon = SECTION_ICONS.get(name, "◆")
        # Reset step counter when entering STEPS; leave steps mode otherwise
        if name == "STEPS":
            self._step_counter = 0
            self._in_steps = True
        else:
            self._in_steps = False
        self._write(f"{icon} {name}\n", "section")
        self._write(DIV + "\n", "dim")

    def add_step(self, text: str, tag: str = "step"):
        """
        Append one line to the trail.

        Inside a STEPS section the line is auto-prefixed with
        "   Step N  " and the counter increments.
        Outside STEPS (GIVEN / METHOD / etc.) text is indented
        with three spaces but NOT numbered.
        """
        if self._in_steps:
            self._step_counter += 1
            prefix = f"   Step {self._step_counter:<2} "
            self._write(prefix, "dim")
            self._write(text + "\n", tag)
        else:
            self._write("   " + text + "\n", tag)

    def add_detail(self, text: str, tag: str = "rule"):
        """Indented sub-line under the current step (no counter increment)."""
        self._write("            → " + text + "\n", tag)

    def add_kv(self, key: str, value: str, tag: str = "step"):
        """Key-value line used inside GIVEN / METHOD / SUMMARY."""
        self._write(f"   {key:<16}:  {value}\n", tag)

    def add_blank(self):
        """Insert an empty line for spacing."""
        self._write("\n", "dim")

    def close(self):
        """Print the closing double-line divider."""
        self._write("\n" + HDIV + "\n", "dim")

    def get_log(self) -> list:
        """Return a copy of the internal log as a list of (text, tag) tuples."""
        return list(self._log)

    # ── Private ───────────────────────────────────────────────────────────────

    def _write(self, text: str, tag: str = "step"):
        self._log.append((text, tag))
        self._widget.configure(state="normal")
        self._widget.insert("end", text, tag)
        self._widget.configure(state="disabled")
        self._widget.see("end")