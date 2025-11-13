import streamlit as st
from supabase import create_client, Client

def initialize_supabase_client(secrets: dict) -> Client:
    try:
        SUPABASE_URL = secrets["supabase"]["url"]
        SUPABASE_KEY = secrets["supabase"]["key"]
    except KeyError as e:
        # Esto nos asegura que si falla la importación es por el secreto
        st.error("Error de configuración: Falta la clave de Supabase.") 
        st.stop()
        
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# 🔑 Definimos la función de acceso con caché aquí para que todos la usen.
@st.cache_resource 
def get_supabase_client() -> Client:
    """Devuelve la instancia del cliente Supabase, cacheada globalmente."""
    return initialize_supabase_client(st.secrets)

# ---

def test_supabase_connection(supabase_client: Client) -> bool:
    """
    Intenta realizar una operación de lectura simple para verificar la conexión.
    Asegúrate de reemplazar 'nombre_de_una_tabla_existente' con una tabla real.
    """
    try:
        # Intenta seleccionar los primeros 0 registros de una tabla existente.
        # Esto verifica la conexión y las credenciales sin transferir muchos datos.
        response = supabase_client.from_('nombre_de_una_tabla_existente').select('*').limit(0).execute()
        
        # Una conexión exitosa generalmente no lanzará una excepción y 
        # la respuesta contendrá datos de la tabla (aunque vacíos por el limit(0)).
        if response and response.data is not None:
            return True
        else:
            # Podría ser un error de credenciales o de la URL si llega aquí sin excepción
            st.error("La conexión fue posible, pero la respuesta no es válida.")
            return False

    except Exception as e:
        st.error(f"❌ Error de conexión a Supabase: {e}")
        return False