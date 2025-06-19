from typing import Any, Dict
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

def calcular_total(items_data: Dict[str, Any]) -> float:
    """Calcula el total general del presupuesto"""
    total = 0
    for categoria, data in items_data.items():
        # Sumar items
        total += sum(item['total'] for item in data['items'])
        # Sumar mano de obra si existe
        total += data.get('mano_obra', 0)
    return total

def main():
    st.title("📋 Generar Nuevo Presupuesto")

    # Verificar autenticación
    if 'user_id' not in st.session_state:
        st.error("🔐 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Volver al inicio")
        st.stop()

    st.subheader("Datos del Cliente", divider="blue")
    with st.status("Selección de cliente y lugar", expanded=True) as status:
        cliente_id, cliente_nombre, lugar_id, lugar_nombre = show_cliente_lugar_selector()
        if cliente_id and lugar_id:
            status.update(label="✅ Completado", state="complete", expanded=False)

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

    # Campo para descripción/notas
    descripcion = st.text_area("Descripción / Notas del presupuesto:", height=100)

    # Paso 5: Guardar
    if st.button("📂 Guardar Presupuesto Completo", type="primary",
                help="Revise todos los datos antes de guardar"):

        with st.spinner("Guardando presupuesto..."):
            try:
                # Calcular total
                total = calcular_total(items_data)
                
                # Crear presupuesto
                presupuesto_id = create_presupuesto(
                    cliente_id=cliente_id,
                    lugar_id=lugar_id,
                    descripcion=descripcion,
                    total=total,
                    user_id=st.session_state.user_id
                )

                if not presupuesto_id:
                    st.error("Error al crear el presupuesto")
                    st.stop()

                # Guardar items
                if not save_presupuesto_completo(presupuesto_id, items_data):
                    st.error("Error al guardar los items del presupuesto")
                    st.stop()

                # Generar PDF
                pdf_path = generar_pdf(cliente_nombre, items_data, lugar_nombre)
                
                # Mostrar éxito y opciones
                st.toast(f"Presupuesto #{presupuesto_id} guardado!", icon="✅")
                st.success("""
                Presupuesto guardado correctamente. 
                ¿Qué deseas hacer ahora?
                """)

                # Botón para descargar PDF
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "📄 Descargar PDF", 
                        f, 
                        file_name=f"presupuesto_{presupuesto_id}.pdf", 
                        mime="application/pdf"
                    )

                cols = st.columns(3)
                with cols[0]:
                    if st.button("🔄 Crear otro presupuesto"):
                        # Limpiar solo los datos del presupuesto, mantener sesión
                        if 'categorias' in st.session_state:
                            del st.session_state['categorias']
                        st.rerun()
                with cols[1]:
                    st.page_link("pages/2_🕒_historial.py", label="📋 Ver Presupuestos")
                with cols[2]:
                    st.page_link("App_principal.py", label="🏠 Ir al Inicio")

            except Exception as e:
                st.error(f"Error al guardar: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    main()