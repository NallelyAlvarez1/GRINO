import tempfile
import os
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from fpdf import FPDF
from utils.database import get_presupuesto_detallado
import locale
import math
import streamlit as st

# ==================== UTILIDADES ====================
def safe_float_value(value: Any) -> float:
    """Convierte un valor a float de forma segura, manejando None, cadenas y errores de conversión."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

# Configuración de locale (se mantiene)
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
    # Usamos int(round(valor)) para trabajar con enteros y evitar problemas de visualización de decimales
    return f"${int(round(valor)):,}".replace(",", "X").replace(".", ",").replace("X", ".")

# ==========  SECCION PDF ==========
# Datos constantes
EMPRESA = "Jardines Alvarez"
CONTACTO_NOMBRE = "Jhonny Nicolas Alvarez"
CONTACTO_TELEFONO = "+569 6904 2513"
CONTACTO_EMAIL = "jhonnynicolasalvarez@gmail.com"

class PDF(FPDF):
    """Clase PDF personalizada para incluir encabezado y pie de página."""
    def header(self):
        self.set_font('Arial', 'B', 12)
        # Nombre de la Empresa
        self.cell(0, 5, EMPRESA, 0, 1, 'C') 
        self.set_font('Arial', '', 9)
        # Datos de contacto
        self.cell(0, 5, f"Contacto: {CONTACTO_NOMBRE} | Teléfono: {CONTACTO_TELEFONO} | Email: {CONTACTO_EMAIL}", 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Página %s de {nb}' % self.page_no(), 0, 0, 'C')

def generar_pdf(cliente_nombre: str, categorias: Dict[str, Any], lugar_cliente: str, descripcion: Optional[str] = None) -> str:
    """
    Genera un archivo PDF con los datos del presupuesto
    """
    try:
        # Inicializar PDF
        pdf = PDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Título del Presupuesto
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'PRESUPUESTO DE TRABAJO', 0, 1, 'L')
        pdf.ln(2)

        # Información del Cliente y Trabajo
        pdf.set_font('Arial', '', 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(50, 6, 'Cliente:', 1, 0, 'L', 1)
        pdf.cell(0, 6, cliente_nombre, 1, 1, 'L', 0)
        
        pdf.cell(50, 6, 'Lugar de Trabajo:', 1, 0, 'L', 1)
        pdf.cell(0, 6, lugar_cliente, 1, 1, 'L', 0)
        
        pdf.cell(50, 6, 'Fecha:', 1, 0, 'L', 1)
        pdf.cell(0, 6, datetime.now().strftime('%d de %B de %Y'), 1, 1, 'L', 0)
        
        if descripcion:
            pdf.cell(50, 6, 'Trabajo a Realizar:', 1, 0, 'L', 1)
            pdf.multi_cell(0, 6, descripcion, 1, 'L', 0)
            
        pdf.ln(5)

        total_general_pdf = 0.0

        # Iterar sobre las categorías (items_data es el diccionario de categorías)
        for cat_nombre, data in categorias.items():
            
            # --- Mano de Obra General ---
            if cat_nombre == 'general':
                mano_obra_general = safe_float_value(data.get('mano_obra', 0))
                if mano_obra_general > 0:
                    pdf.set_font('Arial', 'B', 12)
                    pdf.set_fill_color(220, 220, 255)
                    pdf.cell(0, 7, 'MANO DE OBRA GENERAL', 1, 1, 'L', 1)
                    
                    pdf.set_font('Arial', '', 10)
                    pdf.cell(160, 6, 'Costo de Mano de Obra para el trabajo completo (Global)', 1, 0, 'L')
                    pdf.cell(0, 6, formato_moneda(mano_obra_general), 1, 1, 'R')
                    total_general_pdf += mano_obra_general
                    pdf.ln(3)
                continue
                
            # --- Categorías con Ítems y/o Mano de Obra ---
            items = data.get('items', [])
            mano_obra_cat = safe_float_value(data.get('mano_obra', 0))
            
            if not items and mano_obra_cat == 0:
                continue

            pdf.set_font('Arial', 'B', 12)
            pdf.set_fill_color(220, 220, 220)
            pdf.cell(0, 7, f'CATEGORÍA: {cat_nombre.upper()}', 1, 1, 'L', 1)

            # Encabezados de la tabla de ítems
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(70, 6, 'Descripción', 1, 0, 'L', 1)
            pdf.cell(20, 6, 'Unidad', 1, 0, 'C', 1)
            pdf.cell(20, 6, 'Cant.', 1, 0, 'C', 1)
            pdf.cell(30, 6, 'P. Unitario', 1, 0, 'R', 1)
            pdf.cell(30, 6, 'Total', 1, 1, 'R', 1)

            total_categoria = 0.0
            pdf.set_font('Arial', '', 9)
            
            # Detalle de ítems
            for item in items:
                nombre = item.get('nombre', 'Item')
                unidad = item.get('unidad', 'Unidad')
                cantidad = safe_float_value(item.get('cantidad', 0))
                precio_unitario = safe_float_value(item.get('precio_unitario', 0))
                total_item = safe_float_value(item.get('total', 0))
                notas = item.get('descripcion', '') # El campo en utils.pdf original era 'descripcion'

                total_categoria += total_item
                
                # Fila principal (Nombre y datos numéricos)
                # Ancho: 70 (Nombre) + 20 (Unidad) + 20 (Cant) + 30 (P.U.) + 30 (Total) = 170

                # Guardar posición Y para el multicell
                y_start = pdf.get_y()
                
                # 1. Nombre (MultiCell)
                pdf.multi_cell(70, 5, nombre, 0, 'L', 0, 0, '', y_start) 

                # 2. Datos numéricos (Saltamos el espacio de 70)
                pdf.set_xy(pdf.get_x() + 70, y_start)
                pdf.cell(20, 5, unidad, 0, 0, 'C')
                pdf.cell(20, 5, str(cantidad), 0, 0, 'C')
                pdf.cell(30, 5, formato_moneda(precio_unitario), 0, 0, 'R')
                pdf.cell(30, 5, formato_moneda(total_item), 0, 1, 'R')
                
                # 3. Notas (Si existen)
                if notas:
                    pdf.set_x(10) # Volver al margen izquierdo
                    pdf.set_font('Arial', 'I', 8)
                    pdf.cell(0, 4, f'Nota: {notas}', 0, 1, 'L')
                    pdf.set_font('Arial', '', 9)
                
                pdf.cell(0, 1, '', 'T', 1, 'L') # Separador de línea

            # Detalle Mano de Obra por Categoría
            if mano_obra_cat > 0:
                pdf.set_font('Arial', '', 10)
                pdf.cell(100, 6, f'Mano de Obra para {cat_nombre}', 1, 0, 'L')
                pdf.cell(60, 6, '', 1, 0, 'C') # Celda vacía
                pdf.cell(30, 6, formato_moneda(mano_obra_cat), 1, 1, 'R')
                total_categoria += mano_obra_cat
                
            # Total de la Categoría
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(160, 6, f'TOTAL {cat_nombre.upper()}', 1, 0, 'R', 1)
            pdf.cell(30, 6, formato_moneda(total_categoria), 1, 1, 'R', 1)
            pdf.ln(5)
            
            total_general_pdf += total_categoria

        # TOTAL GENERAL
        pdf.set_font('Arial', 'B', 14)
        pdf.set_fill_color(180, 255, 180) # Verde claro
        pdf.cell(160, 10, 'TOTAL PRESUPUESTO', 1, 0, 'R', 1)
        pdf.cell(30, 10, formato_moneda(total_general_pdf), 1, 1, 'R', 1)

        # Guardar en archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf.output(tmp.name)
            return tmp.name

    except Exception as e:
        print(f"Error generando PDF: {e}")
        st.error(f"Error en generación de PDF: {e}")
        return "" # Devolver cadena vacía si falla

def mostrar_boton_descarga_pdf(presupuesto_id: int) -> Tuple[Optional[bytes], Optional[str], bool]:
    """
    Obtiene el detalle del presupuesto, genera el PDF y devuelve los bytes y el nombre.
    """
    try:
        presupuesto = get_presupuesto_detallado(presupuesto_id)
        if not presupuesto:
            return None, None, False
            
        # 1. Reestructurar los ítems por categoría para el generador de PDF
        categorias = {}
        total_general_mo = 0.0 # Usado solo para MO General si no está en un ítem
        
        for item in presupuesto.get('items', []):
            cat_nombre = item.get('categoria', 'Sin Categoría') or 'Sin Categoría'
            
            # --- MANEJO DE VALORES NUMÉRICOS SEGURO ---
            total_item = safe_float_value(item.get('total'))
            precio_unitario = safe_float_value(item.get('precio_unitario'))
            
            # Inicializar la categoría si es la primera vez
            if cat_nombre not in categorias:
                categorias[cat_nombre] = {'items': [], 'mano_obra': 0.0}

            # Lógica para separar Mano de Obra General
            if 'mano de obra general' in item.get('nombre', '').lower():
                 # Si el ítem es Mano de Obra General, lo mapeamos a la categoría 'general' para el PDF
                 categorias['general'] = {'items': [], 'mano_obra': precio_unitario}
                 total_general_mo += precio_unitario # Sumamos el total de MO general
                 continue
            
            # Lógica para Mano de Obra por Categoría (asumiendo que tiene precio unitario pero no cantidad)
            # Nota: Si el item tiene un nombre que indica MO, y no es MO General.
            if 'mano de obra' in item.get('nombre', '').lower() and total_item > 0:
                 categorias[cat_nombre]['mano_obra'] += total_item
                 continue

            # Item normal
            categorias[cat_nombre]['items'].append({
                'nombre': item.get('nombre', 'Sin nombre'),
                'unidad': item.get('unidad', 'Unidad'),
                'cantidad': safe_float_value(item.get('cantidad', 1)),
                'precio_unitario': precio_unitario,
                'total': total_item,
                'descripcion': item.get('notas', '')  # Usamos 'notas' como descripción en el PDF
            })
            
        # Aseguramos que 'general' exista para la MO general
        if 'general' not in categorias:
            categorias['general'] = {'items': [], 'mano_obra': 0.0}
            
        # 2. Generar PDF
        pdf_path = generar_pdf(
            presupuesto['cliente']['nombre'],
            categorias,
            presupuesto['lugar']['nombre'],
            descripcion=presupuesto.get('descripcion', ''),
        )
        
        if not pdf_path:
            return None, None, False
            
        # 3. Leer el PDF
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        # 4. Eliminar archivo temporal
        try:
            os.unlink(pdf_path)
        except Exception as e:
            print(f"Error al eliminar archivo temporal: {str(e)}")
        
        # 5. Nombre del archivo
        lugar_nombre = presupuesto['lugar']['nombre'].strip().replace(" ", "_").replace("/", "_")
        file_name = f"Presupuesto_{lugar_nombre}_{presupuesto_id}.pdf"

        return pdf_bytes, file_name, True
        
    except Exception as e:
        print(f"Error en mostrar_boton_descarga_pdf: {e}")
        return None, None, False