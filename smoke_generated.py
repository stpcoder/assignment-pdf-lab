#!/usr/bin/env python3
"""Bounded smoke checks for this lab's synthetic model outputs, not a student-code sandbox."""
import argparse
import ast
import builtins
import contextlib
import io
import json
from pathlib import Path
import random
import subprocess
import sys

SAFE_BUILTINS = ("abs", "all", "any", "bool", "dict", "enumerate", "float", "int", "len", "list",
                 "max", "min", "range", "round", "set", "str", "sum", "tuple", "zip", "ValueError", "TypeError")
SAFE_ATTRIBUTES = {"randint", "randrange", "choice", "lower", "upper", "strip", "isdigit", "format", "join", "append"}


def validate(code):
    tree = ast.parse(code)
    if len(list(ast.walk(tree))) > 5000:
        raise ValueError("Too many AST nodes")
    functions = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    allowed_calls = set(SAFE_BUILTINS) | functions | {"print", "input"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef, ast.With, ast.AsyncWith, ast.Await, ast.Lambda)):
            raise ValueError("Unsupported syntax for synthetic smoke check")
        if isinstance(node, ast.FunctionDef) and (node.decorator_list or node.returns or node.args.defaults):
            raise ValueError("Decorators, annotations and defaults require manual review")
        if isinstance(node, ast.arg) and node.annotation:
            raise ValueError("Annotations require manual review")
        if isinstance(node, ast.Import) and any(n.name != "random" for n in node.names):
            raise ValueError("Only random imports are allowed")
        if isinstance(node, ast.ImportFrom) and (node.module != "random" or any(n.name not in ("randint", "randrange", "choice") for n in node.names)):
            raise ValueError("Unsupported import")
        if isinstance(node, ast.ImportFrom):
            allowed_calls.update(n.asname or n.name for n in node.names)
        if isinstance(node, ast.Attribute) and node.attr not in SAFE_ATTRIBUTES:
            raise ValueError("Unsupported attribute")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id not in allowed_calls:
                raise ValueError("Unsupported call: " + node.func.id)
            if not isinstance(node.func, (ast.Name, ast.Attribute)):
                raise ValueError("Indirect calls require manual review")
    return tree


def worker(code, inputs):
    tree = validate(code)
    iterator = iter(inputs)
    output = io.StringIO()
    safe = {name: getattr(builtins, name) for name in SAFE_BUILTINS}
    def fake_input(prompt=""):
        output.write(str(prompt))
        return next(iterator)
    def fake_print(*args, sep=" ", end="\n", **kwargs):
        output.write(sep.join(str(x) for x in args) + end)
        if output.tell() > 20000:
            raise ValueError("Output limit exceeded")
    def limited_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name != "random":
            raise ValueError("Only random is allowed")
        return random
    safe.update(input=fake_input, print=fake_print, __import__=limited_import)
    random.seed(7)
    env = {"__builtins__": safe, "__name__": "__main__"}
    exec(compile(tree, "<synthetic model output>", "exec"), env)
    return output.getvalue()


def smoke(path):
    results = []
    for name, inputs, invalid in (("start_and_quit", ["5", "0", "yes"], 0),
                                   ("invalid_inputs_then_quit", ["3", "5", "5", "0", "YSE", "YES"], 3)):
        try:
            child = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker"],
                input=json.dumps({"code": path.read_text(), "inputs": inputs}), text=True,
                capture_output=True, timeout=4)
            data = json.loads(child.stdout) if child.stdout else {"error": child.stderr[-600:]}
            output = data.get("output", "")
            results.append({"case": name, "passed": child.returncode == 0 and "Game Over!" in output and output.count("Invalid input!") >= invalid,
                            "output": output, "error": data.get("error")})
        except subprocess.TimeoutExpired:
            results.append({"case": name, "passed": False, "error": "timeout"})
    return {"file": str(path), "synthetic_only": True, "cases": results, "all_passed": all(x["passed"] for x in results)}


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        data = json.load(sys.stdin)
        try:
            print(json.dumps({"output": worker(data["code"], data["inputs"])}))
        except Exception as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        return 0
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("files", nargs="+", type=Path)
    args = p.parse_args()
    for path in args.files:
        result = smoke(path)
        path.with_name("smoke.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"file": str(path), "all_passed": result["all_passed"], "errors": [x["error"] for x in result["cases"]]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
