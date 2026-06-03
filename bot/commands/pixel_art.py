from PIL import Image 
from pyrogram import Client
from pyrogram.types import Message
from PIL import Image
import io
import os

async def pixel_art(client: Client, message: Message, f_reduction: int = 10):
    """
    Convierte una imagen a estilo pixel art y la envía como reply
    Debe usarse como reply a una foto
    
    Args:
        client: Cliente de Pyrogram
        message: Mensaje de Telegram (debe ser reply a una foto)
        f_reduction: Factor de reducción (mayor = más pixelado)
    """
    
    if not message.reply_to_message:
        await message.reply_text(
            "Por favor, responde a una imagen.\n"
            "Uso: Responde a una foto con el comando `/pixel`"
        )
        return
    
    reply_msg = message.reply_to_message
    
    has_image = False
    img_path = None
    
    if reply_msg.photo:
        has_image = True
        img_path = await reply_msg.download()
    
    elif reply_msg.document and reply_msg.document.mime_type and reply_msg.document.mime_type.startswith('image/'):
        has_image = True
        img_path = await reply_msg.download()
    
    elif reply_msg.sticker:
        has_image = True
        img_path = await reply_msg.download()
    
    elif reply_msg.animation:
        has_image = True
        img_path = await reply_msg.download()
    
    else:
        await message.reply_text(
            "❌ No se encontró una imagen en el mensaje al que respondes.\n"
            "Por favor, responde a una foto, sticker o imagen."
        )
        return
    
    if not has_image or not img_path:
        await message.reply_text("❌ Error al descargar la imagen.")
        return
    
    try:
        img = Image.open(img_path)
        

        if img.format not in ['JPEG', 'PNG', 'GIF', 'BMP', 'WEBP']:
            await message.reply_text("❌ El archivo no es una imagen válida.")
            return
        

        f_reduction = max(1, min(30, f_reduction))
        
   
        n_w = max(1, img.width // f_reduction)
        n_h = max(1, img.height // f_reduction)
        
      
        img_small = img.resize((n_w, n_h), Image.NEAREST)
        pixel_art_img = img_small.resize(img.size, Image.NEAREST)
        
   
        img_buffer = io.BytesIO()
        save_format = 'PNG' if img.format == 'PNG' else 'JPEG'
        pixel_art_img.save(img_buffer, format=save_format)
        img_buffer.seek(0)
        
        await message.reply_photo(
            photo=img_buffer,
            caption=f"✨ Pixel art (factor {f_reduction}x)\n"
                   f"Original: {img.width}x{img.height}"
        )
        
    except Exception as e:
        await message.reply_text(f"❌ Error al procesar la imagen: {str(e)}")
    
    finally:

        if img_path and os.path.exists(img_path):
            os.remove(img_path)

    
    