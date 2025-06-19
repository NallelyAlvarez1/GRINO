import streamlit as st
from utils.auth import check_login, authenticate

# Configuración de página
st.set_page_config(page_title="Sistema de Presupuestos", layout="wide")
# Al inicio del archivo, después de los imports
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    
# Lógica de login
if not check_login():
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Ingresar"):
            if authenticate(username, password):
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    st.stop()

# Menú principal (solo visible si está autenticado)
st.title("🏠 Menú Principal")
st.write(f"Bienvenido, {st.session_state.usuario}!")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📄 Generar Presupuesto", use_container_width=True):
        st.switch_page("pages/1_📄_presupuestos.py")

with col2:
    if st.button("🕒 Historial Presupuestos", use_container_width=True):
        st.switch_page("pages/2_🕒_historial.py")

with col3:
    if st.button("👥 Clientes registrados", use_container_width=True):
        st.switch_page("pages/3_👥_clientes.py")
