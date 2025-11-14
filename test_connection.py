# test_connection.py
import streamlit as st
from utils.db import get_supabase_client

def test_auth_connection():
    st.title("🔧 Test de Conexión Supabase Auth")
    
    supabase = get_supabase_client()
    
    # Test de conexión básica
    try:
        # Intentar obtener la configuración de auth
        settings = supabase.auth.get_session()
        st.success("✅ Conexión a Supabase establecida")
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return
    
    # Test de registro
    st.subheader("Test de Registro")
    test_email = "test@example.com"
    test_password = "testpassword123"
    
    try:
        # Intentar limpiar usuario de test si existe
        try:
            supabase.auth.sign_in_with_password({"email": test_email, "password": test_password})
            # Si puede iniciar sesión, eliminar el usuario
            user = supabase.auth.get_user()
            if user:
                supabase.auth.admin.delete_user(user.user.id)
        except:
            pass
            
        # Intentar registro
        response = supabase.auth.sign_up({
            "email": test_email,
            "password": test_password
        })
        
        if response.user:
            st.success("✅ Registro funcionando correctamente")
            st.info(f"Usuario ID: {response.user.id}")
        else:
            st.error("❌ Error en registro")
            if hasattr(response, 'error') and response.error:
                st.error(f"Error: {response.error.message}")
                
    except Exception as e:
        st.error(f"❌ Error en test de registro: {e}")

if __name__ == "__main__":
    test_auth_connection()