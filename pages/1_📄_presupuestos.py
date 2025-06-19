import streamlit as st
from utils.components import show_cliente_lugar_selector, show_items_presupuesto, show_mano_obra, show_resumen
from utils.database import create_presupuesto, save_presupuesto_completo
from datetime import datetime

def main():
    st.title("📋 Generar Nuevo Presupuesto")
    
    st.subheader("Datos del Cliente", divider="blue")
    with st.status("Selección de cliente y lugar", expanded=True) as status:
        cliente_id, lugar_id = show_cliente_lugar_selector()
        if cliente_id and lugar_id:
            status.update(label="✅Completado", state="complete", expanded=False)
    
    if not (cliente_id and lugar_id):
        st.stop()
    
    # Paso 2: Agregar items
    st.subheader("Datos del Presupuesto", divider="blue")
    items_data = show_items_presupuesto()
    
    # Validación básica de items
    if not items_data or all(len(cat['items']) == 0 for cat in items_data.values()):
        st.warning("⚠️ Agrega al menos un ítem al presupuesto")
        st.stop()
    
    # Paso 3: Mano de obra (ahora llamada desde components)
    st.subheader("🛠️ Mano de obra", divider="blue")
    show_mano_obra(items_data)

    st.subheader("🧮 Vista previa", divider="blue")
    show_resumen(items_data)
    
    # Paso 4: Detalles finales

    # Confirmación explícita antes de guardar
    if st.button("💾 Guardar Presupuesto Completo", type="primary", 
                help="Revise todos los datos antes de guardar"):
        
        with st.spinner("Guardando presupuesto..."):
            try:
                # Crear el presupuesto (cabecera)
                presupuesto_id = create_presupuesto(
                    cliente_id=cliente_id,
                    lugar_id=lugar_id,
                    user_id=st.session_state.user_id
                )
                
                # Guardar todos los items
                save_presupuesto_completo(presupuesto_id, items_data)
                
                st.toast(f"Presupuesto #{presupuesto_id} guardado!", icon="✅")
                st.success("""
                Presupuesto guardado correctamente. 
                ¿Qué deseas hacer ahora?
                """)
                
                cols = st.columns(3)
                with cols[0]:
                    if st.button("🔄 Crear otro presupuesto"):
                        st.session_state.clear()
                        st.rerun()
                with cols[1]:
                    st.page_link("App_principal.py", 
                                label="📋 Ver Presupuestos")
                with cols[2]:
                    st.page_link("App_principal.py", 
                                label="🏠 Ir al Inicio")
                
            except Exception as e:
                st.error(f"Error al guardar: {str(e)}")
                st.exception(e)  # Solo en desarrollo

if __name__ == "__main__":
    if 'user_id' in st.session_state:
        main()
    else:
        st.error("🔒 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Volver al inicio")