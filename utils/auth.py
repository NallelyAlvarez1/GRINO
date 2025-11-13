import streamlit as st
# from utils.db import get_supabase_client # Se mantiene la importación si la conexión global está aquí
from utils.db import get_supabase_client 

# Asumimos que get_supabase_client() retorna el cliente de Supabase
supabase = get_supabase_client()

# ==================== FUNCIONES DE AUTENTICACIÓN ====================

# ELIMINADAS: hash_password y verify_password - Supabase Auth maneja el hashing

def check_login() -> bool:
    """Verifica si el usuario está logueado."""
    # Verificamos si existe el ID de usuario, que es el UUID de Supabase Auth
    return 'user_id' in st.session_state and st.session_state.user_id is not None

def authenticate(email: str, password: str) -> bool:
    """Autentica credenciales usando Supabase Auth (email/password)."""
    try:
        # Usamos sign_in_with_password de Supabase Auth
        # El método sing_in_with_password devuelve la sesión y el usuario
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        # Si la autenticación es exitosa, guardamos la sesión y el user_id
        if response.user:
            st.session_state.user = response.user
            st.session_state.user_id = response.user.id # El ID de usuario es el UUID de Supabase
            st.session_state.usuario = email # Se usa el email para identificar al usuario en la UI
            return True
        return False
    except Exception as e:
        # Supabase maneja los errores como credenciales incorrectas, pero capturamos por seguridad
        print(f"Error de autenticación: {e}")
        # En caso de error, aseguramos que la sesión no se mantenga
        st.session_state.user = None
        st.session_state.user_id = None
        return False

def register_user(email: str, password: str) -> bool:
    """Registra un nuevo usuario en Supabase Auth."""
    try:
        # Supabase crea el usuario y envía el email de confirmación (si está configurado)
        response = supabase.auth.sign_up({"email": email, "password": password})
        
        # Si el registro es exitoso, response.user tendrá el usuario,
        # aunque puede que no esté confirmado aún, pero la cuenta se crea.
        return True
    except Exception as e:
        print(f"Error al registrar usuario: {e}")
        return False

def sign_out():
    """Cierra la sesión del usuario en Supabase y limpia el estado de Streamlit."""
    try:
        supabase.auth.sign_out()
    except Exception as e:
        print(f"Error al cerrar sesión de Supabase: {e}")
        
    # Limpiar el estado de Streamlit
    if 'user' in st.session_state:
        del st.session_state.user
    if 'user_id' in st.session_state:
        del st.session_state.user_id
    if 'usuario' in st.session_state:
        del st.session_state.usuario
        
    # Limpiar otros estados relacionados
    for key in list(st.session_state.keys()):
        if key.startswith('expander_toggle_'):
            del st.session_state[key]