import io
from fpdf import FPDF


def _monto_texto(valor):
    texto = f"{valor:,.2f}"
    if texto.endswith(".00"):
        texto = texto[:-3]
    return texto


def generar_recibo_pdf(pago, titulo_proyecto, nombre_cliente, nombre_agencia,
                        moneda_actual=None, simbolo_actual=None, tasa_cambio=None):
    pdf = FPDF(format="A4")
    pdf.add_page()
    pdf.set_margin(20)

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, nombre_agencia or "CRM Agencia", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 8, "Recibo de pago", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 11)
    filas = [
        ("Recibo N°", f"#{pago[0]}"),
        ("Fecha", pago[3] or "-"),
        ("Cliente", nombre_cliente),
        ("Proyecto", titulo_proyecto),
    ]
    for etiqueta, valor in filas:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(45, 9, etiqueta, new_x="END", new_y="TOP")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 9, str(valor), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, f"Monto: ${_monto_texto(pago[2])}", new_x="LMARGIN", new_y="NEXT")

    if moneda_actual and moneda_actual != "USD" and tasa_cambio:
        convertido = pago[2] * tasa_cambio
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(90, 90, 90)
        pdf.cell(0, 8, f"Equivalente: {simbolo_actual}{_monto_texto(convertido)} {moneda_actual}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

    buffer = io.BytesIO(bytes(pdf.output()))
    buffer.seek(0)
    return buffer
