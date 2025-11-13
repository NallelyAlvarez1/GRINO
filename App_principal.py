import streamlit as st
from utils.auth import check_login, authenticate, register_user, sign_out
from utils.db import get_supabase_client, test_supabase_connection # Asegúrate de importar la función de prueba

# Obtener el cliente
supabase = get_supabase_client()

# 🚦 Verificar la conexión
st.subheader("Estado de la Conexión a Supabase")
if test_supabase_connection(supabase):
    st.success("✅ Conexión a Supabase establecida y verificada correctamente.")
else:
    st.warning("⚠️ Fallo en la verificación de la conexión a Supabase.")


# Configuración de página
st.set_page_config(page_title="GRINO", page_icon="🌱", layout="wide")



# Al inicio del archivo, asegurar las claves de sesión
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    
# Si el usuario NO ha iniciado sesión
if not check_login():
    st.subheader("Bienvenido a Grino 🧮", divider="blue")

    tabs = st.tabs([f"🔑 Iniciar sesión", f"📝 Registrarse"])

# ------------------- LOGIN -------------------
    with tabs[0]:
        st.markdown("##### Acceso al Sistema")
        with st.form("login_form"):
            email = st.text_input("Correo electrónico") 
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", type="primary"):
                if authenticate(email, password): # <-- Usar el nuevo `authenticate` con email
                    st.success("Inicio de sesión correcto ✅")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas o usuario no confirmado.")
                    st.session_state.user_id = None # Asegurar que el ID se limpie si falla

    # ------------------- REGISTRO -------------------
    with tabs[1]:
        st.markdown("##### Crear una Cuenta")
        with st.form("register_form"):
            email_reg = st.text_input("Correo electrónico para registro")
            password_reg = st.text_input("Contraseña (mínimo 6 caracteres)", type="password")
            password_confirm = st.text_input("Confirmar Contraseña", type="password")
            if st.form_submit_button("Registrar", type="secondary"):
                if not email_reg or not password_reg:
                    st.error("Por favor ingrese correo y contraseña.")
                elif password_reg != password_confirm:
                    st.error("Las contraseñas no coinciden.")
                elif len(password_reg) < 6:
                     st.error("La contraseña debe tener al menos 6 caracteres.")
                elif register_user(email_reg, password_reg): 
                    st.success("Usuario registrado. Por favor, inicie sesión.")
                else:
                    st.error("Error al registrar el usuario. El correo puede estar ya en uso.")
                    
# Si el usuario SÍ ha iniciado sesión
else:
    # --- Sidebar ---
    with st.sidebar:
        st.markdown(f"**👤 Usuario:** `{st.session_state.usuario}`")
        st.markdown(f"**🆔 ID:** `{st.session_state.user_id[:8]}...`")
        if st.button("🚪 Cerrar Sesión", type="primary"):
            sign_out() # Usar la función de Supabase Auth
            st.success("Sesión cerrada correctamente.")
            st.rerun()

    # --- Contenido Principal ---
    st.title("Sistema de Gestión de Presupuestos 🛠️")
    st.header(f"Bienvenido, {st.session_state.usuario}", divider="green")

    paginas = [
        {
            "titulo": "Crear Presupuesto", 
            "icono": "📄", 
            "descripcion": "Genera un nuevo presupuesto de trabajo detallado.", 
            "pagina": "pages/1_📄_presupuestos.py", 
            "key": "pres",
            "imagen_path": "images/imagen1.jpg" # 👈 RUTA DE IMAGEN
        },
        {
            "titulo": "Historial", 
            "icono": "🕒", 
            "descripcion": "Revisa, edita o elimina presupuestos ya creados.", 
            "pagina": "pages/2_🕒_historial.py", 
            "key": "hist",
            "imagen_path": "images/imagen2.jpg" # 👈 RUTA DE IMAGEN
        },
        {
            "titulo": "Clientes Registrados", 
            "icono": "👥", 
            "descripcion": "Revisa y/o elimina clientes registrados.", 
            "pagina": "pages/3_👥_clientes.py", 
            "key": "cli",
            "imagen_path": "images/imagen3.jpg" # 👈 RUTA DE IMAGEN
        }
    ]

    # --- Distribución de Tarjetas ---
    col1, col2, col3 = st.columns(3)
    columnas = [col1, col2, col3]

    for i, p in enumerate(paginas):
        with columnas[i]:
            # Usamos un contenedor con borde para simular la tarjeta (Card)
            with st.container(border=True): 

                st.subheader(f"{p['icono']} {p['titulo']}")
                
                # 1. Colocar la Imagen
                try:
                    col_img_1, col_img_2, col_img_3 = st.columns([1, 2, 1])

                    # 2. Ponemos la imagen en la columna del medio
                    with col_img_2:
                        # Usamos st.image de Streamlit
                        st.image(
                            p['imagen_path'], 
                            width=150,  # 👈 Ajusta este valor según necesites
                            caption=p['titulo']
                        ) 
                except FileNotFoundError:
                    st.warning(f"No se encontró la imagen: {p['imagen_path']}")
                    
                # 2. Título y Descripción

                st.write(p['descripcion'])

                # 3. Botón de Enlace
                st.page_link(
                    p['pagina'], 
                    label=f"Ir a {p['titulo']}", 
                    key=f"link_{p['key']}",
                    use_container_width=True
                )