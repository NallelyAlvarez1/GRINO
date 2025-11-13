from typing import Any, Dict
import streamlit as st
import os # Necesario para eliminar archivo temporal
from utils.pdf import generar_pdf
from utils.auth import check_login
from utils.components import (\
    show_cliente_lugar_selector,\
    show_items_presupuesto,\
    show_mano_obra,\
    show_resumen,\
    safe_numeric_value # Importamos la utilidad de safe_numeric
)
from utils.database import (\
    save_presupuesto_completo
)

st.set_page_config(page_title="GRINO", page_icon="🌱", layout="wide")

def calcular_total(items_data: Dict[str, Any]) -> float:
    """Calcula el total general del presupuesto, usando la utilidad de valores seguros."""
    total = 0.0
    for categoria, data in items_data.items():
        # Sumar items (usando safe_numeric_value)
        total += sum(safe_numeric_value(item['total']) for item in data['items'])
        # Sumar mano de obra (usando safe_numeric_value)
        total += safe_numeric_value(data.get('mano_obra', 0.0))
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
    cliente_id, cliente_nombre, lugar_id, lugar_nombre, descripcion = show_cliente_lugar_selector()

    # Inicialización segura de la estructura de categorías si no existe
    if 'categorias' not in st.session_state:
        st.session_state['categorias'] = {'general': {'items': [], 'mano_obra': 0.0}}
        
    # ========== SECCIÓN ITEMS Y MANO DE OBRA ==========
    show_items_presupuesto()
    show_mano_obra()
    
    # ========== SECCIÓN RESUMEN Y ACCIÓN ==========
    total_general = calcular_total(st.session_state.get('categorias', {}))
    st.markdown("---")
    
    if total_general > 0:
        resumen_total_display = show_resumen() # Muestra el resumen
    else:
        st.info("El presupuesto actual está vacío.")
        resumen_total_display = 0.0
    
    st.markdown("---")
    
    # Botón de Guardar
    if st.button("💾 Guardar y Generar Presupuesto", type="primary", use_container_width=True):
        # 1. Validación
        if not cliente_id or not lugar_id:
            st.error("⚠️ Por favor, seleccione un Cliente y un Lugar de Trabajo.")
        elif total_general <= 0:
            st.error("⚠️ El total del presupuesto debe ser mayor a cero.")
        else:
            try:
                # 2. Guardar en Supabase
                presupuesto_id = save_presupuesto_completo(
                    user_id=st.session_state.user_id,
                    cliente_id=cliente_id,
                    lugar_id=lugar_id,
                    descripcion=descripcion,
                    items_data=st.session_state['categorias'],
                    total_general=total_general
                )

                if not presupuesto_id:
                    st.error("❌ Error al guardar el presupuesto en la base de datos.")
                    st.stop()

                # 3. Preparar la estructura de categorías para el PDF (usa la misma estructura)
                items_data = st.session_state['categorias']

                # 4. Generar PDF (generar_pdf devuelve el path del archivo temporal)
                # Nota: generar_pdf ahora maneja mejor la estructura de items_data
                pdf_path = generar_pdf(cliente_nombre, items_data, lugar_nombre, descripcion=descripcion)
                
                if not pdf_path:
                    st.error("❌ Falló la generación del archivo PDF.")
                    st.stop()
                    
                # 5. Mostrar éxito y opciones
                st.toast(f"Presupuesto #{presupuesto_id} guardado!", icon="✅")
                st.success(f"Presupuesto guardado correctamente (ID: {presupuesto_id}).")

                # 6. Botón para descargar PDF
                with open(pdf_path, "rb") as f:
                    # Formatear nombre del archivo
                    lugar_nombre_limpio = lugar_nombre.strip().replace(" ", "_").replace("/", "_")
                    file_name = f"Presupuesto_{lugar_nombre_limpio}_{presupuesto_id}.pdf"
                    
                    st.download_button(
                        "📄 Descargar PDF", 
                        f, 
                        file_name=file_name, 
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                # 7. Eliminar archivo temporal después de la descarga
                try:
                    os.unlink(pdf_path)
                except Exception as e:
                    print(f"Advertencia: No se pudo eliminar el archivo temporal PDF: {e}")

                # 8. Opciones de navegación
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

is_logged_in = check_login()

if __name__ == "__main__":
    if is_logged_in:
        main()
    else:
        st.error("🔒 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Ir a página de inicio")