import streamlit as st

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
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Any

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
            categorias_agrupadas[cat] = {'items': [], 'mano_obra': 0}
        
        # Lógica para separar Mano de Obra (asumiendo que tiene ese nombre)
        if 'mano de obra' in item.get('nombre', '').lower():
             # Sumamos al total de mano de obra
            categorias_agrupadas[cat]['mano_obra'] += int(round(item.get('total', 0))) 
        else:
            categorias_agrupadas[cat]['items'].append(item)


    # 2. Mostrar la vista previa agrupada por categoría
    for cat, data in categorias_agrupadas.items():
        items = data['items']
        mano_obra = data.get('mano_obra', 0)
        
        if items or mano_obra > 0:
            total_categoria = sum(int(round(item.get('total', 0))) for item in items) + mano_obra
            total_general += total_categoria

            st.markdown(f"**🔹 {cat}**")
            
            if items:
                df_items = pd.DataFrame(items)

                for col in ['cantidad', 'precio_unitario', 'total']:
                    df_items[col] = df_items[col].apply(lambda x: int(round(x)) if x is not None else 0) 

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
                    # Usamos st.metric o st.markdown según tu preferencia de estilo
                    st.markdown(f"**Mano de obra {cat}:** **${mano_obra:,.0f}**")

            # El total de la categoría siempre se muestra
            with col_total:
                st.markdown(f"**Total {cat}:** **${total_categoria:,.0f}**") 
                
            st.divider()
    st.markdown(f"#### 💵 **Total General del Presupuesto:** **${total_general:,.0f}**")




def main():
    st.title("🕒 Historial de Presupuestos")
    try:
        clientes = get_clientes()
        lugares = get_lugares_trabajo()
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        st.stop()

    with st.expander("🔍 Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cliente_filtro = st.selectbox(
                "Filtrar por cliente:",
                options=[None] + [c[0] for c in clientes],
                format_func=lambda x: next((n for i, n in clientes if i == x), "Todos los clientes")
            )
        
        with col2:
            lugar_filtro = st.selectbox(
                "Filtrar por lugar:",
                options=[None] + [l[0] for l in lugares],
                format_func=lambda x: next((n for i, n in lugares if i == x), "Todos los lugares")
            )
        
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
        presupuestos = get_presupuestos_usuario(st.session_state.user_id, filtros)
    except Exception as e:
        st.error(f"Error al obtener presupuestos: {str(e)}")
        st.stop()
    
    if not presupuestos:
        st.info("🔍 No se encontraron presupuestos con los filtros seleccionados")
        return
    
    # Mostrar resumen estadístico
    suma_total = sum(int(round(p['total'])) for p in presupuestos)
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
        with st.container(border=True):
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1, 3])

            # Datos
            col1.write(p['cliente']['nombre'].title())
            col2.write(p['lugar']['nombre'].title())
            col3.write(p['fecha'].strftime('%Y-%m-%d'))
            col4.write(f"**${p['total']:,.2f}**")
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
                        st.session_state['presupuesto_a_editar_id'] = p['id'] 
                        st.switch_page("pages/_✏️ Editar.py")

                with b2: # BOTÓN DESCARGA
                    try:
                        pdf_bytes, file_name, success = mostrar_boton_descarga_pdf(p['id'])
                        if success:
                            st.download_button(
                                label="⬇️",
                                data=pdf_bytes,
                                file_name=file_name,
                                mime="application/pdf",
                                key=f"down_{p['id']}",
                                help="Descargar PDF"
                            )
                    except:
                        pass
                
                with b3: # BOTÓN VISTA PREVIA (TOGGLE EXPANDER)
                    # El botón toggles el estado
                    if st.button("📑", key=f"view_{p['id']}", help="Ver Presupuesto"):
                        st.session_state[state_key] = not st.session_state[state_key]
                        st.rerun() # Necesario para abrir/cerrar inmediatamente

                with b4: # BOTÓN ELIMINAR
                    if st.button("🗑️", key=f"del_{p['id']}", help="Eliminar"):
                        if delete_presupuesto(p['id'], st.session_state.user_id):
                            st.success("Presupuesto eliminado correctamente")
                            st.rerun()
                        else:
                            st.error("No se pudo eliminar el presupuesto")
            
            # LÓGICA DEL EXPANDER (Fuera de las columnas, dentro del contenedor de la fila)
            if st.session_state.get(state_key, False):
                with st.expander(f"Detalle Presupuesto ID: {p['id']}", expanded=True):
                    _show_presupuesto_detail(
                        presupuesto_id=p['id'],
                        cliente_nombre=p['cliente']['nombre'],
                        lugar_nombre=p['lugar']['nombre']
                    )

if __name__ == "__main__":
    if 'user_id' in st.session_state and st.session_state.user_id:
        main()
    else:
        st.error("🔒 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Ir a página de inicio")