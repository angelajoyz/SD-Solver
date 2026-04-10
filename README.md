# SD-Solver — Symbolic Derivative Generator
> Version 1.0.0

SD-Solver is a desktop application that computes derivatives of mathematical
expressions step-by-step, displaying a colour-coded solution trail with rule
identification and optional point evaluation.

---

## Features

- **Two differentiation methods** selectable before every computation:
  - **Symbolic** — exact algebraic result via SymPy rules
  - **Numerical** — finite-difference approximation (Central O(h²), Forward O(h), Backward O(h))
- **Differentiation rules** applied and labelled in the trail:
  Power, Constant, Sum/Difference, Constant Multiple, Product, Chain, Quotient
- **Higher-order derivatives** — orders 1 through 10
- **Animated solution trail** — step-by-step colour-coded audit log replayed with typing effect
- **Point evaluation** — computes f′(a) at a given numeric value
- **Input validation** — 6 sequential checks per run; fields highlighted red on failure
- **Stop / Clear controls** — halt animation mid-playback or reset all fields
- **About / Help dialog** — project info, member credits, version, and usage guide

---

## Dependencies

| Package  | Purpose                        | Install command     |
|----------|--------------------------------|---------------------|
| Python   | Runtime (3.9 or higher)        | —                   |
| SymPy    | Symbolic math engine           | `pip install sympy` |
| tkinter  | GUI framework (stdlib)         | See note below      |

> **tkinter** is bundled with the official Python installer on **Windows** and **macOS**.
> On **Linux** run: `sudo apt install python3-tk`

> **SymPy** is auto-installed by the engine on first run if missing, but it is
> recommended to install it manually beforehand.

---

## How to Run

```bash
# Step 1 — go to the project folder
cd sd-solver

# Step 2 — install SymPy (only needed once)
pip install sympy

# Step 3 — launch the application
python main.py
```

The window opens at 1060 × 860 px and is fully resizable.

---

## File Overview

| File                  | Role                                                          |
|-----------------------|---------------------------------------------------------------|
| `main.py`             | GUI — window, input form, buttons, popups, trail display      |
| `engine.py`           | `DerivativeEngine` — validates inputs, assembles solution trail |
| `numerical_engine.py` | `NumericalEngine` — finite-difference computation             |
| `rules.py`            | `differentiate_with_trail()` — rule-based step generator      |
| `trail_logger.py`     | `TrailLogger` — animated text widget writer, section icons    |

---

## Input Syntax

All expressions must use **Python math notation**:

| Math notation       | Enter as                   |
|---------------------|----------------------------|
| x³ + 2x² − 5x + 1  | `x**3 + 2*x**2 - 5*x + 1` |
| sin(x²)             | `sin(x**2)`                |
| eˣ · cos(x)         | `exp(x) * cos(x)`          |
| ln(x)               | `log(x)`                   |
| (x²+1) / (x−3)     | `(x**2 + 1) / (x - 3)`    |

The engine also accepts `^` in place of `**` and implicit multiplication like `2x`.


