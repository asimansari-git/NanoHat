"""
functions.py — Execution logic for fuge-nanohat tools.
Starting with the safe AST-based calculator and system health check.
"""

import ast
import operator
import math
import psutil

_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def _eval_ast(node):
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")
    elif isinstance(node, ast.Name):
        if node.id in _SAFE_CONSTANTS:
            return _SAFE_CONSTANTS[node.id]
        raise ValueError(f"Unsupported variable: {node.id}")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        if op_type is ast.Pow and (right > 1000 or left > 1e10):
            raise ValueError("Exponent too large")
        return _SAFE_OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _eval_ast(node.operand)
        return _SAFE_OPERATORS[op_type](operand)
    else:
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")


def calculator(expression: str) -> str:
    """Safely evaluates a mathematical expression using AST parsing."""
    try:
        expr_clean = expression.strip()
        tree = ast.parse(expr_clean, mode="eval")
        result = _eval_ast(tree)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def system_health() -> str:
    """Returns current system health: CPU percent, RAM usage, and battery."""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        ram_used_gb = round(mem.used / (1024 ** 3), 2)
        ram_total_gb = round(mem.total / (1024 ** 3), 2)
        ram_pct = mem.percent
        
        battery_str = "N/A"
        try:
            batt = psutil.sensors_battery()
            if batt:
                battery_str = f"{batt.percent}% ({'charging' if batt.power_plugged else 'discharging'})"
        except Exception:
            pass

        return f"CPU: {cpu}% | RAM: {ram_used_gb}GB / {ram_total_gb}GB ({ram_pct}%) | Battery: {battery_str}"
    except Exception as e:
        return f"Error querying system health: {e}"


# Tool dispatch registry
REGISTRY = {
    "calculator": calculator,
    "system_health": system_health,
}
