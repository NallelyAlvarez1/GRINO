import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Asumiendo que estas funciones importadas manejan la conexión a Supabase
from utils.database import (
    get_presupuestos_usuario, 
    get_presupuesto_detallado,
    get_clientes,
    get_lugares_trabajo,
    delete_presupuesto
)
from utils.auth import check_login
from utils.pdf import (
    mostrar_boton_descarga_pdf
)
from utils.components import safe_numeric_value # Importamos la función segura

st.set_page_config(page_title="Historial", page_icon="🌱", layout="wide")
# Ejecuta la comprobación de login al inicio
check_login()



def _show_presupuesto_detail(presupuesto_id: int, cliente_nombre: str, lugar_nombre: str):
    """Obtiene el detalle completo y lo muestra agrupado por categoría."""
    detalle = get_presupuesto_detallado(presupuesto_id)
    if not detalle:
        st.error("No se pudo cargar el detalle del presupuesto.")
        return

    st.markdown(f"**Cliente:** {cliente_nombre} | **Lugar:** {lugar_nombre} | **Descripción:** {detalle.get('descripcion', 'N/A')}")
      
    total_general = 0
    
    # 1. Agrupar ítems por nombre de categoría
    categorias_agrupadas = {}
    for item in detalle.get('items', []):
        cat = item.get('categoria', 'Sin Categoría') or 'Sin Categoría'
        if cat not in categorias_agrupadas:
            categorias_agrupadas[cat] = {'items': [], 'mano_obra': 0.0}
        
        # Usamos la función segura para obtener el total del ítem
        item_total_safe = safe_numeric_value(item.get('total'))
        
        # Lógica para separar Mano de Obra (asumiendo que tiene ese nombre)
        if 'mano de obra' in item.get('nombre', '').lower():
             # Sumamos al total de mano de obra
            categorias_agrupadas[cat]['mano_obra'] += item_total_safe
        else:
            categorias_agrupadas[cat]['items'].append(item)


    # 2. Mostrar la vista previa agrupada por categoría
    for cat, data in categorias_agrupadas.items():
        items = data['items']
        mano_obra = data.get('mano_obra', 0.0)
        
        # Filtramos la MO General si es un ítem aparte
        is_mano_obra_general = 'mano de obra general' in cat.lower() or cat.lower() == 'general'
        
        if items or mano_obra > 0:
            # Usamos la función segura para calcular el total de la categoría
            total_items_suma = sum(safe_numeric_value(item.get('total')) for item in items)
            total_categoria = total_items_suma + mano_obra
            total_general += total_categoria

            # Si es MO general, no mostramos tabla de ítems
            if is_mano_obra_general and total_items_suma == 0:
                st.markdown(f"**🔹 Mano de Obra General**")
            else:
                st.markdown(f"**🔹 {cat}**")
            
            if items:
                df_items = pd.DataFrame(items)

                # Aplicamos la función segura a las columnas numéricas en el DataFrame
                for col in ['cantidad', 'precio_unitario', 'total']:
                    # Convertimos a int para el display, ya que el formato de moneda usa enteros
                    df_items[col] = df_items[col].apply(lambda x: int(round(safe_numeric_value(x)))) 

                # Seleccionar y renombrar columnas para la visualización
                df_display = df_items[[
                    'nombre', 
                    'unidad', 
                    'cantidad', 
                    'precio_unitario', 
                    'total', 
                    'notas'
                ]].rename(columns={'nombre': 'Descripción', 'precio_unitario': 'P. Unitario'})
                
                st.dataframe(
                    df_display,
                    column_config={
                        "P. Unitario": st.column_config.NumberColumn("P. Unitario", format="$%d"),
                        "total": st.column_config.NumberColumn("Total", format="$%d"),
                        "cantidad": st.column_config.NumberColumn("Cantidad", format="%d"),
                        "notas": "Notas" 
                    },
                    hide_index=True,
                    width='stretch'
                )
            
            col_mo, col_total = st.columns([1, 1]) # Divide el espacio en dos columnas iguales

            # Solo mostramos la Mano de Obra si es > 0
            if mano_obra > 0:
                with col_mo:
                    mo_label = "Mano de obra General" if is_mano_obra_general else f"Mano de obra {cat}"
                    st.markdown(f"**{mo_label}:** **${mano_obra:,.0f}**")

            # El total de la categoría siempre se muestra
            with col_total:
                st.markdown(f"**Total {cat}:** **${total_categoria:,.0f}**") 
                
            st.divider()
    st.markdown(f"#### 💵 **Total General del Presupuesto:** **${total_general:,.0f}**")


def main():
    st.title("🕒 Historial de Presupuestos")
    
    # ------------------- VALIDACIÓN DE ACCESO -------------------
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.error("🔐 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Volver al inicio")
        st.stop()
        
    # Intenta cargar datos globales.
    try:
        clientes = get_clientes()
        lugares = get_lugares_trabajo()
    except Exception as e:
        st.error(f"Error al cargar datos globales (clientes/lugares): {str(e)}")
        st.stop()

    # ------------------- FILTROS -------------------
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        # Mapeo de IDs a Nombres para filtros
        clientes_map = {id: nombre for id, nombre in clientes}
        lugares_map = {id: nombre for id, nombre in lugares}
        
        with col1:
            cliente_filtro_nombre = st.selectbox(
                "Filtrar por cliente:",
                options=["Todos los clientes"] + list(clientes_map.values()),
            )
            cliente_filtro = next((id for id, nombre in clientes_map.items() if nombre == cliente_filtro_nombre), None)
        
        with col2:
            lugar_filtro_nombre = st.selectbox(
                "Filtrar por lugar:",
                options=["Todos los lugares"] + list(lugares_map.values()),
            )
            lugar_filtro = next((id for id, nombre in lugares_map.items() if nombre == lugar_filtro_nombre), None)
        
        with col3:
            fecha_filtro = st.selectbox(
                "Filtrar por fecha:",
                options=["Últimos 7 días", "Últimos 30 días", "Últimos 90 días", "Todos"],
                index=2
            )
    
    filtros = {}
    if cliente_filtro:
        filtros['cliente_id'] = cliente_filtro
    if lugar_filtro:
        filtros['lugar_id'] = lugar_filtro
    
    if fecha_filtro == "Últimos 7 días":
        filtros['fecha_inicio'] = datetime.now() - timedelta(days=7)
    elif fecha_filtro == "Últimos 30 días":
        filtros['fecha_inicio'] = datetime.now() - timedelta(days=30)
    elif fecha_filtro == "Últimos 90 días":
        filtros['fecha_inicio'] = datetime.now() - timedelta(days=90)
    
    try:
        # Obtener presupuestos (se asume que la función maneja el user_id de Supabase)
        presupuestos = get_presupuestos_usuario(st.session_state.user_id, filtros)
    except Exception as e:
        st.error(f"Error al obtener presupuestos: {str(e)}")
        return
    
    if not presupuestos:
        st.info("🔍 No se encontraron presupuestos con los filtros seleccionados")
        return
    
    # ------------------- RESUMEN Y LISTA -------------------
    # Mostrar resumen estadístico
    # Usamos safe_numeric_value para la suma total
    suma_total = sum(safe_numeric_value(p.get('total')) for p in presupuestos)
    total_presupuestos = len(presupuestos)
    avg_total = suma_total / total_presupuestos if total_presupuestos else 0
    
    st.metric("📊 Resumen", 
              f"{total_presupuestos} presupuestos", 
              f"Total: ${suma_total:,.0f} | Promedio: ${avg_total:,.0f}")
    
    st.subheader("📋 Presupuestos Generados")

    # Encabezado tipo tabla
    with st.container():
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1, 3])
        col1.markdown("**Cliente**")
        col2.markdown("**Lugar**")
        col3.markdown("**Fecha**")
        col4.markdown("**Total**")
        col5.markdown("**Ítems**")
        col6.markdown("**Acciones**")

    # Filas tipo tabla
    for p in presupuestos:
        # Usamos safe_numeric_value para el display del total
        total_display = safe_numeric_value(p.get('total'))
        
        with st.container(border=True):
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1, 3])

            # Datos
            col1.write(p.get('cliente', {}).get('nombre', 'N/A').title())
            col2.write(p.get('lugar', {}).get('nombre', 'N/A').title())
            col3.write(p.get('fecha', datetime.now()).strftime('%Y-%m-%d'))
            col4.write(f"**${total_display:,.2f}**")
            col5.write(str(p.get('num_items', 0)))

            # Acciones
            with col6:
                # El nuevo set de 4 columnas
                b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
                
                # Clave de estado para el toggle del expander
                state_key = f"expander_toggle_{p['id']}"
                if state_key not in st.session_state:
                    st.session_state[state_key] = False

                with b1: # BOTÓN EDITAR
                    if st.button("✏️", key=f"edit_{p['id']}", help="Editar"):
                        # Limpiar el estado de edición anterior si existe
                        if 'categorias_edicion' in st.session_state:
                            del st.session_state['categorias_edicion']
                        if 'categorias' in st.session_state:
                            del st.session_state['categorias']
                            
                        st.session_state['presupuesto_a_editar_id'] = p['id'] 
                        st.switch_page("pages/_✏️ Editar.py")

                with b2: # BOTÓN DESCARGA
                    try:
                        pdf_bytes, file_name, success = mostrar_boton_descarga_pdf(p['id'])
                        if success and pdf_bytes:
                            st.download_button(
                                label="⬇️",
                                data=pdf_bytes,
                                file_name=file_name,
                                mime="application/pdf",
                                key=f"down_{p['id']}",
                                help="Descargar PDF"
                            )
                        else:
                            st.button("🚫", key=f"down_{p['id']}_disabled", disabled=True, help="PDF no disponible")
                    except Exception as e:
                        st.button("🚫", key=f"down_{p['id']}_error", disabled=True, help=f"Error: {e}")
                
                with b3: # BOTÓN VISTA PREVIA (TOGGLE EXPANDER)
                    # El botón toggles el estado
                    if st.button("📑", key=f"view_{p['id']}", help="Ver Presupuesto"):
                        st.session_state[state_key] = not st.session_state[state_key]
                        st.rerun() # Necesario para abrir/cerrar inmediatamente

                with b4: # BOTÓN ELIMINAR
                    if st.button("🗑️", key=f"del_{p['id']}", help="Eliminar"):
                        # Se podría agregar una confirmación con un modal
                        if delete_presupuesto(p['id'], st.session_state.user_id):
                            st.success("Presupuesto eliminado correctamente")
                            st.rerun()
                        else:
                            st.error("No se pudo eliminar el presupuesto. Revise sus permisos.")
            
            # LÓGICA DEL EXPANDER
            if st.session_state.get(state_key, False):
                with st.expander(f"Detalle Presupuesto ID: {p['id']}", expanded=True):
                    _show_presupuesto_detail(
                        presupuesto_id=p['id'],
                        cliente_nombre=p.get('cliente', {}).get('nombre', 'N/A'),
                        lugar_nombre=p.get('lugar', {}).get('nombre', 'N/A')
                    )
import streamlit as st
from utils.database import get_clientes_detallados, create_cliente, update_cliente, delete_cliente
from utils.auth import check_login
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any

# Ejecuta la comprobación de login al inicio
check_login()

def mostrar_formulario_cliente(cliente_id: Optional[int] = None, datos_actuales: Optional[Dict[str, Any]] = None):
    """Muestra formulario para crear/editar cliente"""
    # Usamos st.form para manejar el estado del formulario de forma atómica
    with st.form(key=f"form_cliente_{cliente_id or 'nuevo'}", border=True):
        nombre = st.text_input(
            "Nombre del cliente*",
            value=datos_actuales['nombre'] if datos_actuales else "",
            help="Nombre completo o razón social"
        )
        
        # [Campos adicionales omitidos por brevedad, pero irían aquí]
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Guardar", type="primary"):
                if not nombre.strip():
                    st.error("El nombre es obligatorio")
                    # No usamos st.stop() dentro del form_submit_button, pero el error es visible
                    return
                
                try:
                    if cliente_id:  # Edición
                        if update_cliente(
                            cliente_id=cliente_id,
                            nombre=nombre.strip(),
                            user_id=st.session_state.user_id
                        ):
                            st.success("Cliente actualizado correctamente")
                            # Limpiar el estado de edición y recargar la página
                            if 'editar_cliente' in st.session_state:
                                del st.session_state['editar_cliente']
                            st.rerun()
                        else:
                            st.error("Error al actualizar el cliente.")
                    else:  # Nuevo
                        new_id = create_cliente(
                            nombre=nombre.strip(),
                            user_id=st.session_state.user_id # Usamos el user_id de Supabase
                        )
                        if new_id:
                            st.success("Cliente creado correctamente")
                            st.rerun()
                        else:
                            st.error("Error al crear el cliente. El nombre puede estar en uso.")
                except Exception as e:
                    st.error(f"Error en la operación de base de datos: {e}")
                    
        with col2:
            if st.form_submit_button("❌ Cancelar"):
                if 'editar_cliente' in st.session_state:
                    del st.session_state['editar_cliente']
                if 'nuevo_cliente_form' in st.session_state:
                    del st.session_state['nuevo_cliente_form']
                st.rerun()

def mostrar_modal_eliminar(cliente_id: int, cliente_nombre: str):
    """Muestra un modal (expander) de confirmación para eliminar."""
    
    # Usamos un contenedor o expander para simular el modal de confirmación
    with st.expander(f"⚠️ Confirmar Eliminación: {cliente_nombre}", expanded=True):
        st.warning(f"¿Está seguro de que desea eliminar el cliente **{cliente_nombre}** (ID: {cliente_id})?")
        st.info("Esta acción eliminará permanentemente al cliente y puede afectar a los presupuestos asociados.")
        
        col_conf, col_cancel = st.columns(2)
        with col_conf:
            if st.button("🔴 SÍ, Eliminar permanentemente", key="confirm_delete_btn", type="primary", use_container_width=True):
                try:
                    if delete_cliente(cliente_id, st.session_state.user_id):
                        st.success("Cliente eliminado correctamente.")
                        del st.session_state['eliminar_cliente']
                        st.rerun()
                    else:
                        st.error("No se pudo eliminar el cliente. Verifique sus permisos.")
                except Exception as e:
                    st.error(f"Error de base de datos al eliminar: {e}")
        with col_cancel:
            if st.button("❌ Cancelar Eliminación", key="cancel_delete_btn", use_container_width=True):
                del st.session_state['eliminar_cliente']
                st.rerun()


def clientes_page():
    st.title("👥 Gestión de Clientes")

    # ------------------- VALIDACIÓN DE ACCESO -------------------
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.error("🔐 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Volver al inicio")
        st.stop()
        
    user_id = st.session_state.user_id

    # Botón para mostrar el formulario de nuevo cliente
    if st.button("➕ Crear Nuevo Cliente", key="new_client_btn", type="secondary"):
        st.session_state['nuevo_cliente_form'] = True
        
    # Mostrar formulario de creación
    if st.session_state.get('nuevo_cliente_form'):
        st.subheader("Crear Nuevo Cliente", divider="blue")
        mostrar_formulario_cliente()
        st.markdown("---")


    # ------------------- TABLA DE CLIENTES -------------------
    st.subheader("Clientes Registrados", divider="blue")
    
    try:
        # Obtener clientes (filtrados por RLS en Supabase, pero aquí pasamos el user_id)
        clientes = get_clientes_detallados(user_id)
    except Exception as e:
        st.error(f"Error al cargar la lista de clientes: {e}")
        clientes = []
        
    if not clientes:
        st.info("No se han encontrado clientes registrados.")
        return

    # Convertir a DataFrame para mostrar
    df_clientes = pd.DataFrame(clientes)
    df_display = df_clientes[['nombre', 'fecha_creacion', 'creado_por', 'id']].rename(
        columns={'nombre': 'Cliente', 'fecha_creacion': 'Fecha Creación', 'creado_por': 'Creado por (Email)', 'id': 'ID'}
    )
    
    # ------------------- Mostrar clientes y controles -------------------
    # Encabezado
    st.markdown("---")
    col_name, col_date, col_user, col_id, col_actions = st.columns([3, 2, 2, 1, 1.5])
    col_name.markdown("**Cliente**")
    col_date.markdown("**Fecha Creación**")
    col_user.markdown("**Creado por**")
    col_id.markdown("**ID**")
    col_actions.markdown("**Acciones**")
    st.markdown("---")
    
    # Filas
    for cliente in clientes:
        col_name, col_date, col_user, col_id, col_actions = st.columns([3, 2, 2, 1, 1.5])
        
        col_name.write(cliente['nombre'])
        col_date.write(cliente['fecha_creacion'])
        col_user.write(cliente['creado_por'])
        # Mostrar solo los primeros 8 caracteres del ID para la tabla
        col_id.write(f"`{cliente['id']}`")
        
        with col_actions:
            b1, b2 = st.columns(2)
            with b1:
                if st.button("✏️", key=f"edit_btn_{cliente['id']}", help="Editar"):
                    st.session_state['editar_cliente'] = cliente['id']
                    # Limpiar modal de nuevo cliente
                    if 'nuevo_cliente_form' in st.session_state: del st.session_state['nuevo_cliente_form']
                    st.rerun()
            with b2:
                if st.button("🗑️", key=f"del_btn_{cliente['id']}", help="Eliminar"):
                    st.session_state['eliminar_cliente'] = cliente['id']
                    st.rerun()
    
    # Mostrar modal de edición si está activo
    if 'editar_cliente' in st.session_state:
        cliente_id_edit = st.session_state['editar_cliente']
        # Buscar el cliente a editar en la lista cargada
        cliente_a_editar = next((c for c in clientes if c['id'] == cliente_id_edit), None)
        
        if cliente_a_editar:
            st.markdown("---")
            st.subheader(f"✏️ Editando: {cliente_a_editar['nombre']}")
            mostrar_formulario_cliente(
                cliente_id=cliente_id_edit,
                datos_actuales={'nombre': cliente_a_editar['nombre']}
            )
        else:
            del st.session_state['editar_cliente']
            st.rerun()
    
    # Mostrar modal de eliminación si está activo
    if 'eliminar_cliente' in st.session_state:
        cliente_id_del = st.session_state['eliminar_cliente']
        cliente_a_eliminar = next((c for c in clientes if c['id'] == cliente_id_del), None)
        
        if cliente_a_eliminar:
            mostrar_modal_eliminar(cliente_id_del, cliente_a_eliminar['nombre'])
        else:
            del st.session_state['eliminar_cliente']
            st.rerun()

if __name__ == "__main__":
    if check_login():
        clientes_page()
    else:
        st.error("🔒 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Ir a página de inicio")
if __name__ == "__main__":
    if 'user_id' in st.session_state and st.session_state.user_id:
        main()
    else:
        st.error("🔒 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Ir a página de inicio")