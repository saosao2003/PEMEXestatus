import pandas as pd
import gspread
import matplotlib.pyplot as plt
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

TOKEN = "8261058843:AAFEGmNVrrxon3n4fJ6nc5DAXaULcSiNZgE"
CHAT_ID = "834897782"
META = 266
SHEET_NAME = "Avance Migraciones 2026"

# ===== GOOGLE SHEETS =====

scope = [
    "https://docs.google.com/spreadsheets/d/1xCqKEGKDqyfvFl7z4Fgy8pv2Js6ra1MfZAR5mS344A4/edit?gid=0#gid=0"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credenciales.json", scope)

client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# ===== CARGAR DATOS =====

def cargar_datos():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df.sort_values('Fecha')

    return df

# ===== KPI =====

def calcular_kpi():

    df = cargar_datos()

    ultimo = df.iloc[-1]

    migrados = int(ultimo['Migrados'])

    porcentaje = (migrados / META) * 100

    faltan = META - migrados

    incremento_diario = df['Migrados'].diff()

    promedio = incremento_diario.mean()

    if promedio > 0:
        dias_restantes = faltan / promedio
        fecha_estimada = datetime.now() + timedelta(days=dias_restantes)
        fecha_estimada = fecha_estimada.strftime("%d-%b-%Y")
    else:
        fecha_estimada = "Sin cálculo"

    return migrados, porcentaje, faltan, promedio, fecha_estimada

# ===== GRAFICA =====

def generar_grafica():

    df = cargar_datos()

    plt.figure()

    plt.plot(df['Fecha'], df['Migrados'])

    plt.axhline(y=META)

    plt.title("Avance Migraciones")

    plt.xlabel("Fecha")

    plt.ylabel("Migrados")

    archivo = "grafica.png"

    plt.savefig(archivo)

    plt.close()

    return archivo

# ===== REPORTE =====

def crear_reporte():

    migrados, porcentaje, faltan, promedio, fecha_estimada = calcular_kpi()

    reporte = f"""
📊 REPORTE DIARIO 20:00

Migrados: {migrados}/{META}
Avance: {porcentaje:.2f}%
Faltan: {faltan}

Promedio diario: {promedio:.2f}

Meta estimada: {fecha_estimada}
"""

    return reporte

# ===== TELEGRAM HANDLER =====

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):

    texto = update.message.text.lower()

    if texto == "avance":

        reporte = crear_reporte()

        await update.message.reply_text(reporte)

        grafica = generar_grafica()

        await update.message.reply_photo(photo=open(grafica, 'rb'))

    elif texto == "hoy":

        df = cargar_datos()

        ultimo = df.iloc[-1]

        porcentaje = (ultimo['Migrados'] / META) * 100

        respuesta = f"""
📅 Hoy

Migrados: {ultimo['Migrados']}
Avance: {porcentaje:.2f}%
"""

        await update.message.reply_text(respuesta)

    elif texto == "proyeccion":

        _, _, _, promedio, fecha_estimada = calcular_kpi()

        await update.message.reply_text(
            f"Meta estimada: {fecha_estimada}\nPromedio: {promedio:.2f}/día"
        )

# ===== REPORTE AUTOMATICO =====

async def enviar_reporte_auto(app):

    reporte = crear_reporte()

    grafica = generar_grafica()

    await app.bot.send_message(chat_id=CHAT_ID, text=reporte)

    await app.bot.send_photo(chat_id=CHAT_ID, photo=open(grafica, 'rb'))

# ===== SCHEDULER =====

scheduler = AsyncIOScheduler(timezone="America/Mexico_City")

# 20:00 hrs
scheduler.add_job(
    enviar_reporte_auto,
    "cron",
    hour=20,
    minute=0,
    args=[ApplicationBuilder().token(TOKEN).build()]
)

scheduler.start()

# ===== MAIN =====

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, responder))

print("Bot corriendo 24/7...")

app.run_polling()