import streamlit as st
import pandas as pd
from typing import Any, Dict, List, Tuple, Optional, Union
from utils.database import (
    create_categoria, 
    get_categorias, 
    get_clientes, 
    create_cliente, 
    get_lugares_trabajo, 
    create_lugar_trabajo
)

# ==================== UTILIDADES ====================
def safe_numeric_value(value: Any) -> float:
    """
    Convierte un valor a float de forma segura, 
    manejando None, cadenas y errores de conversión.
    """
    if value is None:
        return 0.0
    try:
        # Se asegura de que se convierta a float para mantener decimales si existen
        return float(value)
    except (TypeError, ValueError):
        return 0.0

# ==================== SECCION CLIENTE - LUGAR DE TRABAJO ====================
# [Contenido de show_cliente_lugar_selector y _selector_entidad se asume correcto, 
# se enfoca en que las llamadas a create/get sean seguras.]

def _selector_entidad(datos: List[Tuple[int, str]], label: str, key: str, btn_nuevo: str, modal_title: str, placeholder_nombre: str, funcion_creacion: callable, label_visibility: str) -> Optional[int]:
    # ... (cuerpo de la función original)
    # Se incluye el cuerpo completo para que el archivo sea funcional
    
    # Asegura que el cliente/lugar 'Ninguno' se maneje
    opciones_display = ["(Seleccione)"] + [nombre for _, nombre in datos]
    opciones_ids = [None] + [id for id, _ in datos]
    
    # 1. Selector de entidad existente
    entidad_nombre_seleccionada = st.selectbox(
        label=label.capitalize(),
        options=opciones_display,
        key=f"{key}_selector",
        label_visibility=label_visibility,
    )
    
    # 2. Obtener el ID seleccionado
    entidad_id = None
    if entidad_nombre_seleccionada and entidad_nombre_seleccionada != "(Seleccione)":
        try:
            # Buscar el ID basado en el nombre
            entidad_id = next((id for id, nombre in datos if nombre == entidad_nombre_seleccionada), None)
        except StopIteration:
            # Esto no debería ocurrir si las listas están sincronizadas
            entidad_id = None
            
    # 3. Botón para crear nueva entidad
    if st.button(btn_nuevo, key=f"{key}_new_btn", use_container_width=True):
        st.session_state[f'{key}_modal_open'] = True
    
    # 4. Modal de creación (usando expander para simular modal)
    if st.session_state.get(f'{key}_modal_open', False):
        st.subheader(modal_title, divider='blue')
        with st.form(key=f"form_new_{key}", border=True):
            nombre_nuevo = st.text_input(placeholder_nombre, key=f"new_{key}_name")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.form_submit_button("💾 Crear", type="primary"):
                    if nombre_nuevo.strip():
                        # Asegurar que user_id está en la sesión
                        user_id = st.session_state.get('user_id')
                        if user_id:
                            new_id = funcion_creacion(nombre=nombre_nuevo.strip(), user_id=user_id)
                            if new_id:
                                st.session_state[f'{key}_modal_open'] = False
                                st.session_state[f'{key}_selector'] = nombre_nuevo.strip()
                                # Limpiar el caché de clientes para forzar la recarga
                                if key == 'cliente' and 'cliente_data' in st.session_state:
                                    del st.session_state['cliente_data']
                                st.rerun()
                            else:
                                st.error(f"Error al crear {label}. Revise la base de datos.")
                        else:
                            st.error("No se pudo obtener el ID de usuario para crear el registro.")
                    else:
                        st.error(f"El nombre de {label} no puede estar vacío.")
            with col_cancel:
                if st.form_submit_button("❌ Cancelar"):
                    st.session_state[f'{key}_modal_open'] = False
                    st.rerun()

    return entidad_id

def show_cliente_lugar_selector() -> Tuple[int, str, int, str]:
    if 'user_id' not in st.session_state:
        st.error("❌ No has iniciado sesión")
        st.stop()

    try:
        # Si no hay data cacheada de clientes, se carga. (Útil para manejar reruns)
        if "cliente_data" not in st.session_state:
             st.session_state["cliente_data"] = get_clientes()
        clientes = st.session_state["cliente_data"]
        
        lugares = get_lugares_trabajo()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        st.stop()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Cliente")
        cliente_id = _selector_entidad(
            datos=clientes,
            label="cliente",
            key="cliente",
            btn_nuevo="➕ Nuevo cliente",
            modal_title="Nuevo Cliente",
            placeholder_nombre="Nombre de cliente",
            funcion_creacion=create_cliente,
            label_visibility="collapsed" 
        )
        
    with col2:
        st.markdown("#### Lugar de Trabajo")
        lugar_id = _selector_entidad(
            datos=lugares,
            label="lugar",
            key="lugar",
            btn_nuevo="➕ Nuevo lugar",
            modal_title="Nuevo Lugar de Trabajo",
            placeholder_nombre="Nombre del lugar (Ej: Patio, Terraza, etc.)",
            funcion_creacion=create_lugar_trabajo,
            label_visibility="collapsed" 
        )
        
    with col3:
        st.markdown("#### Descripción")
        descripcion = st.text_area("Trabajo a realizar", 
                                   placeholder="Breve descripción del trabajo a presupuestar", 
                                   key="presupuesto_descripcion",
                                   label_visibility="collapsed",
                                   height=80)
    
    # Obtener nombres de forma segura
    cliente_nombre = next((n for i, n in clientes if i == cliente_id), "(No Seleccionado)")
    lugar_nombre = next((n for i, n in lugares if i == lugar_id), "(No Seleccionado)")
    
    # ⚠️ Retorna los IDs y los nombres
    return cliente_id, cliente_nombre, lugar_id, lugar_nombre, descripcion


# ==================== SECCIÓN ITEMS Y CATEGORÍAS ====================

def selector_categoria(key_suffix: str) -> Optional[int]:
    """Muestra un selector de categorías con opción de crear nueva."""
    try:
        # Se obtiene la lista de categorías (id, nombre)
        categorias_raw = get_categorias()
    except Exception as e:
        st.error(f"Error cargando categorías: {e}")
        return None
    
    # Formatear la lista para el selector
    opciones_display = ["(Seleccione)"] + [nombre for _, nombre in categorias_raw]
    opciones_ids = [None] + [id for id, _ in categorias_raw]
    
    col_sel, col_btn = st.columns([3, 1])

    with col_sel:
        cat_nombre_seleccionada = st.selectbox(
            "Categoría",
            options=opciones_display,
            key=f"cat_selector_{key_suffix}",
            label_visibility="collapsed"
        )
        
    # Obtener el ID seleccionado
    cat_id_seleccionada = None
    if cat_nombre_seleccionada and cat_nombre_seleccionada != "(Seleccione)":
        cat_id_seleccionada = next((id for id, nombre in categorias_raw if nombre == cat_nombre_seleccionada), None)
            
    with col_btn:
        if st.button("➕", key=f"new_cat_btn_{key_suffix}", help="Nueva Categoría", use_container_width=True):
            st.session_state[f'cat_modal_open_{key_suffix}'] = True
            
    # Modal de creación de categoría
    if st.session_state.get(f'cat_modal_open_{key_suffix}', False):
        st.subheader("Nueva Categoría", divider='blue')
        with st.form(key=f"form_new_cat_{key_suffix}", border=True):
            nombre_nuevo = st.text_input("Nombre de la categoría", key=f"new_cat_name_{key_suffix}")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.form_submit_button("💾 Crear", type="primary"):
                    if nombre_nuevo.strip():
                        user_id = st.session_state.get('user_id')
                        if user_id:
                            new_id = create_categoria(nombre=nombre_nuevo.strip(), user_id=user_id)
                            if new_id:
                                st.session_state[f'cat_modal_open_{key_suffix}'] = False
                                # Seleccionar la nueva categoría
                                st.session_state[f"cat_selector_{key_suffix}"] = nombre_nuevo.strip() 
                                st.rerun()
                            else:
                                st.error("Error al crear categoría. Revise la base de datos.")
                        else:
                             st.error("No se pudo obtener el ID de usuario.")
                    else:
                        st.error("El nombre no puede estar vacío.")
            with col_cancel:
                if st.form_submit_button("❌ Cancelar"):
                    st.session_state[f'cat_modal_open_{key_suffix}'] = False
                    st.rerun()
                    
    return cat_id_seleccionada

def _render_item_input(cat_nombre: str, item_index: int):
    """Renderiza los inputs para un único ítem dentro de la sesión."""
    # Acceso seguro al ítem
    current_item = st.session_state['categorias'][cat_nombre]['items'][item_index]
    
    col_name, col_unit, col_qty, col_price, col_del = st.columns([3, 1.5, 1.5, 2, 0.7])
    
    with col_name:
        current_item['nombre'] = st.text_input("Descripción", 
                                               value=current_item.get('nombre', ''), 
                                               key=f"item_{cat_nombre}_{item_index}_name",
                                               label_visibility="collapsed")
        # Campo de notas debajo del nombre
        current_item['notas'] = st.text_input("Notas", 
                                              value=current_item.get('notas', ''),
                                              key=f"item_{cat_nombre}_{item_index}_notes",
                                              placeholder="Notas del ítem",
                                              label_visibility="collapsed")

    with col_unit:
        current_item['unidad'] = st.text_input("Unidad", 
                                               value=current_item.get('unidad', 'Unidad'), 
                                               key=f"item_{cat_nombre}_{item_index}_unit",
                                               label_visibility="collapsed")
    with col_qty:
        # Usamos safe_numeric_value en el valor inicial
        current_item['cantidad'] = st.number_input("Cantidad", 
                                                   value=safe_numeric_value(current_item.get('cantidad', 1.0)), 
                                                   min_value=0.0, 
                                                   step=0.1, 
                                                   key=f"item_{cat_nombre}_{item_index}_qty",
                                                   label_visibility="collapsed")
    with col_price:
        # Usamos safe_numeric_value en el valor inicial
        current_item['precio_unitario'] = st.number_input("P. Unitario", 
                                                          value=safe_numeric_value(current_item.get('precio_unitario', 0.0)), 
                                                          min_value=0.0, 
                                                          step=1.0, 
                                                          key=f"item_{cat_nombre}_{item_index}_price",
                                                          label_visibility="collapsed")
                                                          
    with col_del:
        st.write("") # Espacio para alinear el botón
        if st.button("🗑️", key=f"item_{cat_nombre}_{item_index}_del", help="Eliminar ítem"):
            # Marcamos el ítem para eliminación y forzamos un rerun
            st.session_state['categorias'][cat_nombre]['items'].pop(item_index)
            st.rerun()

    # Recalcular el total del ítem con valores seguros
    qty = safe_numeric_value(current_item.get('cantidad'))
    price = safe_numeric_value(current_item.get('precio_unitario'))
    current_item['total'] = qty * price
    
    # Mostrar el subtotal del ítem
    st.markdown(f"<p style='text-align: right; margin-top: -10px; margin-bottom: 5px;'>Subtotal: <b>${current_item['total']:,.2f}</b></p>", unsafe_allow_html=True)
    st.markdown("---")


def show_items_presupuesto():
    """Muestra la interfaz para agregar/editar ítems agrupados por categoría."""
    if 'categorias' not in st.session_state:
        # Estructura inicial: 'general' se usa para mano de obra general
        st.session_state['categorias'] = {'general': {'items': [], 'mano_obra': 0}}

    st.subheader("Ítems por Categoría", divider="blue")
    
    # Sección de selección de categoría para nuevo ítem
    with st.container(border=True):
        st.markdown("##### Agregar nuevo ítem")
        
        # Obtener lista de categorías para el selector
        try:
            categorias_raw = get_categorias()
        except Exception as e:
            st.error(f"Error cargando categorías: {e}")
            categorias_raw = []
            
        # Transformar a diccionario para mapeo ID -> Nombre
        cat_map = {id: nombre for id, nombre in categorias_raw}

        # 1. Selector de categoría (incluyendo las ya existentes en sesión)
        todas_las_cats = list(set(list(cat_map.values()) + list(st.session_state['categorias'].keys())))
        if 'general' in todas_las_cats:
            todas_las_cats.remove('general')
            
        col_sel_cat, col_btn_new_cat = st.columns([3, 1])
        with col_sel_cat:
            nueva_cat_nombre = st.selectbox(
                "Seleccionar Categoría para nuevo ítem",
                options=["(Seleccione)"] + sorted(todas_las_cats),
                key="new_item_cat_selector",
                label_visibility="collapsed"
            )
            
        with col_btn_new_cat:
            if st.button("➕ Cat", key="new_cat_btn_top", help="Crear nueva Categoría", use_container_width=True):
                st.session_state['cat_modal_open_top'] = True
                
        # Simulación de Modal para nueva categoría (usando un expander simple)
        if st.session_state.get('cat_modal_open_top', False):
            with st.expander("Crear Nueva Categoría", expanded=True):
                with st.form(key="form_new_cat_top", border=True):
                    nombre_nuevo = st.text_input("Nombre de la categoría", key="new_cat_name_top")
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("💾 Crear", type="primary"):
                            if nombre_nuevo.strip():
                                user_id = st.session_state.get('user_id')
                                if user_id:
                                    new_id = create_categoria(nombre=nombre_nuevo.strip(), user_id=user_id)
                                    if new_id:
                                        # Agregar la nueva categoría a las opciones y seleccionarla
                                        st.session_state['new_item_cat_selector'] = nombre_nuevo.strip()
                                        st.session_state['cat_modal_open_top'] = False
                                        st.rerun()
                                    else:
                                        st.error("Error al crear categoría.")
                                else:
                                     st.error("No se pudo obtener el ID de usuario.")
                            else:
                                st.error("El nombre no puede estar vacío.")
                    with col_cancel:
                        if st.form_submit_button("❌ Cancelar"):
                            st.session_state['cat_modal_open_top'] = False
                            st.rerun()


        # 2. Botón para agregar ítem
        if nueva_cat_nombre != "(Seleccione)":
            if st.button("➕ Agregar ítem a la categoría", key="add_item_btn", use_container_width=True, type="secondary"):
                cat_nombre = nueva_cat_nombre
                
                if cat_nombre not in st.session_state['categorias']:
                    st.session_state['categorias'][cat_nombre] = {'items': [], 'mano_obra': 0}
                    
                # Agregar nuevo ítem con valores iniciales
                st.session_state['categorias'][cat_nombre]['items'].append({
                    'nombre': '', 
                    'unidad': 'Unidad', 
                    'cantidad': 1.0, 
                    'precio_unitario': 0.0, 
                    'total': 0.0,
                    'categoria': cat_nombre,
                    'notas': ''
                })
                # Forzar rerun para que el nuevo ítem aparezca inmediatamente
                st.rerun()


    st.markdown("---")
    
    # Renderizar ítems por categoría
    categorias_a_mostrar = [cat for cat in st.session_state['categorias'] if cat != 'general']
    
    if not categorias_a_mostrar:
        st.info("Aún no has agregado ítems a ninguna categoría.")
        return

    for cat_nombre in categorias_a_mostrar:
        items_cat = st.session_state['categorias'][cat_nombre]['items']
        
        # Encabezado de la categoría
        st.subheader(f"🛠️ {cat_nombre}", divider='gray')
        
        # Encabezados de columna
        col_name, col_unit, col_qty, col_price, col_del = st.columns([3, 1.5, 1.5, 2, 0.7])
        col_name.write("**Descripción/Notas**")
        col_unit.write("**Unidad**")
        col_qty.write("**Cant.**")
        col_price.write("**P. Unitario**")
        col_del.write("")


        if items_cat:
            for i in range(len(items_cat)):
                # El renderizado gestiona la eliminación, por eso usamos el índice original
                _render_item_input(cat_nombre, i)
        else:
            st.info(f"No hay ítems para la categoría **{cat_nombre}**.")
            st.button(f"🗑️ Eliminar categoría {cat_nombre}", key=f"del_cat_{cat_nombre}", help="Eliminar categoría vacía", 
                      on_click=lambda c=cat_nombre: st.session_state['categorias'].pop(c) or st.rerun())

def show_mano_obra():
    """Muestra el input para mano de obra general y por categoría."""
    st.subheader("Mano de Obra", divider="blue")
    
    # Aseguramos la existencia de la clave
    if 'categorias' not in st.session_state:
        st.session_state['categorias'] = {'general': {'items': [], 'mano_obra': 0}}
        
    if 'general' not in st.session_state['categorias']:
        st.session_state['categorias']['general'] = {'items': [], 'mano_obra': 0}
        
    # 1. Mano de Obra General
    st.session_state['categorias']['general']['mano_obra'] = st.number_input(
        "Mano de Obra General (valor único para el trabajo completo)",
        value=safe_numeric_value(st.session_state['categorias']['general'].get('mano_obra', 0)),
        min_value=0.0,
        step=1000.0,
        key="mo_general"
    )

    st.markdown("---")
    
    # 2. Mano de Obra por Categoría (para categorías con ítems)
    st.markdown("##### Mano de Obra por Categoría (Adicional)")
    
    categorias_a_mostrar = [cat for cat in st.session_state['categorias'] if cat != 'general']
    
    if not categorias_a_mostrar:
        st.info("Agrega ítems primero para asignar mano de obra por categoría.")
        return
        
    for cat_nombre in categorias_a_mostrar:
        # Aseguramos la inicialización de 'mano_obra'
        if 'mano_obra' not in st.session_state['categorias'][cat_nombre]:
             st.session_state['categorias'][cat_nombre]['mano_obra'] = 0.0
             
        st.session_state['categorias'][cat_nombre]['mano_obra'] = st.number_input(
            f"Mano de Obra para: {cat_nombre}",
            value=safe_numeric_value(st.session_state['categorias'][cat_nombre].get('mano_obra', 0)),
            min_value=0.0,
            step=100.0,
            key=f"mo_cat_{cat_nombre}"
        )


def show_resumen():
    """Muestra el resumen final del presupuesto."""
    st.subheader("Resumen del Presupuesto", divider="green")
    
    if 'categorias' not in st.session_state or not st.session_state['categorias']:
        st.info("Comience agregando ítems y mano de obra para ver el resumen.")
        return

    # Usar una lista para el resumen de categorías
    resumen_data = []
    total_general = 0.0

    # 1. Mano de Obra General
    mano_obra_general = safe_numeric_value(st.session_state['categorias']['general'].get('mano_obra', 0.0))
    total_general += mano_obra_general
    
    if mano_obra_general > 0:
         resumen_data.append({
             'Categoría': 'Mano de Obra General',
             'Total Ítems': 0.0,
             'Mano de Obra': mano_obra_general,
             'Total Categoría': mano_obra_general
         })

    # 2. Ítems por Categoría
    for cat, data in st.session_state['categorias'].items():
        if cat == 'general': 
            continue
            
        items_total = sum(safe_numeric_value(item.get('total')) for item in data['items'])
        mano_obra = safe_numeric_value(data.get('mano_obra', 0.0))
        total_categoria = items_total + mano_obra
        total_general += total_categoria

        if total_categoria > 0:
            resumen_data.append({
                'Categoría': cat,
                'Total Ítems': items_total,
                'Mano de Obra': mano_obra,
                'Total Categoría': total_categoria
            })
            
    if not resumen_data:
        st.info("El presupuesto está vacío.")
        return

    # Mostrar resumen en DataFrame
    df_resumen = pd.DataFrame(resumen_data)
    
    st.dataframe(
        df_resumen,
        column_config={
            "Categoría": "Categoría",
            "Total Ítems": st.column_config.NumberColumn("Total Ítems", format="$%d"),
            "Mano de Obra": st.column_config.NumberColumn("Mano de Obra", format="$%d"),
            "Total Categoría": st.column_config.NumberColumn("Total", format="$%d")
        },
        hide_index=True,
        width="stretch"
    )
    
    st.markdown(f"#### 💰 **TOTAL GENERAL DEL PRESUPUESTO:** **${total_general:,.2f}**")
    
    return total_general