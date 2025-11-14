import streamlit as st
import os
import pandas as pd
from typing import Dict, Any, List, Optional
from utils.database import (
    get_presupuesto_detallado,
    save_edited_presupuesto,
    get_clientes,
    get_lugares_trabajo,
    get_categorias,
    get_presupuestos_usuario
)
from utils.components import (\
    selector_categoria,\
    show_items_presupuesto,\
    show_mano_obra,\
    show_resumen,\
    safe_numeric_value 
)
from utils.pdf import generar_pdf
from utils.auth import check_login

st.set_page_config(page_title="Editar", page_icon="🌱", layout="wide")
# Constantes
EDICION_KEY = 'categorias_edicion'
HISTORIAL_PAGE = "pages/2_🕒_historial.py"

def calcular_total_edicion(items_data: Dict[str, Any]) -> float:
    """Calcula el total general del presupuesto, usando la utilidad de valores seguros."""
    total = 0.0
    for categoria, data in items_data.items():
        # Sumar items (usando safe_numeric_value)
        total += sum(safe_numeric_value(item['total']) for item in data['items'])
        # Sumar mano de obra (usando safe_numeric_value)
        total += safe_numeric_value(data.get('mano_obra', 0.0))
    return total

def cargar_presupuesto_en_sesion(presupuesto_id: int):
    """
    Carga los datos de un presupuesto detallado desde la DB al st.session_state[EDICION_KEY].
    """
    detalle = get_presupuesto_detallado(presupuesto_id)
    if not detalle:
        st.error(f"❌ Error al cargar el detalle del presupuesto ID: {presupuesto_id}")
        return False
        
    # Inicializar la estructura de edición
    st.session_state[EDICION_KEY] = {'general': {'items': [], 'mano_obra': 0.0}}
    
    # 1. Cargar metadatos (Cliente, Lugar, Descripción)
    st.session_state['presupuesto_cliente_id'] = detalle['cliente']['id']
    st.session_state['presupuesto_lugar_id'] = detalle['lugar']['id']
    st.session_state['presupuesto_descripcion'] = detalle['descripcion']
    
    # 2. Cargar ítems y Mano de Obra, agrupando por categoría
    for item in detalle['items']:
        cat_nombre = item.get('categoria', 'Sin Categoría') or 'Sin Categoría'
        nombre_item = item.get('nombre', '')
        
        # Aseguramos que los valores numéricos son float y manejamos None
        cantidad = safe_numeric_value(item.get('cantidad', 0))
        precio_unitario = safe_numeric_value(item.get('precio_unitario', 0))
        total = safe_numeric_value(item.get('total', 0))
        
        # Manejo de la Mano de Obra General (asumiendo que tiene un nombre específico)
        if 'mano de obra general' in nombre_item.lower():
            # Asignamos el valor al área general
            st.session_state[EDICION_KEY]['general']['mano_obra'] = total
            continue
            
        # Manejo de Mano de Obra por Categoría (si se registra como ítem simple)
        if 'mano de obra' in nombre_item.lower() and total > 0:
            if cat_nombre not in st.session_state[EDICION_KEY]:
                st.session_state[EDICION_KEY][cat_nombre] = {'items': [], 'mano_obra': 0.0}
            
            st.session_state[EDICION_KEY][cat_nombre]['mano_obra'] += total
            continue
            
        # Ítem normal
        if cat_nombre not in st.session_state[EDICION_KEY]:
            st.session_state[EDICION_KEY][cat_nombre] = {'items': [], 'mano_obra': 0.0}
            
        st.session_state[EDICION_KEY][cat_nombre]['items'].append({
            'nombre': nombre_item,
            'unidad': item.get('unidad', 'Unidad'),
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'total': total,
            'categoria': cat_nombre,
            'notas': item.get('notas', '')
        })
        
    return True

def editar_presupuesto_page():
    # Estilos CSS para compactar la interfaz (se mantiene)
    st.markdown("""
    <style>
    /* 1. Reduce el margen vertical de los contenedores de los widgets de Streamlit */
    /* Clases que contienen st.text_input, st.number_input, st.selectbox */
    div.stTextInput, div.stNumberInput, div.stSelectbox, div.stButton {
        margin-top: -15px !important; 
        margin-bottom: 1px !important;
    }

    /* 2. Reduce el relleno interno de las columnas, acercando los contenidos */
    /* Selector para los contenedores de las columnas */
    div[data-testid="column"] {
        padding-top: 2px !important;
        padding-bottom: 2px !important;
    }

    /* 3. Reduce el espacio entre las etiquetas de los encabezados de columna */
    /* Selector para el st.write("**Encabezado**") */
    div[data-testid="stText"] {
        margin-bottom: 0px !important;
        margin-top: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ------------------- VALIDACIÓN DE ACCESO -------------------
    presupuesto_id = st.session_state.get('presupuesto_a_editar_id')
    user_id = st.session_state.get('user_id')
    
    if not user_id or not presupuesto_id:
        st.error("❌ Acceso denegado. Seleccione un presupuesto del historial.")
        st.page_link(HISTORIAL_PAGE, label="Volver al Historial")
        st.stop()
        
    # ------------------- CARGA INICIAL DE DATOS -------------------
    # Si no se han cargado los datos de edición, cargarlos por primera vez
    if EDICION_KEY not in st.session_state:
        if not cargar_presupuesto_en_sesion(presupuesto_id):
            st.error("❌ No se pudieron cargar los datos. Volviendo al historial.")
            del st.session_state['presupuesto_a_editar_id']
            st.page_link(HISTORIAL_PAGE, label="Volver al Historial")
            st.stop()
        
        # Mover la estructura cargada al estado global 'categorias' para que los componentes la usen
        st.session_state['categorias'] = st.session_state[EDICION_KEY]
    
    # Si los datos están en EDICION_KEY, deben estar en 'categorias' para que los componentes funcionen
    if EDICION_KEY in st.session_state and 'categorias' not in st.session_state:
        st.session_state['categorias'] = st.session_state[EDICION_KEY]

    st.title(f"✏️ Editando Presupuesto ID: {presupuesto_id}")
    st.page_link(HISTORIAL_PAGE, label="Volver al Historial")
    st.markdown("---")
    
    # ------------------- SECCIÓN CLIENTE, LUGAR Y DESCRIPCIÓN -------------------
    
    # Cargar listas de opciones (ya se cargaron las listas en el módulo components.py, pero las recargamos aquí si es necesario)
    try:
        clientes = get_clientes()
        lugares = get_lugares_trabajo()
    except Exception as e:
        st.error(f"Error cargando clientes/lugares: {e}")
        st.stop()
    
    # Selector de cliente (usando el ID cargado previamente)
    cliente_seleccionado = st.session_state.get('presupuesto_cliente_id')
    lugar_seleccionado = st.session_state.get('presupuesto_lugar_id')
    descripcion_inicial = st.session_state.get('presupuesto_descripcion', '')

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Cliente")
        # Función para mapear el ID de cliente a su nombre
        cliente_nombre_inicial = next((n for i, n in clientes if i == cliente_seleccionado), "(Cliente no encontrado)")
        
        # Usamos el nombre inicial para el selectbox
        cliente_nombre_sel = st.selectbox(
            "Cliente",
            options=[n for i, n in clientes],
            index=[n for i, n in clientes].index(cliente_nombre_inicial) if cliente_nombre_inicial in [n for i, n in clientes] else 0,
            key="edit_cliente_selector",
            label_visibility="collapsed"
        )
        # Obtenemos el ID actualizado
        cliente_id_actualizado = next((i for i, n in clientes if n == cliente_nombre_sel), cliente_seleccionado)
        cliente_nombre_actualizado = cliente_nombre_sel
        
    with col2:
        st.markdown("##### Lugar de Trabajo")
        lugar_nombre_inicial = next((n for i, n in lugares if i == lugar_seleccionado), "(Lugar no encontrado)")

        lugar_nombre_sel = st.selectbox(
            "Lugar",
            options=[n for i, n in lugares],
            index=[n for i, n in lugares].index(lugar_nombre_inicial) if lugar_nombre_inicial in [n for i, n in lugares] else 0,
            key="edit_lugar_selector",
            label_visibility="collapsed"
        )
        lugar_id_actualizado = next((i for i, n in lugares if n == lugar_nombre_sel), lugar_seleccionado)
        lugar_nombre_actualizado = lugar_nombre_sel


    st.markdown("##### Descripción del Trabajo")
    descripcion_actualizada = st.text_area("Descripción", 
                                           value=descripcion_inicial, 
                                           key="edit_descripcion_area",
                                           label_visibility="collapsed",
                                           height=80)
    
    st.markdown("---")

    # ------------------- SECCIÓN ITEMS Y MANO DE OBRA (Usando Componentes) -------------------
    # Los componentes show_items_presupuesto y show_mano_obra operan sobre st.session_state['categorias']
    show_items_presupuesto()
    show_mano_obra()
    
    # ------------------- RESUMEN Y BOTÓN DE GUARDAR -------------------
    total_general_actualizado = calcular_total_edicion(st.session_state.get('categorias', {}))

    st.markdown("---")
    
    if total_general_actualizado > 0:
        show_resumen() 
    else:
        st.warning("El total del presupuesto es cero o negativo.")
        
    st.markdown("---")
    
    # Formulario de Guardar
    with st.form("save_edit_form"):
        st.markdown(f"**Total a Guardar:** **${total_general_actualizado:,.2f}**")
        
        if st.form_submit_button("💾 Guardar Edición y Generar PDF", type="primary", width='stretch'):
            if not cliente_id_actualizado or not lugar_id_actualizado:
                st.error("⚠️ Cliente o Lugar de Trabajo no válidos.")
            elif total_general_actualizado <= 0:
                st.error("⚠️ El total del presupuesto editado debe ser mayor a cero.")
            else:
                try:
                    # 1. Guardar en DB (Update principal, Delete items, Insert nuevos items)
                    presupuesto_guardado_id = save_edited_presupuesto(
                        presupuesto_id=presupuesto_id,
                        user_id=user_id,
                        cliente_id=cliente_id_actualizado,
                        lugar_id=lugar_id_actualizado,
                        descripcion=descripcion_actualizada,
                        items_data=st.session_state['categorias'], # Usa la data manipulada por los componentes
                        total_general=total_general_actualizado
                    )
                    
                    if presupuesto_guardado_id:
                        st.success(f"Presupuesto {presupuesto_guardado_id} guardado correctamente. Generando PDF...")
                        
                        # 2. Generar PDF (usa la data de la sesión)
                        pdf_path = generar_pdf(
                            cliente_nombre_actualizado, 
                            st.session_state['categorias'], 
                            lugar_nombre_actualizado, 
                            descripcion=descripcion_actualizada
                        )
                        
                        if not pdf_path:
                            st.error("❌ Falló la generación del archivo PDF.")
                            st.stop()
                            
                        # 3. Leer y ofrecer descarga
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()

                        # Eliminar archivo temporal
                        try:
                            os.unlink(pdf_path)
                        except Exception as e:
                            print(f"Error al eliminar archivo temporal: {str(e)}")
                        
                        # Formatear nombre del archivo igual que en mostrar_boton_descarga_pdf
                        lugar_nombre_limpio = lugar_nombre_actualizado.strip().replace(" ", "_").replace("/", "_")
                        file_name = f"Presupuesto_{lugar_nombre_limpio}_{presupuesto_id}.pdf"

                        # Mostrar botón de descarga con el nuevo formato
                        st.download_button(
                            "📄 Descargar PDF actualizado",
                            pdf_bytes,
                            file_name=file_name,
                            mime="application/pdf",
                            width='stretch'
                        )

                        # 4. Limpiar estado y volver
                        if 'presupuesto_a_editar_id' in st.session_state:
                            del st.session_state['presupuesto_a_editar_id']
                        if EDICION_KEY in st.session_state:
                            del st.session_state[EDICION_KEY]
                        if 'categorias' in st.session_state:
                             del st.session_state['categorias'] # Limpiar categorías para evitar contaminación
                            
                        st.page_link(HISTORIAL_PAGE, label="Volver al Historial para ver el nuevo registro")
                    else:
                        st.error("❌ Error al guardar la edición en la base de datos.")
                except Exception as e:
                    st.error(f"❌ Error crítico al procesar la edición: {e}")
                    st.exception(e)

is_logged_in = check_login()

if __name__ == "__main__":
    if is_logged_in:
        editar_presupuesto_page()
    else:
        st.error("🔒 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Ir a página de inicio")