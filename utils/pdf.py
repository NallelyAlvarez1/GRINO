import tempfile
import os
import base64
from datetime import datetime
from typing import Tuple, Dict, Any
from fpdf import FPDF
from utils.database import get_presupuesto_detallado

# ========== FORMATO TEXTO ==========
def capitalizar(texto: str) -> str:
    """Capitaliza el texto para mostrarlo en el PDF"""
    return texto.capitalize()

def formato_moneda(valor: float) -> str:
    """Formatea valores monetarios con separadores de miles"""
    return f"${valor:,.0f}".replace(",", ".")

# ==========  SECCION PDF ==========
# Datos constantes
EMPRESA = "Presupuesto Jardines Alvarez"
CONTACTO_NOMBRE = "Jhonny Nicolas Alvarez"
CONTACTO_TELEFONO = "+569 6904 2513"
CONTACTO_EMAIL = "jhonnynicolasalvarez@gmail.com"

def generar_pdf(cliente_nombre: str, categorias: Dict[str, Any], lugar_cliente: str) -> str:
    """
        Genera un archivo PDF con los datos del presupuesto
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)

        # Encabezado
        pdf.set_font("Arial", style='B', size=20)
        pdf.set_fill_color(211, 211, 211)
        pdf.cell(190, 15, capitalizar(EMPRESA), ln=True, align='C', fill=True)
        pdf.ln(3)
        pdf.set_font("Arial", style='B', size=16)
        pdf.cell(190, 10, capitalizar(lugar_cliente), ln=True, align='C', fill=True)

        # Fecha y datos de contacto
        fecha_actual = datetime.now().strftime("Fecha: %d %B, %Y")
        pdf.ln(2)
        pdf.set_font("Arial", size=11)
        pdf.cell(95, 5, CONTACTO_NOMBRE, border=0)
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(18, 5, "Cliente:", border=0)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 5, capitalizar(cliente_nombre), border=0, ln=True)
        pdf.cell(95, 5, capitalizar(CONTACTO_TELEFONO), border=0, ln=True)
        pdf.cell(95, 5, capitalizar(CONTACTO_EMAIL), border=0)
        pdf.cell(0, 5, fecha_actual, border=0, ln=True)
        pdf.ln(3)

        # Presupuesto por categoría
        total_general = 0
        for categoria, data in categorias.items():
            items = data.get('items', [])
            mano_obra = data.get('mano_obra', 0)

            pdf.set_font("Arial", style='B', size=11)
            pdf.cell(200, 6, capitalizar(f"{categoria}"), ln=True)
            pdf.set_font("Arial", style='B', size=11)
            pdf.cell(60, 6, capitalizar("Nombre"), border=1)
            pdf.cell(40, 6, capitalizar("Unidad"), border=1)
            pdf.cell(30, 6, capitalizar("Precio Unitario"), border=1)
            pdf.cell(30, 6, capitalizar("Cantidad"), border=1)
            pdf.cell(30, 6, capitalizar("Total"), border=1, ln=True)

            total_categoria = 0
            for item in items:
                pdf.set_font("Arial", size=11)
                pdf.cell(60, 6, capitalizar(item.get('nombre', '')), border=1)
                pdf.cell(40, 6, capitalizar(item.get('unidad', '')), border=1)
                pdf.cell(30, 6, formato_moneda(item.get('precio_unitario', 0)), border=1)
                pdf.cell(30, 6, str(item.get('cantidad', 0)), border=1)
                pdf.cell(30, 6, formato_moneda(item.get('total', 0)), border=1, ln=True)
                total_categoria += item.get('total', 0)

            if mano_obra > 0:
                pdf.cell(160, 6, capitalizar("Mano de Obra"), border=1)
                pdf.cell(30, 6, formato_moneda(mano_obra), border=1, ln=True)
                total_categoria += mano_obra

            pdf.set_font("Arial", style='B', size=11)
            pdf.cell(160, 6, capitalizar("Total"), border=1)
            pdf.cell(30, 6, formato_moneda(total_categoria), border=1, ln=True)
            pdf.ln(5)
            total_general += total_categoria

        # Total general
        pdf.set_font("Arial", style='B', size=11)
        pdf.set_fill_color(211, 211, 211)
        pdf.cell(60, 6, capitalizar("Total"), border=1, align='R', fill=True)
        pdf.cell(30, 6, formato_moneda(total_general), border=1, align='R', ln=True)

        # Guardar en archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_path = temp_file.name
        temp_file.close()
        pdf.output(temp_path)
        
        return temp_path
        
    except Exception as e:
        raise Exception(f"Error al generar PDF: {str(e)}")

def mostrar_boton_descarga_pdf(presupuesto_id: int) -> Tuple[str, bool]:
    """
    Genera y muestra el botón para descargar un presupuesto existente
    """
    try:
        # Obtener datos del presupuesto
        presupuesto = get_presupuesto_detallado(presupuesto_id)
        if not presupuesto:
            return "Presupuesto no encontrado", False
        
        # Procesar items por categoría
        categorias = {}
        for item in presupuesto.get('items', []):
            cat_nombre = item.get('categoria') or 'Sin categoría'
            if cat_nombre not in categorias:
                categorias[cat_nombre] = {'items': [], 'mano_obra': 0}
            
            if item.get('nombre') == 'Mano de Obra':
                categorias[cat_nombre]['mano_obra'] = item.get('precio_unitario', 0)
            else:
                categorias[cat_nombre]['items'].append({
                    'nombre': item.get('nombre', 'Sin nombre'),
                    'unidad': item.get('unidad', 'Unidad'),
                    'cantidad': item.get('cantidad', 1),
                    'precio_unitario': item.get('precio_unitario', 0),
                    'total': item.get('total', 0)
                })
        
        # Generar PDF
        pdf_path = generar_pdf(
            presupuesto['cliente']['nombre'],
            categorias,
            presupuesto['lugar']['nombre']
        )
        
        # Leer y codificar el PDF
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        # Eliminar archivo temporal
        try:
            os.unlink(pdf_path)
        except Exception as e:
            print(f"Error al eliminar archivo temporal: {str(e)}")
        
        # Crear enlace de descarga
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="presupuesto_{presupuesto_id}.pdf">⬇️ Descargar PDF</a>'
        
        return href, True
        
    except Exception as e:
        error_msg = f"Error al generar PDF: {str(e)}"
        print(error_msg)  # Log para depuración
        return error_msg, False

def get_pdf_bytes(presupuesto_id: int) -> bytes:
    """
    Obtiene los bytes del PDF ya generado para un presupuesto
    """
    try:
        pdf_path = f"presupuestos/presupuesto_{presupuesto_id}.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                return f.read()
        return None
    except Exception as e:
        print(f"Error al leer PDF: {str(e)}")
        return None