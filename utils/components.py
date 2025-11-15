import streamlit as st
import pandas as pd
from typing import Any, Dict, List, Tuple, Optional
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
    """Convierte un valor a float de forma segura"""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def clean_integer_input(value: str) -> int:
    """Limpia el input para que solo contenga números enteros"""
    if value is None:
        return 0
    cleaned = ''.join(filter(str.isdigit, str(value)))
    return int(cleaned) if cleaned else 0

# ==================== SECCIÓN CLIENTE - LUGAR DE TRABAJO ====================
def show_cliente_lugar_selector() -> Tuple[Optional[int], str, Optional[int], str, str]:
    """Selector simplificado de cliente y lugar de trabajo"""
    if 'user_id' not in st.session_state:
        st.error("❌ No has iniciado sesión")
        st.stop()

    user_id = st.session_state.user_id

    try:
        clientes = get_clientes(user_id)
        lugares = get_lugares_trabajo(user_id)
    except Exception as e:
        st.error(f"❌ Error cargando datos: {e}")
        st.stop()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 👤 Cliente")
        cliente_id = _selector_entidad(
            datos=clientes,
            label="cliente",
            key="cliente",
            btn_nuevo="➕ Nuevo cliente",
            modal_title="Nuevo Cliente",
            placeholder_nombre="Nombre de cliente",
            funcion_creacion=create_cliente
        )
        
    with col2:
        st.markdown("#### 📍 Lugar de Trabajo")
        lugar_trabajo_id = _selector_entidad(
            datos=lugares,
            label="lugar",
            key="lugar",
            btn_nuevo="➕ Nuevo lugar",
            modal_title="Nuevo Lugar de Trabajo",
            placeholder_nombre="Nombre del lugar",
            funcion_creacion=create_lugar_trabajo
        )
        
    with col3:
        st.markdown("#### 📝 Descripción")
        descripcion = st.text_area("Trabajo a realizar", 
                                   placeholder="Breve descripción del trabajo a realizar", 
                                   key="presupuesto_descripcion",
                                   label_visibility="collapsed",
                                   height=80)

    cliente_nombre = next((n for i, n in clientes if i == cliente_id), "(No Seleccionado)")
    lugar_nombre = next((n for i, n in lugares if i == lugar_trabajo_id), "(No Seleccionado)")
    
    return cliente_id, cliente_nombre, lugar_trabajo_id, lugar_nombre, descripcion

def _selector_entidad(datos: List[Tuple[int, str]], label: str, key: str, btn_nuevo: str, modal_title: str, placeholder_nombre: str, funcion_creacion: callable) -> Optional[int]:
    """Componente genérico para seleccionar/crear entidades"""
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.error("❌ No se pudo obtener el ID de usuario")
        return None
    
    opciones_display = ["(Seleccione)"] + [nombre for _, nombre in datos]
    
    entidad_nombre_seleccionada = st.selectbox(
        label=label.capitalize(),
        options=opciones_display,
        key=f"{key}_selector",
        label_visibility="collapsed",
    )
    
    entidad_id = None
    if entidad_nombre_seleccionada and entidad_nombre_seleccionada != "(Seleccione)":
        entidad_id = next((id for id, nombre in datos if nombre == entidad_nombre_seleccionada), None)
            
    if st.button(btn_nuevo, key=f"{key}_new_btn", use_container_width=True):
        st.session_state[f'{key}_modal_open'] = True
    
    if st.session_state.get(f'{key}_modal_open', False):
        with st.form(key=f"form_new_{key}", border=True):
            st.subheader(modal_title)
            nombre_nuevo = st.text_input(placeholder_nombre, key=f"new_{key}_name")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.form_submit_button("💾 Crear", type="primary", use_container_width=True):
                    if nombre_nuevo.strip():
                        new_id = funcion_creacion(nombre=nombre_nuevo.strip(), user_id=user_id)
                        if new_id:
                            st.session_state[f'{key}_modal_open'] = False
                            st.session_state[f'{key}_selector'] = nombre_nuevo.strip()
                            st.rerun()
                        else:
                            st.error(f"❌ Error al crear {label}")
                    else:
                        st.error(f"⚠️ El nombre de {label} no puede estar vacío.")
            with col_cancel:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state[f'{key}_modal_open'] = False
                    st.rerun()

    return entidad_id

# ==================== SECCIÓN ITEMS Y CATEGORÍAS ====================
def selector_categoria(mostrar_label: bool = True, requerido: bool = True, key_suffix: str = "") -> Tuple[Optional[int], Optional[str]]:
    """Selector simplificado de categorías"""
    if 'user_id' not in st.session_state:
        st.error("❌ No autenticado")
        st.stop()

    try:
        categorias = get_categorias(st.session_state.user_id)
    except Exception as e:
        st.error(f"❌ Error cargando categorías: {e}")
        if requerido:
            st.stop()
        return None, None

    if mostrar_label:
        st.markdown("#### 📂 Categoría")

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
        st.warning("⚠️ Por favor selecciona o crea una categoría")
        st.stop()

    return categoria_id, categoria_nombre

def show_items_presupuesto() -> Dict[str, Any]:
    """Función principal para manejar items del presupuesto"""
    if 'categorias' not in st.session_state:
        st.session_state['categorias'] = {}

    # CONTENEDOR PRINCIPAL
    with st.container(border=True):
        col1, col2 = st.columns([2, 4])
        
        with col1:
            st.markdown("#### 1️⃣ 📂 Categoría")
            categoria_id, categoria_nombre = selector_categoria(
                mostrar_label=False,
                requerido=True,
                key_suffix="principal"
            )
            
                    # 🟢 ACTUALIZACIÓN: Asegurar que la categoría en session_state tenga el ID correcto
            if categoria_id and categoria_nombre:
                # Si la categoría no existe, inicializarla
                if categoria_nombre not in st.session_state['categorias']:
                    st.session_state['categorias'][categoria_nombre] = {
                        'categoria_id': categoria_id,
                        'items': [], 
                        'mano_obra': 0
                    }
                else:
                    # Si ya existe, actualizar el categoria_id por si cambió
                    st.session_state['categorias'][categoria_nombre]['categoria_id'] = categoria_id
            # ----------------------------------------------------

        with col2:
            st.markdown(f"#### 2️⃣ 📦 Agregar Ítems a: **{categoria_nombre}**")
            
            # Primera fila de inputs
            col_nombre, col_cantidad, col_precio = st.columns(3)
            with col_nombre:
                nombre_item = st.text_input("Nombre del Ítem:", key="nombre_item_principal", placeholder="Ej: Plantas, Tierra, etc.")
            with col_cantidad:
                cantidad = st.number_input("Cantidad:", min_value=0, value=1, step=1, key="cantidad_principal")
            with col_precio:
                precio_input = st.text_input("Precio Unitario ($):", value="0", key="precio_principal", placeholder="Solo números")
                precio_unitario = clean_integer_input(precio_input)

            # Segunda fila de inputs
            col_unidad, col_total, col_boton = st.columns(3)
            with col_unidad:
                unidad = st.selectbox(
                    "Unidad:", 
                    ["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro", "Caja", "Kilo (kg)", "Galón (gal)", "Litro", "Par/Juego", "Plancha"], 
                    key="unidad_principal"
                )
            with col_total:
                total = cantidad * precio_unitario
                st.text_input("Total", value=f"${total:,}", disabled=True)
            with col_boton:
                st.write("")  # Espaciado
                st.write("")  # Espaciado
                if st.button("➕ Guardar Ítem", type="primary", use_container_width=True):
                    if not nombre_item.strip():
                        st.error("❌ Nombre del ítem es requerido")
                    else:
                        if categoria_nombre not in st.session_state['categorias']:
                            st.session_state['categorias'][categoria_nombre] = {
                                'categoria_id': categoria_id,  # ← CRÍTICO: Guardar el ID
                                'items': [], 
                                'mano_obra': 0
                            }

                        items_cat = st.session_state['categorias'][categoria_nombre]['items']
                        
                        # Buscar si ya existe el item
                        item_existente = next((i for i in items_cat if i['nombre'] == nombre_item and i['unidad'] == unidad), None)

                        if item_existente:
                            item_existente['cantidad'] += cantidad
                            item_existente['total'] = item_existente['cantidad'] * item_existente['precio_unitario']
                            st.success("✅ ¡Cantidad actualizada!")
                        else:
                            items_cat.append({
                                'nombre': nombre_item,
                                'unidad': unidad,
                                'cantidad': cantidad,
                                'precio_unitario': precio_unitario,
                                'total': total,
                                'categoria': categoria_nombre,
                                'notas': ''
                            })
                            st.success(f"✅ Ítem agregado a '{categoria_nombre}'")
    
    # SECCIÓN EDICIÓN
    with st.expander("📝 Editar Items", expanded=False):
        categorias_a_mostrar = [cat for cat in st.session_state['categorias'] if st.session_state['categorias'][cat]['items']]
        
        if not categorias_a_mostrar:
            st.info("📭 No hay ítems para editar")
            return st.session_state['categorias']
            
        for cat_nombre in categorias_a_mostrar:
            items_cat = st.session_state['categorias'][cat_nombre]['items']
            
            st.write(f"### {cat_nombre}")

            # Encabezados de columna
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2.5, 1.5, 1.2, 1.5, 1.5, 1.8, 0.8, 0.8])
            col1.write("**Descripción**")
            col2.write("**Unidad**")
            col3.write("**Cant.**")
            col4.write("**P. Unitario**")
            col5.write("**Total**")
            col6.write("**Notas**")
            col7.write("**Guardar**")
            col8.write("**Eliminar**")

            for index, item in enumerate(items_cat):
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2.5, 1.5, 1.2, 1.5, 1.5, 1.8, 0.8, 0.8])

                with col1:
                    nuevo_nombre = st.text_input("Nombre", item['nombre'], key=f"nombre_{cat_nombre}_{index}", label_visibility="collapsed")
                with col2:
                    nueva_unidad = st.selectbox("Unidad", ["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro", "Caja", "Kilo (kg)", "Galón (gal)", "Litro", "Par/Juego", "Plancha"],
                                              index=["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro", "Caja", "Kilo (kg)", "Galón (gal)", "Litro", "Par/Juego", "Plancha"].index(item['unidad']) if item['unidad'] in ["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro", "Caja", "Kilo (kg)", "Galón (gal)", "Litro", "Par/Juego", "Plancha"] else 2,
                                              key=f"unidad_{cat_nombre}_{index}", label_visibility="collapsed")
                with col3:
                    nueva_cantidad = st.number_input("Cantidad", min_value=0, step=1, value=item['cantidad'], key=f"cantidad_{cat_nombre}_{index}", label_visibility="collapsed")
                with col4:
                    precio_actual = str(item['precio_unitario'])
                    nuevo_precio_input = st.text_input("Precio", value=precio_actual, key=f"precio_{cat_nombre}_{index}", label_visibility="collapsed")
                    nuevo_precio = clean_integer_input(nuevo_precio_input)
                    
                with col5:
                    nuevo_total = nueva_cantidad * nuevo_precio
                    st.text_input("Total", value=f"${nuevo_total:,}", disabled=True, key=f"total_{cat_nombre}_{index}", label_visibility="collapsed")
                with col6:
                    nuevas_notas = st.text_input("Notas", value=item.get('notas', ''), key=f"notas_{cat_nombre}_{index}", label_visibility="collapsed", placeholder="Notas...")

                with col7:
                    if st.button("💾", key=f"guardar_{cat_nombre}_{index}", help="Guardar cambios", use_container_width=True):
                        st.session_state['categorias'][cat_nombre]['items'][index] = {
                            'nombre': nuevo_nombre,
                            'unidad': nueva_unidad,
                            'cantidad': nueva_cantidad,
                            'precio_unitario': nuevo_precio,
                            'total': nuevo_total,
                            'categoria': cat_nombre,
                            'notas': nuevas_notas
                        }
                        st.success("✅ ¡Cambios guardados!")
                        st.rerun()

                with col8:
                    if st.button("❌", key=f"eliminar_{cat_nombre}_{index}", help="Eliminar ítem", use_container_width=True):
                        del st.session_state['categorias'][cat_nombre]['items'][index]
                        st.success("✅ ¡Ítem eliminado!")
                        st.rerun()
    
    return st.session_state['categorias']

def show_mano_obra(items_data: Dict[str, Any]) -> None:
    """Mano de obra simplificada"""
    with st.expander("🔧 Agregar Mano de Obra", expanded=False):
        st.markdown("### 🛠️ Configurar Mano de Obra")
        
        categorias_con_items = [cat for cat in items_data.keys() if items_data[cat]['items']]
        
        if not categorias_con_items:
            st.warning("📭 Primero agrega ítems a una categoría para asignar mano de obra")
        else:
            categoria_seleccionada = st.selectbox("Seleccionar categoría:", options=categorias_con_items, key="select_cat_mano_obra")
            
            st.markdown("##### 💰 Costo de Mano de Obra")
            costo_input = st.text_input("Costo de mano de obra ($):", value=str(items_data[categoria_seleccionada].get('mano_obra', 0)), key="input_costo_mano_obra")
            costo_mano_obra = clean_integer_input(costo_input)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("💾 Aplicar Mano de Obra", key="btn_aplicar_mano_obra", use_container_width=True):
                    items_data[categoria_seleccionada]['mano_obra'] = costo_mano_obra
                    st.success(f"✅ Mano de obra de **${costo_mano_obra:,}** aplicada a **{categoria_seleccionada}**")
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Limpiar Mano de Obra", key="btn_limpiar_mano_obra", use_container_width=True):
                    items_data[categoria_seleccionada]['mano_obra'] = 0
                    st.success(f"✅ Mano de obra eliminada de **{categoria_seleccionada}**")
                    st.rerun()

def show_resumen(items_data: Dict[str, Any]) -> float:
    """Resumen simplificado del presupuesto"""
    st.subheader("📊 Resumen del Presupuesto", divider="green")
    
    if not items_data or all(not data.get('items') and data.get('mano_obra', 0) == 0 for cat, data in items_data.items()):
        st.info("📭 No hay ítems agregados aún")
        return 0.0

    total_general = 0

    for cat, data in items_data.items():
        items = data.get('items', [])
        mano_obra = data.get('mano_obra', 0)
        
        if items or mano_obra > 0:
            total_categoria = sum(item.get('total', 0) for item in items) + mano_obra
            total_general += total_categoria

            st.markdown(f"#### 🔹 {cat}")
            
            if items:
                df_items = pd.DataFrame(items)
                column_config = {
                    "nombre": st.column_config.TextColumn("Descripción", width="medium"),
                    "unidad": st.column_config.TextColumn("Unidad", width="small"),
                    "cantidad": st.column_config.NumberColumn("Cantidad", width="small"),
                    "precio_unitario": st.column_config.NumberColumn("P. Unitario", format="$%d", width="small"),
                    "total": st.column_config.NumberColumn("Total", format="$%d", width="small")
                }
                
                if 'notas' in df_items.columns and not df_items['notas'].isna().all():
                    column_config["notas"] = st.column_config.TextColumn("Notas", width="medium")
                
                st.dataframe(df_items, column_config=column_config, hide_index=True, use_container_width=True)
            
            if mano_obra > 0:
                st.markdown(f"**Mano de obra {cat}:** **${mano_obra:,}**")
            
            st.markdown(f"**Total {cat}:** **${total_categoria:,}**")
            st.markdown("---")

    if total_general > 0:
        st.markdown(f"#### 💰 **TOTAL GENERAL:** **${total_general:,}**")
    
    return total_general