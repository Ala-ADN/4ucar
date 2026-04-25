"""Server-side renderer (Jinja2 → WeasyPrint for PDF, openpyxl for Excel)."""


def render_pdf(template_name: str, context: dict) -> bytes:
    raise NotImplementedError


def render_excel(template_name: str, context: dict) -> bytes:
    raise NotImplementedError
