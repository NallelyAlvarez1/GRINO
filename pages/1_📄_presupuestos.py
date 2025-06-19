import streamlit as st
from datetime import datetime
from utils.components import (
    show_cliente_lugar_selector,
    show_items_presupuesto,
    show_mano_obra,
    show_resumen
)
from utils.database import (
    create_presupuesto,
    save_presupuesto_completo
)
from utils.pdf import generar_pdf


def main():
    st.title("📋 Generar Nuevo Presupuesto")

    st.subheader("Datos del Cliente", divider="blue")
    with st.status("Selección de cliente y lugar", expanded=True) as status:
        cliente_id, cliente_nombre, lugar_id, lugar_nombre = show_cliente_lugar_selector()
        if cliente_id and lugar_id:
            status.update(label="✅Completado", state="complete", expanded=False)

    if not (cliente_id and lugar_id):
        st.stop()

    # Paso 2: Agregar items
    st.subheader("Datos del Presupuesto", divider="blue")
    items_data = show_items_presupuesto()

    if not items_data or all(len(cat['items']) == 0 for cat in items_data.values()):
        st.warning("⚠️ Agrega al menos un ítem al presupuesto")
        st.stop()

    # Paso 3: Mano de obra
    st.subheader("🛠️ Mano de obra", divider="blue")
    show_mano_obra(items_data)

    # Paso 4: Resumen
    st.subheader("🧮 Vista previa", divider="blue")
    show_resumen(items_data)

    # Paso 5: Guardar
    if st.button("📂 Guardar Presupuesto Completo", type="primary",
                help="Revise todos los datos antes de guardar"):

        with st.spinner("Guardando presupuesto..."):
            try:
                presupuesto_id = create_presupuesto(
                    cliente_id=cliente_id,
                    lugar_id=lugar_id,
                    fecha=datetime.now(),  # o la fecha que uses
                    descripcion="",
                    total=0,
                    detalles=[]
                )


                save_presupuesto_completo(presupuesto_id, items_data)

                pdf_path = generar_pdf(cliente_nombre, items_data, lugar_nombre)
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "📄 Descargar PDF", f, file_name="presupuesto.pdf", mime="application/pdf")

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
                    st.page_link("App_principal.py", label="📋 Ver Presupuestos")
                with cols[2]:
                    st.page_link("App_principal.py", label="🏠 Ir al Inicio")

            except Exception as e:
                st.error(f"Error al guardar: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    if 'user_id' in st.session_state:
        main()
    else:
        st.error("🔐 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Volver al inicio")