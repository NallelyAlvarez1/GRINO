import tempfile
import os
import base64
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from fpdf import FPDF
from utils.database import get_presupuesto_detallado, delete_presupuesto
import locale

try:
    locale.setlocale(locale.LC_TIME, 'es_ES.utf8') 
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, 'es')

# ========== FORMATO TEXTO ==========
def formato_moneda(valor: float) -> str:
    """Formatea valores monetarios con separadores de miles"""
    return f"${valor:,.0f}".replace(",", ".")

# ==========  SECCION PDF ==========
# Datos constantes
EMPRESA = "Jardines Alvarez"
CONTACTO_NOMBRE = "Jhonny Nicolas Alvarez"
CONTACTO_TELEFONO = "+569 6904 2513"
CONTACTO_EMAIL = "jhonnynicolasalvarez@gmail.com"

def generar_pdf(cliente_nombre: str, categorias: Dict[str, Any], lugar_cliente: str, descripcion: Optional[str] = None) -> str:
    """
    Genera un archivo PDF con los datos del presupuesto
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=11)
        
        # Configurar márgenes
        pdf.set_margins(left=10, top=10, right=10)
        pdf.set_auto_page_break(auto=True, margin=15)

        # Encabezado
        COLOR_FONDO = (157, 178, 111)
        pdf.set_fill_color(*COLOR_FONDO)

        ALTO_FRANJA = 26
        MARGEN_X = 10

        # 1. Crear la franja de fondo verde
        y_inicio_fondo = pdf.get_y()
        pdf.set_xy(0, y_inicio_fondo)
        pdf.set_fill_color(175, 192, 138)
        pdf.cell(pdf.w, ALTO_FRANJA, "", border=0, ln=1, fill=True)

        # 2. Texto sobre la franja
        pdf.set_text_color(36, 36, 36)

        # a)"Presupuesto"
        pdf.set_y(y_inicio_fondo + 5)
        pdf.set_x(MARGEN_X)
        pdf.set_font("helvetica", style='B', size=24)
        pdf.cell(100, 10, "Presupuesto", border=0, ln=0, align='L', fill=False)

        # b)Nombre de la Empresa
        pdf.set_x(MARGEN_X)
        pdf.set_font("helvetica", style='', size=18)
        pdf.cell(102, 26, EMPRESA.title(), border=0, ln=0, align='L', fill=False)

        # c)Línea negra debajo del nombre de la empresa
        y_linea = pdf.get_y() + 17
        pdf.set_draw_color(56, 56, 56)
        pdf.set_line_width(0.8)
        pdf.line(MARGEN_X, y_linea, MARGEN_X + 85, y_linea)

        # d)Línea verde debajo franja verde
        y_linea = pdf.get_y() + 23 
        pdf.set_draw_color(175, 192, 138)
        pdf.set_line_width(0.8)
        pdf.line(0, y_linea, pdf.w, y_linea)

        # e) Lugar del cliente
        pdf.set_font("helvetica", style='B', size=22)
        pdf.set_y(y_inicio_fondo + (ALTO_FRANJA / 2) - 6)

        ANCHO_UTIL_PAGINA = 190 
        MARGEN_DERECHO = 10 
        ANCHO_MULTICELL = 90
        POSICION_X_INICIO = ANCHO_UTIL_PAGINA - ANCHO_MULTICELL + MARGEN_DERECHO

        pdf.set_x(POSICION_X_INICIO) 
        pdf.multi_cell(
            w=ANCHO_MULTICELL, 
            h=7,
            txt=lugar_cliente.title(), 
            border=0, 
            align='C', 
            fill=False
        )

        # añadir espacio antes de continuar
        pdf.ln(15) 

        # Fecha y datos de contacto
        fecha_actual = datetime.now().strftime("%d %B, %Y")
        pdf.ln(2)
        pdf.set_font("helvetica", size=12)

        # --- Columna izquierda: datos de contacto ---
        x_inicio = pdf.get_x()
        y_inicio = pdf.get_y()

        pdf.cell(95, 5, CONTACTO_NOMBRE, border=0, ln=True)
        pdf.cell(95, 5, CONTACTO_TELEFONO, border=0, ln=True)
        pdf.cell(95, 5, CONTACTO_EMAIL, border=0, ln=True)

        # Guardamos la altura final de la columna izquierda
        y_fin_contacto = pdf.get_y()

        # --- Línea vertical divisoria ---
        pdf.set_draw_color(56, 56, 56)
        pdf.set_line_width(0.6)
        x_linea = x_inicio + 80
        pdf.line(x_linea, y_inicio, x_linea, y_fin_contacto)

        # --- Columna derecha: Cliente y fecha ---
        pdf.set_xy(x_linea + 5, y_inicio)

        # Cliente 
        pdf.set_font("helvetica", style='B', size=10)
        pdf.cell(40, 5, "Cliente:", border=0)

        # Fecha
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 5, fecha_actual, border=0, ln=True, align='R')

        # Nombre del cliente 
        pdf.set_x(x_linea + 5)
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 6, cliente_nombre.title(), border=0, ln=True)

        # 1. Crear la franja 2 de fondo verde
        y_inicio_fondo = pdf.get_y()
        MARGEN_X_FRANJA = 10
        ALTO = 7

        pdf.set_xy(MARGEN_X_FRANJA, y_inicio_fondo + 10)
        pdf.set_fill_color(175, 192, 138)
        pdf.cell(pdf.w - 2 * MARGEN_X_FRANJA, ALTO, "", border=0, ln=1, fill=True)

        # --- Texto dentro de la franja ---
        pdf.set_text_color(36, 36, 36)
        pdf.set_font("helvetica", style='B', size=12)

        # Centrar verticalmente el texto dentro de la franja
        pdf.set_y(y_inicio_fondo + (ALTO / 2) + 7) 
        pdf.set_x(MARGEN_X_FRANJA + 5)
        
        if descripcion:
            texto_franja = descripcion.strip().capitalize()
        else:
            texto_franja = "Trabajo a Realizar" 

        pdf.cell(0, 6, texto_franja, border=0, ln=1, align='C')

        pdf.ln(3)

        # Presupuesto por categoría
        total_general = 0
        for categoria, data in categorias.items():
            items = data.get('items', [])
            mano_obra = data.get('mano_obra', 0)
        
            if mano_obra > 0:
                items.append({
                    'nombre': 'Mano de Obra',
                    'unidad': 'Unidad', 
                    'cantidad': 1,
                    'precio_unitario': mano_obra,
                    'total': mano_obra,
                    'descripcion': 'Mano de obra'
                })

            # Filtrar categorías vacías
            if not items:
                continue
                
            # Verificar si necesitamos nueva página antes de agregar una categoría
            if pdf.get_y() > 270:
                pdf.add_page()
                pdf.set_y(10)
            
            pdf.set_line_width(0.2)
            pdf.set_font("helvetica", style='B', size=12)
            texto = f"{categoria.title()}"
            pdf.cell(200, 6, texto, ln=True)

            pdf.set_draw_color(194, 207, 165)
            pdf.set_line_width(0.8)
            margen_izquierdo = 10
            ancho_total = 190
            y_linea = pdf.get_y() + 0.2
            pdf.line(margen_izquierdo, y_linea, margen_izquierdo + ancho_total, y_linea)
            pdf.ln(2) 
            
            pdf.set_font("helvetica", style='B', size=11)
            pdf.set_line_width(0.2)
            pdf.set_draw_color(56, 56, 56)
            pdf.cell(75, 6, "Insumo", border='B')
            pdf.cell(25, 6, "Unidad", border='B', align='C')
            pdf.cell(20, 6, "Cantidad", border='B', align='C')
            pdf.cell(35, 6, "Precio Unitario", border='B', align='C')
            pdf.cell(35, 6, "Total", border='B', ln=True, align='C')

            total_categoria = 0
            for item in items:
                # Verificar si necesitamos nueva página antes de agregar un item
                if pdf.get_y() > 270:
                    pdf.add_page()
                    # Redibujar encabezados de tabla en nueva página
                    pdf.set_font("helvetica", style='B', size=11)
                    pdf.cell(75, 6, "Insumo", border='B')
                    pdf.cell(25, 6, "Unidad", border='B', align='C')
                    pdf.cell(20, 6, "Cantidad", border='B', align='C')
                    pdf.cell(35, 6, "Precio Unitario", border='B', align='C')
                    pdf.cell(35, 6, "Total", border='B', ln=True, align='C')
                
                pdf.set_font("helvetica", size=11)
                
                # VERIFICAR SI ES MANO DE OBRA
                if item.get('descripcion') == 'Mano de obra':
                    # Formato especial para mano de obra: solo nombre y total
                    pdf.cell(155, 6, item.get('nombre', '').title(), border=1)
                    pdf.cell(35, 6, formato_moneda(item.get('total', 0)), border=1, ln=True)
                else:
                    # Items normales con todas las columnas
                    pdf.cell(75, 6, item.get('nombre', '').title(), border=1)
                    pdf.cell(25, 6, item.get('unidad', '').title(), border=1)
                    pdf.cell(20, 6, str(int(item.get('cantidad', 0))), border=1)
                    pdf.cell(35, 6, formato_moneda(item.get('precio_unitario', 0)), border=1)
                    pdf.cell(35, 6, formato_moneda(item.get('total', 0)), border=1, ln=True)
                
                total_categoria += item.get('total', 0)

            pdf.set_font("helvetica", style='B', size=11)
            pdf.cell(155, 6, "Total", border=1)
            pdf.cell(35, 6, formato_moneda(total_categoria), border=1, ln=True)
            pdf.ln(5)
            total_general += total_categoria

        # Verificar si hay espacio suficiente para el cuadro del total
        if pdf.get_y() > 270:
            pdf.add_page()
        
        # Total general
        pdf.set_fill_color(194, 207, 165)
        ANCHO_TOTAL = 40
        ALTO_TOTAL = 15
        margen_derecho = 10
        x_inicial = pdf.w - ANCHO_TOTAL - margen_derecho
        y_inicial = pdf.get_y()

        # Dibuja el rectángulo verde
        pdf.rect(x_inicial, y_inicial, ANCHO_TOTAL, ALTO_TOTAL, style='F')

        # Texto "Total"
        pdf.set_xy(x_inicial + 4, y_inicial + 2)
        pdf.set_font("helvetica", style='B', size=11)
        pdf.set_text_color(36, 36, 36)
        pdf.cell(0, 5, "Total", border=0)

        # Monto
        pdf.set_font("helvetica", style='B', size=14)
        pdf.set_text_color(56, 56, 56)
        pdf.set_xy(x_inicial, y_inicial + 6)
        pdf.cell(ANCHO_TOTAL, 8, formato_moneda(total_general), border=0, align='C')

        # Salto de línea después del cuadro
        pdf.ln(ALTO_TOTAL + 2)

        # Guardar en archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_path = temp_file.name
        temp_file.close()
        pdf.output(temp_path)
        
        return temp_path
        
    except Exception as e:
        raise Exception(f"Error al generar PDF: {str(e)}")
    
def mostrar_boton_descarga_pdf(presupuesto_id: int) -> Tuple[bytes, str, bool]:
    """
    Genera y devuelve los bytes de un PDF y el nombre de archivo sugerido
    """
    try:
        # Obtener datos del presupuesto
        presupuesto = get_presupuesto_detallado(presupuesto_id)
        if not presupuesto:
            return None, "", False
        
        # Procesar items por categoría
        categorias = {}
        for item in presupuesto.get('items', []):
            cat_nombre = item.get('categoria') or 'Sin categoría'
            if cat_nombre not in categorias:
                categorias[cat_nombre] = {'items': [], 'mano_obra': 0}
            
            # 🔥 CORREGIR: Incluir mano de obra en la estructura
            if item.get('nombre') == 'Mano de Obra':
                categorias[cat_nombre]['mano_obra'] = item.get('precio_unitario', 0)
            else:
                categorias[cat_nombre]['items'].append({
                    'nombre': item.get('nombre', 'Sin nombre'),
                    'unidad': item.get('unidad', 'Unidad'),
                    'cantidad': item.get('cantidad', 1),
                    'precio_unitario': item.get('precio_unitario', 0),
                    'total': item.get('total', 0),
                    'descripcion': item.get('notas', '')  # 🔥 AGREGAR DESCRIPCIÓN
                })
            
        # Generar PDF
        pdf_path = generar_pdf(
            presupuesto['cliente']['nombre'],
            categorias,
            presupuesto['lugar']['nombre'],
            descripcion=presupuesto.get('descripcion', ''),
        )
        
        # Leer el PDF
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        # Eliminar archivo temporal
        try:
            os.unlink(pdf_path)
        except Exception as e:
            print(f"Error al eliminar archivo temporal: {str(e)}")
        
        # Nombre del archivo
        lugar_nombre = presupuesto['lugar']['nombre'].strip().replace(" ", "_")
        file_name = f"Presupuesto_{lugar_nombre}.pdf"

        return pdf_bytes, file_name, True
        
    except Exception as e:
        error_msg = f"Error al generar PDF: {str(e)}"
        print(error_msg)
        return None, "", False
