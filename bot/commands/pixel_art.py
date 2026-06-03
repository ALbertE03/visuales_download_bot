from PIL import Image 
from pyrogram import Client
from pyrogram.types import Message

from pyrogram import Client, Message
from PIL import Image
import io

async def pixel_art(client: Client, message: Message, img_path: str, f_reduction: int = 10):
    """
    Convierte una imagen a estilo pixel art y la envía como reply
    
    Args:
        client: Cliente de Pyrogram
        message: Mensaje de Telegram
        img_path: Ruta de la imagen
        f_reduction: Factor de reducción (mayor = más pixelado)
    """
    
    try:
        img = Image.open(img_path)
    except FileNotFoundError:
        await message.reply_text("❌ No se encontró la imagen.")
        return
    except Exception as e:
        await message.reply_text(f"❌ Error al abrir la imagen: {str(e)}")
        return
    

    if img.format not in ['JPEG', 'PNG', 'GIF', 'BMP', 'WEBP']:
        await message.reply_text("❌ El archivo no es una imagen válida.")
        return
    

    f_reduction = max(1, f_reduction)
    
    # Calcular nuevas dimensiones
    n_w = max(1, img.width // f_reduction)
    n_h = max(1, img.height // f_reduction)
    
    # Crear efecto pixel art
    img_small = img.resize((n_w, n_h), Image.NEAREST)
    pixel_art = img_small.resize(img.size, Image.NEAREST)
    
    # Guardar en memoria
    img_buffer = io.BytesIO()
    save_format = 'PNG' if img.format == 'PNG' else 'JPEG'
    pixel_art.save(img_buffer, format=save_format)
    img_buffer.seek(0)
    
    await message.reply_photo(
        photo=img_buffer,
        caption=f"✨ Pixel art (factor {f_reduction}x)"
    )