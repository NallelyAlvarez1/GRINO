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

# ==================== SECCION CLIENTE - LUGAR DE TRABAJO ====================
def show_cliente_lugar_selector() -> Tuple[int, str, int, str]:
    if 'user_id' not in st.session_state:
        st.error("❌ No has iniciado sesión")
        st.stop()

    try:
        clientes = st.session_state.get("cliente_data", get_clientes())
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
        cliente_nombre = next((n for i, n in clientes if i == cliente_id), "Desconocido")

    with col2:
        st.markdown("#### Lugar de Trabajo")
        lugar_id = _selector_entidad(
            datos=lugares,
            label="lugares",
            key="lugar",
            btn_nuevo="➕ Nuevo lugar",
            modal_title="Nuevo Lugar",
            placeholder_nombre="Nombre del lugar",
            funcion_creacion=create_lugar_trabajo,
            label_visibility="collapsed" 
        )
        lugar_nombre = next((n for i, n in lugares if i == lugar_id), "Desconocido")
    
    with col3:
        st.markdown("#### Trabajo a realizar")
        st.session_state.descripcion = st.text_input(
            "Descripción del trabajo",
            placeholder="Ejemplo: Instalación de sistema de riego en jardín delantero...",
            key="descripcion_input",
            value=st.session_state.get("descripcion", ""),
            label_visibility="collapsed"
        )

    return cliente_id, cliente_nombre, lugar_id, lugar_nombre,  st.session_state.descripcion

def _selector_entidad(
    datos: Union[List[Tuple], List[Dict]],
    label: str,
    key: str,
    btn_nuevo: str,
    modal_title: str,
    placeholder_nombre: str,
    funcion_creacion: callable,
    label_visibility: str = "visible"  # ✅ PARÁMETRO NUEVO
) -> Optional[int]:
    """Componente seleccionar/crear entidades"""
    
    # Inicializar estado
    if f"{key}_data" not in st.session_state:
        st.session_state[f"{key}_data"] = datos
    
    # Usar datos actualizados
    current_data = st.session_state[f"{key}_data"]
    
    # Convertir datos a formato consistente
    if current_data and isinstance(current_data[0], dict):
        nombres_por_id = {d['id']: d['nombre'] for d in current_data}
        options = [None] + [d['id'] for d in current_data]
    else:
        nombres_por_id = {d[0]: d[1] for d in current_data}
        options = [None] + [d[0] for d in current_data]
    
    # Selector principal
    seleccionado = st.selectbox(
        label,
        options=options,
        format_func=lambda id: "--- Seleccione ---" if id is None else nombres_por_id.get(id, "Desconocido"),
        key=f"select_{key}",
        label_visibility="collapsed"  # ✅ USAR PARÁMETRO
    )
    
    # Popover para crear nuevo
    popover = st.popover(btn_nuevo, width="stretch")
    with popover:
        nombre = st.text_input(placeholder_nombre, key=f"input_nuevo_{key}")
        
        if st.button("💾 Guardar", key=f"btn_guardar_{key}", type="primary"):
            if not nombre.strip():
                st.warning("Nombre requerido")
            elif any(n.lower() == nombre.lower() for n in nombres_por_id.values()):
                st.error(f"Ya existe un {key} con ese nombre")
            else:
                try:
                    # Crear nuevo elemento en la base de datos
                    nuevo_id = funcion_creacion(nombre.strip(), st.session_state.user_id)
                    
                    # Actualizar los datos en session_state
                    if current_data and isinstance(current_data[0], dict):
                        nuevo_item = {'id': nuevo_id, 'nombre': nombre.strip()}
                        st.session_state[f"{key}_data"] = current_data + [nuevo_item]
                    else:
                        nuevo_item = (nuevo_id, nombre.strip())
                        st.session_state[f"{key}_data"] = current_data + [nuevo_item]
                    
                    # Forzar rerun
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error al crear: {e}")

    return seleccionado

# ========== SECCIÓN CATEGORIA - ITEMS ==========
def selector_categoria(mostrar_label: bool = True, requerido: bool = True, key_suffix: str = "") -> Tuple[Optional[int], Optional[str]]:
    """Selector de categorías con capacidad para crear nuevas (usando _selector_entidad)"""
    if 'user_id' not in st.session_state:
        st.error("❌ No autenticado")
        st.stop()

    try:
        categorias = st.session_state.get(f"categorias_data_{key_suffix}", get_categorias())
    except Exception as e:
        st.error(f"Error cargando categorías: {e}")
        if requerido:
            st.stop()
        return None, None

    if mostrar_label:
        st.markdown("#### Categoría")

    categoria_id = _selector_entidad(
        datos=categorias,
        label="Seleccionar categoría",
        key=f"categoria_{key_suffix}",
        btn_nuevo="➕ Nueva categoría",
        modal_title="Nueva Categoría",
        placeholder_nombre="Nombre de la categoría",
        funcion_creacion=create_categoria
    )

    categoria_nombre = next((n for i, n in categorias if i == categoria_id), "Desconocido")

    if requerido and not categoria_id:
        st.warning("Por favor selecciona o crea una categoría")
        st.stop()

    return categoria_id, categoria_nombre

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
                unidad = st.selectbox("Unidad:", ["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro", "Caja", "Kilo (kg)", "Galón (gal)", "Litro", "Par/Juego", "Plancha"], key="unidad_principal")
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
                            st.badge("¡Cambios guardados!", icon=":material/check:", color="green")
                        else:
                            items_cat.append({
                                'nombre': nombre_item,
                                'unidad': unidad,
                                'cantidad': cantidad,
                                'precio_unitario': precio_unitario,
                                'total': total
                            })
                            st.badge(f"Ítem agregado a '{categoria_nombre}'", icon=":material/check:", color="green")
    
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
                    nueva_unidad = st.selectbox("Unidad", ["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro", "Caja", "Kilo (kg)", "Galón (gal)", "Litro", "Par/Juego", "Plancha"],
                                              index=["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro", "Caja", "Kilo (kg)", "Galón (gal)", "Litro", "Par/Juego", "Plancha"].index(item['unidad']),
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
                        st.badge("¡Cambios guardados!", icon=":material/check:", color="green")
                        st.rerun()

                with col7:
                    if st.button("❌", key=f"eliminar_{cat}_{index}"):
                        del st.session_state['categorias'][cat]['items'][index]
                        st.badge("¡Ítem eliminado!", icon=":material/check:", color="green")
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
        
        st.subheader(f"**Mano de obra general:** ${mano_obra_general:,}")

    for cat, data in st.session_state['categorias'].items():
        if cat == 'general': 
            continue
            
        items = data['items']
        mano_obra = data.get('mano_obra', 0)
        
        if items or mano_obra > 0:
            total_categoria = sum(item['total'] for item in items) + mano_obra
            total_general += total_categoria

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
                    width="stretch"
                )
            
            if mano_obra > 0:
                st.markdown(f"**Mano de obra {cat}:** ${mano_obra:,}")
            
            st.markdown(f"**Total {cat}:** ${total_categoria:,}")
                
    st.markdown(f"#### 💵 Total General: ${total_general:,}")