import asyncio
from pyrogram import Client
import streamlit as st

# Usamos los secretos locales
API_ID = st.secrets.get("API_ID")
API_HASH = st.secrets.get("API_HASH")

async def main():
    print("Iniciando generación de sesión...")
    # Se usa in_memory=True para obtener solo el string y no crear archivos
    app = Client("my_userbot_memory", api_id=API_ID, api_hash=API_HASH, in_memory=True)
    await app.start()
    
    session_string = await app.export_session_string()
    
    print("\n\n" + "="*50)
    print("COPIA ESTE TEXTO Y PONLO EN TUS SECRETOS DE STREAMLIT (session_string):")
    print("="*50)
    print(session_string)
    print("="*50 + "\n\n")
    
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
