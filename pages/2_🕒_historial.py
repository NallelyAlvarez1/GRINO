import streamlit as st
from utils.database import get_presupuestos_usuario, get_presupuesto_detallado
from utils.auth import require_login
from utils.pdf import generar_pdf, get_pdf_bytes

require_login()

def main():
    st.title("🕒 Historial de Presupuestos")
    
    # Obtener presupuestos del usuario con filtros básicos
    presupuestos = get_presupuestos_usuario(st.session_state.user_id)
    
    if presupuestos:
        for p in presupuestos:
            with st.expander(f"📌 {p['cliente']['nombre']} - {p['fecha'].strftime('%Y-%m-%d')}"):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**Lugar:** {p['lugar']['nombre']}")
                    st.write(f"**Total:** ${p['total']:,.2f}")
                    st.write(f"**Items:** {p.get('num_items', 0)}")
                
                with col2:
                    if st.button("🔍 Detalles", key=f"det_{p['id']}"):
                        st.session_state['presupuesto_detalle'] = p['id']
                
                with col3:
                    # Asumiendo que tienes una función para generar PDF
                    if st.button("⬇️ PDF", key=f"pdf_{p['id']}"):
                        generar_pdf(p['id'])  # Implementar esta función

        # Mostrar detalles si se seleccionó un presupuesto
        if 'presupuesto_detalle' in st.session_state:
            detalle = get_presupuesto_detallado(st.session_state['presupuesto_detalle'])
            if detalle:
                with st.expander("📋 Detalles completos", expanded=True):
                    st.write(f"**Cliente:** {detalle['cliente']['nombre']}")
                    st.write(f"**Lugar:** {detalle['lugar']['nombre']}")
                    st.write(f"**Fecha:** {detalle['fecha'].strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Total:** ${detalle['total']:,.2f}")
                    
                    for item in detalle['items']:
                        st.write(f"- {item['nombre']} ({item['cantidad']} {item['unidad']} @ ${item['precio_unitario']:,.2f} = ${item['total']:,.2f}")
    else:
        st.info("🔍 No se han creado presupuestos todavía.")

if 'user_id' in st.session_state and st.session_state.user_id:
    main()
else:
    st.error("🔒 Por favor inicie sesión primero")
    st.page_link("login.py", label="Ir a página de login")