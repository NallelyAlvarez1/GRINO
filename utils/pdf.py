import tempfile
import os
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from fpdf import FPDF
from utils.database import get_presupuesto_detallado
import streamlit as st

# ========= UTILIDAD SEGURA ==========
def safe_float(value):
    try:
        if value is None:
            return 0.0
        return float(value)
    except:
        return 0.0

# ========= FORMATO MONEDA ==========
def formato_moneda(valor: float) -> str:
    return f"${int(round(valor)):,}".replace(",", ".")
    

# ========= GENERAR PDF (CÓDIGO B BASE) ==========
def generar_pdf(cliente_nombre: str, lugar_cliente: str, descripcion: str, categorias: Dict[str, Any]) -> str:
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Franja verde superior
        pdf.set_fill_color(0, 102, 51)
        pdf.rect(0, 0, 210, 20, 'F')

        # Título principal
        pdf.set_xy(10, 25)
        pdf.set_font('Helvetica', 'B', 17)
        pdf.cell(0, 10, 'PRESUPUESTO DE TRABAJO', 0, 1, 'L')

        # Datos del cliente
        pdf.ln(3)
        pdf.set_font('Helvetica', '', 11)

        pdf.cell(50, 8, 'Cliente:', 0, 0)
        pdf.cell(0, 8, cliente_nombre, 0, 1)

        pdf.cell(50, 8, 'Lugar de Trabajo:', 0, 0)
        pdf.cell(0, 8, lugar_cliente, 0, 1)

        pdf.cell(50, 8, 'Fecha:', 0, 0)
        pdf.cell(0, 8, datetime.now().strftime('%d/%m/%Y'), 0, 1)

        if descripcion:
            pdf.ln(4)
            pdf.set_font('Helvetica', 'B', 11)
            pdf.cell(0, 8, 'Descripción del Trabajo:', 0, 1)
            pdf.set_font('Helvetica', '', 10)
            pdf.multi_cell(0, 6, descripcion)

        pdf.ln(6)

        total_general = 0.0

        # Recorrer categorías
        for nombre_categoria, data in categorias.items():
            
            items = data.get("items", [])
            mano_obra = safe_float(data.get("mano_obra", 0))

            # Saltar categorías vacías
            if not items and mano_obra == 0:
                continue

            # Bloque categoría
            pdf.set_font('Helvetica', 'B', 13)
            pdf.set_fill_color(220, 220, 220)
            pdf.cell(0, 9, nombre_categoria.upper(), 0, 1, 'L', 1)

            # Encabezado tabla
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(85, 7, 'Descripción', 1, 0, 'L')
            pdf.cell(25, 7, 'Unidad', 1, 0, 'C')
            pdf.cell(20, 7, 'Cant.', 1, 0, 'C')
            pdf.cell(30, 7, 'P. Unitario', 1, 0, 'R')
            pdf.cell(30, 7, 'Total', 1, 1, 'R')

            # Items
            pdf.set_font('Helvetica', '', 10)
            total_categoria = 0

            for item in items:
                nombre = item.get('nombre', '')
                unidad = item.get('unidad', '')
                cantidad = safe_float(item.get('cantidad', 0))
                precio_unitario = safe_float(item.get('precio_unitario', 0))
                total_item = safe_float(item.get('total', cantidad * precio_unitario))

                total_categoria += total_item

                pdf.multi_cell(85, 6, nombre, 1, 'L')
                y = pdf.get_y()
                pdf.set_xy(95, y - 6)
                pdf.cell(25, 6, unidad, 1, 0, 'C')
                pdf.cell(20, 6, str(int(cantidad)), 1, 0, 'C')
                pdf.cell(30, 6, formato_moneda(precio_unitario), 1, 0, 'R')
                pdf.cell(30, 6, formato_moneda(total_item), 1, 1, 'R')

            # Mano de obra por categoría
            if mano_obra > 0:
                total_categoria += mano_obra
                pdf.set_font('Helvetica', 'B', 10)
                pdf.cell(160, 7, f"Mano de Obra ({nombre_categoria})", 1, 0, 'R')
                pdf.cell(30, 7, formato_moneda(mano_obra), 1, 1, 'R')

            # Total categoría
            pdf.set_font('Helvetica', 'B', 11)
            pdf.cell(160, 8, f"TOTAL {nombre_categoria.upper()}", 1, 0, 'R')
            pdf.cell(30, 8, formato_moneda(total_categoria), 1, 1, 'R')

            pdf.ln(3)
            total_general += total_categoria

        # TOTAL GENERAL
        pdf.set_fill_color(0, 140, 70)
        pdf.set_font('Helvetica', 'B', 15)
        pdf.cell(160, 10, 'TOTAL PRESUPUESTO', 1, 0, 'R', True)
        pdf.cell(30, 10, formato_moneda(total_general), 1, 1, 'R')

        # Guardar temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf.output(tmp.name)
            return tmp.name

    except Exception as e:
        st.error(f"Error generando PDF: {e}")
        print("PDF ERROR:", e)
        return ""

def mostrar_boton_descarga_pdf(presupuesto_id: int):
    try:
        data = get_presupuesto_detallado(presupuesto_id)
        if not data:
            return None, None, False

        categorias = {}

        for item in data.get("items", []):
            categoria = item.get("categoria", "Sin Categoría") or "Sin Categoría"

            if categoria not in categorias:
                categorias[categoria] = {"items": [], "mano_obra": 0}

            nombre_item = item.get("nombre", "").lower()

            # Mano de obra general
            if "mano de obra general" in nombre_item:
                if "Mano de Obra General" not in categorias:
                    categorias["Mano de Obra General"] = {"items": [], "mano_obra": 0}
                categorias["Mano de Obra General"]["mano_obra"] += safe_float(item.get("precio_unitario"))
                continue

            # Mano de obra categoría
            if "mano de obra" in nombre_item:
                categorias[categoria]["mano_obra"] += safe_float(item.get("total"))
                continue

            # Item normal
            categorias[categoria]["items"].append({
                "nombre": item.get("nombre"),
                "unidad": item.get("unidad"),
                "cantidad": safe_float(item.get("cantidad")),
                "precio_unitario": safe_float(item.get("precio_unitario")),
                "total": safe_float(item.get("total")),
                "descripcion": item.get("notas", "")
            })

        pdf_path = generar_pdf(
            cliente_nombre=data["cliente"]["nombre"],
            lugar_cliente=data["lugar"]["nombre"],
            descripcion=data.get("descripcion", ""),
            categorias=categorias
        )

        if not pdf_path:
            return None, None, False

        with open(pdf_path, "rb") as f:
            contenido_pdf = f.read()

        os.unlink(pdf_path)

        nombre_archivo = f"Presupuesto_{data['lugar']['nombre'].replace(' ','_')}_{presupuesto_id}.pdf"

        return contenido_pdf, nombre_archivo, True

    except Exception as e:
        print("DESCARGA ERROR:", e)
        return None, None, False
