DIV  = "─" * 62
HDIV = "═" * 62

SECTION_ICONS = {
    "GIVEN":        "①",
    "METHOD":       "②",
    "STEPS":        "③",
    "FINAL ANSWER": "④",
    "VERIFICATION": "⑤",
    "SUMMARY":      "⑥",
}


class TrailLogger:

    def __init__(self, widget):
        self._widget       = widget
        self._step_counter = 0
        self._in_steps     = False
        self._log          = []
        self._stopped      = False
        self._after_ids    = []
        self._on_done      = None

    def clear(self):
        self._step_counter = 0
        self._in_steps     = False
        self._stopped      = False
        self._log.clear()
        for aid in self._after_ids:
            try:
                self._widget.after_cancel(aid)
            except Exception:
                pass
        self._after_ids.clear()
        self._widget.configure(state="normal")
        self._widget.delete("1.0", "end")
        self._widget.configure(state="disabled")

    def stop(self):
        """Signal the animation to halt after the current chunk."""
        self._stopped = True

    def write_header(self):
        self._write("╔" + "═" * 62 + "╗\n", "header")
        self._write("║   SD SOLVER  —  SOLUTION TRAIL" + " " * 30 + "║\n", "header")
        self._write("╚" + "═" * 62 + "╝\n\n", "header")

    def open_section(self, name: str):
        icon = SECTION_ICONS.get(name, "◆")
        if name == "STEPS":
            self._step_counter = 0
            self._in_steps = True
        else:
            self._in_steps = False
        self._write(f"{icon} {name}\n", "section")
        self._write(DIV + "\n", "dim")

    def add_step(self, text: str, tag: str = "step"):
        if self._in_steps:
            self._step_counter += 1
            prefix = f"   Step {self._step_counter:<2} "
            self._write(prefix, "dim")
            self._write(text + "\n", tag)
        else:
            self._write("   " + text + "\n", tag)

    def add_detail(self, text: str, tag: str = "rule"):
        self._write("            → " + text + "\n", tag)

    def add_kv(self, key: str, value: str, tag: str = "step"):
        self._write(f"   {key:<16}:  {value}\n", tag)

    def add_blank(self):
        self._write("\n", "dim")

    def close(self):
        self._write("\n" + HDIV + "\n", "dim")

    def get_log(self) -> list:
        return list(self._log)

    def animate(self, log: list, delay_ms: int = 18, on_done=None):
        """
        Replay a pre-built log list with a typing delay between each chunk.
        Calls on_done("done") when finished or on_done("stopped") if halted.
        """
        self._on_done = on_done
        self._stopped = False
        self._widget.configure(state="normal")
        self._widget.delete("1.0", "end")
        self._widget.configure(state="disabled")
        self._after_ids.clear()
        self._schedule_chunks(log, 0, delay_ms)

    def _schedule_chunks(self, log: list, index: int, delay_ms: int):
        if self._stopped:
            if self._on_done:
                self._on_done("stopped")
            return
        if index >= len(log):
            if self._on_done:
                self._on_done("done")
            return
        text, tag = log[index]
        self._write_direct(text, tag)
        aid = self._widget.after(
            delay_ms,
            lambda: self._schedule_chunks(log, index + 1, delay_ms)
        )
        self._after_ids.append(aid)

    def _write(self, text: str, tag: str = "step"):
        self._log.append((text, tag))
        self._write_direct(text, tag)

    def _write_direct(self, text: str, tag: str = "step"):
        self._widget.configure(state="normal")
        self._widget.insert("end", text, tag)
        self._widget.configure(state="disabled")
        self._widget.see("end")
