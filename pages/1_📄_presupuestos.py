from typing import Any, Dict
import streamlit as st
import os
from utils.pdf import generar_pdf
from utils.auth import check_login
from utils.components import (
    show_cliente_lugar_selector,
    show_items_presupuesto,
    show_mano_obra,
    show_resumen,
    safe_numeric_value
)
from utils.database import save_presupuesto_completo

st.set_page_config(page_title="GRINO", page_icon="🌱", layout="wide")

def calcular_total(items_data: Dict[str, Any]) -> float:
    """Calcula el total general del presupuesto, usando la utilidad de valores seguros."""
    total = 0
    if not items_data or not isinstance(items_data, dict):
        return 0
        
    for categoria, data in items_data.items():
        # Verificar que data tenga la estructura esperada
        if not isinstance(data, dict):
            continue
            
        # Sumar items (usando safe_numeric_value)
        items = data.get('items', [])
        if isinstance(items, list):
            total += sum(safe_numeric_value(item.get('total', 0)) for item in items)
        total += safe_numeric_value(data.get('mano_obra', 0))
    return total
show_items_presupuesto()
def main():
    st.title("📋 Generar Nuevo Presupuesto")

    # Verificar autenticación
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.error("🔐 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Volver al inicio")
        st.stop()

    # ========== SECCIÓN CLIENTE, LUGAR y TRABAJO A REALIZAR ==========
    st.subheader("Datos del Cliente", divider="blue")
    cliente_id, cliente_nombre, lugar_id, lugar_nombre, descripcion = show_cliente_lugar_selector()
    st.session_state.descripcion = descripcion

    # Inicialización segura de la estructura de categorías si no existe
    #if 'categorias' not in st.session_state:
        #st.session_state['categorias'] = {'general': {'items': [], 'mano_obra': 0.0}}
        
    # ========== SECCIÓN ITEMS ==========
    st.subheader("Datos del Presupuesto", divider="blue")
    items_data = show_items_presupuesto()

    if not items_data or all(len(cat['items']) == 0 for cat in items_data.values()):
        st.warning("⚠️ Agrega al menos un ítem al presupuesto")
        st.stop()

     # ========== SECCIÓN MANO DE OBRA ==========
    st.subheader("🛠️ Mano de obra", divider="blue")
    show_mano_obra(items_data)

    # ========== SECCIÓN RESUMEN ==========
    st.subheader("🧮 Vista previa", divider="blue")
    show_resumen(items_data)

    # ========== GUARDADO ==========
    
    if st.button("📂 Guardar Presupuesto Completo", type="primary",
                help="Revise todos los datos antes de guardar"):

        with st.spinner("Guardando presupuesto..."):
            try:
                # Calcular total
                total = calcular_total(items_data)
                
                # Crear presupuesto
                presupuesto_id = save_presupuesto_completo(
                cliente_id=cliente_id,
                lugar_id=lugar_id,
                descripcion=descripcion or "Sin descripción",
                total=total,
                user_id=st.session_state.user_id
                )


                if not presupuesto_id:
                    st.error("Error al crear el presupuesto")
                    st.stop()
    
                if not save_presupuesto_completo(presupuesto_id, items_data):
                    st.error("Error al guardar los items del presupuesto")
                    st.stop()

                # Generar PDF
                pdf_path = generar_pdf(cliente_nombre, items_data, lugar_nombre, descripcion=descripcion)
                
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
# Verificación de login y ejecución principal
is_logged_in = check_login()

if __name__ == "__main__":
    if is_logged_in:
        main()
    else:
        st.error("🔒 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Ir a página de inicio")