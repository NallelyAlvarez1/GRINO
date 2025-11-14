import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from utils.database import get_clientes_detallados, create_cliente, update_cliente, delete_cliente
from utils.auth import check_login
from utils.database import (
    get_presupuestos_usuario, 
    get_presupuesto_detallado,
    get_clientes,
    get_lugares_trabajo,
    delete_presupuesto
)
from utils.pdf import (
    mostrar_boton_descarga_pdf
)
from utils.components import safe_numeric_value

st.set_page_config(page_title="Historial", page_icon="🌱", layout="wide")

def _show_presupuesto_detail(presupuesto_id: int, cliente_nombre: str, lugar_nombre: str):
    """Obtiene el detalle completo y lo muestra agrupado por categoría."""
    try:
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
    except Exception as e:
        st.error(f"Error al mostrar detalle del presupuesto: {str(e)}")

def main():
    st.title("🕒 Historial de Presupuestos")
    
    # ------------------- VALIDACIÓN DE ACCESO -------------------
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.error("🔐 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Volver al inicio")
        st.stop()
    
    # ========== DIAGNÓSTICO ==========
    with st.expander("🔧 Diagnóstico (Click para ver)", expanded=False):
        st.write("**Información de sesión:**")
        st.json({
            'user_id': st.session_state.get('user_id'),
            'user_email': st.session_state.get('user_email')
        })
        
        # Probar la carga de datos básicos
        try:
            clientes_test = get_clientes()
            lugares_test = get_lugares_trabajo()
            st.success(f"✅ Clientes cargados: {len(clientes_test)}")
            st.success(f"✅ Lugares cargados: {len(lugares_test)}")
        except Exception as e:
            st.error(f"❌ Error cargando datos básicos: {e}")
    
    # ========== FILTROS ==========
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        try:
            clientes = get_clientes()
            lugares = get_lugares_trabajo()
            
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
                    index=3  # Por defecto "Todos"
                )
                
        except Exception as e:
            st.error(f"Error al cargar filtros: {str(e)}")
            return
    
    # ========== APLICAR FILTROS ==========
    filtros = {}
    if cliente_filtro:
        filtros['cliente_id'] = cliente_filtro
    if lugar_filtro:
        filtros['lugar_trabajo_id'] = lugar_filtro
    
    if fecha_filtro == "Últimos 7 días":
        filtros['fecha_inicio'] = datetime.now() - timedelta(days=7)
    elif fecha_filtro == "Últimos 30 días":
        filtros['fecha_inicio'] = datetime.now() - timedelta(days=30)
    elif fecha_filtro == "Últimos 90 días":
        filtros['fecha_inicio'] = datetime.now() - timedelta(days=90)
    
    # ========== CARGAR PRESUPUESTOS ==========
    try:
        st.write("🔄 Cargando presupuestos...")
        presupuestos = get_presupuestos_usuario(st.session_state.user_id, filtros)
        
        # Diagnóstico de los resultados
        with st.expander("🔧 Ver datos crudos de presupuestos", expanded=False):
            if presupuestos:
                st.write(f"Se encontraron {len(presupuestos)} presupuestos")
                st.json(presupuestos[:2])  # Mostrar solo los primeros 2 para diagnóstico
            else:
                st.write("No se encontraron presupuestos")
                
    except Exception as e:
        st.error(f"❌ Error al obtener presupuestos: {str(e)}")
        
        # Diagnóstico extendido
        with st.expander("🔧 Diagnóstico detallado del error"):
            st.exception(e)
        return
    
    if not presupuestos:
        st.info("""
        🔍 No se encontraron presupuestos con los filtros seleccionados.
        
        **Posibles causas:**
        - No has creado presupuestos aún
        - Los filtros aplicados son muy restrictivos
        - Hay un problema de permisos en la base de datos
        """)
        
        # Botón para crear nuevo presupuesto
        if st.button("📋 Crear mi primer presupuesto"):
            st.switch_page("pages/1_📋_generar_presupuesto.py")
        return
    
    # ========== MOSTRAR PRESUPUESTOS ==========
    # Resumen estadístico
    suma_total = sum(safe_numeric_value(p.get('total', 0)) for p in presupuestos)
    total_presupuestos = len(presupuestos)
    avg_total = suma_total / total_presupuestos if total_presupuestos else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Presupuestos", f"{total_presupuestos}")
    with col2:
        st.metric("Suma Total", f"${suma_total:,.0f}")
    with col3:
        st.metric("Promedio", f"${avg_total:,.0f}")
    
    st.subheader("📋 Lista de Presupuestos")

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
    for i, p in enumerate(presupuestos):
        # Usamos safe_numeric_value para el display del total
        total_display = safe_numeric_value(p.get('total', 0))
        
        with st.container(border=True):
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1, 3])

            # Datos - con manejo de errores para cada campo
            try:
                cliente_nombre = p.get('cliente', {}).get('nombre', 'N/A')
                col1.write(cliente_nombre.title() if cliente_nombre else 'N/A')
            except:
                col1.write('Error')
                
            try:
                lugar_nombre = p.get('lugar', {}).get('nombre', 'N/A')
                col2.write(lugar_nombre.title() if lugar_nombre else 'N/A')
            except:
                col2.write('Error')
                
            try:
                fecha = p.get('fecha', datetime.now())
                if isinstance(fecha, str):
                    col3.write(fecha)
                else:
                    col3.write(fecha.strftime('%Y-%m-%d'))
            except:
                col3.write('Error')
                
            col4.write(f"**${total_display:,.2f}**")
            col5.write(str(p.get('num_items', 0)))

            # Acciones
            with col6:
                b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
                
                # Clave de estado para el toggle del expander
                state_key = f"expander_toggle_{p['id']}"
                if state_key not in st.session_state:
                    st.session_state[state_key] = False

                with b1: # BOTÓN EDITAR
                    if st.button("✏️", key=f"edit_{p['id']}", help="Editar"):
                        st.session_state['presupuesto_a_editar_id'] = p['id'] 
                        st.switch_page("pages/3_✏️_editar.py")

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
                
                with b3: # BOTÓN VISTA PREVIA
                    if st.button("👁️", key=f"view_{p['id']}", help="Ver Presupuesto"):
                        st.session_state[state_key] = not st.session_state[state_key]
                        st.rerun()

                with b4: # BOTÓN ELIMINAR
                    if st.button("🗑️", key=f"del_{p['id']}", help="Eliminar"):
                        if delete_presupuesto(p['id'], st.session_state.user_id):
                            st.success("Presupuesto eliminado correctamente")
                            st.rerun()
                        else:
                            st.error("No se pudo eliminar el presupuesto.")
            
            # LÓGICA DEL EXPANDER
            if st.session_state.get(state_key, False):
                with st.expander(f"Detalle Presupuesto ID: {p['id']}", expanded=True):
                    _show_presupuesto_detail(
                        presupuesto_id=p['id'],
                        cliente_nombre=cliente_nombre,
                        lugar_nombre=lugar_nombre
                    )

# Verificación de login
is_logged_in = check_login()

if __name__ == "__main__":
    if is_logged_in:
        main()
    else:
        st.error("🔒 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Ir a página de inicio")