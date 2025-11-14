import streamlit as st
# Importaciones necesarias para la autenticación y la base de datos
from utils.auth import check_login, authenticate, register_user, sign_out
from utils.db import get_supabase_client, test_supabase_connection 

# Configuración de página
st.set_page_config(page_title="GRINO", page_icon="🌱", layout="wide")

# --- 1. GESTIÓN DE ESTADO INICIAL ---

# Asegurar que la clave de estado de sesión para el user_id exista
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'usuario' not in st.session_state:
    st.session_state.usuario = "Invitado"

# Determinar si el usuario está logueado
is_logged_in = check_login()

# --- 2. CONTENIDO PROTEGIDO (USUARIO LOGUEADO) ---
# En la sección de usuario logueado, después del sidebar
if is_logged_in:
    st.sidebar.write("---")
    st.sidebar.subheader("🔍 Debug Info")
    st.sidebar.write(f"User ID: `{st.session_state.user_id}`")
    st.sidebar.write(f"Tipo User ID: `{type(st.session_state.user_id)}`")
    st.sidebar.write(f"Usuario: `{st.session_state.usuario}`")
    # Obtener el cliente de Supabase (cacheado)
    supabase = get_supabase_client()
    
    # ------------------- Barra Lateral (Sidebar) -------------------
    with st.sidebar:
        st.subheader("Estado de la Sesión")
        # Mostrar información del usuario
        st.markdown(f"**👤 Usuario:** `{st.session_state.usuario}`")
        # Mostrar solo una parte del ID para hacerlo más corto
        st.markdown(f"**🆔 ID:** `{st.session_state.user_id[:8]}...`")
        
        # Botón de Cerrar Sesión
        if st.button("🚪 Cerrar Sesión", type="primary", use_container_width=True):
            sign_out() # Usar la función de Supabase Auth
            st.success("Sesión cerrada correctamente.")
            st.rerun()

        st.divider()
        
        # 🚦 Verificar la conexión (Solo mostramos el estado en el sidebar)
        st.subheader("Conexión DB")
        if test_supabase_connection(supabase):
            st.success("✅ Supabase conectado.")
        else:
            # Si hay un error, el 'test_supabase_connection' ya habrá mostrado el error
            st.warning("⚠️ Error en la conexión a Supabase.")


    # ------------------- Contenido Principal de la App -------------------
    st.title("Sistema de Gestión de Presupuestos 🛠️")
    st.header(f"Bienvenido/a, {st.session_state.usuario}", divider="green")

    # Definición de las tarjetas de navegación
    paginas = [
    {
    "titulo": "Crear Presupuesto", 
    "icono": "📄", 
    "descripcion": "Genera un nuevo presupuesto de trabajo detallado.", 
    "pagina": "pages/1_📄_presupuestos.py", 
    "key": "pres",
    "imagen_path": "images/imagen1.jpg"
    },
    {
    "titulo": "Historial", 
    "icono": "🕒", 
    "descripcion": "Revisa, edita o elimina presupuestos ya creados.", 
    "pagina": "pages/2_🕒_historial.py", 
    "key": "hist",
    "imagen_path": "images/imagen2.jpg"
    },
    {
    "titulo": "Clientes Registrados", 
    "icono": "👥", 
    "descripcion": "Revisa y/o elimina clientes registrados.", 
    "pagina": "pages/3_👥_clientes.py", 
    "key": "cli",
    "imagen_path": "images/imagen3.jpg"
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
                    # Usamos un truco de columnas internas para centrar la imagen
                    col_img_1, col_img_2, col_img_3 = st.columns([1, 2, 1]) 
                    with col_img_2:
                        st.image(
                            p['imagen_path'], 
                            width=150,  
                            caption=p['titulo']
                        ) 
                except FileNotFoundError:
                    st.warning(f"No se encontró la imagen: {p['imagen_path']}")
                    
                # 2. Descripción
                st.write(p['descripcion'])

                # 3. Botón de Enlace
                st.page_link(
                    p['pagina'], 
                    label=f"Ir a {p['titulo']}", 
                    key=f"link_{p['key']}",
                    use_container_width=True
                )

# --- 3. CONTENIDO PÚBLICO (USUARIO NO LOGUEADO) ---
else:
    st.subheader("Bienvenido a Grino 🧮", divider="blue")
    st.info("Para acceder a las herramientas de gestión de presupuestos, por favor inicie sesión o regístrese.")

    tabs = st.tabs([f"🔑 Iniciar sesión", f"📝 Registrarse"])

    # ------------------- LOGIN -------------------
    with tabs[0]:
        st.markdown("##### Acceso al Sistema")
        with st.form("login_form"):
            email = st.text_input("Correo electrónico", key="login_email").strip().lower()
            password = st.text_input("Contraseña", type="password", key="login_password")
            
            if st.form_submit_button("Ingresar", type="primary", use_container_width=True):
                if not email or not password:
                    st.error("⚠️ Por favor ingrese correo y contraseña.")
                else:
                    if authenticate(email, password):
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas o usuario no existe.")

    with tabs[1]:
        st.markdown("##### Crear una Cuenta")
        with st.form("register_form"):
            email_reg = st.text_input("Correo electrónico", key="reg_email").strip().lower()
            password_reg = st.text_input("Contraseña (mínimo 6 caracteres)", type="password", key="reg_password")
            password_confirm = st.text_input("Confirmar Contraseña", type="password", key="reg_confirm")
            
            if st.form_submit_button("Registrar", type="secondary", use_container_width=True):
                if not email_reg or not password_reg:
                    st.error("⚠️ Por favor ingrese correo y contraseña.")
                elif password_reg != password_confirm:
                    st.error("❌ Las contraseñas no coinciden.")
                elif len(password_reg) < 6:
                    st.error("❌ La contraseña debe tener al menos 6 caracteres.")
                elif register_user(email_reg, password_reg):
                    st.success("📩 Verifica tu email para completar el registro.")
                else:
                    st.error("❌ Error al registrar el usuario. El correo puede estar en uso.")