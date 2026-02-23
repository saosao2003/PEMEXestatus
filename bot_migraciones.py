import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta

TOKEN = "8261058843:AAFEGmNVrrxon3n4fJ6nc5DAXaULcSiNZgE"
META = 266
SHEET_NAME = "Avance Migraciones 2026"

# CONEXION GOOGLE SHEETS
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credenciales.json", scope)

client = gspread.authorize(creds)

sheet = client.open(SHEET_NAME).sheet1


def cargar_datos():

    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')

    return df


def obtener_hoy(df):

    hoy = datetime.now().date()

    fila = df[df['Fecha'].dt.date == hoy]

    if fila.empty:
        return "No hay datos cargados hoy"

    return fila.to_string(index=False)


def obtener_semana(df):

    hoy = datetime.now()
    inicio = hoy - timedelta(days=hoy.weekday())

    semana = df[df['Fecha'] >= inicio]

    return semana.to_string(index=False)


def obtener_semana_pasada(df):

    hoy = datetime.now()

    inicio = hoy - timedelta(days=hoy.weekday() + 7)
    fin = inicio + timedelta(days=6)

    semana = df[(df['Fecha'] >= inicio) & (df['Fecha'] <= fin)]

    return semana.to_string(index=False)


def obtener_avance(df):

    ultimo = df['Migrados'].dropna().iloc[-1]

    porcentaje = (ultimo / META) * 100

    return f"""
Avance actual: {ultimo}/{META}
Porcentaje: {porcentaje:.2f}%
Faltan: {META - ultimo}
"""


async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):

    texto = update.message.text.lower()

    df = cargar_datos()

    if texto == "hoy":
        respuesta = obtener_hoy(df)

    elif texto == "semana":
        respuesta = obtener_semana(df)

    elif texto == "semana pasada":
        respuesta = obtener_semana_pasada(df)

    elif texto == "avance":
        respuesta = obtener_avance(df)

    else:
        respuesta = """
Comandos disponibles:

hoy
semana
semana pasada
avance
"""

    await update.message.reply_text(respuesta)


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, responder))

app.run_polling()
