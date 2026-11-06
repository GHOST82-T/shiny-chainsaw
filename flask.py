import json
import os
import re
from contextlib import contextmanager


class Flask:
    def __init__(self, import_name):
        self.import_name = import_name
        self.routes = {}
        self.config = {}
        self.template_folder = os.path.join(os.path.dirname(__file__), "templates")

    def route(self, path, methods=None):
        def decorator(func):
            self.routes.setdefault(path, []).append((methods or ["GET"], func))
            return func

        return decorator

    @contextmanager
    def app_context(self):
        yield self

    def run(self, *args, **kwargs):
        return None


def _resolve_expression(expr, context):
    expr = expr.strip()
    if not expr:
        return ""

    if expr in context:
        return context[expr]

    current = context
    for part in expr.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part)
        if current is None:
            return None
    return current


def _render_fragment(text, context):
    def replace_loop(match):
        var_name, iterable_name, inner = match.groups()
        sequence = _resolve_expression(iterable_name, context)
        if sequence is None:
            return ""

        output = ""
        for item in sequence:
            local_context = dict(context)
            local_context[var_name] = item
            output += _render_fragment(inner, local_context)
        return output

    def replace_variable(match):
        expr = match.group(1).strip()
        value = _resolve_expression(expr, context)
        if value is None:
            return ""
        return str(value)

    rendered = re.sub(
        r"{%\s*for\s+(\w+)\s+in\s+([A-Za-z_]\w*)\s*%}(.*?){%\s*endfor\s*%}",
        replace_loop,
        text,
        flags=re.DOTALL,
    )
    rendered = re.sub(r"{{\s*([^{}]+?)\s*}}", replace_variable, rendered)
    return rendered


def render_template(template_name, **context):
    template_path = os.path.join(os.path.dirname(__file__), "templates", template_name)
    with open(template_path, "r", encoding="utf-8") as handle:
        template_text = handle.read()
    return _render_fragment(template_text, context)


def jsonify(value=None, **kwargs):
    if value is None and kwargs:
        payload = kwargs
    elif value is not None and kwargs:
        payload = dict(value)
        payload.update(kwargs)
    else:
        payload = value
    return json.dumps(payload)


__all__ = ["Flask", "render_template", "jsonify"]
