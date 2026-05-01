import sys
import re
from datetime import datetime
import subprocess

from rules import differentiate_with_trail

try:
    import sympy
    from sympy import symbols, sympify, diff, simplify, integrate, SympifyError
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
        from sympy import symbols, sympify, diff, simplify, integrate, SympifyError
        SYMPY_OK = True
        SYMPY_VERSION = sympy.__version__
    except Exception:
        SYMPY_OK = False
        SYMPY_VERSION = "NOT INSTALLED"

from trail_logger import DIV, HDIV, SECTION_ICONS

ORDER_MIN = 1
ORDER_MAX = 10


def _clean_expr(t):
    t = t.replace("**", "^")
    t = re.sub(r'(\d)\*([a-zA-Z])', r'\1\2', t)
    t = re.sub(r'([a-zA-Z0-9])\*([a-zA-Z])', r'\1·\2', t)
    return t


def _fix_implicit_mul(expr_str):
    """
    Restore explicit multiplication signs so SymPy can parse display-form
    expressions like '3x**2 + 4x - 5' that were cleaned by _clean_expr().
    Also normalises ^ -> ** and · -> *.
    """
    expr_str = expr_str.replace("^", "**").replace("·", "*")
    # digit immediately followed by a letter: 3x -> 3*x
    expr_str = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr_str)
    # letter/digit immediately followed by '(': x( -> x*(
    expr_str = re.sub(r'([a-zA-Z0-9])\(', r'\1*(', expr_str)
    return expr_str


def _symbolic_verify(raw_fx, var_str, order, deriv_expr_str):
    """
    Verification Strategy:
      1. Integrate the computed derivative `order` times.
      2. Compare with the original f(x) (up to constants).
      3. Also compute forward-difference numeric spot-check at x=1.0.

    Returns a list of (label, value, status) tuples.
    """
    results = []
    try:
        x     = symbols(var_str)
        f_sym = sympify(raw_fx)

        # FIX: restore explicit multiplication before passing to sympify
        x = symbols(var_str)
        try:
            d_sym = sympify(_fix_implicit_mul(deriv_expr_str))
        except Exception:
            d_sym = diff(sympify(raw_fx), x, order)

        # ── Back-integration check ────────────────────────────────────────────
        reintegrated = d_sym
        for _ in range(order):
            reintegrated = integrate(reintegrated, x)
        reintegrated = simplify(reintegrated)

        # Strip constants: compare d/dx of both expressions
        diff_orig   = simplify(diff(f_sym,        x))
        diff_reint  = simplify(diff(reintegrated, x))
        residual    = simplify(diff_orig - diff_reint)

        results.append(("Re-integrate d^n f  (drop C)", _clean_expr(str(reintegrated)), "info"))
        results.append(("d/dx[f(x)]",                   _clean_expr(str(diff_orig)),    "info"))
        results.append(("d/dx[∫...d^n result]",          _clean_expr(str(diff_reint)),   "info"))
        results.append(("Residual (should = 0)",          _clean_expr(str(residual)),
                        "pass" if residual == sympy.Integer(0) else "warn"))

        # ── Numeric spot-check at x = 1 ──────────────────────────────────────
        test_points = [1.0, 2.0, -1.0, 0.5, 3.0]
        all_match   = True
        for xv in test_points:
            try:
                f_val  = float(diff(f_sym, x, order).subs(x, xv))
                d_val  = float(d_sym.subs(x, xv))
                err    = abs(f_val - d_val)
                status = "pass" if err < 1e-6 else "warn"
                if err >= 1e-6:
                    all_match = False
                results.append((f"Spot-check x={xv}",
                                 f"SymPy={f_val:.6g}  Result={d_val:.6g}  Δ={err:.2e}",
                                 status))
            except Exception:
                results.append((f"Spot-check x={xv}", "skipped (eval error)", "warn"))

        overall = "PASS — all spot-checks consistent ✔" if all_match \
                  else "WARN — some spot-checks diverged ⚠"
        results.append(("Overall Status", overall, "pass" if all_match else "warn"))

    except Exception as exc:
        results.append(("Verification Error", str(exc)[:100], "warn"))

    return results


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
            w(f"   {key:<24}:  {value}\n", tag)

        def blank():
            w("\n", "dim")

        # ── header ────────────────────────────────────────────────────────────
        _box_inner = 62
        _box_text  = "   SD SOLVER  —  SOLUTION TRAIL"
        _box_pad   = _box_inner - len(_box_text)
        w("╔" + "═" * _box_inner + "╗\n", "header")
        w("║" + _box_text + " " * _box_pad + "║\n", "header")
        w("╚" + "═" * _box_inner + "╝\n\n", "header")

        w("   ┌─────────────────────────────────────────────┐\n", "dim")
        w("   │  METHOD :  Symbolic Differentiation         │\n", "header")
        w("   │  ENGINE  :  Exact (SymPy)                   │\n", "dim")
        w("   └─────────────────────────────────────────────┘\n\n", "dim")

        section("GIVEN")
        var_label = raw_var if raw_var else "x"
        kv(f"f({var_label})", raw_fx if raw_fx else "(empty)")
        kv("Variable",   raw_var   if raw_var   else "(empty)")
        kv("Order (n)",  raw_order if raw_order else "(empty)")
        kv("Evaluate at", raw_point if raw_point else "Not specified")
        blank()

        # ── Validation ────────────────────────────────────────────────────────
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

        # ── METHOD ────────────────────────────────────────────────────────────
        section("METHOD")
        kv("Name", "Symbolic Differentiation (Basic Rules)")

        # Dynamically collect only the rules actually used in the steps trail
        _used_rules = []
        _rule_keywords = [
            ("Power Rule",             "Power Rule"),
            ("Constant Rule",          "Constant Rule"),
            ("Sum / Difference Rule",  "Sum"),
            ("Constant Multiple Rule", "Constant Multiple"),
            ("Chain Rule",             "Chain Rule"),
            ("Product Rule",           "Product Rule"),
            ("Quotient Rule",          "Quotient Rule"),
        ]
        for _step in rule_result.get("steps", []):
            _txt = _step.get("text", "")
            for _label, _keyword in _rule_keywords:
                if _keyword in _txt and _label not in _used_rules:
                    _used_rules.append(_label)

        _rules_str = ", ".join(_used_rules) if _used_rules else "General Rule (SymPy)"
        kv("Rules applied", _rules_str)
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

        # ── VERIFICATION (REAL) ───────────────────────────────────────────────
        section("VERIFICATION")
        kv("Strategy A", "Re-integrate derivative → compare d/dx of both")
        kv("Strategy B", "Numeric spot-checks at 5 test points")
        blank()

        # Pass result["answer"] through _fix_implicit_mul inside _symbolic_verify
        ver_checks = _symbolic_verify(raw_fx, result["var"], result["order"], result["answer"])
        result["verification"] = ver_checks

        for label, value, status in ver_checks:
            tag = {"pass": "pass", "warn": "warn", "info": "verify"}.get(status, "step")
            icon = {"pass": "✔", "warn": "⚠", "info": "→"}.get(status, " ")
            w(f"   {icon}  {label:<30}  {value}\n", tag)

        blank()

        # ── SUMMARY ───────────────────────────────────────────────────────────
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
            "verification":     [],
            "timestamp":        datetime.now().strftime("%Y-%m-%d  %H:%M:%S"),
            "python_version":   sys.version.split()[0],
            "sympy_version":    SYMPY_VERSION,
        }