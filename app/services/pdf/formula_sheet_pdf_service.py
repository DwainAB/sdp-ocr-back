"""
Génération de la "fiche formule" en PDF.

Reprend le design de la pyramide olfactive utilisé pour l'email
(app/api/endpoints/emails.py::_build_pyramid_html) : encadré du nom du
parfum, image de la pyramide, colonnes de notes avec pourcentages,
footer Studio des Parfums.

Utilisé notamment pour les formules qui n'ont aucune fiche/document
associé (ex: formules créées digitalement) afin de fournir un
téléchargement de remplacement reprenant la même charte graphique.
"""
import os
import base64
from io import BytesIO
from typing import Optional

from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

STATIC_PATH = os.path.join(os.path.dirname(__file__), "../../static/images")
PYRAMID_IMAGE_PATH = os.path.join(STATIC_PATH, "pyramide.png")


def get_pyramid_image_base64() -> Optional[str]:
    try:
        if os.path.exists(PYRAMID_IMAGE_PATH):
            with open(PYRAMID_IMAGE_PATH, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Erreur lecture image pyramide: {e}")
    return None


def _parse_quantity(note: dict) -> float:
    try:
        return float(str(note.get("quantity") or "0").replace(",", "."))
    except (ValueError, TypeError):
        return 0.0


def _sum_quantities(notes: list) -> float:
    return sum(_parse_quantity(n) for n in notes)


def _format_notes_html(notes: list) -> str:
    """Affiche TOUTES les notes de la catégorie avec leur quantité en ml."""
    if not notes:
        return "<p style='margin:0;color:#999;font-size:13px'>—</p>"
    rows = ""
    for n in notes:
        qty = n.get("quantity")
        qty_html = f"<span style='color:#888'>{qty} ml</span>" if qty else ""
        rows += (
            "<div style='display:flex;justify-content:space-between;"
            "border-bottom:1px dotted #e5e5e5;padding:3px 0;font-size:13px'>"
            f"<span>{n.get('name', '')}</span>{qty_html}"
            "</div>"
        )
    return rows


def _percentages(top_notes: list, heart_notes: list, base_notes: list) -> dict:
    total_top = _sum_quantities(top_notes)
    total_heart = _sum_quantities(heart_notes)
    total_base = _sum_quantities(base_notes)
    grand_total = total_top + total_heart + total_base

    if grand_total > 0:
        return {
            "top": round(total_top / grand_total * 100),
            "heart": round(total_heart / grand_total * 100),
            "base": round(total_base / grand_total * 100),
            "total_ml": grand_total,
        }
    return {"top": 0, "heart": 0, "base": 0, "total_ml": 0}


def generate_formula_sheet_html(customer: dict, formula: dict) -> str:
    top_notes = formula.get("top_notes") or []
    heart_notes = formula.get("heart_notes") or []
    base_notes = formula.get("base_notes") or []
    pct = _percentages(top_notes, heart_notes, base_notes)

    pyramid_b64 = get_pyramid_image_base64()
    if pyramid_b64:
        pyramid_img_tag = f"""
            <img src="data:image/png;base64,{pyramid_b64}"
                 alt="Pyramide olfactive"
                 style="width:100%;max-width:220px;height:auto;display:block;margin:0 auto;">
        """
    else:
        pyramid_img_tag = "<div style='width:220px;height:280px;background:#f0f0f0;margin:0 auto'></div>"

    customer_name = f"{customer.get('last_name', '') or customer.get('nom', '')} {customer.get('first_name', '') or customer.get('prenom', '')}".strip()
    perfume_name = formula.get("perfume_name") or "Non renseigné"
    reference = formula.get("reference") or f"Formule #{formula.get('id', '')}"
    date = formula.get("date") or ""

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    @page {{
        size: A4;
        margin: 1.8cm;
    }}
    body {{
        margin: 0;
        padding: 0;
        background: #ffffff;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        color: #333;
    }}
</style>
</head>
<body>

<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="font-size:15px;line-height:1.6">

<p style="text-align:center;font-size:11px;letter-spacing:2px;color:#999;text-transform:uppercase;margin:0 0 6px">
    Fiche formule
</p>

<p>Bonjour {customer_name},</p>

<p>Voici la pyramide olfactive de votre création.</p>

<div style="margin:20px 0;text-align:center">
    <span style="font-size:22px;font-weight:bold;color:#c00000;border:2px solid #c00000;padding:10px 18px;display:inline-block">
        {perfume_name}
    </span>
</div>

<p>
Cette composition {f"a été créée le {date} et " if date else ""}est enregistrée sous la référence
<strong>{reference}</strong>.
</p>

</td></tr>

<tr><td height="20"></td></tr>

<tr><td>
<table width="100%" cellpadding="0" cellspacing="0">
<tr>

<td width="42%" valign="top" align="center">
{pyramid_img_tag}
<p style="margin-top:14px;font-size:13px;color:#666">
    Total formule : <strong style="color:#333">{pct['total_ml']:.2f} ml</strong>
</p>
</td>

<td width="58%" valign="top" style="padding-left:25px">

<h3 style="margin:0 0 8px;font-size:15px;border-bottom:1px solid #ddd;padding-bottom:4px">
    Notes de tête — {pct['top']}%
</h3>
{_format_notes_html(top_notes)}

<h3 style="margin:16px 0 8px;font-size:15px;border-bottom:1px solid #ddd;padding-bottom:4px">
    Notes de cœur — {pct['heart']}%
</h3>
{_format_notes_html(heart_notes)}

<h3 style="margin:16px 0 8px;font-size:15px;border-bottom:1px solid #ddd;padding-bottom:4px">
    Notes de fond — {pct['base']}%
</h3>
{_format_notes_html(base_notes)}

</td>

</tr>
</table>
</td></tr>

<tr><td style="padding-top:30px">
<p style="color:#c00000;font-weight:bold;text-align:center">
    Nous vous rappelons que vous pouvez recommander dès que vous le souhaitez.
</p>
</td></tr>

<tr><td style="padding-top:24px;font-size:12px;color:#666;text-align:center">
<hr style="border:none;border-top:2px solid #333;margin-bottom:15px">
<strong>Le Studio des Parfums – Paris</strong><br>
23 rue du Bourg Tibourg – 75004 Paris<br>
Tél : +33 (0)1 40 29 90 84<br>
www.studiodesparfums-paris.fr
</td></tr>

</table>

</body>
</html>
"""


def generate_formula_sheet_pdf(customer: dict, formula: dict) -> bytes:
    """Génère le PDF de la fiche formule (bytes prêts à être renvoyés en réponse HTTP)."""
    html_content = generate_formula_sheet_html(customer, formula)
    font_config = FontConfiguration()
    html = HTML(string=html_content)
    pdf_buffer = BytesIO()
    html.write_pdf(pdf_buffer, font_config=font_config)
    return pdf_buffer.getvalue()
