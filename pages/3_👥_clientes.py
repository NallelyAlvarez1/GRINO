import streamlit as st
from fpdf import FPDF
from datetime import datetime
import locale
import psycopg2
from io import BytesIO
import json
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
import sqlite3  


import time

# Verificar si el usuario está logueado
if "usuario" not in st.session_state or not st.session_state["usuario"]:
    # Mostrar el mensaje de advertencia
    st.warning("❌ Debes iniciar sesión primero.")
    time.sleep(1)
    
    # Redirigir a la página de inicio
    st.switch_page("inicio.py")


def obtener_usuario_id():
    try:
        # Obtener el correo del usuario desde la session_state
        usuario_email = st.session_state.get("usuario_email")
        if not usuario_email:
            st.error("⚠ No hay un usuario autenticado.")
            return None

        # Conectar a la base de datos
        conn = conectar_bd()
        cursor = conn.cursor()

        # Obtener el ID del usuario en la base de datos
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (usuario_email,))
        usuario_id = cursor.fetchone()

        cursor.close()
        conn.close()

        return usuario_id[0] if usuario_id else None
    except Exception as e:
        st.error(f"Error obteniendo usuario: {e}")
        return None
    
# 📌 Conexión a la base de datos
def conectar_bd():
    return psycopg2.connect(
        dbname="presu",
        user="postgres",
        password="019283",
        host="localhost",
        port="5432"
    )

# 📌 Obtener usuario automáticamente
def obtener_usuario_id():
    try:
        usuario_email = st.session_state.get("usuario_email")
        if not usuario_email:
            st.error("⚠ No hay un usuario autenticado.")
            return None

        conn = conectar_bd()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (usuario_email,))
        usuario_id = cursor.fetchone()

        cursor.close()
        conn.close()

        return usuario_id[0] if usuario_id else None
    except Exception as e:
        st.error(f"Error obteniendo usuario: {e}")
        return None

# 📌 Función para guardar el presupuesto en la BD
def guardar_presupuesto_en_bd(cliente_id, categorias, pdf):
    try:
        # Obtener el ID del usuario de la sesión directamente
        usuario_id = obtener_usuario_id()
        if not usuario_id:
            st.error("⚠ No se encontró el usuario. Asegúrate de haber iniciado sesión.")
            return None

        # Conectar a la base de datos
        conn = conectar_bd()
        conn.autocommit = True  # 🔥 Asegura que los cambios se guarden
        cursor = conn.cursor()

        categorias_json = json.dumps(categorias)

        # Convertir el PDF a binario correctamente
        pdf_bytes = pdf.output(dest="S").encode("latin1")

        # Insertar el presupuesto en la base de datos
        cursor.execute("""
            INSERT INTO presupuestos (usuario_id, cliente_id, categorias, pdf)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (usuario_id, cliente_id, categorias_json, psycopg2.Binary(pdf_bytes)))

        presupuesto_id = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        conn.close()

        st.success(f"✅ Presupuesto guardado con éxito (ID {presupuesto_id}).")
        return presupuesto_id

    except psycopg2.Error as e:
        st.error(f"❌ Error al guardar el presupuesto: {e}")
        return None
    
# Función para capitalizar la primera letra de cada oración
def capitalizar(texto):
    return texto.capitalize()

# Función moneda
def formato_moneda(valor):
    return f"${valor:,.0f}".replace(",", ".")

# Datos constantes
EMPRESA = "Presupuesto Jardines Alvarez"
CONTACTO_NOMBRE = "Jhonny Nicolas Alvarez"
CONTACTO_TELEFONO = "+569 6904 2513"
CONTACTO_EMAIL = "jhonnynicolasalvarez@gmail.com"

# Función para crear el PDF
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

    # Obtener la fecha actual y formatearla
    fecha_actual = datetime.now().strftime("Fecha: %d %B, %Y")
    # Datos de contacto
    pdf.ln(2)
    pdf.set_font("Arial", size=11)
    pdf.cell(95, 5, CONTACTO_NOMBRE, border=0)

    # Cliente en negrita
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(18, 5, "Cliente:", border=0)

    # Cliente_nombre en texto normal
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 5, capitalizar(cliente_nombre), border=0, ln=True)

    # Teléfono
    pdf.cell(95, 5, capitalizar(CONTACTO_TELEFONO), border=0, ln=True)

    # Email y fecha en la misma línea
    pdf.cell(95, 5, capitalizar(CONTACTO_EMAIL), border=0)  # Email en la primera mitad
    pdf.cell(0, 5, fecha_actual, border=0, ln=True)

    pdf.ln(3)

    # Presupuesto por categoría
    total_general = 0
    for categoria, data in categorias.items():
        items = data['items']
        mano_obra = data['mano_obra']

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

        # Agregar valor de mano de obra si está presente
        if mano_obra > 0:
            pdf.cell(160, 6, capitalizar("Mano de Obra"), border=1)
            pdf.cell(30, 6, formato_moneda(mano_obra), border=1, ln=True)
            total_categoria += mano_obra

        # Total por categoría
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

# Interfaz de Streamlit
# Crear una barra superior con el nombre del usuario en la esquina superior derecha
col1, col2 = st.columns([8, 2])  # Ajuste de columnas para alineación
with col2:
    st.subheader(f"👤 **{st.session_state['usuario']}**")  # Nombre del usuario alineado a la derecha
st.header("Generador de Presupuestos", divider="rainbow")

col1, col2 = st.columns(2)
with col1:
    cliente_nombre = st.text_input("Nombre del Cliente:", "")
with col2:
    lugar_cliente = st.text_input("Lugar de trabajo:", "")

st.subheader("Items del presupuesto", divider="rainbow")

# Gestión dinámica de categorías
if 'categorias' not in st.session_state:
    st.session_state['categorias'] = {}

# Entrada para agregar categoría y datos del ítem
col1, col2 = st.columns(2)
with col1:
    categoria_item = st.text_input("Nombre de la Categoría para el Ítem:")
with col2:
    nombre_item = st.text_input("Nombre del Ítem:")

col1, col2, col3 = st.columns(3)
with col1:
    unidad = st.selectbox("Unidad:", ["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro"])
with col2:
    cantidad = st.number_input("Cantidad:", min_value=1, step=1)
with col3:
    precio_unitario = st.number_input("Precio Unitario:", min_value=0)
    

total = precio_unitario * cantidad

if st.button("Agregar Ítem"):
    if not categoria_item:
        st.error("Por favor, ingrese el nombre de la categoría para el ítem.")
    elif not nombre_item:
        st.error("Por favor, ingrese el nombre del ítem.")
    else:
        # Inicializar la categoría si no existe
        if categoria_item not in st.session_state['categorias']:
            st.session_state['categorias'][categoria_item] = {'items': [], 'mano_obra': 0}

        # Agregar el ítem a la lista de ítems dentro de la categoría
        st.session_state['categorias'][categoria_item]['items'].append({
            'nombre': nombre_item,
            'unidad': unidad,
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'total': total
        })

        st.success(f"Ítem '{nombre_item}' agregado correctamente en la categoría '{categoria_item}'.")

# Entrada para agregar mano de obra
st.subheader("Agregar Mano de Obra", divider="rainbow")

col1, col2 = st.columns(2)
with col1:
    categoria_mano_obra = st.text_input("Nombre de la Categoría para la Mano de Obra:")
with col2:
    mano_obra = st.number_input("Costo de Mano de Obra:", min_value=0, step=1)

if st.button("Agregar Mano de Obra"):
    if not categoria_mano_obra:
        st.error("Por favor, ingrese el nombre de la categoría para la mano de obra.")
    elif mano_obra <= 0:
        st.error("Por favor, ingrese un costo válido para la mano de obra.")
    else:
        # Inicializar la categoría si no existe
        if categoria_mano_obra not in st.session_state['categorias']:
            st.session_state['categorias'][categoria_mano_obra] = {'items': [], 'mano_obra': 0}

        # Agregar o actualizar el costo de mano de obra
        st.session_state['categorias'][categoria_mano_obra]['mano_obra'] = mano_obra

        st.success(f"Mano de obra de ${mano_obra:.2f} agregada correctamente en la categoría '{categoria_mano_obra}'.")

import pandas as pd

st.subheader("Resumen de presupuesto", divider="rainbow")
total_general = 0

for cat, data in st.session_state['categorias'].items():
    items = data['items']
    mano_obra = data['mano_obra']
    
    if items or mano_obra > 0:
        total_categoria = sum(item['total'] for item in items) + mano_obra
        total_general += total_categoria

        st.write(f"### {cat}")  # Mostrar el nombre de la categoría

        # Mostrar encabezados solo una vez
        col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 2, 2, 2, 2, 0.8, 0.8])
        col1.write("**Nombre**")
        col2.write("**Unidad**")
        col3.write("**Cantidad**")
        col4.write("**Precio**")
        col5.write("**Total**")

        # Cambio de la visibilidad de las etiquetas para mejorar accesibilidad
        for index, item in enumerate(items):
            col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 2, 2, 2, 2, 0.8, 0.8])

            with col1:
                nuevo_nombre = st.text_input("Nombre del ítem", item['nombre'], key=f"nombre_{cat}_{index}")  # Etiqueta visible
            with col2:
                nueva_unidad = st.selectbox("Unidad", ["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro"],
                                            index=["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro"].index(item['unidad']),
                                            key=f"unidad_{cat}_{index}")
            with col3:
                nueva_cantidad = st.number_input("Cantidad", min_value=1, step=1, value=item['cantidad'],
                                                key=f"cantidad_{cat}_{index}")
            with col4:
                nuevo_precio = st.number_input("Precio Unitario", min_value=0, value=item['precio_unitario'],
                                            key=f"precio_{cat}_{index}")
            with col5:
                nuevo_total = nueva_cantidad * nuevo_precio
                st.write(formato_moneda(nuevo_total))

            with col6:
                if st.button("💾", key=f"guardar_{cat}_{index}"):
                    st.session_state['categorias'][cat]['items'][index] = {
                        'nombre': nuevo_nombre,
                        'unidad': nueva_unidad,
                        'cantidad': nueva_cantidad,
                        'precio_unitario': nuevo_precio,
                        'total': nuevo_total
                    }
                    st.rerun()

            with col7:
                if st.button("❌", key=f"eliminar_{cat}_{index}"):
                    del st.session_state['categorias'][cat]['items'][index]
                    st.rerun()


        # 💡 Mover la sección de la mano de obra **fuera** del bucle de los ítems
        if mano_obra > 0:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**Mano de Obra:** {formato_moneda(mano_obra)}")
            with col2:
                if st.button("❌ Eliminar", key=f"eliminar_mano_obra_{cat}_unique"):
                    st.session_state['categorias'][cat]['mano_obra'] = 0
                    st.rerun()



st.write(f"### Total General: {formato_moneda(total_general)}")


# 📌 Botón para guardar presupuesto
if st.button("Guardar Presupuesto"):
    usuario_id = obtener_usuario_id()

    if usuario_id:
        cliente_id = obtener_usuario_id(usuario_id)  # Solo una llamada a la función
        
        if not cliente_id:
            st.error("⚠ No se pudo obtener el cliente.")
        elif not any(st.session_state.get('categorias', {}).values()):
            st.error("Por favor, agregue al menos un ítem al presupuesto.")
        else:
            # Variables necesarias (asegúrate de que existen)
            cliente_nombre = st.session_state.get('cliente_nombre', "")  # Usa el valor almacenado en session_state
            lugar_cliente = st.session_state.get('lugar_cliente', "")  # Si también quieres guardar el lugar del cliente

            # Generar el PDF con los datos actuales
            pdf = generar_pdf(cliente_nombre, st.session_state['categorias'], lugar_cliente)

            # Guardar en la BD
            presupuesto_id = guardar_presupuesto_en_bd(
                cliente_id=cliente_id,
                categorias=st.session_state['categorias'],
                pdf=pdf
            )

            if presupuesto_id:
                st.success(f"✅ Presupuesto guardado exitosamente con ID {presupuesto_id}.")

                # Generar archivo PDF en memoria
                pdf_bytes = BytesIO()
                pdf.output(pdf_bytes)
                pdf_bytes.seek(0)

                # Botón de descarga automática del PDF
                st.download_button(
                    label="📄 Descargar PDF",
                    data=pdf_bytes,
                    file_name=f"Presupuesto_{cliente_nombre.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("❌ Error al guardar el presupuesto.")

    else:
        st.error("⚠ No se pudo obtener el ID del usuario.")
