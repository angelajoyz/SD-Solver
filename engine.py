"""
engine.py  —  SD Solver  Week 2
Handles all input validation and (stub) symbolic computation.

validate_and_compute() returns a single result dict consumed by main.py.
"""

import sys
from datetime import datetime

import subprocess

try:
    import sympy
    from sympy import symbols, sympify, diff, simplify, SympifyError
    SYMPY_OK = True
    SYMPY_VERSION = sympy.__version__
except ImportError:
    # SymPy not found in this Python — install it automatically
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "sympy"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        import sympy
        from sympy import symbols, sympify, diff, simplify, SympifyError
        SYMPY_OK = True
        SYMPY_VERSION = sympy.__version__
    except Exception:
        SYMPY_OK = False
        SYMPY_VERSION = "NOT INSTALLED"


# ── Validation constants ──────────────────────────────────────────────────────
ORDER_MIN = 1
ORDER_MAX = 10


class DerivativeEngine:
    """Validates inputs and runs symbolic differentiation via SymPy."""

    # ── Public entry point ────────────────────────────────────────────────────
    def validate_and_compute(
        self,
        raw_fx: str,
        raw_var: str,
        raw_order: str,
        raw_point: str,
    ) -> dict:
        """
        Run all validation checks, then compute if valid.
        Always returns a complete result dict so the UI only needs to read it.
        """
        result = self._base_result(raw_fx, raw_var, raw_order, raw_point)
        steps  = result["validation_steps"]

        # ── Check 1: f(x) not empty ──────────────────────────────────────────
        if not raw_fx:
            steps.append(self._step(1, "f(x) field — required, not empty",
                                    "FAIL", "f(x) cannot be empty."))
            result["field_errors"]["fx"] = "f(x) cannot be empty."
            result["ok"] = False
            # No point continuing — remaining checks need a parseable expression
            steps.append(self._step(2, "f(x) — SymPy parse check",     "SKIP", "Skipped (empty input)"))
            steps.append(self._step(3, "Variable — single alpha char",  "SKIP", "Skipped (empty f(x))"))
            steps.append(self._step(4, "Derivative order — integer",    "SKIP", "Skipped (empty f(x))"))
            steps.append(self._step(5, "Derivative order — range 1–10", "SKIP", "Skipped (empty f(x))"))
            steps.append(self._step(6, "Evaluate at x — numeric (opt)", "SKIP", "Skipped (empty f(x))"))
            return result

        steps.append(self._step(1, "f(x) field — required, not empty", "PASS"))

        # ── Check 2: f(x) parseable by SymPy ────────────────────────────────
        sym_expr = None
        if not SYMPY_OK:
            steps.append(self._step(2, "f(x) — SymPy parse check", "FAIL",
                                    "SymPy is not installed. Run: pip install sympy"))
            result["field_errors"]["fx"] = "SymPy not installed."
            result["ok"] = False
        else:
            try:
                sym_expr = sympify(raw_fx, evaluate=False)
                steps.append(self._step(2, "f(x) — SymPy parse check", "PASS",
                                        f"Parsed OK → {sym_expr}"))
            except (SympifyError, TypeError, SyntaxError, ValueError) as exc:
                short = str(exc).split("\n")[0][:80]
                steps.append(self._step(2, "f(x) — SymPy parse check", "FAIL",
                                        f"Cannot parse expression. {short}  "
                                        f"Hint: use Python syntax, e.g. x**3 + 2*x - 1"))
                result["field_errors"]["fx"] = "Not a valid math expression."
                result["ok"] = False

        if not result["ok"]:
            steps.append(self._step(3, "Variable — single alpha char",  "SKIP", "Skipped (parse failed)"))
            steps.append(self._step(4, "Derivative order — integer",    "SKIP", "Skipped (parse failed)"))
            steps.append(self._step(5, "Derivative order — range 1–10", "SKIP", "Skipped (parse failed)"))
            steps.append(self._step(6, "Evaluate at x — numeric (opt)", "SKIP", "Skipped (parse failed)"))
            return result

        # ── Check 3: variable is a single alphabetic character ───────────────
        var_str = raw_var if raw_var else "x"
        if not (len(var_str) == 1 and var_str.isalpha()):
            steps.append(self._step(3, "Variable — single alpha char", "FAIL",
                                    f"'{var_str}' is not a single letter (a–z / A–Z)."))
            result["field_errors"]["var"] = "Must be a single letter, e.g. x, y, t."
            result["ok"] = False
        else:
            steps.append(self._step(3, "Variable — single alpha char", "PASS",
                                    f"'{var_str}' is valid."))
            result["var"] = var_str

        # ── Check 4: order is a positive integer ─────────────────────────────
        order_int = None
        order_str = raw_order if raw_order else "1"
        try:
            order_int = int(order_str)
            if order_int != float(order_str):   # catches "1.5"
                raise ValueError
            steps.append(self._step(4, "Derivative order — integer", "PASS",
                                    f"Order = {order_int}"))
            result["order"] = order_int
        except (ValueError, TypeError):
            steps.append(self._step(4, "Derivative order — integer", "FAIL",
                                    f"'{order_str}' is not an integer.  "
                                    "Hint: enter a whole number, e.g. 1, 2, 3."))
            result["field_errors"]["order"] = "Must be a whole number (1–10)."
            result["ok"] = False

        # ── Check 5: order in range 1–10 ─────────────────────────────────────
        if order_int is not None:
            if ORDER_MIN <= order_int <= ORDER_MAX:
                steps.append(self._step(5, f"Derivative order — range {ORDER_MIN}–{ORDER_MAX}", "PASS",
                                        f"{order_int} is within [{ORDER_MIN}, {ORDER_MAX}]."))
            else:
                steps.append(self._step(5, f"Derivative order — range {ORDER_MIN}–{ORDER_MAX}", "FAIL",
                                        f"{order_int} is out of range.  "
                                        f"Allowed: {ORDER_MIN} ≤ n ≤ {ORDER_MAX}."))
                result["field_errors"]["order"] = f"Order must be between {ORDER_MIN} and {ORDER_MAX}."
                result["ok"] = False
        else:
            steps.append(self._step(5, f"Derivative order — range {ORDER_MIN}–{ORDER_MAX}",
                                    "SKIP", "Skipped (invalid order)"))

        # ── Check 6: evaluate-at point is numeric (optional field) ───────────
        point_val = None
        if raw_point:
            try:
                point_val = float(raw_point)
                steps.append(self._step(6, "Evaluate at x — numeric (opt)", "PASS",
                                        f"x = {point_val}"))
                result["raw_point"] = raw_point
            except ValueError:
                steps.append(self._step(6, "Evaluate at x — numeric (opt)", "FAIL",
                                        f"'{raw_point}' is not a number.  "
                                        "Leave blank or enter a real number, e.g. 0, 2.5, -1."))
                result["field_errors"]["point"] = "Must be a number or left blank."
                result["ok"] = False
        else:
            steps.append(self._step(6, "Evaluate at x — numeric (opt)", "PASS",
                                    "Field is blank — evaluation will be skipped."))

        # ── Bail if any validation failed ─────────────────────────────────────
        if not result["ok"]:
            return result

        # ── Compute (Week 2: SymPy diff as thin stub) ─────────────────────────
        try:
            sym_var  = symbols(result["var"])
            expr     = sympify(raw_fx)
            deriv    = diff(expr, sym_var, result["order"])
            deriv    = simplify(deriv)
            result["answer"] = str(deriv)

            if point_val is not None:
                try:
                    num_val = float(deriv.subs(sym_var, point_val))
                    result["point_value"] = f"{num_val:.6g}"
                except Exception:
                    result["point_value"] = "[evaluation error]"
        except Exception as exc:
            result["ok"] = False
            result["answer"] = "Computation error — see trail"
            steps.append(self._step(7, "SymPy computation", "FAIL", str(exc)[:120]))
            return result

        result["timestamp"] = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        return result

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _step(num: int, label: str, status: str, detail: str = "") -> dict:
        return {"num": num, "label": label, "status": status, "detail": detail}

    @staticmethod
    def _base_result(raw_fx, raw_var, raw_order, raw_point) -> dict:
        return {
            "ok":               True,
            "raw_fx":           raw_fx,
            "raw_var":          raw_var,
            "raw_order":        raw_order,
            "raw_point":        raw_point,
            "var":              raw_var if raw_var else "x",
            "order":            1,
            "answer":           "—",
            "point_value":      None,
            "validation_steps": [],
            "field_errors":     {},
            "timestamp":        datetime.now().strftime("%Y-%m-%d  %H:%M:%S"),
            "python_version":   sys.version.split()[0],
            "sympy_version":    SYMPY_VERSION,
        }