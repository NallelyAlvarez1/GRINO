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

def main():
    st.title("📋 Generar Nuevo Presupuesto")

    # Verificar autenticación
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.error("🔐 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Volver al inicio")
        st.stop()

    # ========== SECCIÓN CLIENTE, LUGAR y TRABAJO A REALIZAR ==========
    st.subheader("Datos del Cliente", divider="blue")
    cliente_id, cliente_nombre, lugar_trabajo_id, lugar_nombre, descripcion = show_cliente_lugar_selector()
    st.session_state.descripcion = descripcion

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
    total_general = calcular_total(items_data)

    # 🚨 AÑADIR ESTE PRINT PARA DEPURAR 🚨
        # 🚨 MEJOR DEPURACIÓN 🚨
    import json
    st.subheader("🔍 Depuración - items_data")
    
    # Verificar IDs de categorías
    for cat_nombre, cat_data in items_data.items():
        has_id = 'categoria_id' in cat_data and cat_data['categoria_id'] is not None
        status = "✅" if has_id else "❌"
        st.write(f"{status} {cat_nombre}: ID = {cat_data.get('categoria_id', 'MISSING')}")
    
    st.code(json.dumps(items_data, indent=2, ensure_ascii=False))
    # -------------------------------------
    # 🚨 DEPURACIÓN: Mostrar el estado de las categorías en la sesión
    st.subheader("🔍 Depuración - st.session_state['categorias']")
    st.write(st.session_state['categorias'])
    
    if st.button("📂 Guardar Presupuesto Completo", ...):
    
        with st.spinner("Guardando presupuesto..."):
            try:
                presupuesto_id = save_presupuesto_completo(
                    user_id=st.session_state.user_id,
                    cliente_id=cliente_id,
                    lugar_trabajo_id=lugar_trabajo_id,
                    descripcion=descripcion,
                    items_data=items_data,
                    total=total_general
                )

                if presupuesto_id:

                    # VALIDACIÓN DE items_data
                    if not isinstance(items_data, dict):
                        st.error("Error interno: los datos de ítems no son válidos.")
                        st.stop()

                    # Generar PDF
 # Llama a la función generar_pdf con los nombres de argumento correctos
                    pdf_path = generar_pdf(
                        cliente_nombre=cliente_nombre,      # ¡CORREGIDO!
                        categorias=items_data,
                        lugar_cliente=lugar_nombre,         # ¡CORREGIDO!
                        descripcion=descripcion
                    )

                    # VALIDACIÓN DE RUTA PDF
                    if not pdf_path or not os.path.exists(pdf_path):
                        st.error("Error generando PDF: archivo no creado.")
                        st.stop()

                    st.toast(f"Presupuesto #{presupuesto_id} guardado!", icon="✅")
                    st.success("Presupuesto guardado correctamente. ¿Qué deseas hacer ahora?")

                    # Botón de descarga PDF
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
                            st.session_state.pop('categorias', None)
                            st.rerun()
                    with cols[1]:
                        st.page_link("pages/2_🕒_historial.py", "📋 Ver Presupuestos")
                    with cols[2]:
                        st.page_link("App_principal.py", "🏠 Ir al Inicio")

                else:
                    st.error("Error al crear el presupuesto")

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