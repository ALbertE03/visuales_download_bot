import asyncio
import requests
import streamlit as st
from pyrogram import Client,types
from pyrogram.types import Message

GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")

def query_github_api(endpoint, method="GET", payload=None):
    """Realiza una petición a la API REST de GitHub"""
    url = f"https://api.github.com/{endpoint.lstrip('/')}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    try:
        if method.upper() == "GET":
            r = requests.get(url, headers=headers, timeout=15)
        elif method.upper() == "POST":
            r = requests.post(url, headers=headers, json=payload, timeout=15)
        elif method.upper() == "PUT":
            r = requests.put(url, headers=headers, json=payload, timeout=15)
        elif method.upper() == "DELETE":
            r = requests.delete(url, headers=headers, timeout=15)
        elif method.upper() == "PATCH":
            r = requests.patch(url, headers=headers, json=payload, timeout=15)
        else:
            return None, "Método HTTP no soportado"

        if r.status_code in [200, 201]:
            return r.json(), None
        elif r.status_code == 204:
            return {"status": "success"}, None
        else:
            err_msg = "Error desconocido"
            try:
                err_msg = r.json().get("message", err_msg)
            except:
                err_msg = r.text
            return None, f"HTTP {r.status_code}: {err_msg}"
    except Exception as e:
        return None, f"Excepción de red: {e}"


async def ghuser_handler(client: Client, message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("Uso: `/ghuser <username>`\nEj: `/ghuser torvalds`")
        return

    username = parts[1].strip()
    loading_msg = await message.reply_text(f"Buscando información de <b>{username}</b> en GitHub...")

    loop = asyncio.get_event_loop()
    data, error = await loop.run_in_executor(None, lambda: query_github_api(f"users/{username}"))

    if error or not data:
        await loading_msg.edit_text(f"❌ Error buscando a {username}:\n`{error}`")
        return

    login = data.get("login")
    name = data.get("name") or "Sin Nombre"
    bio = data.get("bio") or "Sin biografía"
    blog = data.get("blog") or ""
    followers = data.get("followers", 0)
    following = data.get("following", 0)
    public_repos = data.get("public_repos", 0)
    html_url = data.get("html_url")

    text = (
        f"👤 <b><a href='{html_url}'>{login}</a></b>\n\n"
        f"📛 <b>Nombre:</b> {name}\n"
        f"📝 <b>Bio:</b> {bio}\n"
        f"🔗 <b>Blog:</b> {blog if blog else 'N/A'}\n"
        f"👥 <b>Seguidores:</b> {followers} | <b>Siguiendo:</b> {following}\n"
        f"📦 <b>Repos Públicos:</b> {public_repos}"
    )
    await loading_msg.edit_text(text, disable_web_page_preview=True)


async def ghrepo_handler(client: Client, message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("Uso: `/ghrepo <owner/repo>`\nEj: `/ghrepo pyrogram/pyrogram`")
        return

    repo = parts[1].strip()
    loading_msg = await message.reply_text(f"Buscando repositorio <b>{repo}</b> en GitHub...")

    loop = asyncio.get_event_loop()
    data, error = await loop.run_in_executor(None, lambda: query_github_api(f"repos/{repo}"))

    if error or not data:
        await loading_msg.edit_text(f"❌ Error buscando el repo {repo}:\n`{error}`")
        return

    full_name = data.get("full_name")
    description = data.get("description") or "Sin descripción"
    language = data.get("language") or "N/A"
    stars = data.get("stargazers_count", 0)
    forks = data.get("forks_count", 0)
    open_issues = data.get("open_issues_count", 0)
    html_url = data.get("html_url")

    text = (
        f"📦 <b><a href='{html_url}'>{full_name}</a></b>\n\n"
        f"📝 <b>Descripción:</b> {description}\n"
        f"💻 <b>Lenguaje:</b> {language}\n"
        f"⭐ <b>Estrellas:</b> {stars}\n"
        f"🍴 <b>Forks:</b> {forks}\n"
        f"🐞 <b>Issues Abiertos:</b> {open_issues}"
    )
    await loading_msg.edit_text(text, disable_web_page_preview=True)


async def ghsearch_handler(client: Client, message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("Uso: `/ghsearch <descripción o tags>`\nEj: `/ghsearch telegram bot in:readme`")
        return

    query = parts[1].strip()
    loading_msg = await message.reply_text(f"Buscando repositorios para: <b>{query}</b>...")

    loop = asyncio.get_event_loop()

    data, error = await loop.run_in_executor(None, lambda: query_github_api(f"search/repositories?q={query}&sort=stars&order=desc&per_page=5"))

    if error or not data:
        await loading_msg.edit_text(f"❌ Error en búsqueda:\n`{error}`")
        return

    items = data.get("items", [])
    if not items:
        await loading_msg.edit_text(f"No se encontraron repositorios para: <b>{query}</b>")
        return

    text = f"🔎 <b>Resultados para:</b> <i>{query}</i>\n\n"
    for item in items:
        text += f"📦 <b><a href='{item.get('html_url')}'>{item.get('full_name')}</a></b> (⭐ {item.get('stargazers_count')})\n"
        desc = item.get('description') or 'Sin descripción'
        text += f"📝 <i>{desc[:100]}{'...' if len(desc)>100 else ''}</i>\n\n"

    await loading_msg.edit_text(text, disable_web_page_preview=True)


async def ghcreate_handler(client: Client, message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("Uso: `/ghcreate <nombre-del-repo> [descripción]`\nEj: `/ghcreate mi-bot-test Bot hecho en python`")
        return

    if not GITHUB_TOKEN:
        await message.reply_text("Se requiere GITHUB_TOKEN en secrets para crear repositorios.")
        return

    args = parts[1].split(maxsplit=1)
    repo_name = args[0]
    repo_desc = args[1] if len(args) > 1 else ""

    loading_msg = await message.reply_text(f"Creando repositorio <b>{repo_name}</b>...")

    payload = {
        "name": repo_name,
        "description": repo_desc,
        "private": False,
        "auto_init": True
    }

    loop = asyncio.get_event_loop()
    data, error = await loop.run_in_executor(None, lambda: query_github_api("user/repos", method="POST", payload=payload))

    if error or not data:
        await loading_msg.edit_text(f"Error creando repo:\n`{error}`")
        return

    html_url = data.get("html_url")
    owner = data.get("owner", {}).get("login")
    await loading_msg.edit_text(
        f"✅ <b>Repositorio creado exitosamente!</b>\n"
        f"👤 <b>Dueño:</b> {owner}\n"
        f"📦 <b><a href='{html_url}'>{repo_name}</a></b>",
         link_preview_options=types.LinkPreviewOptions(
        is_disabled=True 
    )
    )
