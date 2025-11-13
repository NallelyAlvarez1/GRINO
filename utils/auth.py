import bcrypt
import streamlit as st
from utils.database import get_db


def hash_password(password: str) -> str:
    """Genera hash seguro con bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(input_password: str, hashed_password: str) -> bool:
    """Verifica contraseña contra hash almacenado"""
    return bcrypt.checkpw(input_password.encode('utf-8'), hashed_password.encode('utf-8'))

def check_login():
    """Verifica si el usuario está logueado (para App_principal.py)"""
    return 'usuario' in st.session_state and st.session_state.usuario

def authenticate(username: str, password: str) -> bool:
    """Autentica credenciales contra la DB y guarda el user_id"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, password_hash FROM usuarios WHERE username = %s", 
                    (username,)
                )
                result = cur.fetchone()
                if result and verify_password(password, result[1]):
                    st.session_state.user_id = result[0]
                    st.session_state.usuario = username
                    return True
        return False
    except Exception as e:
        st.error(f"Error de autenticación: {e}")
        return False