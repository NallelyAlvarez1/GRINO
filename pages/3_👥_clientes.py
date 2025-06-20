import streamlit as st
from utils.database import get_clientes, create_cliente, update_cliente, delete_cliente
from utils.auth import require_login
import pandas as pd
from datetime import datetime

require_login()

def mostrar_formulario_cliente(cliente_id=None, datos_actuales=None):
    """Muestra formulario para crear/editar cliente"""
    with st.form(key=f"form_cliente_{cliente_id or 'nuevo'}", border=True):
        nombre = st.text_input(
            "Nombre del cliente*",
            value=datos_actuales['nombre'] if datos_actuales else "",
            help="Nombre completo o razón social"
        )
        
        # Campos adicionales podrían ir aquí (email, teléfono, etc.)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Guardar", type="primary"):
                if not nombre.strip():
                    st.error("El nombre es obligatorio")
                    st.stop()
                
                try:
                    if cliente_id:  # Edición
                        update_cliente(
                            cliente_id=cliente_id,
                            nombre=nombre.strip(),
                            user_id=st.session_state.user_id
                        )
                        st.success("Cliente actualizado correctamente")
                    else:  # Nuevo
                        create_cliente(
                            nombre=nombre.strip(),
                            user_id=st.session_state.user_id
                        )
                        st.success("Cliente creado correctamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {str(e)}")
        
        with col2:
            if st.form_submit_button("✖️ Cancelar"):
                st.rerun()

def mostrar_modal_eliminar(cliente_id, cliente_nombre):
    """Muestra confirmación para eliminar cliente"""
    with st.popover("⚠️ Confirmar eliminación", use_container_width=True):
        st.warning(f"¿Eliminar cliente: {cliente_nombre}?")
        if st.button("🗑️ Eliminar definitivamente", type="primary"):
            try:
                delete_cliente(cliente_id)
                st.success("Cliente eliminado")
                st.rerun()
            except Exception as e:
                st.error(f"Error al eliminar: {str(e)}")
        if st.button("↩️ Cancelar"):
            pass

def main():
    st.title("👥 Gestión de Clientes")
    
    # Barra de búsqueda y botón nuevo
    col1, col2 = st.columns([4, 1])
    with col1:
        busqueda = st.text_input("Buscar clientes", placeholder="Escribe para filtrar...")
    with col2:
        if st.button("➕ Nuevo cliente", use_container_width=True):
            st.session_state['nuevo_cliente'] = True
    
    # Mostrar formulario de nuevo cliente si está activo
    if st.session_state.get('nuevo_cliente'):
        with st.expander("📝 Nuevo Cliente", expanded=True):
            mostrar_formulario_cliente()
            if st.button("Cerrar formulario"):
                del st.session_state['nuevo_cliente']
                st.rerun()
        st.divider()
    
    # Obtener clientes del usuario actual
    try:
        clientes = get_clientes(st.session_state.user_id)
    except Exception as e:
        st.error(f"Error al cargar clientes: {str(e)}")
        st.stop()
    
    # Filtrar por búsqueda
    if busqueda:
        clientes = [c for c in clientes if busqueda.lower() in c['nombre'].lower()]
    
    if not clientes:
        st.info("No hay clientes registrados")
        return
    
    # Mostrar en cuadrícula (4 por fila)
    cols = st.columns(4)
    for i, cliente in enumerate(clientes):
        with cols[i % 4]:
            with st.container(border=True):
                # Avatar con inicial
                inicial = cliente['nombre'][0].upper()
                st.markdown(f"""
                    <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                        <div style="
                            width: 60px; 
                            height: 60px; 
                            background-color: #4e8cff; 
                            color: white; 
                            border-radius: 50%; 
                            display: flex; 
                            align-items: center; 
                            justify-content: center;
                            font-size: 24px;
                            font-weight: bold;
                        ">{inicial}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Nombre del cliente
                st.markdown(f"<h3 style='text-align: center;'>{cliente['nombre']}</h3>", unsafe_allow_html=True)
                
                # Fecha de registro (si está disponible)
                if 'fecha_registro' in cliente:
                    fecha = cliente['fecha_registro'].strftime("%d/%m/%Y")
                    st.caption(f"Registrado: {fecha}")
                
                # Botones de acción
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Editar", key=f"edit_{cliente['id']}", use_container_width=True):
                        st.session_state['editar_cliente'] = cliente['id']
                
                with col2:
                    if st.button("🗑️ Eliminar", key=f"del_{cliente['id']}", use_container_width=True):
                        st.session_state['eliminar_cliente'] = cliente['id']
    
    # Mostrar modal de edición si está activo
    if 'editar_cliente' in st.session_state:
        cliente_id = st.session_state['editar_cliente']
        cliente = next((c for c in clientes if c['id'] == cliente_id), None)
        
        if cliente:
            with st.expander(f"✏️ Editando: {cliente['nombre']}", expanded=True):
                mostrar_formulario_cliente(
                    cliente_id=cliente_id,
                    datos_actuales={'nombre': cliente['nombre']}
                )
                if st.button("Cerrar edición"):
                    del st.session_state['editar_cliente']
                    st.rerun()
        else:
            del st.session_state['editar_cliente']
            st.rerun()
    
    # Mostrar modal de eliminación si está activo
    if 'eliminar_cliente' in st.session_state:
        cliente_id = st.session_state['eliminar_cliente']
        cliente = next((c for c in clientes if c['id'] == cliente_id), None)
        
        if cliente:
            mostrar_modal_eliminar(cliente_id, cliente['nombre'])
        else:
            del st.session_state['eliminar_cliente']
            st.rerun()

if __name__ == "__main__":
    if 'user_id' in st.session_state and st.session_state.user_id:
        main()
    else:
        st.error("🔒 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Ir a página de inicio")