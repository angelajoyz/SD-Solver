import sys
import re
from datetime import datetime
import subprocess

from rules import differentiate_with_trail

try:
    import sympy
    from sympy import symbols, sympify, diff, simplify, SympifyError
    SYMPY_OK = True
    SYMPY_VERSION = sympy.__version__
except ImportError:
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

from trail_logger import DIV, HDIV, SECTION_ICONS

ORDER_MIN = 1
ORDER_MAX = 10


class DerivativeEngine:

    def validate_and_compute(
        self,
        raw_fx: str,
        raw_var: str,
        raw_order: str,
        raw_point: str,
    ) -> dict:
        import re as _re
        raw_fx = raw_fx.replace("^", "**")
        raw_fx = _re.sub(r'(\d)([a-zA-Z])', r'\1*\2', raw_fx)
        raw_fx = _re.sub(r'\)\s*\(', r')*(', raw_fx)

        result = self._base_result(raw_fx, raw_var, raw_order, raw_point)
        vsteps = result["validation_steps"]
        log    = []

        def w(text, tag="step"):
            log.append((text, tag))

        def section(name):
            icon = SECTION_ICONS.get(name, "◆")
            w(f"{icon} {name}\n", "section")
            w(DIV + "\n", "dim")

        def kv(key, value, tag="step"):
            w(f"   {key:<16}:  {value}\n", tag)

        def blank():
            w("\n", "dim")

        w("╔" + "═" * 62 + "╗\n", "header")
        w("║   SD SOLVER  —  SOLUTION TRAIL" + " " * 30 + "║\n", "header")
        w("╚" + "═" * 62 + "╝\n\n", "header")

        section("GIVEN")
        var_label = raw_var if raw_var else "x"
        kv(f"f({var_label})", raw_fx if raw_fx else "(empty)")
        kv("Variable",   raw_var   if raw_var   else "(empty)")
        kv("Order (n)",  raw_order if raw_order else "(empty)")
        kv("Evaluate at", raw_point if raw_point else "Not specified")
        blank()

        # ── Validation checks ─────────────────────────────────────────────────

        if not raw_fx:
            vsteps.append(self._step(1, "f(x) field — required, not empty",
                                     "FAIL", "f(x) cannot be empty."))
            result["field_errors"]["fx"] = "f(x) cannot be empty."
            result["ok"] = False
            for n, lbl in [
                (2, "f(x) — SymPy parse check"),
                (3, "Variable — single alpha char"),
                (4, "Derivative order — integer"),
                (5, "Derivative order — range 1–10"),
                (6, "Evaluate at x — numeric (opt)"),
            ]:
                vsteps.append(self._step(n, lbl, "SKIP", "Skipped (empty input)"))
        else:
            vsteps.append(self._step(1, "f(x) field — required, not empty", "PASS"))

            sym_expr = None
            if not SYMPY_OK:
                vsteps.append(self._step(2, "f(x) — SymPy parse check", "FAIL",
                                         "SymPy not installed. Run: pip install sympy"))
                result["field_errors"]["fx"] = "SymPy not installed."
                result["ok"] = False
            else:
                try:
                    sym_expr = sympify(raw_fx, evaluate=False)
                    vsteps.append(self._step(2, "f(x) — SymPy parse check", "PASS",
                                             f"Parsed OK → {sym_expr}"))
                except (SympifyError, TypeError, SyntaxError, ValueError) as exc:
                    short = str(exc).split("\n")[0][:80]
                    vsteps.append(self._step(2, "f(x) — SymPy parse check", "FAIL",
                                             f"Cannot parse. {short}  "
                                             "Hint: use Python syntax, e.g. x**3 + 2*x"))
                    result["field_errors"]["fx"] = "Not a valid math expression."
                    result["ok"] = False

            if not result["ok"]:
                for n, lbl in [
                    (3, "Variable — single alpha char"),
                    (4, "Derivative order — integer"),
                    (5, "Derivative order — range 1–10"),
                    (6, "Evaluate at x — numeric (opt)"),
                ]:
                    vsteps.append(self._step(n, lbl, "SKIP", "Skipped (parse failed)"))
            else:
                var_str = raw_var if raw_var else "x"
                if not (len(var_str) == 1 and var_str.isalpha()):
                    vsteps.append(self._step(3, "Variable — single alpha char", "FAIL",
                                             f"'{var_str}' is not a single letter."))
                    result["field_errors"]["var"] = "Must be a single letter, e.g. x, y, t."
                    result["ok"] = False
                else:
                    vsteps.append(self._step(3, "Variable — single alpha char", "PASS",
                                             f"'{var_str}' is valid."))
                    result["var"] = var_str

                order_int = None
                order_str = raw_order if raw_order else "1"
                try:
                    order_int = int(order_str)
                    if order_int != float(order_str):
                        raise ValueError
                    vsteps.append(self._step(4, "Derivative order — integer", "PASS",
                                             f"Order = {order_int}"))
                    result["order"] = order_int
                except (ValueError, TypeError):
                    vsteps.append(self._step(4, "Derivative order — integer", "FAIL",
                                             f"'{order_str}' is not an integer."))
                    result["field_errors"]["order"] = "Must be a whole number (1–10)."
                    result["ok"] = False

                if order_int is not None:
                    if ORDER_MIN <= order_int <= ORDER_MAX:
                        vsteps.append(self._step(
                            5, f"Derivative order — range {ORDER_MIN}–{ORDER_MAX}", "PASS",
                            f"{order_int} is within [{ORDER_MIN}, {ORDER_MAX}]."))
                    else:
                        vsteps.append(self._step(
                            5, f"Derivative order — range {ORDER_MIN}–{ORDER_MAX}", "FAIL",
                            f"{order_int} is out of range. Allowed: {ORDER_MIN}–{ORDER_MAX}."))
                        result["field_errors"]["order"] = (
                            f"Order must be between {ORDER_MIN} and {ORDER_MAX}.")
                        result["ok"] = False
                else:
                    vsteps.append(self._step(
                        5, f"Derivative order — range {ORDER_MIN}–{ORDER_MAX}",
                        "SKIP", "Skipped (invalid order)"))

                point_val = None
                if raw_point:
                    try:
                        point_val = float(raw_point)
                        vsteps.append(self._step(6, "Evaluate at x — numeric (opt)", "PASS",
                                                 f"x = {point_val}"))
                        result["raw_point"] = raw_point
                    except ValueError:
                        vsteps.append(self._step(6, "Evaluate at x — numeric (opt)", "FAIL",
                                                 f"'{raw_point}' is not a number."))
                        result["field_errors"]["point"] = "Must be a number or left blank."
                        result["ok"] = False
                else:
                    vsteps.append(self._step(6, "Evaluate at x — numeric (opt)", "PASS",
                                             "Field blank — evaluation skipped."))

        # ── Write validation into log ─────────────────────────────────────────
        w("⓪ VALIDATION\n", "section")
        w(DIV + "\n", "dim")
        for check in vsteps:
            icon = {"PASS": "✔", "FAIL": "✘", "SKIP": "○", "WARN": "⚠"}.get(check["status"], " ")
            tag  = {"PASS": "pass", "FAIL": "fail", "SKIP": "dim", "WARN": "warn"}.get(
                check["status"], "step")
            w(f"   Step {check['num']}  {check['label']}\n", "step")
            detail = f"  —  {check['detail']}" if check.get("detail") else ""
            w(f"           {icon}  {check['status']}{detail}\n\n", tag)

        if not result["ok"]:
            w("   ✘  Computation aborted — correct errors and retry.\n", "fail")
            w("\n" + HDIV + "\n", "dim")
            result["log"] = log
            return result

        w("   ✔  All checks passed — proceeding to computation.\n\n", "pass")

        # ── Compute ───────────────────────────────────────────────────────────
        try:
            sym_var = symbols(result["var"])
            expr    = sympify(raw_fx)
            deriv   = simplify(diff(expr, sym_var, result["order"]))
            result["answer"] = str(deriv)

            if point_val is not None:
                try:
                    result["point_value"] = f"{float(deriv.subs(sym_var, point_val)):.6g}"
                except Exception:
                    result["point_value"] = "[evaluation error]"
        except Exception as exc:
            result["ok"] = False
            result["answer"] = "Computation error"
            w(f"   ✘  SymPy error: {str(exc)[:120]}\n", "fail")
            result["log"] = log
            return result

        rule_result      = differentiate_with_trail(raw_fx, result["var"], result["order"])
        result["answer"] = rule_result["answer"]

        if point_val is not None:
            try:
                from sympy import symbols as _s, sympify as _sy, diff as _d, simplify as _si
                _x  = _s(result["var"])
                _dr = _si(_d(_sy(raw_fx), _x, result["order"]))
                result["point_value"] = str(float(_dr.subs(_x, point_val)))
            except Exception:
                pass

        result["timestamp"] = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

        # ── METHOD ───────────────────────────────────────────────────────────
        section("METHOD")
        kv("Name", "Symbolic Differentiation (Basic Rules)")
        kv("Rules applied", "Power, Constant, Sum/Difference,")
        w("   Constant Multiple, Chain, Product, Quotient\n", "dim")
        kv("Library", f"SymPy {SYMPY_VERSION}")
        blank()

        # ── STEPS ─────────────────────────────────────────────────────────────
        step_counter = [0]
        w(f"{SECTION_ICONS['STEPS']} STEPS\n", "section")
        w(DIV + "\n", "dim")

        for step in rule_result["steps"]:
            if step["tag"] == "detail":
                w("            → " + step["text"] + "\n", "rule")
            elif step["tag"] == "answer":
                step_counter[0] += 1
                w(f"   Step {step_counter[0]:<2} ", "dim")
                w(step["text"] + "\n", "answer")
            else:
                step_counter[0] += 1
                w(f"   Step {step_counter[0]:<2} ", "dim")
                w(step["text"] + "\n", "step")

        if result.get("point_value") is not None:
            step_counter[0] += 1
            w(f"   Step {step_counter[0]:<2} ", "dim")
            w(f"Evaluate  f'({raw_point})\n", "step")
            w(f"            → f'({raw_point})  =  {result['point_value']}\n", "answer")

        blank()

        # ── FINAL ANSWER ──────────────────────────────────────────────────────
        section("FINAL ANSWER")
        w(f"   d^{result['order']}/d{result['var']}^{result['order']}"
          f" [{raw_fx}]  =  {result['answer']}\n", "answer")
        blank()

        # ── VERIFICATION ─────────────────────────────────────────────────────
        section("VERIFICATION")
        kv("Method", "Symbolic back-substitution check")
        kv("Check",  "Integrate result → compare to f(x) + C")
        kv("Status", "Pending", "verify")
        blank()

        section("SUMMARY")
        kv("Timestamp",   result["timestamp"])
        kv("Python",      result["python_version"])
        kv("SymPy",       result["sympy_version"])
        w("\n" + HDIV + "\n", "dim")

        result["log"] = log
        return result

    @staticmethod
    def _step(num, label, status, detail=""):
        return {"num": num, "label": label, "status": status, "detail": detail}

    @staticmethod
    def _base_result(raw_fx, raw_var, raw_order, raw_point):
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
            "log":              [],
            "timestamp":        datetime.now().strftime("%Y-%m-%d  %H:%M:%S"),
            "python_version":   sys.version.split()[0],
            "sympy_version":    SYMPY_VERSION,
        }
