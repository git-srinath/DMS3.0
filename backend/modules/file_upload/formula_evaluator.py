"""
Formula Evaluator for File Upload Module
Reuses the safe formula evaluation pattern from reports module.
"""
import ast
from typing import Optional, Dict, Any


class FormulaEvaluator:
    """Evaluates simple arithmetic/string expressions safely using Python AST."""

    SAFE_FUNCTIONS = {
        "CONCAT": lambda *args: "".join("" if arg is None else str(arg) for arg in args),
        "COALESCE": lambda *args: next((arg for arg in args if arg not in (None, "")), None),
        "SPLIT": lambda value, delimiter, index=0: (
            str(value).split(delimiter)[int(index)] if value is not None else None
        ),
        "UPPER": lambda value: value.upper() if isinstance(value, str) else (str(value).upper() if value is not None else None),
        "LOWER": lambda value: value.lower() if isinstance(value, str) else (str(value).lower() if value is not None else None),
        "TRIM": lambda value: value.strip() if isinstance(value, str) else (str(value).strip() if value is not None else None),
        "ABS": lambda value: abs(float(value)) if value is not None else None,
        "ROUND": lambda value, digits=0: round(float(value), int(digits)) if value is not None else None,
        "LEN": lambda value: len(value) if value is not None else 0,
        "SUBSTRING": lambda value, start, length=None: (
            str(value)[int(start):int(start) + int(length)] if length is not None
            else str(value)[int(start):] if value is not None else None
        ),
        "REPLACE": lambda value, old, new: str(value).replace(str(old), str(new)) if value is not None else None,
    }

    ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)
    ALLOWED_UNARYOPS = (ast.UAdd, ast.USub)

    def evaluate(self, expression: Optional[str], context: Dict[str, Any]) -> Any:
        """
        Evaluate a formula expression safely.
        
        Args:
            expression: Formula expression string (e.g., "COL1 + COL2", "UPPER(COL1)")
            context: Dictionary with column values (keys should be uppercase column names)
            
        Returns:
            Evaluated result or None if expression is empty/invalid
            
        Raises:
            ValueError: If formula syntax is invalid or uses disallowed functions
        """
        if expression is None:
            return None
        expr = expression.strip()
        if not expr:
            return None
        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError as exc:
            raise ValueError(f"Invalid formula syntax: {exc.msg}") from exc
        return self._eval_node(tree.body, context)

    def _eval_node(self, node, context):
        """Recursively evaluate AST node."""
        if isinstance(node, ast.BinOp) and isinstance(node.op, self.ALLOWED_BINOPS):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            return self._apply_binop(node.op, left, right)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, self.ALLOWED_UNARYOPS):
            operand = self._eval_node(node.operand, context)
            return -operand if isinstance(node.op, ast.USub) else operand
        if isinstance(node, ast.Name):
            key = node.id.upper()
            return context.get(key)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Num):  # Python <3.8 compatibility
            return node.n
        if isinstance(node, ast.Call):
            func_name = self._get_func_name(node.func)
            if func_name not in self.SAFE_FUNCTIONS:
                raise ValueError(f"Function '{func_name}' is not allowed in formulas")
            args = [self._eval_node(arg, context) for arg in node.args]
            return self.SAFE_FUNCTIONS[func_name](*args)
        raise ValueError("Unsupported expression component in formula")

    def _apply_binop(self, op, left, right):
        """Apply binary operation safely."""
        if isinstance(op, ast.Add):
            if isinstance(left, str) or isinstance(right, str):
                return ("" if left is None else str(left)) + ("" if right is None else str(right))
            return (left or 0) + (right or 0)
        if isinstance(op, ast.Sub):
            return (left or 0) - (right or 0)
        if isinstance(op, ast.Mult):
            return (left or 0) * (right or 0)
        if isinstance(op, ast.Div):
            if right in (0, None):
                return None
            return (left or 0) / right
        if isinstance(op, ast.Mod):
            if right in (0, None):
                return None
            return (left or 0) % right
        raise ValueError("Unsupported arithmetic operator in formula")

    def _get_func_name(self, func_node):
        """Extract function name from AST node."""
        if isinstance(func_node, ast.Name):
            return func_node.id.upper()
        raise ValueError("Only simple function names are allowed in formulas")

