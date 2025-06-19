import streamlit as st
import psycopg2
import pandas as pd
from typing import Any, Dict, List, Tuple, Optional
from utils.database import (
    create_categoria, 
    get_categorias, 
    get_clientes, 
    create_cliente, 
    get_lugares_trabajo, 
    create_lugar_trabajo,
    contar_items_presupuesto
)

# ==================== SECCION CLIENTE - LUGAR DE TRABAJO ====================
def show_cliente_lugar_selector() -> Tuple[int, str, int, str]:
    if 'user_id' not in st.session_state:
        st.error("❌ No has iniciado sesión")
        st.stop()

    try:
        clientes = get_clientes()
        lugares = get_lugares_trabajo()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Cliente")
        cliente_id = _selector_entidad(
            datos=clientes,
            label="Seleccionar cliente",
            key="cliente",
            btn_nuevo="➕ Nuevo cliente",
            modal_title="Nuevo Cliente",
            placeholder_nombre="Nombre de cliente",
            funcion_creacion=create_cliente
        )
        cliente_nombre = next((n for i, n in clientes if i == cliente_id), "Desconocido")

    with col2:
        st.markdown("#### Lugar de Trabajo")
        lugar_id = _selector_entidad(
            datos=lugares,
            label="Seleccionar lugar",
            key="lugar",
            btn_nuevo="➕ Nuevo lugar",
            modal_title="Nuevo Lugar",
            placeholder_nombre="Nombre del lugar",
            funcion_creacion=create_lugar_trabajo
        )
        lugar_nombre = next((n for i, n in lugares if i == lugar_id), "Desconocido")

    return cliente_id, cliente_nombre, lugar_id, lugar_nombre

def _selector_entidad(
    datos: List[Tuple[int, str]],
    label: str,
    key: str,
    btn_nuevo: str,
    modal_title: str,
    placeholder_nombre: str,
    funcion_creacion: callable
) -> Optional[int]:
    """Componente para seleccionar/crear entidades"""
    nombres_por_id = {d[0]: d[1] for d in datos}
    options = [None] + [d[0] for d in datos] if datos else [None]

    seleccionado = st.selectbox(
        label,
        options=options,
        format_func=lambda id: "--- Seleccione ---" if id is None else nombres_por_id.get(id, "Desconocido"),
        key=f"select_{key}"
    )

    popover = st.popover(btn_nuevo, use_container_width=True)
    with popover:
        nombre = st.text_input(placeholder_nombre, key=f"input_nuevo_{key}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Guardar", key=f"btn_guardar_{key}", type="primary"):
                if not nombre.strip():
                    st.warning("Nombre requerido")
                elif any(n.lower() == nombre.lower() for _, n in datos):
                    st.error(f"Ya existe un {key} con ese nombre")
                else:
                    try:
                        nuevo_id = funcion_creacion(nombre.strip(), st.session_state.user_id)
                        st.session_state[f"{key}_actual"] = nuevo_id
                    except Exception as e:
                        st.error(f"Error al crear: {e}")
        
        with col2:
            if st.button("✖️ Cancelar", key=f"btn_cancelar_{key}"):
                st.rerun()

    return st.session_state.get(f"{key}_actual", seleccionado)

# ========== SECCIÓN CATEGORIA - ITEMS ==========
def selector_categoria(
    mostrar_label: bool = True, 
    requerido: bool = True, 
    key_suffix: str = ""
) -> Tuple[Optional[int], Optional[str]]:
    """
    Selector de categorías con capacidad para crear nuevas
    """
    if 'user_id' not in st.session_state:
        st.error("❌ No autenticado")
        st.stop()

    try:
        categorias = get_categorias()
        nombres_por_id = {d[0]: d[1] for d in categorias}
        
        select_key = f"select_categoria_{key_suffix}"
        btn_key = f"btn_nueva_categoria_{key_suffix}"
        input_key = f"input_nueva_categoria_{key_suffix}"
        

        if mostrar_label:
            st.markdown("#### Categoría")
        
        if categorias:
            opciones = [(cat[0], cat[1]) for cat in categorias]
            
            categoria_id = st.selectbox(
                "Seleccionar categoría",
                options=[op[0] for op in opciones],
                format_func=lambda id: nombres_por_id.get(id, "Desconocido"),
                key=select_key,
                label_visibility="collapsed" if not mostrar_label else "visible"
            )
            categoria_nombre = nombres_por_id.get(categoria_id, "")
        else:
            categoria_id = None
            st.info("No hay categorías registradas")
        btn_nuevo = st.button("➕ Agregar Categoria", key=btn_key, use_container_width=True)

        if btn_nuevo:
            with st.form(key=f"form_nueva_categoria_{key_suffix}", border=True):
                nuevo_nombre = st.text_input("Nombre de la nueva categoría:", key=input_key)
                
                cols = st.columns(2)
                with cols[0]:
                    if st.form_submit_button("💾 Guardar", type="primary"):
                        if not nuevo_nombre.strip():
                            st.error("Nombre requerido")
                        elif any(n.lower() == nuevo_nombre.lower() for _, n in categorias):
                            st.error("¡Esta categoría ya existe!")
                        else:
                            try:
                                nuevo_id = create_categoria(nuevo_nombre.strip(), st.session_state.user_id)
                                st.session_state[f"categoria_actual_{key_suffix}"] = nuevo_id
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al crear categoría: {e}")
                
                with cols[1]:
                    if st.form_submit_button("✖️ Cancelar"):
                        pass

        categoria_id = st.session_state.get(f"categoria_actual_{key_suffix}", categoria_id)
        categoria_nombre = nombres_por_id.get(categoria_id, 
                                           nuevo_nombre if btn_nuevo and not categoria_id else "")
        
        if requerido and not categoria_id:
            st.warning("Por favor selecciona o crea una categoría")
            st.stop()
            
        return categoria_id, categoria_nombre
            
    except Exception as e:
        st.error(f"Error al cargar categorías: {e}")
        if requerido:
            st.stop()
        return None, None

def show_items_presupuesto() -> Dict[str, Any]:
    if 'categorias' not in st.session_state:
        st.session_state['categorias'] = {}

    # ========== SECCIÓN CATEGORIA E ITEMS ==========    
    with st.container(border=True):
        col1, col2 = st.columns([2, 4])
        with col1:
            st.markdown("#### 1️⃣ Seleccionar/Crear Categoría")
            categoria_id, categoria_nombre = selector_categoria(
                mostrar_label=False,
                requerido=True,
                key_suffix="principal"
            )

        with col2:
            st.markdown(f"#### 2️⃣ Agregar Ítems a: {categoria_nombre}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                nombre_item = st.text_input("Nombre del Ítem:", key="nombre_item_principal")
            with col2:
                cantidad = st.number_input("Cantidad:", min_value=1, step=1, value=1, key="cantidad_principal")
            with col3:
                precio_unitario = st.number_input("Precio Unitario ($):", min_value=0, value=0, step=1, key="precio_principal")

            col1, col2, col3 = st.columns(3)
            with col1:
                unidad = st.selectbox("Unidad:", ["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro"], key="unidad_principal")
            with col2:
                total = cantidad * precio_unitario
                st.text_input("Total", value=f"${total:,}", disabled=True)
            with col3:
                st.write("")
                st.write("")
                if st.button("➕ Guardar Ítem", type="primary"):
                    if not nombre_item:
                        st.error("Nombre del ítem es requerido")
                    else:
                        if categoria_nombre not in st.session_state['categorias']:
                            st.session_state['categorias'][categoria_nombre] = {'items': [], 'mano_obra': 0}

                        items_cat = st.session_state['categorias'][categoria_nombre]['items']
                        item_existente = next((i for i in items_cat if i['nombre'] == nombre_item and i['unidad'] == unidad), None)

                        if item_existente:
                            item_existente['cantidad'] += cantidad
                            item_existente['total'] = item_existente['cantidad'] * item_existente['precio_unitario']
                            st.success("¡Cantidad actualizada!")
                        else:
                            items_cat.append({
                                'nombre': nombre_item,
                                'unidad': unidad,
                                'cantidad': cantidad,
                                'precio_unitario': precio_unitario,
                                'total': total
                            })
                            st.success(f"Ítem agregado a '{categoria_nombre}'")
    
    # ========== SECCIÓN DE EDICIÓN ==========
    with st.expander("📝 Editar Items", expanded=False):
        for cat, datos in st.session_state['categorias'].items():
            items = datos['items']
            if not items: 
                continue
                
            st.write(f"### {cat}") 

            col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 2, 2, 2, 2, 0.8, 0.8])
            col1.write("**Nombre**")
            col2.write("**Unidad**")
            col3.write("**Cantidad**")
            col4.write("**Precio Unitario**")
            col5.write("**Total**")
            col6.write("**Guardar**")
            col7.write("**Eliminar**")

            for index, item in enumerate(items):
                col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 2, 2, 2, 2, 0.8, 0.8])

                with col1:
                    nuevo_nombre = st.text_input("Nombre", item['nombre'], 
                                              key=f"nombre_{cat}_{index}", label_visibility="collapsed")
                with col2:
                    nueva_unidad = st.selectbox("Unidad", ["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro"],
                                              index=["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro"].index(item['unidad']),
                                              key=f"unidad_{cat}_{index}", label_visibility="collapsed")
                with col3:
                    nueva_cantidad = st.number_input("Cantidad", min_value=1, step=1, value=item['cantidad'],
                                                    key=f"cantidad_{cat}_{index}", label_visibility="collapsed")
                with col4:
                    nuevo_precio = st.number_input("Precio", min_value=0, value=item['precio_unitario'],
                                                key=f"precio_{cat}_{index}", label_visibility="collapsed")
                with col5:
                    nuevo_total = nueva_cantidad * nuevo_precio
                    st.text_input("Total", value=f"${nuevo_total:,}", disabled=True, 
                                key=f"total_{cat}_{index}", label_visibility="collapsed")

                with col6:
                    if st.button("💾", key=f"guardar_{cat}_{index}"):
                        st.session_state['categorias'][cat]['items'][index] = {
                            'nombre': nuevo_nombre,
                            'unidad': nueva_unidad,
                            'cantidad': nueva_cantidad,
                            'precio_unitario': nuevo_precio,
                            'total': nuevo_total
                        }
                        st.success("¡Cambios guardados!")
                        st.rerun()

                with col7:
                    if st.button("❌", key=f"eliminar_{cat}_{index}"):
                        del st.session_state['categorias'][cat]['items'][index]
                        st.success("¡Ítem eliminado!")
                        st.rerun()
    
    return st.session_state['categorias']
    
# ========== SECCIÓN MANO DE OBRA ==========
def show_mano_obra(items_data: Dict[str, Any]) -> None:
    with st.expander("Agregar Mano de Obra", expanded=False):
        st.markdown("### Configurar Mano de Obra")
        
        categorias_con_items = [cat for cat in items_data.keys() if items_data[cat]['items']]
        
        if not categorias_con_items:
            st.warning("Primero agrega items a una categoría")
        else:
            categoria_seleccionada = st.selectbox(
                "Seleccionar categoría:",
                options=categorias_con_items,
                key="select_cat_mano_obra"
            )
            
            costo_mano_obra = st.number_input(
                "Costo de mano de obra ($):",
                min_value=0,
                value=items_data[categoria_seleccionada].get('mano_obra', 0),
                step=1,
                key="input_costo_mano_obra"
            )
            
            if st.button("💾 Aplicar Mano de Obra", key="btn_aplicar_mano_obra"):
                items_data[categoria_seleccionada]['mano_obra'] = costo_mano_obra
                st.success(f"Mano de obra aplicada a {categoria_seleccionada}")


    # ========== SECCIÓN RESUMEN ==========

def show_resumen(items_data: Dict[str, Any]) -> None:
    if not st.session_state['categorias']:
        st.info("No hay items agregados aún")
        return {}

    total_general = 0

    if 'general' in st.session_state['categorias'] and st.session_state['categorias']['general'].get('mano_obra', 0) > 0:
        mano_obra_general = st.session_state['categorias']['general']['mano_obra']
        total_general += mano_obra_general
        
        with st.container(border=True):
            st.subheader(f"**Mano de obra general:** ${mano_obra_general:,}")

    for cat, data in st.session_state['categorias'].items():
        if cat == 'general': 
            continue
            
        items = data['items']
        mano_obra = data.get('mano_obra', 0)
        
        if items or mano_obra > 0:
            total_categoria = sum(item['total'] for item in items) + mano_obra
            total_general += total_categoria

            with st.container(border=True):
                st.markdown(f"**🔹 {cat}**")
                
                if items:
                    df_items = pd.DataFrame(items)
                    st.dataframe(
                        df_items,
                        column_config={
                            "nombre": "Descripción",
                            "unidad": "Unidad",
                            "cantidad": "Cantidad",
                            "precio_unitario": st.column_config.NumberColumn("P. Unitario", format="$%d"),
                            "total": st.column_config.NumberColumn("Total", format="$%d")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                
                if mano_obra > 0:
                    st.markdown(f"**Mano de obra {cat}:** ${mano_obra:,}")
                    st.markdown(f"**Total {cat}:** ${total_categoria:,}")
                
    st.markdown(f"#### 💵 Total General: ${total_general:,}")