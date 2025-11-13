import streamlit as st
from utils.auth import check_login, authenticate, hash_password
from utils.database import get_db


# Configuración de página
st.set_page_config(page_title="Sistema de Presupuestos", layout="wide")
# Al inicio del archivo, después de los imports
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    
# Si el usuario NO ha iniciado sesión
if not check_login():
    st.subheader("Bienvenido a Grino 🧮", divider="blue")

    tabs = st.tabs(["🔑 Iniciar sesión", "📝 Registrarse"])

    # ------------------- LOGIN -------------------
    with tabs[0]:
        with st.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
                if authenticate(username, password):
                    st.success("Inicio de sesión correcto ✅")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

    # ------------------- REGISTRO -------------------
    with tabs[1]:
        with st.form("register_form"):
            st.markdown("### 📝 Crear nueva cuenta")

            # --- Campos de usuario y contraseñas ---
            st.text_input("Nombre de usuario", key="username")

            col_pass1, col_pass2 = st.columns(2)
            with col_pass1:
                password = st.text_input("Contraseña", type="password", key="password")
            with col_pass2:
                password_confirm = st.text_input("Confirmar contraseña", type="password", key="password_confirm")

            # --- Advertencia visual ---
            st.info("💡 *Los datos que escriba a continuación se mostrarán en los presupuestos generados.*")

            # --- Campos personales (dos columnas) ---
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre", key="nombre")
            with col2:
                apellidos = st.text_input("Apellidos", key="apellidos")

            # --- Campos de contacto (dos columnas) ---
            col3, col4 = st.columns(2)
            with col3:
                correo = st.text_input("Correo electrónico", key="correo")
            with col4:
                telefono = st.text_input("Número de teléfono", key="telefono")

            # --- Botón de envío centrado ---
            st.markdown("<br>", unsafe_allow_html=True)
            btn_col = st.columns([2, 1, 2])[1]
            with btn_col:
                submit = st.form_submit_button("Registrarme", use_container_width=True)

        # --- Procesar registro ---
        if submit:
            username = st.session_state.username
            password = st.session_state.password
            password_confirm = st.session_state.password_confirm
            nombre = st.session_state.nombre
            apellidos = st.session_state.apellidos
            correo = st.session_state.correo
            telefono = st.session_state.telefono

            # Validaciones
            if not username or not password:
                st.error("❌ Por favor completa usuario y contraseña.")
            elif password != password_confirm:
                st.error("⚠️ Las contraseñas no coinciden. Inténtalo de nuevo.")
            else:
                try:
                    with get_db() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                """
                                INSERT INTO usuarios (username, password_hash, nombre_completo, es_admin, fecha_registro, correo, telefono)
                                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s)
                                """,
                                (
                                    username,
                                    hash_password(password),  # Solo se guarda la contraseña principal
                                    f"{nombre} {apellidos}".strip(),
                                    False,
                                    correo,
                                    telefono,
                                )
                            )
                            conn.commit()
                    st.success("✅ Usuario registrado con éxito. Ahora puedes iniciar sesión.")
                except Exception as e:
                    st.error(f"Error al registrar usuario: {e}")


    st.stop()


# --- Configuración de la Página ---
st.set_page_config(
    page_title="Menú Principal",
    page_icon="🏠",
    layout="wide"
)

# --- Título y Bienvenida (Basado en tu imagen) ---
st.title("🏠 Menú Principal")
st.subheader(f"**Bienvenido, {st.session_state.get('user_name', 'admin')}!**", divider="blue")

# --- Definición de las Tarjetas con Rutas de Imagen ---
paginas = [
    {
        "titulo": "Generar Presupuesto", 
        "icono": "📄", 
        "descripcion": "Crea un nuevo presupuesto.", 
        "pagina": "pages/1_📄_Presupuestos.py", 
        "key": "gen",
        "imagen_path": "images/imagen1.jpg" # 👈 RUTA DE IMAGEN
    },
    {
        "titulo": "Historial Presupuestos", 
        "icono": "🕒", 
        "descripcion": "Revisa, descarga o edita presupuestos anteriores.", 
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
                    st.image(
                        p['imagen_path'], 
                        width=150  # 👈 Ajusta este valor según necesites
                    ) 
            except FileNotFoundError:
                st.warning(f"No se encontró la imagen: {p['imagen_path']}")
                
            # 2. Título y Descripción

            st.markdown(f"<p style='text-align: center;'>{p['descripcion']}</p>", unsafe_allow_html=True)
            
            # 3. Botón de Acción
            if st.button(f"Ir a {p['titulo']}", key=f"btn_{p['key']}", type="secondary", width="stretch"):
                 st.switch_page(p['pagina'])