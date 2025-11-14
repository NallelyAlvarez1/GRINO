import streamlit as st
# Usamos supabase-py
from supabase import create_client, Client

def initialize_supabase_client(secrets: dict) -> Client:
    """Inicializa y configura el cliente Supabase usando las secrets de Streamlit."""
    try:
        # 🚨 Asegúrate de que las rutas 'supabase' y 'url'/'key' coincidan con tu secrets.toml
        SUPABASE_URL = secrets["supabase"]["url"]
        SUPABASE_KEY = secrets["supabase"]["key"]
    except KeyError as e:
        # Detiene la aplicación si faltan las claves de configuración
        st.error(f"Error de configuración: Falta la clave de Supabase en `st.secrets`: {e}") 
        st.stop()
        
    # Agregamos una verificación simple para asegurar que las variables no estén vacías
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Error de configuración: Las URL o KEY de Supabase están vacías.") 
        st.stop()

    return create_client(SUPABASE_URL, SUPABASE_KEY)

# 🔑 Definimos la función de acceso con caché para usarla globalmente.
@st.cache_resource 
def get_supabase_client() -> Client:
    """Devuelve la instancia del cliente Supabase, cacheada globalmente."""
    return initialize_supabase_client(st.secrets)

# 🧪 Función de Verificación de Conexión (usando una tabla de prueba)
def test_supabase_connection(supabase_client: Client) -> bool:
    """
    Intenta realizar una operación de lectura simple para verificar la conexión.
    REEMPLAZA 'tu_tabla_de_prueba' con una tabla real.
    """
    try:
        # Usa una tabla que sepas que existe, por ejemplo, 'profiles' o 'users' (si es tu tabla personalizada)
        # O la tabla que usaste para la prueba anterior.
        response = supabase_client.from_('tu_tabla_de_prueba').select('*').limit(0).execute() 
        
        if response and response.data is not None:
            return True
        else:
            st.error("La conexión fue posible, pero la respuesta de la API no es válida.")
            return False

    except Exception as e:
        # Este error es el que capturará problemas de credenciales si Supabase las rechaza
        st.error(f"❌ Error de conexión/API de Supabase: {e}")
        return False
    
