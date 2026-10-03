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


def generar_factura_pdf(factura, numero_formateado, nombre_proyecto, nombre_cliente, nombre_agencia, items, subtotal, total, saldo):
    pdf = FPDF(format="A4")
    pdf.add_page()
    pdf.set_margin(20)

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, nombre_agencia or "CRM Agencia", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 8, "Factura", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 11)
    filas = [
        ("Factura N°", numero_formateado),
        ("Cliente", nombre_cliente),
        ("Proyecto", nombre_proyecto),
        ("Vencimiento", factura[7] or "-"),
    ]
    for etiqueta, valor in filas:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(45, 9, etiqueta, new_x="END", new_y="TOP")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 9, str(valor), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(8)

    ancho_desc = 90
    ancho_col = 25
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(ancho_desc, 8, "Descripción", new_x="END", new_y="TOP")
    pdf.cell(ancho_col, 8, "Cant.", new_x="END", new_y="TOP", align="R")
    pdf.cell(ancho_col, 8, "Precio", new_x="END", new_y="TOP", align="R")
    pdf.cell(ancho_col, 8, "Importe", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.set_draw_color(220, 220, 220)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())

    pdf.set_font("Helvetica", "", 10)
    for item in items:
        cantidad = item[3] or 0
        precio = item[4] or 0
        importe = cantidad * precio
        pdf.cell(ancho_desc, 9, item[2] or "", new_x="END", new_y="TOP")
        pdf.cell(ancho_col, 9, _monto_texto(cantidad), new_x="END", new_y="TOP", align="R")
        pdf.cell(ancho_col, 9, f"${_monto_texto(precio)}", new_x="END", new_y="TOP", align="R")
        pdf.cell(ancho_col, 9, f"${_monto_texto(importe)}", new_x="LMARGIN", new_y="NEXT", align="R")

    pdf.ln(6)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(ancho_desc + ancho_col * 2, 8, "Subtotal", new_x="END", new_y="TOP", align="R")
    pdf.cell(ancho_col, 8, f"${_monto_texto(subtotal)}", new_x="LMARGIN", new_y="NEXT", align="R")

    if factura[4]:
        pdf.cell(ancho_desc + ancho_col * 2, 8, "Descuento", new_x="END", new_y="TOP", align="R")
        pdf.cell(ancho_col, 8, f"-${_monto_texto(factura[4])}", new_x="LMARGIN", new_y="NEXT", align="R")

    if factura[5]:
        pdf.cell(ancho_desc + ancho_col * 2, 8, f"Impuesto ({_monto_texto(factura[5])}%)", new_x="END", new_y="TOP", align="R")
        pdf.cell(ancho_col, 8, "", new_x="LMARGIN", new_y="NEXT", align="R")

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(ancho_desc + ancho_col * 2, 10, "Total", new_x="END", new_y="TOP", align="R")
    pdf.cell(ancho_col, 10, f"${_monto_texto(total)}", new_x="LMARGIN", new_y="NEXT", align="R")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(ancho_desc + ancho_col * 2, 8, "Saldo pendiente", new_x="END", new_y="TOP", align="R")
    pdf.cell(ancho_col, 8, f"${_monto_texto(saldo)}", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.set_text_color(0, 0, 0)

    if factura[8]:
        pdf.ln(8)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(90, 90, 90)
        pdf.multi_cell(0, 7, factura[8])
        pdf.set_text_color(0, 0, 0)

    buffer = io.BytesIO(bytes(pdf.output()))
    buffer.seek(0)
    return buffer


def generar_cotizacion_pdf(cotizacion, nombre_cliente, nombre_agencia, items, subtotal, total):
    pdf = FPDF(format="A4")
    pdf.add_page()
    pdf.set_margin(20)

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, nombre_agencia or "CRM Agencia", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 8, "Cotización", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 11)
    filas = [
        ("Cotización N°", f"#{cotizacion[0]}"),
        ("Título", cotizacion[2] or "-"),
        ("Cliente", nombre_cliente),
        ("Válida hasta", cotizacion[6] or "-"),
    ]
    for etiqueta, valor in filas:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(45, 9, etiqueta, new_x="END", new_y="TOP")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 9, str(valor), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(8)

    ancho_desc = 90
    ancho_col = 25
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(ancho_desc, 8, "Descripción", new_x="END", new_y="TOP")
    pdf.cell(ancho_col, 8, "Cant.", new_x="END", new_y="TOP", align="R")
    pdf.cell(ancho_col, 8, "Precio", new_x="END", new_y="TOP", align="R")
    pdf.cell(ancho_col, 8, "Importe", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.set_draw_color(220, 220, 220)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())

    pdf.set_font("Helvetica", "", 10)
    for item in items:
        cantidad = item[3] or 0
        precio = item[4] or 0
        importe = cantidad * precio
        pdf.cell(ancho_desc, 9, item[2] or "", new_x="END", new_y="TOP")
        pdf.cell(ancho_col, 9, _monto_texto(cantidad), new_x="END", new_y="TOP", align="R")
        pdf.cell(ancho_col, 9, f"${_monto_texto(precio)}", new_x="END", new_y="TOP", align="R")
        pdf.cell(ancho_col, 9, f"${_monto_texto(importe)}", new_x="LMARGIN", new_y="NEXT", align="R")

    pdf.ln(6)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(ancho_desc + ancho_col * 2, 8, "Subtotal", new_x="END", new_y="TOP", align="R")
    pdf.cell(ancho_col, 8, f"${_monto_texto(subtotal)}", new_x="LMARGIN", new_y="NEXT", align="R")

    if cotizacion[4]:
        pdf.cell(ancho_desc + ancho_col * 2, 8, "Descuento", new_x="END", new_y="TOP", align="R")
        pdf.cell(ancho_col, 8, f"-${_monto_texto(cotizacion[4])}", new_x="LMARGIN", new_y="NEXT", align="R")

    if cotizacion[5]:
        pdf.cell(ancho_desc + ancho_col * 2, 8, f"Impuesto ({_monto_texto(cotizacion[5])}%)", new_x="END", new_y="TOP", align="R")
        pdf.cell(ancho_col, 8, "", new_x="LMARGIN", new_y="NEXT", align="R")

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(ancho_desc + ancho_col * 2, 10, "Total", new_x="END", new_y="TOP", align="R")
    pdf.cell(ancho_col, 10, f"${_monto_texto(total)}", new_x="LMARGIN", new_y="NEXT", align="R")

    if cotizacion[7]:
        pdf.ln(8)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(90, 90, 90)
        pdf.multi_cell(0, 7, cotizacion[7])
        pdf.set_text_color(0, 0, 0)

    buffer = io.BytesIO(bytes(pdf.output()))
    buffer.seek(0)
    return buffer
