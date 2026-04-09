from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "docs/implementation/instructivo_flujos_ausentes.md"
PDF_PATH = ROOT / "docs/implementation/instructivo_flujos_ausentes.pdf"


def render_pdf() -> None:
    lines = MD_PATH.read_text(encoding="utf-8").splitlines()

    c = canvas.Canvas(str(PDF_PATH), pagesize=A4)
    width, height = A4
    left = 2.0 * cm
    right = 2.0 * cm
    top = height - 2.0 * cm
    bottom = 2.0 * cm
    usable = width - left - right
    y = top

    for raw in lines:
        line = raw.rstrip()

        if not line:
            y -= 0.45 * cm
            if y < bottom:
                c.showPage()
                y = top
            continue

        if line.startswith("# "):
            c.setFont("Helvetica-Bold", 16)
            wrapped = simpleSplit(line[2:].strip(), "Helvetica-Bold", 16, usable)
            for w in wrapped:
                if y < bottom:
                    c.showPage()
                    y = top
                c.drawString(left, y, w)
                y -= 0.8 * cm
            y -= 0.2 * cm
            continue

        if line.startswith("## "):
            c.setFont("Helvetica-Bold", 12)
            wrapped = simpleSplit(line[3:].strip(), "Helvetica-Bold", 12, usable)
            for w in wrapped:
                if y < bottom:
                    c.showPage()
                    y = top
                c.drawString(left, y, w)
                y -= 0.62 * cm
            y -= 0.08 * cm
            continue

        if line.startswith("### "):
            c.setFont("Helvetica-Bold", 11)
            wrapped = simpleSplit(line[4:].strip(), "Helvetica-Bold", 11, usable)
            for w in wrapped:
                if y < bottom:
                    c.showPage()
                    y = top
                c.drawString(left, y, w)
                y -= 0.56 * cm
            y -= 0.05 * cm
            continue

        if line.strip() == "---":
            if y < bottom + 1.0 * cm:
                c.showPage()
                y = top
            c.setLineWidth(0.6)
            c.line(left, y, width - right, y)
            y -= 0.5 * cm
            continue

        c.setFont("Helvetica", 10)
        content = line
        indent = 0
        bullet = False

        stripped = line.lstrip()
        if stripped.startswith("- "):
            indent = 0.5 * cm
            bullet = True
        elif len(stripped) > 2 and stripped[0].isdigit() and stripped[1] == ".":
            indent = 0.5 * cm

        wrapped = simpleSplit(content, "Helvetica", 10, usable - indent)
        for i, w in enumerate(wrapped):
            if y < bottom:
                c.showPage()
                y = top
            x = left + indent
            if i == 0 and bullet:
                c.drawString(left + 0.15 * cm, y, "*")
            c.drawString(x, y, w)
            y -= 0.46 * cm

    c.save()


if __name__ == "__main__":
    render_pdf()
    print(PDF_PATH)
