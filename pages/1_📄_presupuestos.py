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
    total = 0.0
    # Verificar que items_data no sea None y sea un diccionario
    if not items_data or not isinstance(items_data, dict):
        return 0.0
        
    for categoria, data in items_data.items():
        # Verificar que data tenga la estructura esperada
        if not isinstance(data, dict):
            continue
            
        # Sumar items (usando safe_numeric_value)
        items = data.get('items', [])
        if isinstance(items, list):
            total += sum(safe_numeric_value(item.get('total', 0)) for item in items)
        
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
    # Calcular total general de forma segura
    categorias = st.session_state.get('categorias', {})
    total_general = calcular_total(categorias)
    
    st.markdown("---")
    
    if total_general > 0:
        # Mostrar el resumen - asumiendo que show_resumen() muestra la información
        resumen_total_display = show_resumen()  
    else:
        st.info("El presupuesto actual está vacío. Agregue items y/o mano de obra para continuar.")
        resumen_total_display = 0.0
    
    st.markdown("---")
    
    # Botón de Guardar
    if st.button("💾 Guardar y Generar Presupuesto", type="primary", use_container_width=True):
        # 1. Validación completa
        validation_errors = []
        
        if not cliente_id:
            validation_errors.append("Seleccione un Cliente")
        if not lugar_id:
            validation_errors.append("Seleccione un Lugar de Trabajo")
        if total_general <= 0:
            validation_errors.append("El total del presupuesto debe ser mayor a cero")
        if not categorias or all(len(data.get('items', [])) == 0 and data.get('mano_obra', 0) <= 0 
                               for data in categorias.values()):
            validation_errors.append("Agregue al menos un item o mano de obra al presupuesto")
        
        if validation_errors:
            st.error("⚠️ " + ", ".join(validation_errors))
            return
        
        try:
            # 2. Guardar en Supabase
            with st.spinner("Guardando presupuesto..."):
                presupuesto_id = save_presupuesto_completo(
                    user_id=st.session_state.user_id,
                    cliente_id=cliente_id,
                    lugar_id=lugar_id,
                    descripcion=descripcion or "Sin descripción",
                    items_data=categorias,
                    total_general=total_general
                )

            if not presupuesto_id:
                st.error("❌ Error al guardar el presupuesto en la base de datos.")
                return

            # 3. Generar PDF
            with st.spinner("Generando PDF..."):
                pdf_path = generar_pdf(
                    cliente_nombre, 
                    categorias, 
                    lugar_nombre, 
                    descripcion=descripcion or "Sin descripción"
                )
                
            if not pdf_path or not os.path.exists(pdf_path):
                st.error("❌ Falló la generación del archivo PDF.")
                # Aún así mostramos éxito en el guardado
                st.success(f"Presupuesto guardado correctamente (ID: {presupuesto_id}), pero hubo un error con el PDF.")
            else:
                # 4. Mostrar éxito y opciones
                st.toast(f"Presupuesto #{presupuesto_id} guardado!", icon="✅")
                st.success(f"Presupuesto guardado correctamente (ID: {presupuesto_id}).")

                # 5. Botón para descargar PDF
                with open(pdf_path, "rb") as f:
                    # Formatear nombre del archivo de forma más segura
                    lugar_nombre_limpio = "".join(c for c in lugar_nombre if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    lugar_nombre_limpio = lugar_nombre_limpio.replace(" ", "_")
                    file_name = f"Presupuesto_{lugar_nombre_limpio}_{presupuesto_id}.pdf"
                    
                    st.download_button(
                        "📄 Descargar PDF", 
                        f.read(),  # Leer el contenido completo
                        file_name=file_name, 
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"download_{presupuesto_id}"
                    )
                
                # 6. Eliminar archivo temporal después de ofrecer la descarga
                try:
                    os.unlink(pdf_path)
                except Exception as e:
                    # Solo mostrar warning en consola, no interrumpir flujo
                    st.warning(f"No se pudo eliminar el archivo temporal: {e}")

            # 7. Opciones de navegación (mostrar siempre, incluso si falló el PDF)
            st.markdown("---")
            st.subheader("¿Qué desea hacer ahora?")
            
            cols = st.columns(3)
            with cols[0]:
                if st.button("🔄 Crear otro presupuesto", use_container_width=True):
                    # Limpiar estado para nuevo presupuesto
                    if 'categorias' in st.session_state:
                        del st.session_state['categorias']
                    st.rerun()
            with cols[1]:
                st.page_link("pages/2_🕒_historial.py", label="📋 Ver Presupuestos", icon="📋")
            with cols[2]:
                st.page_link("App_principal.py", label="🏠 Ir al Inicio", icon="🏠")

        except Exception as e:
            st.error(f"❌ Error inesperado al guardar el presupuesto: {str(e)}")
            # Opcional: mostrar más detalles en modo debug
            if st.session_state.get('debug', False):
                st.exception(e)

# Verificación de login y ejecución principal
is_logged_in = check_login()

if __name__ == "__main__":
    if is_logged_in:
        main()
    else:
        st.error("🔒 Por favor inicie sesión primero")
        st.page_link("App_principal.py", label="Ir a página de inicio")