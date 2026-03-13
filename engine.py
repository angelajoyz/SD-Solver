import sys
from datetime import datetime

import subprocess
from rules import differentiate_with_trail

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
        logger=None,
    ) -> dict:
        """
        Run all validation checks, then compute if valid.
        Always returns a complete result dict so the UI only needs to read it.
        """
        # ── Normalise input: accept ^ and implicit multiplication ────────────
        import re as _re
        raw_fx = raw_fx.replace("^", "**")
        # Add * between digit and letter: 2x -> 2*x, 3x^2 -> 3*x**2
        raw_fx = _re.sub(r'(\d)([a-zA-Z])', r'\1*\2', raw_fx)
        # Add * between ) and (: )(  -> )*(
        raw_fx = _re.sub(r'\)\s*\(', r')*(', raw_fx)

        result = self._base_result(raw_fx, raw_var, raw_order, raw_point)
        steps  = result["validation_steps"]

        # ── Write trail header + GIVEN via logger ─────────────────────────
        if logger:
            logger.write_header()
            logger.open_section("GIVEN")
            var_label = raw_var if raw_var else "x"
            logger.add_kv(f"f({var_label})", raw_fx if raw_fx else "(empty)")
            logger.add_kv("Variable", raw_var if raw_var else "(empty)")
            logger.add_kv("Order (n)", raw_order if raw_order else "(empty)")
            logger.add_kv("Evaluate at", raw_point if raw_point else "Not specified")
            logger.add_blank()

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

        # ── Write VALIDATION section via logger ──────────────────────────────
        if logger:
            from trail_logger import DIV
            logger._write("⓪ VALIDATION\n", "section")
            logger._write(DIV + "\n", "dim")
            for check in steps:
                icon = {"PASS": "✔", "FAIL": "✘", "SKIP": "○", "WARN": "⚠"}.get(check["status"], " ")
                tag  = {"PASS": "pass", "FAIL": "fail", "SKIP": "dim", "WARN": "warn"}.get(check["status"], "step")
                logger._write(f"   Step {check['num']}  {check['label']}\n", "step")
                detail = f"  —  {check['detail']}" if check.get("detail") else ""
                logger._write(f"           {icon}  {check['status']}{detail}\n\n", tag)
            if not result["ok"]:
                logger._write("   ✘  Computation aborted — correct errors and retry.\n", "fail")
                from trail_logger import HDIV
                logger._write("\n" + HDIV + "\n", "dim")
            else:
                logger._write("   ✔  All checks passed — proceeding to computation.\n\n", "pass")

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

        # ── Recompute answer via rule engine (replaces stub diff) ──────────
        try:
            from rules import differentiate_with_trail as _dw
            _r = _dw(raw_fx, result["var"], result["order"])
            result["answer"] = _r["answer"]
            # Re-evaluate point with updated answer
            if result.get("point_value") is not None:
                from sympy import symbols as _sym, sympify as _symp, diff as _diff
                _x   = _sym(result["var"])
                _f   = _symp(raw_fx)
                _d   = _diff(_f, _x, result["order"])
                from sympy import simplify as _simp
                _d   = _simp(_d)
                try:
                    result["point_value"] = str(float(_d.subs(_x, float(raw_point))))
                except Exception:
                    pass
        except Exception:
            pass  # fall back to existing answer

        result["timestamp"] = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

        # ── Write remaining trail sections via logger ──────────────────────
        if logger:
            # Write validation result
            logger.open_section("METHOD")
            logger.add_kv("Name", "Symbolic Differentiation (Basic Rules)")
            logger.add_kv("Rules applied", "Power, Constant, Sum/Difference,")
            logger.add_step("Constant Multiple, Chain, Product, Quotient", "dim")
            logger.add_kv("Library", f"SymPy {SYMPY_VERSION}")
            logger.add_blank()

            # ── Run rule engine and write real STEPS ─────────────────────────
            rule_result = differentiate_with_trail(raw_fx, result["var"], result["order"])
            result["answer"] = rule_result["answer"]

            logger.open_section("STEPS")
            for step in rule_result["steps"]:
                if step["tag"] == "detail":
                    logger.add_detail(step["text"])
                elif step["tag"] == "answer":
                    logger.add_step(step["text"], "answer")
                else:
                    logger.add_step(step["text"])
            if result.get("point_value") is not None:
                logger.add_step(f"Evaluate  f'({raw_point})")
                logger.add_detail(f"f'({raw_point})  =  {result['point_value']}", "answer")
            logger.add_blank()

            logger.open_section("FINAL ANSWER")
            logger.add_step(
                f"d^{result['order']}/d{result['var']}^{result['order']} [{raw_fx}]  =  {result['answer']}",
                "answer"
            )
            logger.add_blank()

            logger.open_section("VERIFICATION")
            logger.add_kv("Method", "Symbolic back-substitution check")
            logger.add_kv("Check", "Integrate result → compare to f(x) + C")
            logger.add_kv("Status", "⏳ Pending — Week 9", "verify")
            logger.add_blank()

            logger.open_section("SUMMARY")
            logger.add_kv("Timestamp", result["timestamp"])
            logger.add_kv("Python", result["python_version"])
            logger.add_kv("SymPy", result["sympy_version"])
            logger.add_kv("Status", "✅ Trail logger complete (Week 3)")
            logger.add_kv("Next", "Full rule engine — Week 4")
            logger.close()

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