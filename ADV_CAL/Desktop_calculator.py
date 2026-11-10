# ================= ADVANCED CALCULATOR =================

import cmath
import re
import ast
import json
import math
import operator
import os
import statistics
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, filedialog

from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4


# Optional graphing libraries
try:
    import numpy as np
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False


# ================= PREMIUM NAVY GOLD THEME =================

NAVY = "#0A1128"        # Main background
PANEL = "#111B33"       # Sidebar / panels
CARD = "#182544"        # Calculator display / result boxes
BLUE = "#1E3A8A"        # Main button accent
GOLD = "#D4AF37"        # Premium gold accent
WHITE = "#F5F7FA"       # Main text
MUTED = "#94A3B8"       # Secondary text
GREEN = "#22C55E"       # Calculate / success buttons
RED = "#EF4444"         # Clear / error buttons


# ================= MAIN WINDOW =================

root = tk.Tk()
root.title("Advanced Calculator")
root.geometry("1150x760")
root.minsize(900, 620)
root.configure(bg=NAVY)

expression = tk.StringVar()
status = tk.StringVar(value="Ready")
history = []
HISTORY_FILE = "calculator_history.json"

current_mode = "Basic Calculator"
active_expression = expression
active_calculate = None
active_entry = None


# ================= PERMANENT HISTORY =================

def save_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as file:
            json.dump(history, file, indent=4)
    except OSError:
        pass


def load_history():
    global history

    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as file:
                loaded_history = json.load(file)

            if isinstance(loaded_history, list):
                history = loaded_history

        except (OSError, json.JSONDecodeError):
            history = []


def close_app():
    save_history()
    root.destroy()


# ================= SAFE CALCULATOR ENGINE =================

BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log10,
    "ln": math.log,
    "abs": abs,
    "exp": math.exp,
}

NAMES = {
    "pi": math.pi,
    "π": math.pi,
    "e": math.e,
}


def safe_eval(text):
    text = text.strip().replace("^", "**")

    # Percentage fix
    # 50% -> (50/100)
    text = re.sub(
        r"(?<![\d.])(\d+\.?\d*)\s*%(?![\d(])",
        r"(\1/100)",
        text
    )

    # 200 + 10% -> (200)*(1+10/100)
    text = re.sub(
        r"(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)\s*%",
        r"(\1)*(1+\2/100)",
        text
    )

    # 200 - 10% -> (200)*(1-10/100)
    text = re.sub(
        r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*%",
        r"(\1)*(1-\2/100)",
        text
    )

    # 200 * 10% -> (200)*(10/100)
    text = re.sub(
        r"(\d+\.?\d*)\s*\*\s*(\d+\.?\d*)\s*%",
        r"(\1)*(\2/100)",
        text
    )

    # 200 / 10% -> (200)/(10/100)
    text = re.sub(
        r"(\d+\.?\d*)\s*/\s*(\d+\.?\d*)\s*%",
        r"(\1)/(\2/100)",
        text
    )

    if not text:
        raise ValueError("Enter a calculation first.")

    tree = ast.parse(text, mode="eval")

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)

        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float):
                return node.value

        if isinstance(node, ast.Name) and node.id in NAMES:
            return NAMES[node.id]

        if isinstance(node, ast.BinOp) and type(node.op) in BINOPS:
            return BINOPS[type(node.op)](
                visit(node.left),
                visit(node.right)
            )

        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARYOPS:
            return UNARYOPS[type(node.op)](
                visit(node.operand)
            )

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id

            if name in FUNCTIONS and len(node.args) == 1:
                return FUNCTIONS[name](visit(node.args[0]))

        raise ValueError("Unsupported expression.")

    result = visit(tree)

    if isinstance(result, complex):
        raise ValueError("Complex results are not supported.")

    if not math.isfinite(float(result)):
        raise ValueError("The result is not finite.")

    return result


def format_result(value):
    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    if isinstance(value, float):
        return f"{value:.12g}"

    return str(value)


# ================= SHARED UI FUNCTIONS =================

def make_button(parent, text, command, color=PANEL):
    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=color,
        fg=WHITE,
        activebackground=GOLD,
        activeforeground=NAVY,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Segoe UI", 12, "bold")
    )

    button.bind(
        "<Enter>",
        lambda event: button.config(bg=GOLD, fg=NAVY)
    )

    button.bind(
        "<Leave>",
        lambda event: button.config(bg=color, fg=WHITE)
    )

    return button


def clear_content():
    for widget in content.winfo_children():
        widget.destroy()


def set_active_keyboard(variable, calculate_function, entry=None):
    global active_expression, active_calculate, active_entry

    active_expression = variable
    active_calculate = calculate_function
    active_entry = entry


def show_error(title, error):
    messagebox.showerror(title, str(error), parent=root)


# ================= BASIC CALCULATOR =================

def build_basic():
    clear_content()

    tk.Label(
        content,
        text="Basic Calculator",
        font=("Segoe UI", 23, "bold"),
        bg=NAVY,
        fg=WHITE
    ).pack(anchor="w", pady=(0, 15))

    display = tk.Entry(
        content,
        textvariable=expression,
        font=("Consolas", 25),
        bg="#182544",
        fg=WHITE,
        insertbackground=WHITE,
        selectbackground=BLUE,
        justify="right",
        relief="flat"
    )
    display.pack(fill="x", ipady=18, pady=(0, 15))

    grid = tk.Frame(content, bg=NAVY)
    grid.pack(fill="both", expand=True)

    buttons = [
        ("C", 0, 0, RED), ("⌫", 0, 1, PANEL),
        ("(", 0, 2, PANEL), (")", 0, 3, PANEL),
        ("7", 1, 0, PANEL), ("8", 1, 1, PANEL),
        ("9", 1, 2, PANEL), ("÷", 1, 3, BLUE),
        ("4", 2, 0, PANEL), ("5", 2, 1, PANEL),
        ("6", 2, 2, PANEL), ("×", 2, 3, BLUE),
        ("1", 3, 0, PANEL), ("2", 3, 1, PANEL),
        ("3", 3, 2, PANEL), ("−", 3, 3, BLUE),
        ("0", 4, 0, PANEL), (".", 4, 1, PANEL),
        ("%", 4, 2, PANEL), ("+", 4, 3, BLUE),
    ]

    def press(value):
        if value == "C":
            expression.set("")
        elif value == "⌫":
            expression.set(expression.get()[:-1])
        else:
            replacements = {
                "÷": "/",
                "×": "*",
                "−": "-"
            }
            expression.set(
                expression.get() + replacements.get(value, value)
            )

    def calculate(event=None):
        try:
            result = safe_eval(expression.get())
            history.append(
                f"{expression.get()} = {format_result(result)}"
            )
            expression.set(format_result(result))
            status.set("Calculation successful")
        except Exception as error:
            show_error("Calculation Error", error)

        return "break"

    for text, row, col, color in buttons:
        make_button(
            grid,
            text,
            lambda value=text: press(value),
            color
        ).grid(
            row=row, column=col,
            sticky="nsew", padx=5, pady=5
        )

    make_button(
        grid, "=", calculate, GREEN
    ).grid(
        row=5, column=0, columnspan=4,
        sticky="nsew", padx=5, pady=5
    )

    for col in range(4):
        grid.columnconfigure(col, weight=1)

    for row in range(6):
        grid.rowconfigure(row, weight=1)

    def copy_result():
        result_text = expression.get().strip()

        if not result_text:
            show_error(
                "Copy Error",
                "There is no result to copy."
            )
            return

        root.clipboard_clear()
        root.clipboard_append(result_text)
        status.set("Result copied to clipboard")

    copy_button = make_button(
        content,
        "Copy Result",
        copy_result,
        BLUE
    )
    copy_button.pack(anchor="w", pady=(0, 15))

    display.bind("<Return>", calculate)
    display.bind("<KP_Enter>", calculate)

    set_active_keyboard(expression, calculate, display)


# ================= SCIENTIFIC CALCULATOR =================

def build_scientific():
    clear_content()

    tk.Label(
        content, text="Scientific Calculator",
        font=("Segoe UI", 23, "bold"),
        bg=NAVY, fg=WHITE
    ).pack(anchor="w", pady=(0, 10))

    tk.Label(
        content,
        text="Functions: sin, cos, tan, sqrt, log, ln, exp, abs, pi, e. Angles use radians.",
        bg=NAVY, fg=MUTED, wraplength=750
    ).pack(anchor="w", pady=(0, 10))

    sci_expression = tk.StringVar()

    display = tk.Entry(
        content, textvariable=sci_expression,
        font=("Consolas", 22), bg="#182544",
        fg=WHITE, insertbackground=WHITE,
        selectbackground=BLUE, justify="right",
        relief="flat"
    )
    display.pack(fill="x", ipady=14, pady=(0, 12))

    grid = tk.Frame(content, bg=NAVY)
    grid.pack(fill="both", expand=True)

    buttons = [
        "7", "8", "9", "/", "C",
        "4", "5", "6", "*", "(",
        "1", "2", "3", "-", ")",
        "0", ".", "^", "+", "=",
        "sin(", "cos(", "tan(", "sqrt(", "pi",
        "log(", "ln(", "exp(", "abs(", "e"
    ]

    def calculate(event=None):
        try:
            result = safe_eval(sci_expression.get())
            history.append(
                f"{sci_expression.get()} = {format_result(result)}"
            )
            sci_expression.set(format_result(result))
            status.set("Scientific calculation successful")
        except Exception as error:
            show_error("Scientific Calculator", error)

        return "break"

    def press(value):
        if value == "C":
            sci_expression.set("")
        elif value == "=":
            calculate()
        else:
            sci_expression.set(sci_expression.get() + value)

    for index, text in enumerate(buttons):
        row, col = divmod(index, 5)

        color = (
            RED if text == "C"
            else GREEN if text == "="
            else BLUE if text in ("/", "*", "-", "+")
            else PANEL
        )

        make_button(
            grid, text, lambda value=text: press(value), color
        ).grid(
            row=row, column=col,
            sticky="nsew", padx=4, pady=4
        )

    for col in range(5):
        grid.columnconfigure(col, weight=1)

    for row in range(6):
        grid.rowconfigure(row, weight=1)

    display.bind("<Return>", calculate)
    display.bind("<KP_Enter>", calculate)

    set_active_keyboard(sci_expression, calculate, display)


# ================= GRAPHING CALCULATOR =================

def build_graphing():
    clear_content()

    tk.Label(
        content, text="Graphing Calculator",
        font=("Segoe UI", 23, "bold"),
        bg=NAVY, fg=WHITE
    ).pack(anchor="w", pady=(0, 12))

    if not GRAPH_AVAILABLE:
        tk.Label(
            content,
            text=(
                "Graphing requires NumPy and Matplotlib.\n\n"
                "Open the VS Code terminal and run:\n"
                "python -m pip install numpy matplotlib"
            ),
            bg=NAVY, fg=WHITE, justify="left",
            font=("Segoe UI", 13)
        ).pack(anchor="w", pady=20)

        set_active_keyboard(None, None)
        return

    controls = tk.Frame(content, bg=NAVY)
    controls.pack(fill="x", pady=8)

    tk.Label(controls, text="y =", bg=NAVY, fg=WHITE).pack(side="left")

    function = tk.StringVar(value="sin(x)")
    function_entry = tk.Entry(
        controls, textvariable=function, width=18,
        font=("Consolas", 13)
    )
    function_entry.pack(side="left", padx=8)

    tk.Label(controls, text="Min x", bg=NAVY, fg=WHITE).pack(side="left")

    xmin = tk.StringVar(value="-10")
    xmin_entry = tk.Entry(controls, textvariable=xmin, width=7)
    xmin_entry.pack(side="left", padx=4)

    tk.Label(controls, text="Max x", bg=NAVY, fg=WHITE).pack(side="left")

    xmax = tk.StringVar(value="10")
    xmax_entry = tk.Entry(controls, textvariable=xmax, width=7)
    xmax_entry.pack(side="left", padx=4)

    figure = Figure(figsize=(7, 4.5), dpi=100)
    axes = figure.add_subplot(111)

    canvas = FigureCanvasTkAgg(figure, master=content)
    canvas.get_tk_widget().pack(fill="both", expand=True)

    def plot(event=None, save_to_history=True):
        try:
            expression_text = function.get().replace("^", "**")
            low = float(xmin.get())
            high = float(xmax.get())

            if low >= high:
                raise ValueError("Minimum x must be less than maximum x.")

            x = np.linspace(low, high, 1000)

            allowed = {
                "sin": np.sin,
                "cos": np.cos,
                "tan": np.tan,
                "sqrt": np.sqrt,
                "log": np.log10,
                "ln": np.log,
                "exp": np.exp,
                "abs": np.abs,
                "pi": np.pi,
                "π": np.pi,
                "e": np.e,
                "x": x
            }

            tree = ast.parse(expression_text, mode="eval")

            def evaluate(node):
                if isinstance(node, ast.Expression):
                    return evaluate(node.body)

                if isinstance(node, ast.Constant):
                    if type(node.value) in (int, float):
                        return node.value

                if isinstance(node, ast.Name) and node.id in allowed:
                    return allowed[node.id]

                if isinstance(node, ast.BinOp) and type(node.op) in BINOPS:
                    return BINOPS[type(node.op)](
                        evaluate(node.left),
                        evaluate(node.right)
                    )

                if isinstance(node, ast.UnaryOp) and type(node.op) in UNARYOPS:
                    return UNARYOPS[type(node.op)](
                        evaluate(node.operand)
                    )

                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    name = node.func.id

                    if (
                        name in allowed
                        and callable(allowed[name])
                        and len(node.args) == 1
                    ):
                        return allowed[name](evaluate(node.args[0]))

                raise ValueError(
                    "Try sin(x), cos(x), x**2, or sqrt(x)."
                )

            y = evaluate(tree)

            if np.isscalar(y):
                y = np.full_like(x, y, dtype=float)

            if np.iscomplexobj(y):
                raise ValueError("Complex graphs are not supported.")

            axes.clear()
            axes.plot(x,y,color="#D4AF37",linewidth=2,label=f"y = {expression_text}"
)
            axes.axhline(0, color="gray", linewidth=0.7)
            axes.axvline(0, color="gray", linewidth=0.7)
            axes.grid(True, alpha=0.3)
            axes.legend()
            axes.set_xlabel("x")
            axes.set_ylabel("y")
            axes.set_title("Function Graph")
            canvas.draw()

            if save_to_history:
                history.append(f"Graph: y = {function.get()}")

            status.set("Graph plotted successfully")

        except Exception as error:
            show_error("Graph Error", error)

        return "break"

    make_button(
        controls, "Plot Graph", plot, BLUE
    ).pack(side="left", padx=8)

    function_entry.bind("<Return>", plot)
    xmin_entry.bind("<Return>", plot)
    xmax_entry.bind("<Return>", plot)

    set_active_keyboard(function, plot, function_entry)
    plot(save_to_history=False)


# ================= FINANCIAL CALCULATOR =================

def build_financial():
    clear_content()

    tk.Label(
        content, text="Financial Calculator",
        font=("Segoe UI", 23, "bold"),
        bg=NAVY, fg=WHITE
    ).pack(anchor="w", pady=(0, 15))

    principal = tk.StringVar(value="10000")
    rate = tk.StringVar(value="7")
    years = tk.StringVar(value="3")
    loan_rate = tk.StringVar(value="8")
    months = tk.StringVar(value="36")

    fields = [
        ("Principal amount (₹)", principal),
        ("Annual interest rate (%)", rate),
        ("Time (years)", years),
        ("Loan annual rate (%)", loan_rate),
        ("Loan duration (months)", months)
    ]

    form = tk.Frame(content, bg=NAVY)
    form.pack(anchor="w")

    first_entry = None

    for row, (label, variable) in enumerate(fields):
        tk.Label(
            form, text=label, bg=NAVY, fg=WHITE,
            font=("Segoe UI", 12)
        ).grid(
            row=row, column=0, sticky="w",
            pady=8, padx=(0, 15)
        )

        field = tk.Entry(
            form, textvariable=variable, width=18,
            font=("Consolas", 13)
        )
        field.grid(row=row, column=1, sticky="w", pady=8, ipady=5)

        if first_entry is None:
            first_entry = field

        field.bind(
            "<Return>",
            lambda event: (calculate_finance(), "break")[1]
        )

    output = tk.Label(
        content, text="Your results will appear here.",
        bg=PANEL, fg=WHITE, justify="left",
        anchor="w", font=("Segoe UI", 12), padx=15, pady=15
    )
    output.pack(fill="x", pady=20)

    def calculate_finance():
        try:
            p = float(principal.get())
            r = float(rate.get()) / 100
            t = float(years.get())
            lr = float(loan_rate.get()) / 1200
            n = int(months.get())

            if p < 0 or r < 0 or t < 0 or lr < 0 or n <= 0:
                raise ValueError(
                    "Use non-negative values and a positive month count."
                )

            simple = p * r * t
            compound = p * (1 + r) ** t

            if lr == 0:
                emi = p / n
            else:
                emi = p * lr * (1 + lr) ** n / ((1 + lr) ** n - 1)

            output.config(text=(
                f"Simple interest: ₹{simple:,.2f}\n"
                f"Total with simple interest: ₹{p + simple:,.2f}\n"
                f"Compound amount (annual): ₹{compound:,.2f}\n"
                f"Estimated monthly EMI: ₹{emi:,.2f}\n"
                f"Total loan payments: ₹{emi * n:,.2f}"
            ))

            history.append(
                f"Finance: Principal ₹{p:,.2f}, "
                f"Rate {r * 100:.2f}%, {t:g} years, "
                f"EMI ₹{emi:,.2f}"
            )

            status.set("Financial calculation successful")

        except Exception as error:
            show_error("Finance Error", error)

    make_button(
        content, "Calculate Finance", calculate_finance, GREEN
    ).pack(anchor="w")

    set_active_keyboard(None, calculate_finance, first_entry)


# ================= PRINTING CALCULATOR =================

def build_printing():
    clear_content()

    tk.Label(
        content, text="Printing Calculator",
        font=("Segoe UI", 23, "bold"),
        bg=NAVY, fg=WHITE
    ).pack(anchor="w", pady=(0, 12))

    tk.Label(
        content,
        text=" When you go another tab must save the calculation tape nither it erase.",
        bg=NAVY, fg=MUTED
    ).pack(anchor="w", pady=(0, 12))

    value = tk.StringVar()

    entry = tk.Entry(
        content, textvariable=value, font=("Consolas", 18),
        bg="#182544", fg=WHITE, insertbackground=WHITE,
        selectbackground=BLUE, relief="flat"
    )
    entry.pack(fill="x", ipady=10, pady=(0, 10))

    tape = tk.Text(
        content, height=16, bg="#182544", fg=WHITE,
        font=("Consolas", 12), relief="flat"
    )
    tape.pack(fill="both", expand=True, pady=(0, 10))

    tape.insert("end", "ADVANCED CALCULATOR - TAPE\n")
    tape.insert(
        "end",
        datetime.now().strftime("Date: %Y-%m-%d %H:%M:%S") + "\n"
    )
    tape.insert("end", "-" * 38 + "\n")

    def calculate_tape(event=None):
        try:
            expr = value.get().strip()
            result = format_result(safe_eval(expr))

            history.append(f"{expr} = {result}")

            tape.insert("end", f"{expr}\n = {result}\n\n")
            tape.see("end")
            value.set("")
            status.set("Calculation added to tape")

        except Exception as error:
            show_error("Printing Calculator", error)

        return "break"

    def save_tape_txt():
        path = filedialog.asksaveasfilename(
            parent=root,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )

        if path:
            try:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(tape.get("1.0", "end-1c"))

                messagebox.showinfo(
                    "Saved",
                    "Calculation tape saved as TXT.",
                    parent=root
                )

            except OSError as error:
                show_error("Save Error", error)

    def save_tape_pdf():
        path = filedialog.asksaveasfilename(
            parent=root,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )

        if path:
            try:
                tape_text = tape.get("1.0", "end-1c")

                pdf = pdf_canvas.Canvas(path, pagesize=A4)
                width, height = A4

                pdf.setFont("Helvetica", 12)
                y_position = height - 50

                for line in tape_text.split("\n"):
                    pdf.drawString(50, y_position, line)
                    y_position -= 20

                    if y_position < 50:
                        pdf.showPage()
                        pdf.setFont("Helvetica", 12)
                        y_position = height - 50

                pdf.save()

                messagebox.showinfo(
                    "Saved",
                    "Calculation tape saved as PDF.",
                    parent=root
                )

            except Exception as error:
                show_error("Save Error", error)

    buttons = tk.Frame(content, bg=NAVY)
    buttons.pack(fill="x", pady=(10, 0))

    make_button(
        buttons,
        "Calculate / Add to Tape",
        calculate_tape,
        GREEN
    ).pack(side="left", padx=(0, 8))

    make_button(
        buttons,
        "Save as TXT",
        save_tape_txt,
        BLUE
    ).pack(side="left", padx=(0, 8))

    make_button(
        buttons,
        "Save as PDF",
        save_tape_pdf,
        GOLD
    ).pack(side="left")

    entry.bind("<Return>", calculate_tape)
    entry.bind("<KP_Enter>", calculate_tape)

    set_active_keyboard(value, calculate_tape, entry)


# ================= PROGRAMMER CALCULATOR =================

def build_programmer():
    clear_content()

    tk.Label(
        content, text="Programmer Calculator",
        font=("Segoe UI", 23, "bold"),
        bg=NAVY, fg=WHITE
    ).pack(anchor="w", pady=(0, 12))

    tk.Label(
        content,
        text="Convert integers between binary, octal, decimal and hexadecimal.",
        bg=NAVY, fg=MUTED
    ).pack(anchor="w", pady=(0, 16))

    number = tk.StringVar(value="0")
    base = tk.StringVar(value="Decimal")

    tk.Label(content, text="Number", bg=NAVY, fg=WHITE).pack(anchor="w")

    entry = tk.Entry(
        content, textvariable=number, font=("Consolas", 18),
        bg="#182544", fg=WHITE, insertbackground=WHITE,
        selectbackground=BLUE, relief="flat"
    )
    entry.pack(fill="x", ipady=9, pady=(5, 15))

    tk.Label(content, text="Input base", bg=NAVY, fg=WHITE).pack(anchor="w")

    options = tk.Frame(content, bg=NAVY)
    options.pack(anchor="w", pady=8)

    for option in ("Binary", "Octal", "Decimal", "Hexadecimal"):
        tk.Radiobutton(
            options, text=option, variable=base, value=option,
            bg=NAVY, fg=WHITE, selectcolor=PANEL,
            activebackground=NAVY, activeforeground=WHITE
        ).pack(side="left", padx=(0, 10))

    output = tk.Label(
        content, text="", bg=PANEL, fg=WHITE,
        font=("Consolas", 14), justify="left",
        anchor="w", padx=15, pady=15
    )
    output.pack(fill="x", pady=20)

    def convert(event=None, save_to_history=True):
        try:
            radix = {
                "Binary": 2,
                "Octal": 8,
                "Decimal": 10,
                "Hexadecimal": 16
            }[base.get()]

            value = int(number.get().strip(), radix)

            output.config(text=(
                f"Binary:      {bin(value)}\n"
                f"Octal:       {oct(value)}\n"
                f"Decimal:     {value}\n"
                f"Hexadecimal: {hex(value)}\n"
                f"Bit length:  {value.bit_length()}"
            ))

            if save_to_history:
                history.append(
                    f"{number.get()} ({base.get()}) = {value}"
                )

            status.set("Number converted successfully")

        except Exception:
            show_error(
                "Input Error",
                "Enter a valid integer for the selected base."
            )

        return "break"

    make_button(
        content, "Convert Number", convert, GREEN
    ).pack(anchor="w")

    entry.bind("<Return>", convert)
    entry.bind("<KP_Enter>", convert)

    set_active_keyboard(number, convert, entry)
    convert(save_to_history=False)


# ================= UNIT CONVERTER =================

def build_unit_converter():
    clear_content()

    tk.Label(
        content, text="Unit Converter",
        font=("Segoe UI", 23, "bold"),
        bg=NAVY, fg=WHITE
    ).pack(anchor="w", pady=(0, 12))

    tk.Label(
        content,
        text="Convert Length, Weight, Temperature, Data and Time units.",
        bg=NAVY, fg=MUTED
    ).pack(anchor="w", pady=(0, 12))

    category = tk.StringVar(value="Length")
    from_unit = tk.StringVar(value="Meter")
    to_unit = tk.StringVar(value="Kilometer")
    input_value = tk.StringVar(value="1")

    units = {
        "Length": {
            "Millimeter": 0.001,
            "Centimeter": 0.01,
            "Meter": 1,
            "Kilometer": 1000,
            "Inch": 0.0254,
            "Foot": 0.3048,
            "Yard": 0.9144,
            "Mile": 1609.344
        },
        "Weight": {
            "Milligram": 0.000001,
            "Gram": 0.001,
            "Kilogram": 1,
            "Metric Ton": 1000,
            "Ounce": 0.0283495,
            "Pound": 0.453592
        },
        "Data": {
            "Bit": 0.125,
            "Byte": 1,
            "Kilobyte": 1024,
            "Megabyte": 1024 ** 2,
            "Gigabyte": 1024 ** 3,
            "Terabyte": 1024 ** 4
        },
        "Time": {
            "Millisecond": 0.001,
            "Second": 1,
            "Minute": 60,
            "Hour": 3600,
            "Day": 86400,
            "Week": 604800
        },
        "Temperature": {
            "Celsius": "C",
            "Fahrenheit": "F",
            "Kelvin": "K"
        }
    }

    form = tk.Frame(content, bg=NAVY)
    form.pack(anchor="w")

    tk.Label(
        form, text="Category", bg=NAVY, fg=WHITE,
        font=("Segoe UI", 12)
    ).grid(row=0, column=0, sticky="w", pady=8, padx=(0, 15))

    category_menu = tk.OptionMenu(
        form, category, *units.keys(),
        command=lambda selected: update_units()
    )
    category_menu.config(
        bg=PANEL, fg=WHITE, activebackground=BLUE,
        activeforeground=WHITE, relief="flat",
        font=("Segoe UI", 11)
    )
    category_menu.grid(row=0, column=1, sticky="w", pady=8)

    tk.Label(
        form, text="Value", bg=NAVY, fg=WHITE,
        font=("Segoe UI", 12)
    ).grid(row=1, column=0, sticky="w", pady=8, padx=(0, 15))

    value_entry = tk.Entry(
        form, textvariable=input_value, width=18,
        font=("Consolas", 13)
    )
    value_entry.grid(row=1, column=1, sticky="w", pady=8, ipady=5)

    tk.Label(
        form, text="From", bg=NAVY, fg=WHITE,
        font=("Segoe UI", 12)
    ).grid(row=2, column=0, sticky="w", pady=8, padx=(0, 15))

    from_menu = tk.OptionMenu(form, from_unit, *units["Length"].keys())
    from_menu.config(
        bg=PANEL, fg=WHITE, activebackground=BLUE,
        activeforeground=WHITE, relief="flat",
        font=("Segoe UI", 11)
    )
    from_menu.grid(row=2, column=1, sticky="w", pady=8)

    tk.Label(
        form, text="To", bg=NAVY, fg=WHITE,
        font=("Segoe UI", 12)
    ).grid(row=3, column=0, sticky="w", pady=8, padx=(0, 15))

    to_menu = tk.OptionMenu(form, to_unit, *units["Length"].keys())
    to_menu.config(
        bg=PANEL, fg=WHITE, activebackground=BLUE,
        activeforeground=WHITE, relief="flat",
        font=("Segoe UI", 11)
    )
    to_menu.grid(row=3, column=1, sticky="w", pady=8)

    output = tk.Label(
        content, text="Result will appear here.",
        bg=PANEL, fg=WHITE, justify="left",
        anchor="w", font=("Consolas", 15),
        padx=15, pady=15
    )
    output.pack(fill="x", pady=20)

    def update_units():
        unit_names = list(units[category.get()].keys())

        from_unit.set(unit_names[0])
        to_unit.set(unit_names[1])

        from_menu["menu"].delete(0, "end")
        to_menu["menu"].delete(0, "end")

        for unit_name in unit_names:
            from_menu["menu"].add_command(
                label=unit_name,
                command=lambda value=unit_name: from_unit.set(value)
            )
            to_menu["menu"].add_command(
                label=unit_name,
                command=lambda value=unit_name: to_unit.set(value)
            )

        output.config(text="Result will appear here.")

    def convert_temperature(value, from_unit_name, to_unit_name):
        if from_unit_name == "Celsius":
            celsius = value
        elif from_unit_name == "Fahrenheit":
            celsius = (value - 32) * 5 / 9
        else:
            celsius = value - 273.15

        if to_unit_name == "Celsius":
            return celsius
        elif to_unit_name == "Fahrenheit":
            return celsius * 9 / 5 + 32
        else:
            return celsius + 273.15

    def convert(event=None):
        try:
            value = float(input_value.get())
            from_unit_name = from_unit.get()
            to_unit_name = to_unit.get()

            if category.get() == "Temperature":
                result = convert_temperature(
                    value, from_unit_name, to_unit_name
                )
            else:
                from_factor = units[category.get()][from_unit_name]
                to_factor = units[category.get()][to_unit_name]
                result = value * from_factor / to_factor

            result_text = format_result(result)

            output.config(text=(
                f"{value} {from_unit_name} = "
                f"{result_text} {to_unit_name}"
            ))

            history.append(
                f"Unit: {value} {from_unit_name} = "
                f"{result_text} {to_unit_name}"
            )

            status.set("Unit conversion successful")

        except Exception:
            show_error(
                "Input Error",
                "Enter a valid number."
            )

        return "break"

    make_button(
        content, "Convert Unit", convert, GREEN
    ).pack(anchor="w")

    value_entry.bind("<Return>", convert)

    set_active_keyboard(input_value, convert, value_entry)


# ================= STATISTICS CALCULATOR =================

def build_statistics():
    clear_content()

    tk.Label(
        content, text="Statistics Calculator",
        font=("Segoe UI", 23, "bold"),
        bg=NAVY, fg=WHITE
    ).pack(anchor="w", pady=(0, 12))

    tk.Label(
        content,
        text="Enter numbers separated by commas.\nExample: 10, 20, 30, 40, 50",
        bg=NAVY, fg=MUTED, justify="left"
    ).pack(anchor="w", pady=(0, 12))

    numbers_input = tk.StringVar()

    entry = tk.Entry(
        content, textvariable=numbers_input,
        font=("Consolas", 18), bg="#182544",
        fg=WHITE, insertbackground=WHITE,
        selectbackground=BLUE, relief="flat"
    )
    entry.pack(fill="x", ipady=10, pady=(0, 12))

    output = tk.Label(
        content, text="Your statistics will appear here.",
        bg=PANEL, fg=WHITE, justify="left",
        anchor="w", font=("Consolas", 14),
        padx=15, pady=15
    )
    output.pack(fill="x", pady=20)

    def calculate_statistics(event=None):
        try:
            text = numbers_input.get().strip()

            if not text:
                raise ValueError("Enter numbers first.")

            numbers = [
                float(number.strip())
                for number in text.split(",")
                if number.strip() != ""
            ]

            if len(numbers) < 2:
                raise ValueError("Enter at least two numbers.")

            total = sum(numbers)
            count = len(numbers)
            mean_value = statistics.mean(numbers)
            median_value = statistics.median(numbers)
            minimum_value = min(numbers)
            maximum_value = max(numbers)
            standard_deviation = statistics.stdev(numbers)

            output.config(text=(
                f"Count: {count}\n"
                f"Sum: {format_result(total)}\n"
                f"Mean: {format_result(mean_value)}\n"
                f"Median: {format_result(median_value)}\n"
                f"Minimum: {format_result(minimum_value)}\n"
                f"Maximum: {format_result(maximum_value)}\n"
                f"Standard Deviation: {format_result(standard_deviation)}"
            ))

            history.append(
                f"Statistics: {text} | Mean = "
                f"{format_result(mean_value)}, Median = "
                f"{format_result(median_value)}"
            )

            status.set("Statistics calculated successfully")

        except Exception as error:
            show_error("Statistics Error", error)

        return "break"

    make_button(
        content, "Calculate Statistics", calculate_statistics, GREEN
    ).pack(anchor="w")

    entry.bind("<Return>", calculate_statistics)
    entry.bind("<KP_Enter>", calculate_statistics)

    set_active_keyboard(numbers_input, calculate_statistics, entry)


# ================= DATE & AGE CALCULATOR =================

def build_date_calculator():
    clear_content()

    tk.Label(
        content, text="Date & Age Calculator",
        font=("Segoe UI", 23, "bold"),
        bg=NAVY, fg=WHITE
    ).pack(anchor="w", pady=(0, 12))

    tk.Label(
        content,
        text="Use date format: YYYY-MM-DD\nExample: 2005-06-15",
        bg=NAVY, fg=MUTED, justify="left"
    ).pack(anchor="w", pady=(0, 12))

    birth_date = tk.StringVar()
    end_date = tk.StringVar(
        value=datetime.now().strftime("%Y-%m-%d")
    )
    days_to_add = tk.StringVar(value="30")

    form = tk.Frame(content, bg=NAVY)
    form.pack(anchor="w")

    tk.Label(
        form, text="Date of Birth", bg=NAVY, fg=WHITE,
        font=("Segoe UI", 12)
    ).grid(row=0, column=0, sticky="w", pady=8, padx=(0, 15))

    birth_entry = tk.Entry(
        form, textvariable=birth_date, width=18,
        font=("Consolas", 13)
    )
    birth_entry.grid(row=0, column=1, sticky="w", pady=8, ipady=5)

    tk.Label(
        form, text="Compare Date", bg=NAVY, fg=WHITE,
        font=("Segoe UI", 12)
    ).grid(row=1, column=0, sticky="w", pady=8, padx=(0, 15))

    end_entry = tk.Entry(
        form, textvariable=end_date, width=18,
        font=("Consolas", 13)
    )
    end_entry.grid(row=1, column=1, sticky="w", pady=8, ipady=5)

    tk.Label(
        form, text="Add Days", bg=NAVY, fg=WHITE,
        font=("Segoe UI", 12)
    ).grid(row=2, column=0, sticky="w", pady=8, padx=(0, 15))

    days_entry = tk.Entry(
        form, textvariable=days_to_add, width=18,
        font=("Consolas", 13)
    )
    days_entry.grid(row=2, column=1, sticky="w", pady=8, ipady=5)

    output = tk.Label(
        content, text="Your result will appear here.",
        bg=PANEL, fg=WHITE, justify="left",
        anchor="w", font=("Consolas", 14),
        padx=15, pady=15
    )
    output.pack(fill="x", pady=20)

    def calculate_date(event=None):
        try:
            born = datetime.strptime(
                birth_date.get().strip(), "%Y-%m-%d"
            ).date()

            compare_date = datetime.strptime(
                end_date.get().strip(), "%Y-%m-%d"
            ).date()

            if born > compare_date:
                raise ValueError(
                    "Date of birth cannot be after the compare date."
                )

            years = compare_date.year - born.year
            months = compare_date.month - born.month
            days = compare_date.day - born.day

            if days < 0:
                months -= 1

                if compare_date.month == 1:
                    previous_month = datetime(
                        compare_date.year - 1, 12, 1
                    ).date()
                else:
                    previous_month = datetime(
                        compare_date.year,
                        compare_date.month - 1,
                        1
                    ).date()

                next_month = datetime(
                    previous_month.year + (previous_month.month == 12),
                    (previous_month.month % 12) + 1,
                    1
                ).date()

                days += (next_month - previous_month).days

            if months < 0:
                years -= 1
                months += 12

            total_days = (compare_date - born).days

            added_days = int(days_to_add.get())
            future_date = born + timedelta(days=added_days)

            output.config(text=(
                f"Age: {years} years, {months} months, {days} days\n"
                f"Total days: {total_days}\n"
                f"{born} + {added_days} days = {future_date}"
            ))

            history.append(
                f"Date: Born {born}, Age {years} years "
                f"{months} months {days} days, "
                f"Total {total_days} days"
            )

            status.set("Date calculation successful")

        except ValueError as error:
            show_error(
                "Date Error",
                "Use a valid date in YYYY-MM-DD format."
                if "time data" in str(error)
                or "unconverted" in str(error)
                else error
            )

        except Exception as error:
            show_error("Date Error", error)

        return "break"

    make_button(
        content, "Calculate Date", calculate_date, GREEN
    ).pack(anchor="w")

    birth_entry.bind("<Return>", calculate_date)
    end_entry.bind("<Return>", calculate_date)
    days_entry.bind("<Return>", calculate_date)

    set_active_keyboard(birth_date, calculate_date, birth_entry)


# ================= BMI HEALTH CALCULATOR =================

def build_bmi():
    clear_content()

    tk.Label(
        content, text="BMI Health Calculator",
        font=("Segoe UI", 23, "bold"),
        bg=NAVY, fg=WHITE
    ).pack(anchor="w", pady=(0, 12))

    tk.Label(
        content,
        text="Enter height in centimeters and weight in kilograms.",
        bg=NAVY, fg=MUTED
    ).pack(anchor="w", pady=(0, 12))

    height = tk.StringVar(value="170")
    weight = tk.StringVar(value="65")

    form = tk.Frame(content, bg=NAVY)
    form.pack(anchor="w")

    tk.Label(
        form, text="Height (cm)", bg=NAVY, fg=WHITE,
        font=("Segoe UI", 12)
    ).grid(row=0, column=0, sticky="w", pady=8, padx=(0, 15))

    height_entry = tk.Entry(
        form, textvariable=height, width=18,
        font=("Consolas", 13)
    )
    height_entry.grid(row=0, column=1, sticky="w", pady=8, ipady=5)

    tk.Label(
        form, text="Weight (kg)", bg=NAVY, fg=WHITE,
        font=("Segoe UI", 12)
    ).grid(row=1, column=0, sticky="w", pady=8, padx=(0, 15))

    weight_entry = tk.Entry(
        form, textvariable=weight, width=18,
        font=("Consolas", 13)
    )
    weight_entry.grid(row=1, column=1, sticky="w", pady=8, ipady=5)

    output = tk.Label(
        content, text="Your BMI result will appear here.",
        bg=PANEL, fg=WHITE, justify="left",
        anchor="w", font=("Consolas", 15),
        padx=15, pady=15
    )
    output.pack(fill="x", pady=20)

    def calculate_bmi(event=None):
        try:
            height_cm = float(height.get())
            weight_kg = float(weight.get())

            if height_cm <= 0 or weight_kg <= 0:
                raise ValueError(
                    "Height and weight must be greater than zero."
                )

            height_m = height_cm / 100
            bmi = weight_kg / (height_m ** 2)

            if bmi < 18.5:
                category = "Underweight"
            elif bmi < 25:
                category = "Normal weight"
            elif bmi < 30:
                category = "Overweight"
            else:
                category = "Obese"

            bmi_result = format_result(bmi)

            output.config(text=(
                f"Height: {height_cm:g} cm\n"
                f"Weight: {weight_kg:g} kg\n\n"
                f"BMI: {bmi_result}\n"
                f"Category: {category}"
            ))

            history.append(
                f"BMI: Height {height_cm:g} cm, "
                f"Weight {weight_kg:g} kg, "
                f"BMI {bmi_result} ({category})"
            )

            status.set("BMI calculated successfully")

        except ValueError:
            show_error(
                "BMI Error",
                "Enter valid height and weight numbers."
            )

        except Exception as error:
            show_error("BMI Error", error)

        return "break"

    make_button(
        content, "Calculate BMI", calculate_bmi, GREEN
    ).pack(anchor="w")

    height_entry.bind("<Return>", calculate_bmi)
    weight_entry.bind("<Return>", calculate_bmi)

    set_active_keyboard(height, calculate_bmi, height_entry)


# ================= HISTORY =================

def build_history():
    clear_content()

    tk.Label(
        content, text="Calculation History",
        font=("Segoe UI", 23, "bold"),
        bg=NAVY, fg=WHITE
    ).pack(anchor="w", pady=(0, 12))

    history_box = tk.Text(
        content, bg="#182544", fg=WHITE,
        font=("Consolas", 13), relief="flat"
    )
    history_box.pack(fill="both", expand=True, pady=(0, 10))

    if not history:
        history_box.insert("end", "No calculations yet.")
    else:
        for item in reversed(history):
            history_box.insert("end", item + "\n")

    def save_history_txt():
        path = filedialog.asksaveasfilename(
            parent=root,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )

        if path:
            try:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(history_box.get("1.0", "end-1c"))

                messagebox.showinfo(
                    "Saved",
                    "History saved as TXT.",
                    parent=root
                )

            except OSError as error:
                show_error("Save Error", error)

    def save_history_pdf():
        path = filedialog.asksaveasfilename(
            parent=root,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )

        if path:
            try:
                history_text = history_box.get("1.0", "end-1c")

                pdf = pdf_canvas.Canvas(path, pagesize=A4)
                width, height = A4

                pdf.setFont("Helvetica-Bold", 16)
                pdf.drawString(50, height - 50, "Calculation History")

                pdf.setFont("Helvetica", 12)
                y_position = height - 90

                for line in history_text.split("\n"):
                    pdf.drawString(50, y_position, line)
                    y_position -= 20

                    if y_position < 50:
                        pdf.showPage()
                        pdf.setFont("Helvetica", 12)
                        y_position = height - 50

                pdf.save()

                messagebox.showinfo(
                    "Saved",
                    "History saved as PDF.",
                    parent=root
                )

            except Exception as error:
                show_error("Save Error", error)

    def clear_history():
        history.clear()
        save_history()
        build_history()

    buttons = tk.Frame(content, bg=NAVY)
    buttons.pack(fill="x", pady=(10, 0))

    left_buttons = tk.Frame(buttons, bg=NAVY)
    left_buttons.pack(side="left")

    make_button(
        left_buttons,
        "Save History as TXT",
        save_history_txt,
        BLUE
    ).pack(side="left", padx=(0, 8))

    make_button(
        left_buttons,
        "Save History as PDF",
        save_history_pdf,
        GOLD
    ).pack(side="left")

    make_button(
        buttons,
        "Clear History",
        clear_history,
        RED
    ).pack(side="right")


# ================= APP NAVIGATION =================

# ================= EQUATION SOLVER =================

def build_equation_solver():
    clear_content()

    tk.Label(
        content, text="Equation Solver",
        font=("Segoe UI", 23, "bold"),
        bg=NAVY, fg=WHITE
    ).pack(anchor="w", pady=(0, 12))

    tk.Label(
        content,
        text="Solve linear and quadratic equations.\n"
             "Linear: ax + b = c\n"
             "Quadratic: ax² + bx + c = 0",
        bg=NAVY, fg=MUTED, justify="left"
    ).pack(anchor="w", pady=(0, 12))

    equation_type = tk.StringVar(value="Linear Equation")

    a_value = tk.StringVar(value="2")
    b_value = tk.StringVar(value="5")
    c_value = tk.StringVar(value="11")

    form = tk.Frame(content, bg=NAVY)
    form.pack(anchor="w")

    tk.Label(
        form, text="Equation Type", bg=NAVY, fg=WHITE,
        font=("Segoe UI", 12)
    ).grid(row=0, column=0, sticky="w", pady=8, padx=(0, 15))

    type_menu = tk.OptionMenu(
        form, equation_type,
        "Linear Equation",
        "Quadratic Equation"
    )
    type_menu.config(
        bg=PANEL, fg=WHITE, activebackground=BLUE,
        activeforeground=WHITE, relief="flat",
        font=("Segoe UI", 11)
    )
    type_menu.grid(row=0, column=1, sticky="w", pady=8)

    tk.Label(
        form, text="Value of a", bg=NAVY, fg=WHITE,
        font=("Segoe UI", 12)
    ).grid(row=1, column=0, sticky="w", pady=8, padx=(0, 15))

    a_entry = tk.Entry(
        form, textvariable=a_value, width=18,
        font=("Consolas", 13)
    )
    a_entry.grid(row=1, column=1, sticky="w", pady=8, ipady=5)

    tk.Label(
        form, text="Value of b", bg=NAVY, fg=WHITE,
        font=("Segoe UI", 12)
    ).grid(row=2, column=0, sticky="w", pady=8, padx=(0, 15))

    b_entry = tk.Entry(
        form, textvariable=b_value, width=18,
        font=("Consolas", 13)
    )
    b_entry.grid(row=2, column=1, sticky="w", pady=8, ipady=5)

    tk.Label(
        form, text="Value of c", bg=NAVY, fg=WHITE,
        font=("Segoe UI", 12)
    ).grid(row=3, column=0, sticky="w", pady=8, padx=(0, 15))

    c_entry = tk.Entry(
        form, textvariable=c_value, width=18,
        font=("Consolas", 13)
    )
    c_entry.grid(row=3, column=1, sticky="w", pady=8, ipady=5)

    output = tk.Label(
        content, text="Your solution will appear here.",
        bg=PANEL, fg=WHITE, justify="left",
        anchor="w", font=("Consolas", 15),
        padx=15, pady=15
    )
    output.pack(fill="x", pady=20)

    def solve_equation(event=None):
        try:
            a = float(a_value.get())
            b = float(b_value.get())
            c = float(c_value.get())

            if equation_type.get() == "Linear Equation":
                if a == 0:
                    raise ValueError(
                        "Value of a cannot be zero in a linear equation."
                    )

                x = (c - b) / a

                output.config(text=(
                    f"Equation: {a:g}x + {b:g} = {c:g}\n\n"
                    f"Solution:\n"
                    f"x = {format_result(x)}"
                ))

                history.append(
                    f"Linear: {a:g}x + {b:g} = {c:g} | x = {format_result(x)}"
                )

            else:
                if a == 0:
                    raise ValueError(
                        "Value of a cannot be zero in a quadratic equation."
                    )

                discriminant = b ** 2 - 4 * a * c
                root_part = cmath.sqrt(discriminant)

                root1 = (-b + root_part) / (2 * a)
                root2 = (-b - root_part) / (2 * a)

                if discriminant > 0:
                    root_type = "Two different real roots"
                elif discriminant == 0:
                    root_type = "One repeated real root"
                else:
                    root_type = "Two complex roots"

                output.config(text=(
                    f"Equation: {a:g}x² + {b:g}x + {c:g} = 0\n\n"
                    f"Discriminant: {format_result(discriminant)}\n"
                    f"{root_type}\n\n"
                    f"Root 1: {format_result(root1.real)}"
                    f"{'' if root1.imag == 0 else f' + {format_result(root1.imag)}i'}\n"
                    f"Root 2: {format_result(root2.real)}"
                    f"{'' if root2.imag == 0 else f' + {format_result(root2.imag)}i'}"
                ))

                history.append(
                    f"Quadratic: {a:g}x² + {b:g}x + {c:g} = 0 | "
                    f"Roots: {format_result(root1.real)}, "
                    f"{format_result(root2.real)}"
                )

            status.set("Equation solved successfully")

        except ValueError as error:
            show_error("Equation Error", error)

        except Exception as error:
            show_error("Equation Error", error)

        return "break"

    make_button(
        content, "Solve Equation", solve_equation, GREEN
    ).pack(anchor="w")

    a_entry.bind("<Return>", solve_equation)
    b_entry.bind("<Return>", solve_equation)
    c_entry.bind("<Return>", solve_equation)

    set_active_keyboard(a_value, solve_equation, a_entry)

    # ================= SHOPPING CALCULATOR =================

def build_shopping():
    clear_content()

    tk.Label(
        content, text="Shopping Calculator",
        font=("Segoe UI", 23, "bold"),
        bg=NAVY, fg=WHITE
    ).pack(anchor="w", pady=(0, 12))

    tk.Label(
        content,
        text="Calculate discount, tip and GST for shopping bills.",
        bg=NAVY, fg=MUTED
    ).pack(anchor="w", pady=(0, 12))

    price = tk.StringVar(value="1000")
    discount = tk.StringVar(value="10")
    tip = tk.StringVar(value="0")
    gst = tk.StringVar(value="18")

    form = tk.Frame(content, bg=NAVY)
    form.pack(anchor="w")

    fields = [
        ("Price (₹)", price),
        ("Discount (%)", discount),
        ("Tip (%)", tip),
        ("GST (%)", gst)
    ]

    first_entry = None

    for row, (label, variable) in enumerate(fields):
        tk.Label(
            form, text=label, bg=NAVY, fg=WHITE,
            font=("Segoe UI", 12)
        ).grid(
            row=row, column=0, sticky="w",
            pady=8, padx=(0, 15)
        )

        field = tk.Entry(
            form, textvariable=variable, width=18,
            font=("Consolas", 13)
        )
        field.grid(row=row, column=1, sticky="w", pady=8, ipady=5)

        if first_entry is None:
            first_entry = field

        field.bind(
            "<Return>",
            lambda event: (calculate_shopping(), "break")[1]
        )

    output = tk.Label(
        content, text="Your shopping result will appear here.",
        bg=PANEL, fg=WHITE, justify="left",
        anchor="w", font=("Consolas", 15),
        padx=15, pady=15
    )
    
    output.pack(fill="x", pady=20)

    def calculate_shopping():
        try:
            original_price = float(price.get())
            discount_percent = float(discount.get())
            tip_percent = float(tip.get())
            gst_percent = float(gst.get())

            if original_price < 0:
                raise ValueError("Price cannot be negative.")

            if discount_percent < 0 or tip_percent < 0 or gst_percent < 0:
                raise ValueError(
                    "Discount, tip and GST cannot be negative."
                )

            discount_amount = (
                original_price * discount_percent / 100
            )

            price_after_discount = (
                original_price - discount_amount
            )

            tip_amount = (
                price_after_discount * tip_percent / 100
            )

            gst_amount = (
                price_after_discount * gst_percent / 100
            )

            final_price = (
                price_after_discount + tip_amount + gst_amount
            )

            output.config(text=(
                f"Original price: ₹{original_price:,.2f}\n"
                f"Discount ({discount_percent:g}%): "
                f"-₹{discount_amount:,.2f}\n"
                f"Price after discount: ₹{price_after_discount:,.2f}\n"
                f"Tip ({tip_percent:g}%): ₹{tip_amount:,.2f}\n"
                f"GST ({gst_percent:g}%): ₹{gst_amount:,.2f}\n\n"
                f"Final price: ₹{final_price:,.2f}"
            ))

            history.append(
                f"Shopping: ₹{original_price:,.2f}, "
                f"Discount {discount_percent:g}%, "
                f"Tip {tip_percent:g}%, "
                f"GST {gst_percent:g}% | "
                f"Final ₹{final_price:,.2f}"
            )

            status.set("Shopping calculation successful")

        except ValueError:
            show_error(
                "Shopping Error",
                "Enter valid numbers for price, discount, tip and GST."
            )

        except Exception as error:
            show_error("Shopping Error", error)

    make_button(
        content, "Calculate Shopping", calculate_shopping, GREEN
    ).pack(anchor="w")

    set_active_keyboard(price, calculate_shopping, first_entry)

BUILDERS = {
    "Basic Calculator": build_basic,
    "Scientific Calculator": build_scientific,
    "Graphing Calculator": build_graphing,
    "Financial Calculator": build_financial,
    "Printing Calculator": build_printing,
    "Programmer Calculator": build_programmer,
    "Unit Converter": build_unit_converter,
    "Statistics Calculator": build_statistics,
    "Date Calculator": build_date_calculator,
    "BMI Calculator": build_bmi,
    "Equation Solver": build_equation_solver,
    "Shopping Calculator": build_shopping,
    "History": build_history,

}


def show_calculator(mode):

    global current_mode

    current_mode = mode

    for widget in nav_buttons.winfo_children():
        if isinstance(widget, tk.Button):
            if widget.cget("text") == mode:
                widget.configure(
                    bg=GOLD,
                    fg=NAVY
                )
            else:
                widget.configure(
                    bg=PANEL,
                    fg=WHITE
                )

    BUILDERS[mode]()
    status.set(mode + " opened")


# ================= KEYBOARD SUPPORT =================

def keyboard_handler(event):
    global current_mode

    shortcuts = {
        "F1": "Basic Calculator",
        "F2": "Scientific Calculator",
        "F3": "Graphing Calculator",
        "F4": "Financial Calculator",
        "F5": "Printing Calculator",
        "F6": "Programmer Calculator",
        "F7": "History",
        "F8": "Unit Converter",
        "F9": "Statistics Calculator",
        "F10": "Date Calculator",
        "F11": "BMI Calculator",
        "F12": "Equation Solver"
    }

    if event.keysym in shortcuts:
        show_calculator(shortcuts[event.keysym])

        if active_entry is not None:
            active_entry.focus_set()

        return "break"

    focused = root.focus_get()

    if event.keysym == "Escape":
        if isinstance(focused, tk.Entry):
            focused.delete(0, tk.END)
        elif active_expression is not None:
            active_expression.set("")
        return "break"

    if isinstance(focused, (tk.Entry, tk.Text)):
        if (
            event.keysym in ("Return", "KP_Enter")
            and current_mode == "Financial Calculator"
            and active_calculate is not None
        ):
            active_calculate()
            return "break"

        return None

    if event.keysym in ("Return", "KP_Enter"):
        if active_calculate is not None:
            active_calculate()
        return "break"

    if event.keysym == "BackSpace":
        if active_expression is not None:
            active_expression.set(active_expression.get()[:-1])
        return "break"

    if event.keysym == "Delete":
        if active_expression is not None:
            active_expression.set("")
        return "break"

    if active_expression is None:
        return None

    char = event.char

    if not char or not char.isprintable():
        return None

    allowed = "0123456789+-*/%.()^"

    if char in allowed:
        active_expression.set(active_expression.get() + char)
        return "break"

    if current_mode in (
        "Scientific Calculator",
        "Graphing Calculator"
    ) and char.isalpha():
        active_expression.set(active_expression.get() + char)
        return "break"

    if (
        current_mode == "Programmer Calculator"
        and char.upper() in "ABCDEF"
    ):
        active_expression.set(active_expression.get() + char.upper())
        return "break"

    return None


# ================= WELCOME ANIMATION =================

def show_welcome():
    root.withdraw()

    welcome = tk.Toplevel(root)
    welcome.overrideredirect(True)
    welcome.configure(bg=NAVY)

    width, height = 600, 350

    x = (welcome.winfo_screenwidth() - width) // 2
    y = (welcome.winfo_screenheight() - height) // 2

    welcome.geometry(f"{width}x{height}+{x}+{y}")

    tk.Label(
        welcome,
        text="✦",
        font=("Arial", 38),
        bg=NAVY,
        fg=GOLD
    ).pack(pady=(30, 5))

    tk.Label(
        welcome,
        text="WELCOME!",
        font=("Arial", 30, "bold"),
        bg=NAVY,
        fg=WHITE
    ).pack(pady=5)

    tk.Label(
        welcome,
        text="Welcome to Advanced Calculator",
        font=("Arial", 15),
        bg=NAVY,
        fg="#94A3B8"
    ).pack(pady=10)

    tk.Label(
        welcome,
        text="Smart calculations & Simple experience.",
        font=("Arial", 11),
        bg=NAVY,
        fg=MUTED
    ).pack(pady=5)

    progress = tk.Canvas(
        welcome,
        width=300,
        height=6,
        bg="#182544",
        highlightthickness=0
    )
    progress.pack(pady=25)

    bar = progress.create_rectangle(
        0, 0, 0, 6,
        fill=BLUE,
        outline=""
    )

    def animate(step=0):
        if not welcome.winfo_exists():
            return

        progress.coords(bar, 0, 0, step, 6)

        if step < 300:
            welcome.after(
                40,
                lambda: animate(min(step + 6, 300))
            )

    def finish():
        if welcome.winfo_exists():
            welcome.destroy()

        root.deiconify()
        root.lift()

        if active_entry is not None:
            active_entry.focus_set()
        else:
            root.focus_force()

    animate()
    welcome.after(2200, finish)


# ================= SIDEBAR MENU =================

def toggle_menu():
    if sidebar.winfo_manager():
        sidebar.pack_forget()
    else:
        sidebar.pack(
            side="left",
            fill="y",
            padx=(0, 16),
            before=content
        )


# ================= MAIN LAYOUT =================

header = tk.Frame(root, bg=NAVY)
header.pack(fill="x", padx=22, pady=(18, 10))

tk.Label(
    header,
    text="✦  ADVANCED CALCULATOR",
    bg=NAVY,
    fg=WHITE,
    font=("Segoe UI", 19, "bold")
).pack(side="left")

tk.Label(
    header,
    text="",
    bg=NAVY,
    fg=MUTED,
    font=("Segoe UI", 9, "bold", "underline")
).pack(side="right", pady=8)

menu_button = tk.Button(
    header,
    text="☰",
    font=("Segoe UI", 20, "bold"),
    bg=NAVY,
    fg=WHITE,
    activebackground=PANEL,
    activeforeground=GOLD,
    bd=0,
    cursor="hand2",
    command=toggle_menu
)
menu_button.pack(
    side="left",
    padx=(0, 12),
    before=header.winfo_children()[0]
)

body = tk.Frame(root, bg=NAVY)
body.pack(fill="both", expand=True, padx=18, pady=8)

# ================= SCROLLABLE SIDEBAR =================

sidebar = tk.Frame(body, bg=PANEL, width=250)
sidebar.pack_propagate(False)
sidebar.pack_forget()

sidebar_canvas = tk.Canvas(
    sidebar,
    bg=PANEL,
    highlightthickness=0,
    width=250
)

sidebar_scrollbar = tk.Scrollbar(
    sidebar,
    orient="vertical",
    command=sidebar_canvas.yview
)

sidebar_scrollable_frame = tk.Frame(
    sidebar_canvas,
    bg=PANEL
)

sidebar_scrollable_frame.bind(
    "<Configure>",
    lambda event: sidebar_canvas.configure(
        scrollregion=sidebar_canvas.bbox("all")
    )
)

sidebar_canvas.create_window(
    (0, 0),
    window=sidebar_scrollable_frame,
    anchor="nw"
)

sidebar_canvas.configure(
    yscrollcommand=sidebar_scrollbar.set,
    yscrollincrement=20
)

sidebar_canvas.pack(side="left", fill="both", expand=True)
sidebar_scrollbar.pack(side="right", fill="y")


def scroll_sidebar(event):
    if event.delta > 0:
        sidebar_canvas.yview_scroll(-2, "units")
    else:
        sidebar_canvas.yview_scroll(2, "units")


def bind_sidebar_scroll(event):
    sidebar_canvas.bind_all("<MouseWheel>", scroll_sidebar)


def unbind_sidebar_scroll(event):
    sidebar_canvas.unbind_all("<MouseWheel>")


sidebar_canvas.bind("<Enter>", bind_sidebar_scroll)
sidebar_canvas.bind("<Leave>", unbind_sidebar_scroll)
sidebar_scrollable_frame.bind("<Enter>", bind_sidebar_scroll)
sidebar_scrollable_frame.bind("<Leave>", unbind_sidebar_scroll)

# ================= SIDEBAR CONTENT =================

tk.Label(
    sidebar_scrollable_frame,
    text="CALCULATORS",
    bg=PANEL,
    fg=MUTED,
    font=("Segoe UI", 10, "bold")
).pack(anchor="w", padx=16, pady=(18, 12))

nav_buttons = tk.Frame(
    sidebar_scrollable_frame,
    bg=PANEL
)
nav_buttons.pack(fill="x", padx=8)

for mode in BUILDERS:
    make_button(
        nav_buttons,
        mode,
        lambda selected=mode: show_calculator(selected),
        PANEL
    ).pack(fill="x", pady=4)

for button in nav_buttons.winfo_children():
    button.bind("<Enter>", bind_sidebar_scroll)
    button.bind("<Leave>", unbind_sidebar_scroll)

tk.Label(
    sidebar_scrollable_frame,
    text="KEYBOARD SHORTCUTS",
    bg=PANEL,
    fg=GOLD,
    font=("Segoe UI", 10, "bold")
).pack(anchor="w", padx=12, pady=(24, 6))

tk.Label(
    sidebar_scrollable_frame,
    text=(
        "F1: Basic\n"
        "F2: Scientific\n"
        "F3: Graphing\n"
        "F4: Financial\n"
        "F5: Printing\n"
        "F6: Programmer\n"
        "F7: History\n"
        "F8: Unit Converter\n"
        "F9: Statistics\n"
        "F10: Date\n"
        "F11: BMI\n"
        "F12: Equation\n\n"
        "Enter: Calculate\n"
        "Backspace: Delete last\n"
        "Esc: Clear input"
    ),
    bg=PANEL,
    fg=MUTED,
    justify="left",
    font=("Segoe UI", 9)
).pack(anchor="w", padx=12, pady=(0, 20))

# ================= MAIN CONTENT =================

content = tk.Frame(body, bg=NAVY)
content.pack(side="left", fill="both", expand=True)

# ================= FOOTER =================

footer = tk.Frame(root, bg="#070B18")
footer.pack(fill="x", side="bottom")

tk.Label(
    footer,
    textvariable=status,
    bg="#070B18",
    fg=MUTED,
    font=("Segoe UI", 9)
).pack(side="left", padx=20, pady=8)

tk.Label(
    footer,
    text="Python • Tkinter",
    bg="#070B18",
    fg=GOLD,
    font=("Segoe UI", 9)
).pack(side="right", padx=20, pady=8)

# ================= START APP =================

root.bind_all("<KeyPress>", keyboard_handler)

load_history()

show_calculator("Basic Calculator")

root.after(100, show_welcome)

root.protocol("WM_DELETE_WINDOW", close_app)

root.mainloop()