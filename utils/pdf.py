import tempfile
import os
import base64
from datetime import datetime
from fpdf import FPDF
from database import save_presupuesto_completo, get_presupuesto_detallado

def capitalizar(texto):
    return texto.capitalize()

def formato_moneda(valor):
    return f"${valor:,.0f}".replace(",", ".")

# Datos constantes
EMPRESA = "Presupuesto Jardines Alvarez"
CONTACTO_NOMBRE = "Jhonny Nicolas Alvarez"
CONTACTO_TELEFONO = "+569 6904 2513"
CONTACTO_EMAIL = "jhonnynicolasalvarez@gmail.com"

def generar_pdf(cliente_nombre, categorias, lugar_cliente):
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
        items = data['items']
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
            pdf.cell(60, 6, capitalizar(item['nombre']), border=1)
            pdf.cell(40, 6, capitalizar(item['unidad']), border=1)
            pdf.cell(30, 6, formato_moneda(item['precio_unitario']), border=1)
            pdf.cell(30, 6, str(item['cantidad']), border=1)
            pdf.cell(30, 6, formato_moneda(item['total']), border=1, ln=True)
            total_categoria += item['total']

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

    return pdf

def guardar_presupuesto_completo(presupuesto_id: int, categorias: dict, cliente_nombre: str, lugar_nombre: str):
    """Guarda el presupuesto en la base de datos y genera el PDF"""
    try:
        # 1. Guardar en la base de datos
        save_presupuesto_completo(presupuesto_id, categorias)
        
        # 2. Generar PDF
        pdf = generar_pdf(cliente_nombre, categorias, lugar_nombre)
        
        # 3. Crear archivo temporal para el PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf.output(tmpfile.name)
            tmpfile.seek(0)
            pdf_bytes = tmpfile.read()
        
        # 4. Convertir a base64 para descarga
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="presupuesto_{presupuesto_id}.pdf">⬇️ Descargar PDF</a>'
        
        return href, True
    except Exception as e:
        return f"Error al guardar: {str(e)}", False

def mostrar_boton_descarga_pdf(presupuesto_id: int):
    """Muestra el botón para descargar un presupuesto existente"""
    presupuesto = get_presupuesto_detallado(presupuesto_id)
    if not presupuesto:
        return "Presupuesto no encontrado", False
    
    categorias = {}
    for item in presupuesto['items']:
        cat_nombre = item['categoria'] or 'Sin categoría'
        if cat_nombre not in categorias:
            categorias[cat_nombre] = {'items': [], 'mano_obra': 0}
        
        if item['nombre'] == 'Mano de Obra':
            categorias[cat_nombre]['mano_obra'] = item['precio_unitario']
        else:
            categorias[cat_nombre]['items'].append({
                'nombre': item['nombre'],
                'unidad': item['unidad'],
                'cantidad': item['cantidad'],
                'precio_unitario': item['precio_unitario'],
                'total': item['total']
            })
    
    pdf = generar_pdf(
        presupuesto['cliente']['nombre'],
        categorias,
        presupuesto['lugar']['nombre']
    )
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        tmpfile.seek(0)
        pdf_bytes = tmpfile.read()
    
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="presupuesto_{presupuesto_id}.pdf">⬇️ Descargar PDF</a>'
    
    return href, True

def get_pdf_bytes(presupuesto_id: int) -> bytes:
    """
    Obtiene los bytes del PDF ya generado para un presupuesto
    Implementa según cómo almacenes los PDFs (filesystem/S3/base de datos)
    """
    # Ejemplo para PDFs guardados en filesystem:
    pdf_path = f"presupuestos/presupuesto_{presupuesto_id}.pdf"
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            return f.read()
    return None