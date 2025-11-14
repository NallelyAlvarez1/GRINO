import tempfile
import os
from fpdf import FPDF
from datetime import datetime
import streamlit as st


# ============================================
# FUNCIONES BÁSICAS — (Tomadas del Código A)
# ============================================

def safe_float_value(value):
    """Convierte valores a float de forma segura."""
    try:
        if value is None:
            return 0.0
        return float(value)
    except:
        return 0.0


def formato_moneda(valor: float) -> str:
    """Formatea valores como $12.345."""
    return f"${int(round(valor)):,}".replace(",", ".")
    

# ============================================
#   GENERAR PDF — Estilo moderno (Código B)
# ============================================

def generar_pdf_moderno(cliente: str, lugar: str, categorias: dict, descripcion: str = ""):
    try:
        pdf = FPDF()
        pdf.add_page()

        # Mejor espaciado estándar
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_line_width(0.4)

        # ============================
        # BARRA VERDE SUPERIOR
        # ============================
        pdf.set_fill_color(57, 181, 74)
        pdf.rect(0, 0, 220, 40, "F")

        # TÍTULO EN BARRA VERDE
        pdf.set_font("Helvetica", "B", 23)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(10, 8)
        pdf.cell(0, 10, "PRESUPUESTO", 0, 1, "L")

        # SUBTÍTULO FECHA
        pdf.set_font("Helvetica", "", 11)
        pdf.set_xy(10, 20)
        fecha = datetime.now().strftime("%d/%m/%Y")
        pdf.cell(0, 10, f"Fecha: {fecha}", 0, 1, "L")

        # ============================
        # BARRA VERDE 2
        # ============================
        pdf.set_fill_color(31, 183, 38)
        pdf.rect(0, 40, 220, 10, "F")

        # TITULO NEGRO
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(10, 53)
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 10, "Presupuesto de Jardines Jhonny Alvarez", 0, 1, "L")

        # ============================
        # DATOS CLIENTE
        # ============================
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_xy(10, 75)
        pdf.cell(0, 10, "Tu Cliente:", 0, 1, "L")

        pdf.set_font("Helvetica", "", 14)
        pdf.set_xy(10, 90)
        pdf.multi_cell(0, 7, f"Cliente: {cliente}")

        pdf.set_xy(10, 110)
        pdf.multi_cell(0, 7, f"Lugar de Trabajo: {lugar}")

        if descripcion:
            pdf.set_xy(10, 125)
            pdf.multi_cell(0, 7, f"Descripción del Trabajo: {descripcion}")

        pdf.ln(5)

        # ============================================
        #          TABLAS POR CATEGORÍA
        # ============================================

        total_general = 0.0

        for nombre_cat, data in categorias.items():

            items = data.get("items", [])
            mo_categoria = safe_float_value(data.get("mano_obra", 0))

            # Si no hay nada, saltar
            if not items and mo_categoria == 0:
                continue

            # TITULO DE CATEGORÍA
            pdf.set_font("Helvetica", "B", 15)
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(0, 10, nombre_cat.upper(), 0, 1, "L")

            # Encabezado tabla
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(80, 8, "Descripción", 1)
            pdf.cell(20, 8, "Unidad", 1, 0, "C")
            pdf.cell(20, 8, "Cant.", 1, 0, "C")
            pdf.cell(35, 8, "P. Unitario", 1, 0, "R")
            pdf.cell(35, 8, "Total", 1, 1, "R")

            pdf.set_font("Helvetica", "", 10)

            total_cat = 0

            for item in items:
                nombre = item.get("nombre", "")
                unidad = item.get("unidad", "")
                cantidad = safe_float_value(item.get("cantidad"))
                precio_unit = safe_float_value(item.get("precio_unitario"))
                total_item = safe_float_value(item.get("total"))
                nota = item.get("descripcion", "")

                total_cat += total_item

                # Nombre (MultiCell)
                y1 = pdf.get_y()
                pdf.multi_cell(80, 6, nombre, 1, "L")
                y2 = pdf.get_y()
                altura = y2 - y1

                # Mover items extras
                pdf.set_xy(10 + 80, y1)
                pdf.cell(20, altura, unidad, 1, 0, "C")
                pdf.cell(20, altura, str(cantidad), 1, 0, "C")
                pdf.cell(35, altura, formato_moneda(precio_unit), 1, 0, "R")
                pdf.cell(35, altura, formato_moneda(total_item), 1, 1, "R")

                # Nota
                if nota:
                    pdf.set_font("Helvetica", "I", 9)
                    pdf.multi_cell(0, 5, f"Nota: {nota}")
                    pdf.set_font("Helvetica", "", 10)

            # Mano de obra categoría
            if mo_categoria > 0:
                total_cat += mo_categoria
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(155, 8, "Mano de obra", 1, 0, "R")
                pdf.cell(35, 8, formato_moneda(mo_categoria), 1, 1, "R")

            # Total categoría
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(155, 10, f"TOTAL {nombre_cat.upper()}", 1, 0, "R")
            pdf.cell(35, 10, formato_moneda(total_cat), 1, 1, "R")

            pdf.ln(4)

            total_general += total_cat

        # ============================
        # TOTAL GENERAL
        # ============================
        pdf.set_fill_color(57, 181, 74)
        pdf.set_font("Helvetica", "B", 17)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(155, 12, "TOTAL PRESUPUESTO", 1, 0, "R", 1)
        pdf.cell(35, 12, formato_moneda(total_general), 1, 1, "R", 1)

        # Guardar PDF temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf.output(tmp.name)
            return tmp.name

    except Exception as e:
        st.error(f"Error generando PDF: {e}")
        return ""
    

# ============================================
#      FUNCIÓN DE INTEGRACIÓN STREAMLIT
# ============================================

def mostrar_boton_descarga_pdf(presupuesto_id: int, presupuesto):
    """
    Recibe el presupuesto ya consultado desde la BD y genera el PDF moderno.
    """
    try:
        categorias = {}

        for item in presupuesto.get("items", []):
            cat = item.get("categoria", "General") or "General"

            if cat not in categorias:
                categorias[cat] = {"items": [], "mano_obra": 0}

            nombre = item.get("nombre", "").lower()

            # Mano de obra general
            if "mano de obra general" in nombre:
                categorias.setdefault("General", {"items": [], "mano_obra": 0})
                categorias["General"]["mano_obra"] += safe_float_value(item.get("precio_unitario"))
                continue

            # Mano de obra categoría
            if "mano de obra" in nombre:
                categorias[cat]["mano_obra"] += safe_float_value(item.get("total"))
                continue

            # Item normal
            categorias[cat]["items"].append({
                "nombre": item.get("nombre", ""),
                "unidad": item.get("unidad", "Unidad"),
                "cantidad": safe_float_value(item.get("cantidad")),
                "precio_unitario": safe_float_value(item.get("precio_unitario")),
                "total": safe_float_value(item.get("total")),
                "descripcion": item.get("notas", "")
            })

        pdf_path = generar_pdf_moderno(
            presupuesto["cliente"]["nombre"],
            presupuesto["lugar"]["nombre"],
            categorias,
            presupuesto.get("descripcion", ""),
        )

        if not pdf_path:
            return None, None, False

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        os.unlink(pdf_path)

        nombre_archivo = f"Presupuesto_{presupuesto_id}.pdf"

        return pdf_bytes, nombre_archivo, True

    except Exception as e:
        st.error(f"Error final: {e}")
        return None, None, False
