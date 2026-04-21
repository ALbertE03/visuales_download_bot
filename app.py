import streamlit as st
from run import setup_bots
from bot.config import CONFIG

# Configuración de la página
st.set_page_config(
    page_title="Visuales Bot Control",
    page_icon="🤖",
    layout="centered"
)

# Título y mensaje solicitado
st.title("🤖 Visuales Bot System")
st.write("### Hola Mundo")

# Iniciar los bots de forma persistente
@st.cache_resource
def init_telegram_bots():
    try:
        bot_app, userbot_app = setup_bots()
        return bot_app, userbot_app, True
    except Exception as e:
        return None, None, str(e)

# Ejecutar inicio
bot, userbot, status = init_telegram_bots()

# Interfaz de estado
st.divider()
if status is True:
    st.success("✅ Bots activos y funcionando en segundo plano.")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Bot Principal", "Conectado")
    with col2:
        st.metric("Userbot", "Conectado")
    
    st.info("ℹ️ El Bot y el Userbot están respondiendo a comandos en Telegram.")
else:
    st.error(f"❌ Error al iniciar los bots: {status}")

# Información adicional
st.sidebar.title("Configuración")
st.sidebar.write(f"**Workers de descarga:** {CONFIG.CANT_WORKER.value}")
st.sidebar.write(f"**Workers de subida:** {CONFIG.UPLOAD_WORKER.value}")
st.sidebar.write(f"**Grupo objetivo:** {CONFIG.TARGET_GROUP.value}")

if st.sidebar.button("Reiniciar caché de Streamlit"):
    st.cache_resource.clear()
    st.rerun()
