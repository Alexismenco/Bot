from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.error import BadRequest
import os
from dotenv import load_dotenv
import json

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Cargar datos desde el archivo JSON
def load_scorts_data():
    try:
        with open('scorts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Guardar datos en el archivo JSON
def save_scorts_data(data):
    with open('scorts.json', 'w') as f:
        json.dump(data, f, indent=4)

scorts_info = load_scorts_data()

# Obtener las variables de entorno
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
COLABORADOR_1 = int(os.getenv('COLABORADOR_1'))

print(f'Telegram Token: {TELEGRAM_TOKEN}')
print(f'Admin ID: {ADMIN_ID}')
print(f'Colaborador 1 ID: {COLABORADOR_1}')

# Token del bot de Telegram
TOKEN = TELEGRAM_TOKEN

# Ciudades
ciudades = ["Ancud", "Castro", "Quemchi", "Dalcahue", "Quellón", "Chonchi"]

# Lista de IDs de usuarios autorizados
authorized_users = [ADMIN_ID, COLABORADOR_1]  

# Función de inicio
async def start(update: Update, context):
    keyboard = [[InlineKeyboardButton(ciudad, callback_data=ciudad)] for ciudad in ciudades]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Selecciona una ciudad:', reply_markup=reply_markup)

# Función para manejar las selecciones de ciudades
async def button(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id
    ciudad = query.data
    scorts = scorts_info.get(ciudad, [])
    scorts_activadas = [scort for scort in scorts if scort.get('activada', False)]

    if not scorts_activadas:
        await query.message.reply_text(f'No hay scorts disponibles en {ciudad}.')
        return

    for scort in scorts_activadas:
        text = (
            f"<b>Nombre:</b> {scort['nombre']}\n"
            f"<b>Edad:</b> {scort['edad']}\n"
            f"<b>Lugar propio:</b> {scort['lugar']}\n"
            f"<b>Medidas:</b> {scort['medidas']}\n"
            f"<b>Estatura:</b> {scort['estatura']}\n"
            f"<b>Telegram:</b> <a href='{scort['telegram']}'>{scort['nombre']}</a>"
        )

        keyboard = [
            [InlineKeyboardButton("Contactar", url=scort['telegram'])]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.message.reply_photo(photo=scort['foto'], caption=text, reply_markup=reply_markup, parse_mode='HTML')
        except BadRequest as e:
            print(f"Error al enviar foto: {e}")
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

    await query.message.reply_text(f'Aquí hay {len(scorts_activadas)} scorts disponibles en {ciudad} 😈.')
# Función para manejar el comando /agregarscort
# Función para manejar el comando /agregarscort
async def add_scort(update: Update, context):
    user_id = update.message.from_user.id
    if user_id not in authorized_users:
        await update.message.reply_text("No tienes permiso para usar este comando.")
        return

    if len(context.args) < 9:
        await update.message.reply_text("Uso: /agregarscort <Ciudad> <Nombre> <Edad (25)> <lugar (Sí/No)> <telegram> <URL_foto> <activada (true/false)> <medidas (90-60-90)> <estatura (160 cm) >")
        return

    ciudad, nombre, edad, lugar, telegram, foto, activada, medidas, estatura = context.args[:9]
    activada = activada.lower() == 'true'

    if ciudad not in scorts_info:
        scorts_info[ciudad] = []

    new_scort = {
        "nombre": nombre,
        "edad": int(edad),
        "lugar": lugar,
        "telegram": 'https://t.me/' + telegram,
        "foto": foto,
        "activada": activada,
        "medidas": medidas,
        "estatura": estatura
    }

    scorts_info[ciudad].append(new_scort)
    save_scorts_data(scorts_info)  # Guardar datos actualizados en el archivo JSON

    await update.message.reply_text(f"Scort añadida en {ciudad}: {nombre}, {edad}, {lugar}, {telegram}, {'activada' if activada else 'desactivada'}, {medidas}, {estatura}")

# Lista todas las scort
async def listar_scorts(update: Update, context):
    user_id = update.message.from_user.id
    if user_id not in authorized_users:
        await update.message.reply_text("No tienes permiso para usar este comando.")
        return

    for ciudad, scorts in scorts_info.items():
        for scort in scorts:
            scort_info = (
                f"Nombre: {scort['nombre']}\n"
                f"Edad: {scort['edad']}\n"
                f"Lugar: {scort['lugar']}\n"
                f"Telegram: {scort['telegram']}\n"
                f"Foto: {scort['foto']}\n"
                f"Activada: {'Sí' if scort['activada'] else 'No'}\n"
            )
            # No incluir botón de eliminar en esta función
            reply_markup = None
            await update.message.reply_text(scort_info, reply_markup=reply_markup)

# Función para manejar el comando /eliminar_scort
async def eliminar_scort(update: Update, context):
    user_id = update.message.from_user.id
    if user_id not in authorized_users:
        await update.message.reply_text("No tienes permiso para usar este comando.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Uso: /eliminar_scort <enlace_de_Telegram>")
        return

    enlace_telegram = context.args[0]

    # Iterar sobre todas las ciudades y scorts para encontrar y eliminar la scort
    scort_eliminada = False
    for ciudad, scorts in scorts_info.items():
        for scort in scorts:
            if scort['telegram'] == enlace_telegram:
                scorts.remove(scort)
                scort_eliminada = True
                save_scorts_data(scorts_info)  # Guardar datos actualizados en el archivo JSON
                await update.message.reply_text(f"Scort eliminada exitosamente de {ciudad}: {scort['nombre']}")
                break  # Salir del bucle interno si encontramos y eliminamos la scort

    if not scort_eliminada:
        await update.message.reply_text("No se encontró ninguna scort con el enlace de Telegram proporcionado.")

# Función para manejar el comando /cambiar_activacion
async def cambiar_activacion_scort(update: Update, context):
    user_id = update.message.from_user.id
    if user_id not in authorized_users:
        await update.message.reply_text("No tienes permiso para usar este comando.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Uso: /cambiar_activacion <enlace_de_Telegram>")
        return

    enlace_telegram = context.args[0]

    # Iterar sobre todas las ciudades y scorts para encontrar y cambiar la activación de la scort
    scort_modificada = False
    for ciudad, scorts in scorts_info.items():
        for scort in scorts:
            if scort['telegram'] == enlace_telegram:
                scort['activada'] = not scort['activada']  # Cambiar el valor de activada
                scort_modificada = True
                save_scorts_data(scorts_info)  # Guardar datos actualizados en el archivo JSON
                estado = 'activada' if scort['activada'] else 'desactivada'
                await update.message.reply_text(f"Activación de scort cambiada a {estado} para {scort['nombre']} en {ciudad}")
                break  # Salir del bucle interno si encontramos y modificamos la scort

    if not scort_modificada:
        await update.message.reply_text("No se encontró ninguna scort con el enlace de Telegram proporcionado.")

# Función para manejar mensajes de texto
async def echo(update: Update, context):
    await update.message.reply_text('Usa /start para comenzar.')

# Función para manejar el comando /help
async def help_command(update: Update, context):
    user_id = update.message.from_user.id

    if user_id in authorized_users:
        message = (
            "🤖 Lista de Comandos Disponibles\n\n"
            "/start - Inicia el bot y selecciona una ciudad para ver las scorts disponibles.\n"
            "/help - Muestra esta lista de comandos.\n"
            "/ayuda - Muestra esta lista de comandos.\n"
            "/obtenerid - Obtiene tu ID de usuario.\n"
            "/agregarscort <Ciudad> <Nombre> <Edad> <lugar (Sí/No)> <telegram> <URL_foto> <activada (true/false)> - Agrega una nueva scort.\n"
            "/listar_scorts - Lista todas las scorts disponibles.\n"
            "/eliminar_scort <enlace_de_Telegram> - Elimina una scort por su enlace de Telegram.\n"
            "/cambiar_activacion <enlace_de_Telegram> - Cambia la activación de una scort por su enlace de Telegram."
        )
    else:
        message = "🤖 <b>Comandos Disponibles:</b>\n\n/start - Inicia el bot y selecciona una ciudad para ver las scorts disponibles.\n/obtenerid - Obtiene tu ID de usuario."

    await update.message.reply_text(message)

# Función para manejar el comando /ayuda
async def ayuda_command(update: Update, context):
    user_id = update.message.from_user.id

    if user_id in authorized_users:
        message = (
            "🤖 Lista de Comandos Disponibles\n\n"
            "/start - Inicia el bot y selecciona una ciudad para ver las scorts disponibles.\n"
            "/help - Muestra esta lista de comandos.\n"
            "/ayuda - Muestra esta lista de comandos.\n"
            "/obtenerid - Obtiene tu ID de usuario.\n"
            "/agregarscort <Ciudad> <Nombre> <Edad> <lugar (Sí/No)> <telegram> <URL_foto> <activada (true/false)> - Agrega una nueva scort.\n"
            "/listar_scorts - Lista todas las scorts disponibles.\n"
            "/eliminar_scort <enlace_de_Telegram> - Elimina una scort por su enlace de Telegram.\n"
            "/cambiar_activacion <enlace_de_Telegram> - Cambia la activación de una scort por su enlace de Telegram."
        )
    else:
        message = "🤖 <b>Comandos Disponibles:</b>\n\n/start - Inicia el bot y selecciona una ciudad para ver las scorts disponibles.\n/obtenerid - Obtiene tu ID de usuario."

    await update.message.reply_text(message)

# Función para manejar el comando /getid
async def get_id(update: Update, context):
    user_id = update.message.from_user.id
    print(user_id)
    await update.message.reply_text(f'Tu ID de usuario es: {user_id}')

# Función para manejar errores y logs
async def error(update: Update, context):
    print(f'Update {update} causó el error {context.error}')

# Configuración del bot
def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("iniciar", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ayuda", ayuda_command))
    application.add_handler(CommandHandler("obtenerid", get_id))
    application.add_handler(CommandHandler("agregarscort", add_scort))
    application.add_handler(CommandHandler("listar_scorts", listar_scorts))
    application.add_handler(CommandHandler("eliminar_scort", eliminar_scort))
    application.add_handler(CommandHandler("cambiar_activacion", cambiar_activacion_scort))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Manejo de errores
    application.add_error_handler(error)

    application.run_polling()

if __name__ == '__main__':
    main()
