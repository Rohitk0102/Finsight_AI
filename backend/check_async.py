import ast
import os

def check_file(filepath):
    with open(filepath, "r") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except Exception:
            return
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for child in ast.walk(node):
                if isinstance(child, ast.Await):
                    print(f"{filepath}:{child.lineno} - await inside sync function '{node.name}'")
        elif isinstance(node, ast.AsyncFunctionDef):
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                    if isinstance(child.func.value, ast.Name) and child.func.value.id == "requests":
                        print(f"{filepath}:{child.lineno} - requests used inside async function '{node.name}'")
                    if isinstance(child.func.value, ast.Name) and child.func.value.id == "time" and child.func.attr == "sleep":
                        print(f"{filepath}:{child.lineno} - time.sleep used inside async function '{node.name}'")

for root, dirs, files in os.walk("backend/app"):
    for file in files:
        if file.endswith(".py"):
            check_file(os.path.join(root, file))
