import sys
from datetime import datetime

try:
    import sympy
    from sympy import symbols, sympify, SympifyError
    SYMPY_OK = True
    SYMPY_VERSION = sympy.__version__
except ImportError:
    SYMPY_OK = False
    SYMPY_VERSION = "NOT INSTALLED"

from trail_logger import DIV, HDIV, SECTION_ICONS

ORDER_MIN = 1
ORDER_MAX = 10
H_DEFAULT = 1e-5   # step size for finite difference


class NumericalEngine:
    """
    Approximates derivatives using finite difference methods.

    1st-order formulas
    ──────────────────
    Forward  : f'(x) ≈ [f(x+h) − f(x)]   / h          O(h)
    Backward : f'(x) ≈ [f(x)   − f(x−h)] / h          O(h)
    Central  : f'(x) ≈ [f(x+h) − f(x−h)] / 2h         O(h²)  ← default

    Higher-order (n-th derivative via central difference, repeated):
    Uses the generalised central-difference stencil coefficients.
    """

    # ── public entry point ────────────────────────────────────────────────────
    def validate_and_compute(
        self,
        raw_fx:    str,
        raw_var:   str,
        raw_order: str,
        raw_point: str,
        scheme:    str = "central",   # "forward" | "backward" | "central"
        h:         float = H_DEFAULT,
    ) -> dict:
        import re as _re

        raw_fx = raw_fx.replace("^", "**")
        raw_fx = _re.sub(r'(\d)([a-zA-Z])', r'\1*\2', raw_fx)
        raw_fx = _re.sub(r'\)\s*\(', r')*(', raw_fx)

        result = self._base_result(raw_fx, raw_var, raw_order, raw_point, scheme, h)
        vsteps = result["validation_steps"]
        log    = []

        def w(text, tag="step"):
            log.append((text, tag))

        def section(name):
            icon = SECTION_ICONS.get(name, "◆")
            w(f"{icon} {name}\n", "section")
            w(DIV + "\n", "dim")

        def kv(key, value, tag="step"):
            w(f"   {key:<20}:  {value}\n", tag)

        def blank():
            w("\n", "dim")

        # ── header ────────────────────────────────────────────────────────────
        w("╔" + "═" * 62 + "╗\n", "header")
        w("║   SD SOLVER  —  SOLUTION TRAIL" + " " * 30 + "║\n", "header")
        w("╚" + "═" * 62 + "╝\n\n", "header")

        # ── METHOD BADGE — clearly identifies which method is being used ──────
        w("   ┌─────────────────────────────────────────────┐\n", "dim")
        w("   │  METHOD :  Numerical Differentiation        │\n", "header")
        w("   │  ENGINE  :  Finite Difference (Approx.)     │\n", "dim")
        w("   └─────────────────────────────────────────────┘\n\n", "dim")

        section("GIVEN")
        var_label = raw_var if raw_var else "x"
        kv(f"f({var_label})", raw_fx if raw_fx else "(empty)")
        kv("Variable",        raw_var   if raw_var   else "(empty)")
        kv("Order (n)",       raw_order if raw_order else "(empty)")
        kv("Evaluate at",     raw_point if raw_point else "⚠  Required for numerical")
        kv("Scheme",          scheme.capitalize() + " Difference")
        kv("Step size (h)",   str(h))
        blank()

        # ── validation ────────────────────────────────────────────────────────
        # Step 1 — f(x) not empty
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
                (6, "Evaluate at x — required for numerical"),
            ]:
                vsteps.append(self._step(n, lbl, "SKIP", "Skipped (empty input)"))
        else:
            vsteps.append(self._step(1, "f(x) field — required, not empty", "PASS"))

            # Step 2 — SymPy parse
            sym_expr = None
            if not SYMPY_OK:
                vsteps.append(self._step(2, "f(x) — SymPy parse check", "FAIL",
                                         "SymPy not installed."))
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
                                             f"Cannot parse. {short}"))
                    result["field_errors"]["fx"] = "Not a valid math expression."
                    result["ok"] = False

            if not result["ok"]:
                for n, lbl in [
                    (3, "Variable — single alpha char"),
                    (4, "Derivative order — integer"),
                    (5, "Derivative order — range 1–10"),
                    (6, "Evaluate at x — required for numerical"),
                ]:
                    vsteps.append(self._step(n, lbl, "SKIP", "Skipped (parse failed)"))
            else:
                # Step 3 — variable
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

                # Step 4 — order integer
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

                # Step 5 — order range
                if order_int is not None:
                    if ORDER_MIN <= order_int <= ORDER_MAX:
                        vsteps.append(self._step(
                            5, f"Derivative order — range {ORDER_MIN}–{ORDER_MAX}", "PASS",
                            f"{order_int} is within [{ORDER_MIN}, {ORDER_MAX}]."))
                    else:
                        vsteps.append(self._step(
                            5, f"Derivative order — range {ORDER_MIN}–{ORDER_MAX}", "FAIL",
                            f"{order_int} is out of range."))
                        result["field_errors"]["order"] = (
                            f"Order must be between {ORDER_MIN} and {ORDER_MAX}.")
                        result["ok"] = False
                else:
                    vsteps.append(self._step(
                        5, f"Derivative order — range {ORDER_MIN}–{ORDER_MAX}",
                        "SKIP", "Skipped (invalid order)"))

                # Step 6 — evaluation point (REQUIRED for numerical)
                point_val = None
                if not raw_point:
                    vsteps.append(self._step(6, "Evaluate at x — required for numerical",
                                             "FAIL",
                                             "Numerical method needs a point x = value."))
                    result["field_errors"]["point"] = (
                        "Required for Numerical method. Enter a number.")
                    result["ok"] = False
                else:
                    try:
                        point_val = float(raw_point)
                        vsteps.append(self._step(6, "Evaluate at x — required for numerical",
                                                 "PASS", f"x = {point_val}"))
                        result["raw_point"] = raw_point
                    except ValueError:
                        vsteps.append(self._step(6, "Evaluate at x — required for numerical",
                                                 "FAIL",
                                                 f"'{raw_point}' is not a number."))
                        result["field_errors"]["point"] = "Must be a number."
                        result["ok"] = False

        # ── write validation into log ─────────────────────────────────────────
        w("⓪ VALIDATION\n", "section")
        w(DIV + "\n", "dim")
        for check in vsteps:
            icon = {"PASS": "✔", "FAIL": "✘", "SKIP": "○", "WARN": "⚠"}.get(
                check["status"], " ")
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

        # ── compute ───────────────────────────────────────────────────────────
        try:
            fx_lambda = self._make_lambda(raw_fx, result["var"])
            approx, fd_steps = self._finite_difference(
                fx_lambda, point_val, result["order"], scheme, h
            )
            result["answer"]      = f"{approx:.8g}"
            result["point_value"] = result["answer"]
            result["fd_steps"]    = fd_steps
        except Exception as exc:
            result["ok"]     = False
            result["answer"] = "Computation error"
            w(f"   ✘  Error: {str(exc)[:120]}\n", "fail")
            result["log"] = log
            return result

        result["timestamp"] = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

        # ── METHOD section ────────────────────────────────────────────────────
        section("METHOD")
        kv("Name",         "Numerical Differentiation (Finite Difference)")
        kv("Scheme",       scheme.capitalize() + " Difference")
        kv("Step size h",  str(h))
        if scheme == "central":
            kv("Formula (n=1)", "[ f(x+h) − f(x−h) ] / 2h   → O(h²)")
        elif scheme == "forward":
            kv("Formula (n=1)", "[ f(x+h) − f(x)   ] / h    → O(h)")
        else:
            kv("Formula (n=1)", "[ f(x)   − f(x−h) ] / h    → O(h)")
        kv("Higher orders", "Generalised central-difference stencil")
        blank()

        # ── STEPS section ─────────────────────────────────────────────────────
        w(f"{SECTION_ICONS['STEPS']} STEPS\n", "section")
        w(DIV + "\n", "dim")

        step_counter = [0]
        for fd_step in fd_steps:
            if fd_step["tag"] == "detail":
                w("            → " + fd_step["text"] + "\n", "rule")
            elif fd_step["tag"] == "answer":
                step_counter[0] += 1
                w(f"   Step {step_counter[0]:<2} ", "dim")
                w(fd_step["text"] + "\n", "answer")
            else:
                step_counter[0] += 1
                w(f"   Step {step_counter[0]:<2} ", "dim")
                w(fd_step["text"] + "\n", "step")

        blank()

        # ── FINAL ANSWER ──────────────────────────────────────────────────────
        section("FINAL ANSWER")
        w(f"   d^{result['order']}/d{result['var']}^{result['order']}"
          f" [{raw_fx}]  at  {result['var']} = {raw_point}"
          f"  ≈  {result['answer']}\n", "answer")
        blank()

        # ── VERIFICATION ──────────────────────────────────────────────────────
        section("VERIFICATION")
        kv("Method",  "Compare with smaller h (h/10)")
        try:
            approx2, _ = self._finite_difference(
                fx_lambda, point_val, result["order"], scheme, h / 10
            )
            diff_val = abs(approx - approx2)
            kv("h      result",  f"{approx:.8g}")
            kv("h/10   result",  f"{approx2:.8g}")
            kv("Δ (difference)", f"{diff_val:.3e}")
            kv("Status", "Consistent ✔" if diff_val < 1e-4 else "Large Δ — check h ⚠",
               "pass" if diff_val < 1e-4 else "warn")
        except Exception:
            kv("Status", "Verification skipped", "warn")
        blank()

        # ── SUMMARY ───────────────────────────────────────────────────────────
        section("SUMMARY")
        kv("Timestamp",   result["timestamp"])
        kv("Python",      result["python_version"])
        kv("SymPy",       result["sympy_version"])
        w("\n" + HDIV + "\n", "dim")

        result["log"] = log
        return result

    # ── finite difference core ─────────────────────────────────────────────────
    def _finite_difference(self, f, x, order, scheme, h):
        """
        Returns (approximation, list_of_step_dicts).
        Uses generalised central-difference stencil for any order n.
        For forward/backward only 1st-order is formula-shown; higher orders
        fall back to repeated application.
        """
        steps = []

        def s(text, tag="step"):   steps.append({"text": text, "tag": tag})
        def d(text, tag="detail"): steps.append({"text": text, "tag": tag})

        x0 = x  # evaluation point

        if order == 1:
            if scheme == "central":
                fp = f(x0 + h)
                fm = f(x0 - h)
                approx = (fp - fm) / (2 * h)
                s(f"Central difference  n=1  at  x = {x0}")
                d(f"f(x+h) = f({x0+h:.6g}) = {fp:.8g}")
                d(f"f(x-h) = f({x0-h:.6g}) = {fm:.8g}")
                d(f"[ f(x+h) - f(x-h) ] / 2h  =  [{fp:.6g} - {fm:.6g}] / {2*h:.2e}")
                s(f"≈  {approx:.8g}", "answer")
            elif scheme == "forward":
                fp = f(x0 + h)
                f0 = f(x0)
                approx = (fp - f0) / h
                s(f"Forward difference  n=1  at  x = {x0}")
                d(f"f(x+h) = f({x0+h:.6g}) = {fp:.8g}")
                d(f"f(x)   = f({x0:.6g})   = {f0:.8g}")
                d(f"[ f(x+h) - f(x) ] / h  =  [{fp:.6g} - {f0:.6g}] / {h:.2e}")
                s(f"≈  {approx:.8g}", "answer")
            else:  # backward
                f0 = f(x0)
                fm = f(x0 - h)
                approx = (f0 - fm) / h
                s(f"Backward difference  n=1  at  x = {x0}")
                d(f"f(x)   = f({x0:.6g})   = {f0:.8g}")
                d(f"f(x-h) = f({x0-h:.6g}) = {fm:.8g}")
                d(f"[ f(x) - f(x-h) ] / h  =  [{f0:.6g} - {fm:.6g}] / {h:.2e}")
                s(f"≈  {approx:.8g}", "answer")

        else:
            # Generalised central-difference stencil coefficients
            # Using the formula: f^(n)(x) ≈ (1/h^n) * Σ_k C(n,k)*(-1)^(n-k)*f(x+(k-n/2)*h)
            # Implemented as repeated central difference
            s(f"Higher-order ({order}) central difference at x = {x0}")
            d(f"Apply central difference {order} time(s) recursively")

            # Recursive application: D^n f ≈ D^(n-1)[ D f ]
            # We use the central stencil coefficients via Pascal's triangle approach
            import math
            coeffs = [(-1) ** (order - k) * math.comb(order, k) for k in range(order + 1)]
            points = [x0 + (k - order / 2) * h for k in range(order + 1)]

            fvals = [f(p) for p in points]
            approx = sum(c * fv for c, fv in zip(coeffs, fvals)) / (h ** order)

            for i, (p, fv, c) in enumerate(zip(points, fvals, coeffs)):
                d(f"f({p:.6g}) = {fv:.8g}   coeff = {c:+d}")
            d(f"Σ coeff·f(x_i) / h^{order}  =  {approx:.8g}")
            s(f"≈  {approx:.8g}", "answer")

        return approx, steps

    # ── helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _make_lambda(expr_str: str, var_str: str):
        """Convert a SymPy-parseable string into a callable Python lambda."""
        from sympy import symbols as _sym, sympify as _sy, lambdify
        x = _sym(var_str)
        expr = _sy(expr_str)
        fn = lambdify(x, expr, modules=["numpy", "sympy"])
        return fn

    @staticmethod
    def _step(num, label, status, detail=""):
        return {"num": num, "label": label, "status": status, "detail": detail}

    @staticmethod
    def _base_result(raw_fx, raw_var, raw_order, raw_point, scheme, h):
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
            "fd_steps":         [],
            "validation_steps": [],
            "field_errors":     {},
            "log":              [],
            "scheme":           scheme,
            "h":                h,
            "timestamp":        datetime.now().strftime("%Y-%m-%d  %H:%M:%S"),
            "python_version":   sys.version.split()[0],
            "sympy_version":    SYMPY_VERSION,
        }