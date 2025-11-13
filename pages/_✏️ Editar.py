import streamlit as st
import os
import pandas as pd
from typing import Dict, Any, List
from utils.database import (
    get_presupuesto_detallado,
    save_edited_presupuesto,
    get_clientes,
    get_lugares_trabajo,
    get_categorias,
    get_presupuestos_usuario
)
from utils.components import selector_categoria
from utils.pdf import generar_pdf
from utils.auth import check_login

# Insertar esto al principio de editar_presupuesto_page()
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
    margin-bottom: -10px !important;
    margin-top: -10px !important;
}

</style>
""", unsafe_allow_html=True)

check_login()

def mostrar_selector_presupuestos():
    """Muestra un selector de presupuestos para editar"""
    st.subheader("Seleccionar Presupuesto a Editar")
    
    # Obtener los presupuestos del usuario actual
    try:
        presupuestos = get_presupuestos_usuario(st.session_state.user_id)
    except Exception as e:
        st.error(f"Error al cargar presupuestos: {e}")
        return

    if not presupuestos:
        st.info("No hay presupuestos para editar.")
        return

    # Formatear las opciones para el selectbox
    opciones = []
    for p in presupuestos:
        # Formato: "ID: [id] - Cliente: [cliente] - Lugar: [lugar] - Total: $[total]"
        texto = f"ID: {p['id']} - Cliente: {p['cliente']['nombre']} - Lugar: {p['lugar']['nombre']} - Total: ${p['total']:,.0f}"
        opciones.append((p['id'], texto))

    # Selectbox
    selected_option = st.selectbox(
        "Selecciona un presupuesto:",
        options=opciones,
        format_func=lambda x: x[1]  # Mostrar el texto formateado
    )

    if selected_option:
        presupuesto_id = selected_option[0]
        if st.button("Cargar Presupuesto para Editar", type="primary"):
            st.session_state['presupuesto_a_editar_id'] = presupuesto_id
            st.rerun()

def show_resumen_edicion(edicion_data: Dict[str, Any]) -> None:
    if not edicion_data['categorias']:
        st.info("No hay items agregados aún")
        return

    total_general = 0

    for cat, data in edicion_data['categorias'].items():
        items = data.get('items', [])
        
        if not items:
            continue
            
        total_categoria = sum(item['total'] for item in items)
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
                use_container_width=True
            )
        
        st.markdown(f"**Total {cat}:** ${total_categoria:,}")
            
    st.markdown(f"#### 💵 Total General: ${total_general:,}")

def editar_presupuesto_page():
    HISTORIAL_PAGE = "pages/2_🕒_historial.py"

    # Si no hay presupuesto seleccionado, mostramos el selector
    if 'presupuesto_a_editar_id' not in st.session_state:
        mostrar_selector_presupuestos()
        # También mostramos un enlace al historial por si prefieren ir allí
        st.page_link(HISTORIAL_PAGE, label="Ir al Historial 🕒")
        return

    # Si hay presupuesto seleccionado, mostramos el formulario
    try:
        presupuesto_id = int(st.session_state['presupuesto_a_editar_id'])
    except Exception:
        st.error("❌ ID de presupuesto inválido.")
        del st.session_state['presupuesto_a_editar_id']
        st.rerun()

    # Botón para seleccionar otro presupuesto
    if st.button("⬅️ Seleccionar otro presupuesto"):
        del st.session_state['presupuesto_a_editar_id']
        st.rerun()

    mostrar_formulario_edicion(presupuesto_id)

def mostrar_formulario_edicion(presupuesto_id):
    st.subheader(f"✏️ Editar Presupuesto ID: {presupuesto_id}")
    HISTORIAL_PAGE = "pages/2_🕒_historial.py"
    #st.page_link(HISTORIAL_PAGE, label="⬅️ Volver al Historial")

    # Clave específica por presupuesto para evitar colisiones
    EDICION_KEY = f"edicion_data_{presupuesto_id}"

    # Cargar listas de referencia siempre (clientes/lugares/categorias)
    try:
        clientes = get_clientes()  # lista de tuples (id, nombre)
        lugares = get_lugares_trabajo()
        categorias = get_categorias()
    except Exception as e:
        st.error(f"Error cargando datos de referencia: {e}")
        st.stop()

    clientes_dict = {id: nombre for id, nombre in clientes}
    lugares_dict = {id: nombre for id, nombre in lugares}
    categorias_id_to_name = {id: nombre for id, nombre in categorias}
    clientes_name_to_id = {nombre: id for id, nombre in clientes}
    lugares_name_to_id = {nombre: id for id, nombre in lugares}

    OPCIONES_UNIDAD = ["m²", "m³", "Unidad", "Metro lineal", "Saco", "Metro", "Caja", "Kilo (kg)", "Galón (gal)", "Litro", "Par/Juego", "Plancha"]

    # --- Cargar detalle del presupuesto (solo la primera vez) ---
    if EDICION_KEY not in st.session_state:
        try:
            detalle = get_presupuesto_detallado(presupuesto_id)
        except Exception as e:
            st.error(f"Error al solicitar presupuesto detallado: {e}")
            st.stop()

        if not detalle:
            st.error("❌ No se encontraron datos del presupuesto seleccionado. (detalle es None)")
            # borrar id y ofrecer volver
            if 'presupuesto_a_editar_id' in st.session_state:
                del st.session_state['presupuesto_a_editar_id']
            #st.page_link(HISTORIAL_PAGE, label="Volver al Historial")
            st.stop()

        # Mapear items plano a la estructura por nombre de categoría (igual que tu versión original)
        items_por_categoria_nombre: Dict[str, Dict[str, Any]] = {}
        for item in detalle.get('items', []):
            cat_id = item.get('categoria_id', None)
            cat_nombre = categorias_id_to_name.get(cat_id, item.get('categoria') or 'Sin Categoría')

            item_data = {
                'nombre': item.get('nombre', item.get('nombre_personalizado')) or item.get('nombre_personalizado') or '',
                'unidad': item.get('unidad') or 'Unidad',
                'cantidad': float(item.get('cantidad') or 0.0), 
                'precio_unitario': float(item.get('precio_unitario') or 0.0),
                'total': float(item.get('total') or 0.0),
                'categoria_id': cat_id,
                'descripcion': item.get('descripcion', '')
            }

            if cat_nombre not in items_por_categoria_nombre:
                items_por_categoria_nombre[cat_nombre] = {'items': []}

            items_por_categoria_nombre[cat_nombre]['items'].append(item_data)

        # Inicializar el estado con la estructura que usa tu UI
        st.session_state[EDICION_KEY] = {
            "cliente_id": detalle['cliente']['id'],
            "lugar_id": detalle['lugar']['id'],
            "descripcion_original": detalle.get('descripcion', f"Presupuesto original ID {presupuesto_id}"),
            "categorias": items_por_categoria_nombre
        }

    # --- Recuperar datos desde session_state ---
    edicion_data = st.session_state[EDICION_KEY]

    # === Cabecera (Cliente, Lugar y Descripción) ===
    st.subheader("1. Datos del cliente")
    col_cli, col_lug, col_desc = st.columns(3)

    with col_cli:
        cliente_seleccionado_nombre = clientes_dict.get(edicion_data['cliente_id'], 'Cliente Desconocido')
        nuevo_cliente_nombre = st.selectbox(
            "Cliente:",
            options=list(clientes_dict.values()),
            index=list(clientes_dict.values()).index(cliente_seleccionado_nombre) if cliente_seleccionado_nombre in clientes_dict.values() else 0,
            key=f"edit_cliente_{presupuesto_id}"
        )
        edicion_data['cliente_id'] = clientes_name_to_id.get(nuevo_cliente_nombre)

    with col_lug:
        lugar_seleccionado_nombre = lugares_dict.get(edicion_data['lugar_id'], 'Lugar Desconocido')
        nuevo_lugar_nombre = st.selectbox(
            "Lugar de Trabajo:",
            options=list(lugares_dict.values()),
            index=list(lugares_dict.values()).index(lugar_seleccionado_nombre) if lugar_seleccionado_nombre in lugares_dict.values() else 0,
            key=f"edit_lugar_{presupuesto_id}"
        )
        edicion_data['lugar_id'] = lugares_name_to_id.get(nuevo_lugar_nombre)

    with col_desc:
        nueva_descripcion = st.text_input(
            "Trabajo a realizar:",
            placeholder="Ejemplo: Instalación de sistema de riego...",
            value=edicion_data.get('descripcion_original', ""), 
            key=f"descripcion_input_{presupuesto_id}"
        ) 
        edicion_data['descripcion_original'] = nueva_descripcion
    # ------------------------------------------

    st.divider()

    # === Edición de items (sin expander) ===
    st.subheader("2. Edición de Ítems")

    total_general = 0.0
    items_editados_final: List[Dict[str, Any]] = []

    # Mostrar todas las categorías y sus items directamente
    # Mostrar todas las categorías y sus items directamente
    for cat, datos in list(edicion_data['categorias'].items()):
        items = datos.get('items', [])
        
        # Saltar categorías vacías
        if not items:
            continue
        
    # Resto del código...

        st.markdown(f"### **{cat}**")

        # Encabezados
        col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 2, 0.8])
        col1.write("**Nombre**")
        col2.write("**Unidad**")
        col3.write("**Cantidad**")
        col4.write("**P. Unitario**")
        col5.write("**Total**")
        col6.write("**Borrar**")

        # Iterar sobre una copia del índice porque podemos eliminar items
        for index in range(len(items)):
            item = items[index]
            col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 2, 0.8])

            with col1:
                nuevo_nombre = st.text_input("Nombre", item['nombre'],
                                            key=f"nombre_{presupuesto_id}_{cat}_{index}", label_visibility="collapsed")
            with col2:
                nueva_unidad = st.selectbox("Unidad", OPCIONES_UNIDAD,
                                            index=OPCIONES_UNIDAD.index(item['unidad']) if item['unidad'] in OPCIONES_UNIDAD else 0,
                                            key=f"unidad_{presupuesto_id}_{cat}_{index}", label_visibility="collapsed")
            with col3:
                # CAMBIO 1: Cantidad con format="%.0f" para mostrar solo enteros
                nueva_cantidad = st.number_input("Cantidad", min_value=0.0, step=1.0, value=float(item['cantidad']),
                                                key=f"cantidad_{presupuesto_id}_{cat}_{index}", format="%.0f", label_visibility="collapsed")
            with col4:
                # CAMBIO 2: Precio con format="%.0f" para mostrar solo enteros
                nuevo_precio = st.number_input("Precio", min_value=0.0, step=1.0, value=float(item['precio_unitario']),
                                            key=f"precio_{presupuesto_id}_{cat}_{index}", format="%.0f", label_visibility="collapsed")

            nuevo_total = nueva_cantidad * nuevo_precio

            with col5:
                # El total ya usa :,.0f, lo cual es correcto para mostrar entero formateado con separador de miles.
                st.text_input("Total", value=f"${nuevo_total:,.0f}", disabled=True,
                            key=f"total_{presupuesto_id}_{cat}_{index}", label_visibility="collapsed")

            with col6:
                if st.button("❌", key=f"eliminar_{presupuesto_id}_{cat}_{index}"):
                    # eliminar item y recargar
                    del edicion_data['categorias'][cat]['items'][index]
                    # Si la categoría queda vacía, eliminar la categoría
                    if not edicion_data['categorias'][cat]['items']:
                        del edicion_data['categorias'][cat]
                    st.success(f"¡Ítem eliminado de {cat}!")
                    st.session_state[EDICION_KEY] = edicion_data
                    st.rerun()

            # actualizar el item en el estado
            item['nombre'] = nuevo_nombre
            item['unidad'] = nueva_unidad
            item['cantidad'] = nueva_cantidad # Se guarda como float para la base de datos
            item['precio_unitario'] = nuevo_precio # Se guarda como float para la base de datos
            item['total'] = nuevo_total

            total_general += nuevo_total

            items_editados_final.append({
                'categoria_id': item.get('categoria_id'),
                'nombre_personalizado': nuevo_nombre,
                'unidad': nueva_unidad,
                'cantidad': nueva_cantidad,
                'precio_unitario': nuevo_precio,
                'total': nuevo_total,
                'descripcion': item.get('descripcion', '')
            })

        st.divider()

    st.metric("Total General Calculado", f"${total_general:,.0f}")

    # === Expander cerrado para añadir nuevo ítem ===
    with st.expander("➕ Añadir nuevo ítem", expanded=True):
        col1, col2 = st.columns([2, 4])
        with col1:
            nueva_categoria_id, nueva_categoria_nombre = selector_categoria(
                mostrar_label=False,
                requerido=False, # Si el ítem no se va a guardar de inmediato, no lo hacemos requerido
                key_suffix=f"nuevo_item_cat_{presupuesto_id}"
            )
        with col2:
            col1, col2, col3 = st.columns(3)
            with col1:
                nuevo_nombre = st.text_input("Nombre del ítem", key=f"nuevo_item_{presupuesto_id}")
            with col2:
                nueva_cantidad = st.number_input("Cantidad", min_value=0.0, step=1.0, key=f"cantidad_nueva_{presupuesto_id}", format="%.0f")
            with col3:
                nuevo_precio = st.number_input("Precio unitario", min_value=0.0, step=1.0, key=f"precio_nueva_{presupuesto_id}", format="%.0f")
                
            
            col1, col2 = st.columns(2)
            with col1:
                nueva_unidad = st.selectbox("Unidad", OPCIONES_UNIDAD, key=f"unidad_nueva_{presupuesto_id}")
            with col2:
                total = nueva_cantidad * nuevo_precio
                st.text_input("Total", value=f"${total:,}", disabled=True)

            if st.button("💡 Agregar ítem", key=f"btn_agregar_item_{presupuesto_id}"):
                if not nueva_categoria_id or not nuevo_nombre:
                    st.warning("Por favor completa la categoría y el nombre del ítem.")
                else:
                    nuevo_item = {
                        "nombre": nuevo_nombre,
                        "unidad": nueva_unidad,
                        "cantidad": nueva_cantidad,
                        "precio_unitario": nuevo_precio,
                        "total": nueva_cantidad * nuevo_precio,
                        "categoria_id": nueva_categoria_id,
                        "descripcion": nueva_descripcion
                    }
                    if nueva_categoria_nombre not in edicion_data["categorias"]:
                        edicion_data["categorias"][nueva_categoria_nombre] = {"items": []}
                    
                    edicion_data["categorias"][nueva_categoria_nombre]["items"].append(nuevo_item)
                    st.success(f"✅ Ítem agregado a {nueva_categoria_nombre}")
                    st.session_state[EDICION_KEY] = edicion_data
                    st.rerun()

        # === Expander cerrado para añadir mano de obra ===
    with st.expander("🛠️ Añadir mano de obra", expanded=False):
        st.markdown("### Configurar Mano de Obra")
        
        # Selector de categoría desde la base de datos
        col1, col2 = st.columns(2)
        with col1:
            st.write("Selecciona la categoría:")
            categoria_mano_id, categoria_mano_nombre = selector_categoria(
                mostrar_label=False,
                requerido=False,
                key_suffix=f"mano_obra_{presupuesto_id}"
            )
        
        with col2:
            st.write("Nombre del trabajo:")
            nombre_trabajo = st.text_input(
                "Descripción del trabajo", 
                value="Mano de Obra",  # Valor por defecto
                placeholder="Ej: Instalación de riegos, Montaje de estructura...",
                key=f"desc_mano_{presupuesto_id}",
                label_visibility="collapsed"
            )
        
        # Solo precio (cantidad fija en 1 para mano de obra)
        precio_trabajo = st.number_input(
            "Precio de la mano de obra:", 
            min_value=0.0, 
            step=1.0, 
            value=0.0,
            key=f"precio_mano_{presupuesto_id}", 
            format="%.0f"
        )
        
        # Mostrar total calculado (siempre cantidad = 1)
        total_mano_obra = precio_trabajo  # cantidad fija = 1
        st.metric("Total Mano de Obra", f"${total_mano_obra:,.0f}")

        if st.button("🧰 Agregar Mano de Obra", key=f"btn_agregar_mano_{presupuesto_id}"):
            if not categoria_mano_id:
                st.warning("Por favor selecciona una categoría.")
            elif not nombre_trabajo.strip():
                st.warning("Por favor ingresa un nombre para el trabajo.")
            else:
                nuevo_item = {
                    "nombre": nombre_trabajo.strip(),
                    "unidad": "Unidad",
                    "cantidad": 1,
                    "precio_unitario": precio_trabajo,
                    "total": precio_trabajo,
                    "categoria_id": categoria_mano_id,
                    "descripcion": "Mano de obra"
                }
                
                if categoria_mano_nombre not in edicion_data["categorias"]:
                    edicion_data["categorias"][categoria_mano_nombre] = {"items": []}
                
                # Verificar si ya existe un item con el MISMO NOMBRE en esta categoría
                item_existente = next(
                    (item for item in edicion_data["categorias"][categoria_mano_nombre]["items"] 
                    if item.get('nombre') == nombre_trabajo.strip()), 
                    None
                )
                
                if item_existente:
                    # Actualizar item existente si tiene el mismo nombre
                    item_existente['precio_unitario'] = precio_trabajo
                    item_existente['total'] = precio_trabajo
                    st.success(f"✅ '{nombre_trabajo.strip()}' actualizado en {categoria_mano_nombre}")
                else:
                    # Agregar nuevo item si el nombre es diferente
                    edicion_data["categorias"][categoria_mano_nombre]["items"].append(nuevo_item)
                    st.success(f"✅ '{nombre_trabajo.strip()}' agregado a {categoria_mano_nombre}")
                
                st.session_state[EDICION_KEY] = edicion_data
                st.rerun()

    st.divider()

    # === SECCIÓN RESUMEN ===
    st.subheader("3. Resumen del Presupuesto")
    show_resumen_edicion(edicion_data)

    st.divider()

    # === Guardar Edición como nuevo presupuesto ===
    if st.button("💾 Guardar Edición como Nuevo Presupuesto", type="primary", use_container_width=True):
        st.info("Calculando y guardando nueva versión...")
        try:
            # Preparar lista plana para save_edited_presupuesto
            lista_items_flat = []
            for cat_nombre, cat_data in edicion_data['categorias'].items():
                for itm in cat_data.get('items', []):
                    lista_items_flat.append({
                        'categoria_id': itm.get('categoria_id'),
                        'nombre_personalizado': itm['nombre'],
                        'unidad': itm['unidad'],
                        'cantidad': itm['cantidad'],
                        'precio_unitario': itm['precio_unitario'],
                        'total': itm['total'],
                        'descripcion': itm.get('descripcion', '')
                    })

            nuevo_id = save_edited_presupuesto(
                cliente_id=edicion_data['cliente_id'],
                lugar_id=edicion_data['lugar_id'],
                descripcion_original=edicion_data.get('descripcion_original'),
                total=total_general,
                user_id=st.session_state.user_id,
                items_data=lista_items_flat
            )

            if nuevo_id:
                st.success(f"✅ ¡Edición guardada exitosamente! Nuevo Presupuesto ID: {nuevo_id}")

                # Generar PDF usando nombres desde los dicts que cargamos arriba
                cliente_nombre = clientes_dict.get(edicion_data['cliente_id'], "Cliente desconocido")
                lugar_nombre = lugares_dict.get(edicion_data['lugar_id'], "Lugar desconocido")
                descripcion_actualizada = edicion_data.get('descripcion_original', '')
                # Generar PDF y obtener bytes (igual que en mostrar_boton_descarga_pdf)
                pdf_path = generar_pdf(
                    cliente_nombre, 
                    edicion_data['categorias'], 
                    lugar_nombre,
                    descripcion=descripcion_actualizada  # ← Agregar este parámetro
                )
                
                # Leer el PDF en bytes
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                
                # Eliminar archivo temporal
                try:
                    os.unlink(pdf_path)
                except Exception as e:
                    print(f"Error al eliminar archivo temporal: {str(e)}")
                
                # Formatear nombre del archivo igual que en mostrar_boton_descarga_pdf
                lugar_nombre_limpio = lugar_nombre.strip().replace(" ", "_")
                file_name = f"Presupuesto_{lugar_nombre_limpio}.pdf"

                # Mostrar botón de descarga con el nuevo formato
                st.download_button(
                    "📄 Descargar PDF actualizado",
                    pdf_bytes,
                    file_name=file_name,
                    mime="application/pdf",
                    use_container_width=True
                )

                # Limpiar estado y volver
                if 'presupuesto_a_editar_id' in st.session_state:
                    del st.session_state['presupuesto_a_editar_id']
                if EDICION_KEY in st.session_state:
                    del st.session_state[EDICION_KEY]

                st.page_link(HISTORIAL_PAGE, label="Volver al Historial para ver el nuevo registro")
            else:
                st.error("❌ Error al guardar la edición en la base de datos.")
        except Exception as e:
            st.error(f"❌ Error crítico al procesar la edición: {e}")
            st.exception(e)




if __name__ == "__main__":
    editar_presupuesto_page()