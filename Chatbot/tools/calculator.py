import ast
import operator
import re

class CalculatorTool:
    name = "calculator"
    description = "Safely evaluates mathematical expressions."

    _OPERATORS = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
        ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos,
    }

    def _eval_node(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self._OPERATORS[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            return self._OPERATORS[type(node.op)](operand)
        raise ValueError(f"Unsupported AST node: {type(node)}")

    def execute(self, expression: str) -> str:
        try:
            cleaned = re.sub(r'(\d+(?:\.\d+)?)%\s*of\s*(\d+(?:\.\d+)?)', r'(\1 / 100) * \2', expression, flags=re.IGNORECASE)
            cleaned = cleaned.replace('%', '/100').replace('x', '*').replace('₹', '').replace('$', '')
            cleaned = re.sub(r'[^0-9+\-*/().\s]', '', cleaned).strip()

            parsed = ast.parse(cleaned, mode='eval')
            result = self._eval_node(parsed.body)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return str(result)
        except Exception as e:
            return f"Calculation Error: {str(e)}"