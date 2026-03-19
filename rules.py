import re
import sympy
from sympy import (
    symbols, sympify, diff, simplify, Add, Mul, Pow,
    Number, Integer, Symbol, sin, cos, tan, exp, log
)

_SUP = str.maketrans("0123456789+-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻")

def sup(n) -> str:
    return str(n).translate(_SUP)

def to_hat(expr) -> str:
    s = str(expr)
    s = re.sub(r'\*\*', '^', s)
    s = re.sub(r'(\d)\*([a-zA-Z])', r'\1\2', s)
    return s

def fmt_term(coeff, var_str, exp_val) -> str:
    try:
        c = int(coeff) if float(coeff) == int(float(coeff)) else float(coeff)
        e = int(exp_val) if float(exp_val) == int(float(exp_val)) else float(exp_val)
    except Exception:
        return str(coeff * symbols(var_str)**exp_val)
    if e == 0:
        return str(c)
    exp_str = sup(e)
    if c == 1:
        return f"{var_str}{exp_str}"
    elif c == -1:
        return f"-{var_str}{exp_str}"
    else:
        return f"{c}{var_str}{exp_str}"

def identify_rule(term, var) -> str:
    if not term.free_symbols or var not in term.free_symbols:
        return "Constant Rule"
    if term == var:
        return "Power Rule"
    if isinstance(term, Pow) and term.base == var:
        return "Power Rule"
    if isinstance(term, Mul):
        args = term.args
        all_simple = all(
            isinstance(a, Number) or a == var or
            (isinstance(a, Pow) and a.base == var)
            for a in args
        )
        if all_simple:
            return "Constant Multiple + Power Rule"
        return "Product Rule"
    if isinstance(term, Pow):
        return "Chain Rule (Power)"
    if term.is_Function:
        return "Basic Function Rule" if any(a == var for a in term.args) else "Chain Rule"
    return "General Rule (SymPy)"

def extract_ce(term, var):
    if not term.free_symbols or var not in term.free_symbols:
        return None
    if term == var:
        return (sympy.Integer(1), sympy.Integer(1))
    if isinstance(term, Pow) and term.base == var:
        return (sympy.Integer(1), term.exp)
    if isinstance(term, Mul):
        coeff, exp_val, found = sympy.Integer(1), sympy.Integer(0), False
        for a in term.args:
            if isinstance(a, Number):
                coeff *= a
            elif a == var:
                exp_val = sympy.Integer(1); found = True
            elif isinstance(a, Pow) and a.base == var:
                exp_val = a.exp; found = True
            else:
                return None
        return (coeff, exp_val) if found else None
    return None


def differentiate_with_trail(expr_str: str, var_str: str, order: int) -> dict:
    x    = symbols(var_str)
    expr = sympify(expr_str)
    steps = []

    def s(text, tag="step"):   steps.append({"text": text, "tag": tag})
    def d(text, tag="detail"): steps.append({"text": text, "tag": tag})

    if order > 1:
        s(f"Apply differentiation {order} time(s) — showing each pass")
        current = expr

        for i in range(1, order + 1):
            import re as _re2
            _inp = str(current).replace('**', '^')
            _inp = _re2.sub(r'(\d)\*([a-zA-Z])', r'\1\2', _inp)
            _inp = _re2.sub(r'([a-zA-Z0-9])\*([a-zA-Z])', r'\1·\2', _inp)
            d(f"Pass {i}:  d/d{var_str}[{_inp}]")

            current = simplify(diff(current, x))

            import re as _re
            _cur = str(current).replace('**', '^')
            _cur = _re.sub(r'(\d)\*([a-zA-Z])', r'\1\2', _cur)
            _cur = _re.sub(r'([a-zA-Z0-9])\*([a-zA-Z])', r'\1·\2', _cur)
            d(f"       =  {_cur}")

        final = current

        import re as _re3
        def _clean(t):
            t = t.replace("**", "^")
            t = _re3.sub(r'(\d)\*([a-zA-Z])', r'\1\2', t)
            t = _re3.sub(r'([a-zA-Z0-9])\*([a-zA-Z])', r'\1·\2', t)
            return t

        s(f"= {_clean(str(final))}", "answer")
        for step in steps:
            step["text"] = _clean(step["text"])
        return {"answer": _clean(str(final)), "steps": steps}

    is_sum     = isinstance(expr, Add)
    terms      = expr.as_ordered_terms() if is_sum else [expr]
    all_simple = all(
        extract_ce(t, x) is not None or not t.free_symbols or x not in t.free_symbols
        for t in terms
    )

    s(f"d/d{var_str}({expr_str.replace('**', '^')})")

    if all_simple:
        rule_label = "Power Rule" if not is_sum else "Power Rule  +  Sum / Difference Rule"
        s(f"Use the {rule_label}.")

        if is_sum:
            rewritten = []
            for t in terms:
                ce = extract_ce(t, x)
                if ce:
                    rewritten.append(fmt_term(float(ce[0]), var_str, float(ce[1])))
                else:
                    v = t
                    rewritten.append(str(int(v) if v.is_integer else v))
            d("= " + "  +  ".join(rewritten))

            dparts = []
            for t in terms:
                ce = extract_ce(t, x)
                if ce:
                    dparts.append(f"d/d{var_str}( {fmt_term(float(ce[0]), var_str, float(ce[1]))} )")
                else:
                    v = t
                    dparts.append(f"d/d{var_str}( {int(v) if v.is_integer else v} )")
            d("= " + "  +  ".join(dparts))

        raw_parts, simp_parts = [], []
        for t in terms:
            ce = extract_ce(t, x)
            if ce:
                c_val = float(ce[0])
                e_val = float(ce[1])
                n1    = e_val - 1
                raw_parts.append(
                    f"{c_val:g} * {e_val:g}{var_str}"
                    f"{sup(int(e_val))+'⁻¹' if e_val == int(e_val) else sup(e_val - 1)}"
                )
                new_c = c_val * e_val
                simp_parts.append(fmt_term(new_c, var_str, n1))
            else:
                raw_parts.append("0")
                simp_parts.append("0")

        d("= " + "  +  ".join(raw_parts))
        d("= " + "  +  ".join(simp_parts))

        final = simplify(diff(expr, x))
        s(f"= {final}", "answer")

    elif not is_sum and isinstance(expr, Mul):
        s("Use the Product Rule:  d/dx[u·v] = u'·v + u·v'")
        args = [a for a in expr.args if a != sympy.Integer(1)]
        u  = args[0]
        v  = sympy.Mul(*args[1:])
        du = diff(u, x)
        dv = diff(v, x)
        d(f"Let  u = {u},   v = {v}")
        d(f"     u' = {du},   v' = {dv}")
        d(f"= ({du})·({v})  +  ({u})·({dv})")
        final = simplify(du * v + u * dv)
        d(f"= {du * v + u * dv}")
        s(f"= {final}", "answer")

    elif not is_sum and expr.is_Function:
        s("Use the Chain Rule:  d/dx[f(g(x))] = f'(g(x)) · g'(x)")
        inner   = expr.args[0]
        outer_d = diff(expr.func(x), x)
        inner_d = diff(inner, x)
        at_g    = outer_d.subs(x, inner)
        d(f"f(u) = {expr.func.__name__}(u),   g(x) = {inner}")
        d(f"f'(u) = {outer_d},   g'(x) = {inner_d}")
        d(f"= {at_g}  ·  {inner_d}")
        final = simplify(at_g * inner_d)
        s(f"= {final}", "answer")

    else:
        s("Apply differentiation rules")
        final = simplify(diff(expr, x, order))
        d(f"= {final}")
        s(f"= {final}", "answer")

    def clean(t):
        t = t.replace("**", "^")
        t = re.sub(r'(\d)\*([a-zA-Z(])',          r'\1\2',   t)
        t = re.sub(r'\)\*([a-zA-Z])',              r')\1',    t)
        t = re.sub(r'([a-zA-Z0-9])\*([a-zA-Z])',  r'\1·\2',  t)
        t = re.sub(r'(\^[\d]+)([a-zA-Z])',         r'\1·\2',  t)
        t = re.sub(r'([a-zA-Z])\*\(',              r'\1(',    t)
        return t

    for step in steps:
        step["text"] = clean(step["text"])

    answer_str = clean(str(simplify(diff(expr, x, order))))
    return {"answer": answer_str, "steps": steps}
