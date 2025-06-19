import streamlit as st
from utils.database import (
    get_presupuestos_usuario, 
    get_presupuesto_detallado,
    get_clientes,
    get_lugares_trabajo
)
from utils.auth import require_login
from utils.pdf import mostrar_boton_descarga_pdf
from datetime import datetime, timedelta
import pandas as pd

require_login()

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
    total_presupuestos = len(presupuestos)
    suma_total = sum(p['total'] for p in presupuestos)
    avg_total = suma_total / total_presupuestos if total_presupuestos > 0 else 0
    
    st.metric("📊 Resumen", 
              f"{total_presupuestos} presupuestos", 
              f"Total: ${suma_total:,.2f} | Promedio: ${avg_total:,.2f}")
    
    # Mostrar presupuestos en cuadrícula
    st.subheader("📋 Presupuestos Generados")
    
    cols = st.columns(3)  
    
    for i, p in enumerate(presupuestos):
        with cols[i % 3]:
            with st.container(border=True):
                # Encabezado
                st.markdown(f"### {p['cliente']['nombre']}")
                st.caption(f"📅 {p['fecha'].strftime('%Y-%m-%d')}")
                
                # Detalles básicos
                st.write(f"**Lugar:** {p['lugar']['nombre']}")
                st.write(f"**Total:** ${p['total']:,.2f}")
                st.write(f"**Items:** {p.get('num_items', 0)}")
                
                # Botones de acción
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔍 Detalles", key=f"det_{p['id']}"):
                        st.session_state['presupuesto_detalle'] = p['id']
                        st.rerun()
                
                with col2:
                    try:
                        pdf_html, success = mostrar_boton_descarga_pdf(p['id'])
                        if success:
                            st.markdown(pdf_html, unsafe_allow_html=True)
                        else:
                            st.error(pdf_html) 
                    except Exception as e:
                        st.error(f"Error inesperado al generar PDF: {str(e)}")

    if 'presupuesto_detalle' in st.session_state:
        st.divider()
        st.subheader("📋 Detalles del Presupuesto")
        
        try:
            detalle = get_presupuesto_detallado(st.session_state['presupuesto_detalle'])
            if not detalle:
                st.error("No se encontraron detalles del presupuesto")
                del st.session_state['presupuesto_detalle']
                st.rerun()
            
            if st.button("✖️ Cerrar detalles"):
                del st.session_state['presupuesto_detalle']
                st.rerun()
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Cliente:** {detalle['cliente']['nombre']}")
                st.markdown(f"**Lugar:** {detalle['lugar']['nombre']}")
                st.markdown(f"**Fecha:** {detalle['fecha'].strftime('%Y-%m-%d %H:%M')}")
            
            with col2:
                st.metric("Total", f"${detalle['total']:,.2f}")
            
            categorias = {}
            for item in detalle['items']:
                cat = item.get('categoria', 'Sin categoría') or 'Sin categoría'
                if cat not in categorias:
                    categorias[cat] = []
                categorias[cat].append(item)
            
            for categoria, items in categorias.items():
                with st.expander(f"📁 {categoria}", expanded=True):
                    df = pd.DataFrame(items)
                    df['P. Unitario'] = df['precio_unitario'].apply(lambda x: f"${x:,.2f}")
                    df['Total'] = df['total'].apply(lambda x: f"${x:,.2f}")
                    
                    st.dataframe(
                        df[['nombre', 'unidad', 'cantidad', 'P. Unitario', 'Total']],
                        column_config={
                            'nombre': 'Descripción',
                            'unidad': 'Unidad',
                            'cantidad': 'Cantidad'
                        },
                        hide_index=True,
                        use_container_width=True
                    )
            
            try:
                pdf_html, success = mostrar_boton_descarga_pdf(detalle['id'])
                if success:
                    st.markdown(pdf_html, unsafe_allow_html=True)
                else:
                    st.error(pdf_html) 
            except Exception as e:
                st.error(f"Error inesperado al generar PDF: {str(e)}")
                
        except Exception as e:
            st.error(f"Error al cargar detalles: {str(e)}")
            del st.session_state['presupuesto_detalle']
            st.rerun()

if __name__ == "__main__":
    if 'user_id' in st.session_state and st.session_state.user_id:
        main()
    else:
        st.error("🔒 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Ir a página de inicio")