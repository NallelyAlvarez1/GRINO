import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional

# Importamos el cliente Supabase de la carpeta utils
# NOTA: Si el cliente está en utils/db.py, usa esta ruta:
from utils.db import get_supabase_client 
# Si tu archivo se llama 'supabase_client.py' y está en la raíz, 
# la importación original era correcta, pero es mejor usar utils.db

# 2. Obtener el cliente de Supabase (uso de caché)
try:
    supabase = get_supabase_client()
except Exception as e:
    st.error(f"Error al inicializar Supabase. Verifica la conexión. {e}")
    st.stop()


# ===============================================
# CONFIGURACIÓN Y REDIRECCIÓN DE SEGURIDAD
# ===============================================

st.set_page_config(page_title="NBooks", page_icon="📚", layout="wide")

# --- CSS para estilos mejorados de tarjetas ---
# Usamos un bloque de estilo para mejorar el aspecto de los elementos custom HTML
st.markdown("""
<style>
    /* Estilo para los títulos y autores en las tarjetas */
    .stMarkdown p {
        margin: 0 !important;
        padding: 0 !important;
    }
    /* Asegurar que las imágenes en popovers sean responsivas */
    .stPopover img {
        max-width: 100%;
        height: auto;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    /* Estilo para el contenedor de la tarjeta principal */
    .stContainer {
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 15px;
    }
</style>
""", unsafe_allow_html=True)


# --- Redirección si no hay usuario (Control de Seguridad) ---
# Usamos 'user_id' si se almacena después del login, o simplemente 'user'.
if "user" not in st.session_state or st.session_state.user is None:
    st.switch_page("pages/0_login.py")
    # st.stop() # Opcional, pero st.switch_page suele ser suficiente


# ===============================================
# ENCABEZADO Y CERRAR SESIÓN
# ===============================================

col1, col2 = st.columns([5,1])
with col1:
    st.title("📚 Bienvenido a NBooks")
with col2:
    st.markdown("")
    if st.button("Cerrar sesión", key="logout_btn"):
        # Limpiar el estado de sesión
        st.session_state.pop("user", None)
        # Puedes limpiar más datos de sesión aquí si es necesario
        st.switch_page("pages/0_login.py")

st.markdown("Explora tus libros registrados y gestiona su progreso de lectura.")


# ===============================================
# FUNCIONES AUXILIARES (DEFINICIÓN LIMPIA)
# ===============================================

def obtener_badge_estado(estado: str) -> str:
    """Retorna el markdown para el badge del estado de lectura."""
    estado_limpio = estado.strip().lower()
    color_map = {
        "leído": ("green", "check_circle"),
        "por leer": ("blue", "bookmark_add"),
        "en proceso": ("orange", "hourglass_top"),
        "no leído": ("gray", "visibility_off"),
        "abandonado": ("red", "cancel"),
    }
    color, icon = color_map.get(estado_limpio, ("gray", "help"))
    return f":{color}-badge[:material/{icon}: {estado.strip()}]"

@st.cache_data(show_spinner=False)
def get_book_data():
    """Carga los datos de los libros con caché para mejorar el rendimiento."""
    try:
        # Asumiendo que esta vista/tabla solo devuelve los libros del usuario logueado
        data = supabase.table("vista_libros").select("*").execute()
        return data.data or []
    except Exception as e:
        st.error(f"Error al cargar libros: {e}")
        return []

def actualizar_estado(libro_id: int, nuevo_estado: str):
    """Actualiza el estado de lectura de un libro y refresca la página."""
    try:
        if nuevo_estado:
            # Asegúrate de que estás usando el ID correcto para el filtro
            supabase.table("libros").update({"estado_lectura": nuevo_estado}).eq("id", libro_id).execute()
            st.success(f"Estado actualizado a '{nuevo_estado}'.")
            
            # Invalidar la caché para que se recarguen los datos
            get_book_data.clear() 
            st.rerun()
    except Exception as e:
        st.error(f"Fallo al actualizar el estado: {e}")

def get_unique_types(libros: List[Dict[str, Any]]) -> List[str]:
    """Extrae todos los tipos únicos para la lista de filtros."""
    tipos_unicos = set()
    for libro in libros:
        tipos_str = libro.get("tipos")
        if tipos_str:
            for tipo in tipos_str.split(','):
                tipo_limpio = tipo.strip()
                if tipo_limpio:
                    tipos_unicos.add(tipo_limpio)
    
    return ["Todos"] + sorted(list(tipos_unicos))


# ===============================================
# FILTROS Y PROCESAMIENTO
# ===============================================

# --- Cargar libros (usando la función caché) ---
libros = get_book_data()
tipos_disponibles = get_unique_types(libros)

# --- Controles de Filtro ---
col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1.5]) 

with col1:
    busqueda_filtro = st.text_input("🔍 Buscar (Título/Autor/Tipo)")

with col2:
    tipo_filtro = st.selectbox(
        "🏷️ Tipo",
        tipos_disponibles
    )

with col3:
    autor_filtro = st.text_input("👤 Autor")

with col4:
    estado_filtro = st.selectbox(
        "📖 Estado",
        ["Todos", "Leído", "Por leer", "En proceso", "No leído", "Abandonado"]
    )


# --- Aplicar filtros ---
libros_filtrados = []
busqueda_lower = busqueda_filtro.lower()

for libro in libros:
    # Obtener valores seguros y en minúsculas
    nombre_lower = (libro.get('nombre') or "").lower()
    autor_lower = (libro.get('autor') or "").lower()
    tipos_lower = (libro.get('tipos') or "").lower()
    estado_actual = libro.get('estado_lectura')
    
    # 1. Filtro de Búsqueda General (Título o Autor o Tipos)
    match_busqueda = busqueda_lower in nombre_lower or busqueda_lower in autor_lower or busqueda_lower in tipos_lower
    
    # 2. Filtro por Autor
    match_autor = autor_filtro.lower() in autor_lower
    
    # 3. Filtro por Tipo
    match_tipo = (
        tipo_filtro == "Todos" 
        or tipo_filtro.lower() in tipos_lower
    )
    
    # 4. Filtro por Estado
    match_estado = (
        estado_filtro == "Todos" 
        or estado_actual == estado_filtro
    )
    
    # Combinar todos los filtros
    if match_busqueda and match_autor and match_tipo and match_estado:
        libros_filtrados.append(libro)
        
st.divider()

# ===============================================
# RENDERIZADO DE LIBROS
# ===============================================

if not libros_filtrados:
    st.info("No hay libros que coincidan con los filtros.")
else:
    # RENDERIZADO EN FILAS DE 4
    for i in range(0, len(libros_filtrados), 4):
        cols = st.columns(4)
        for j, col in enumerate(cols):
            if i + j < len(libros_filtrados):
                libro = libros_filtrados[i + j]
                libro_id = libro['id']

                # Definición de la URL de la portada
                portada_url = (
                    f"https://osanryewvmaofxtfnzqk.supabase.co/storage/v1/object/public/"
                    f"portadas_libros/{libro['portada_path']}"
                ) if libro.get("portada_path") else "https://placehold.co/150x220/808080/FFFFFF?text=Sin+Portada"

                with col.container(border=True):
                    # --- Estructura de la Tarjeta ---
                    portada_col, datos_col = st.columns([1, 2]) 

                    with portada_col:
                        # Imagen de la portada (Tamaño ajustado para la tarjeta)
                        st.image(portada_url, width=70, use_column_width="auto") # Usamos st.image para manejo más fácil
                        
                    with datos_col:
                        # Título del libro (Usamos markdown con HTML para estilo)
                        st.markdown(
                            f"""
                            <p style='font-size: 16px; font-weight: bold; margin-bottom: 2px; line-height: 1.1;'>
                                {libro['nombre'] or 'Título Desconocido'}
                            </p>
                            <p style='font-size: 13px; font-style: italic; color: #666; margin-bottom: 5px;'>
                                por {libro['autor'] or 'Desconocido'}
                            </p>
                            """,
                            unsafe_allow_html=True
                        )

                        # Estado y Kindle
                        estado_col, kindle_col = st.columns([3, 2])

                        with estado_col:
                            badge_estado = obtener_badge_estado(libro['estado_lectura'])
                            st.markdown(badge_estado)

                        with kindle_col:
                            st.markdown(
                                f"""
                                <p style='padding-top: 5px; font-size: 12px; text-align: right; line-height: 1;'>
                                    Kindle {'✅' if libro.get('en_kindle') else '❌'}
                                </p>
                                """,
                                unsafe_allow_html=True,
                            )

                    # --- Modal (Pop-up) para Ver Detalles y Cambiar Estado ---
                    with st.popover("Ver Detalles", use_container_width=True):

                        pop_col1, pop_col2 = st.columns([2, 3]) 
                        
                        # --- Columna 1: Portada y Controles ---
                        with pop_col1:
                            # Portada Grande en el popover
                            st.image(portada_url, use_column_width=True)
                            
                            st.markdown("---")
                            
                            # Control para cambiar estado
                            nuevo_estado = st.selectbox(
                                "Cambiar estado", 
                                ["Leído", "Por leer", "En proceso", "No leído", "Abandonado"],
                                index=[
                                    "Leído", "Por leer", "En proceso", "No leído", "Abandonado"
                                ].index(libro["estado_lectura"]),
                                key=f"popover_estado_{libro_id}",
                                label_visibility="collapsed" # Ocultamos la etiqueta
                            )
                            
                            if st.button("Guardar Estado", key=f"btn_guardar_{libro_id}", use_container_width=True):
                                if nuevo_estado != libro["estado_lectura"]:
                                    actualizar_estado(libro_id, nuevo_estado)
                                else:
                                    st.info("El estado no ha cambiado. Cierra la ventana.", icon="ℹ️")

                        # --- Columna 2: Detalles del Libro ---
                        with pop_col2:
                            st.subheader(libro['nombre'] or 'Título Desconocido')
                            st.markdown(f"**Autor:** {libro['autor'] or 'Desconocido'}")
                            st.markdown(f"**Estado Actual:** {obtener_badge_estado(libro['estado_lectura'])}")
                            
                            st.divider()

                            # Badges de tipos
                            tipos_cadena = libro.get('tipos') or ""
                            tipos_lista = [t.strip() for t in tipos_cadena.split(',') if t.strip()]
                            tipos_badges_markdown = " ".join([f":violet-badge[{tipo}]" for tipo in tipos_lista])
                            st.markdown(f"**Tipos:** {tipos_badges_markdown}")
                            
                            st.markdown("---")
                            st.write("**Descripción:**")
                            st.write(libro.get('descripcion', 'No hay descripción disponible para este libro.'))