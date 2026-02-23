import openpyxl
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta

TOKEN = "8261058843:AAFEGmNVrrxon3n4fJ6nc5DAXaULcSiNZgE"
META = 266
EXCEL_FILE = "./avance.xlsx"


# ===== CARGAR DATOS =====

def cargar_datos():

    wb = openpyxl.load_workbook(EXCEL_FILE)
    sheet = wb.active

    datos = []

    for row in sheet.iter_rows(min_row=2, values_only=True):

        if row[0] and row[1]:

            fecha = row[0]
            migrados = int(row[1])

            telmex = int(row[2]) if row[2] else 0
            totalplay = int(row[3]) if row[3] else 0

            datos.append({
                "fecha": fecha,
                "migrados": migrados,
                "telmex": telmex,
                "totalplay": totalplay
            })

    return datos


# ===== HOY =====

def comando_hoy():

    datos = cargar_datos()

    ultimo = datos[-1]

    porcentaje = (ultimo["migrados"] / META) * 100

    return f"""
📅 Hoy: {ultimo["fecha"].strftime("%d-%b-%Y")}

Migrados: {ultimo["migrados"]}
Telmex: {ultimo["telmex"]}
Totalplay: {ultimo["totalplay"]}

Avance: {porcentaje:.2f}%
"""


# ===== AVANCE =====

def comando_avance():

    datos = cargar_datos()

    migrados = datos[-1]["migrados"]

    porcentaje = (migrados / META) * 100

    barra = "█" * int(porcentaje/5) + "░" * (20-int(porcentaje/5))

    return f"""
📊 AVANCE

{migrados}/{META}
{barra}
{porcentaje:.2f}%
"""


# ===== FALTAN =====

def comando_faltan():

    datos = cargar_datos()

    migrados = datos[-1]["migrados"]

    faltan = META - migrados

    return f"Faltan {faltan} migraciones"


# ===== SEMANA =====

def comando_semana():

    datos = cargar_datos()

    hoy = datetime.now()

    inicio = hoy - timedelta(days=hoy.weekday())

    texto = "📅 Semana actual\n\n"

    for d in datos:

        if d["fecha"] >= inicio:

            texto += f'{d["fecha"].strftime("%d-%b")}: {d["migrados"]}\n'

    return texto


# ===== SEMANA PASADA =====

def comando_semana_pasada():

    datos = cargar_datos()

    hoy = datetime.now()

    inicio = hoy - timedelta(days=hoy.weekday()+7)
    fin = inicio + timedelta(days=6)

    texto = "📅 Semana pasada\n\n"

    for d in datos:

        if inicio <= d["fecha"] <= fin:

            texto += f'{d["fecha"].strftime("%d-%b")}: {d["migrados"]}\n'

    return texto


# ===== DETALLE SEMANA =====

def comando_detalle_semana():

    datos = cargar_datos()

    hoy = datetime.now()
    inicio = hoy - timedelta(days=hoy.weekday())

    total = 0

    for d in datos:

        if d["fecha"] >= inicio:
            total += d["migrados"]

    return f"Total semana actual: {total}"


# ===== PROYECCION =====

def comando_proyeccion():

    datos = cargar_datos()

    incrementos = []

    for i in range(1, len(datos)):
        incrementos.append(
            datos[i]["migrados"] - datos[i-1]["migrados"]
        )

    promedio = sum(incrementos) / len(incrementos)

    faltan = META - datos[-1]["migrados"]

    dias = faltan / promedio if promedio > 0 else 0

    fecha_estimada = datetime.now() + timedelta(days=dias)

    return f"""
📈 Proyección

Promedio diario: {promedio:.2f}

Meta estimada:
{fecha_estimada.strftime("%d-%b-%Y")}
"""


# ===== GRAFICA =====

def generar_grafica():

    datos = cargar_datos()

    fechas = [d["fecha"] for d in datos]
    migrados = [d["migrados"] for d in datos]

    plt.figure()

    plt.plot(fechas, migrados, marker="o")

    plt.title("Avance Migraciones")

    plt.xlabel("Fecha")
    plt.ylabel("Migrados")

    plt.grid()

    archivo = "grafica.png"

    plt.savefig(archivo)

    plt.close()

    return archivo


# ===== COMPARATIVO =====

def generar_comparativo():

    datos = cargar_datos()

    fechas = [d["fecha"] for d in datos]
    telmex = [d["telmex"] for d in datos]
    totalplay = [d["totalplay"] for d in datos]

    plt.figure()

    plt.plot(fechas, telmex)
    plt.plot(fechas, totalplay)

    plt.title("Telmex vs Totalplay")

    plt.xlabel("Fecha")
    plt.ylabel("Migraciones")

    plt.grid()

    archivo = "comparativo.png"

    plt.savefig(archivo)

    plt.close()

    return archivo


# ===== TELEGRAM =====

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):

    texto = update.message.text.lower()

    if texto == "hoy":
        await update.message.reply_text(comando_hoy())

    elif texto == "avance":
        await update.message.reply_text(comando_avance())

    elif texto == "faltan":
        await update.message.reply_text(comando_faltan())

    elif texto == "semana":
        await update.message.reply_text(comando_semana())

    elif texto == "semana pasada":
        await update.message.reply_text(comando_semana_pasada())

    elif texto == "detalle semana":
        await update.message.reply_text(comando_detalle_semana())

    elif texto == "proyeccion":
        await update.message.reply_text(comando_proyeccion())

    elif texto == "grafica":

        archivo = generar_grafica()

        await update.message.reply_photo(photo=open(archivo, "rb"))

    elif texto == "comparativo":

        archivo = generar_comparativo()

        await update.message.reply_photo(photo=open(archivo, "rb"))

    else:

        await update.message.reply_text(
            "Comandos:\nhoy\navance\nfaltan\nsemana\nsemana pasada\ndetalle semana\nproyeccion\ngrafica\ncomparativo"
        )


# ===== MAIN =====

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, responder))

print("Bot PRO corriendo 🚀")

app.run_polling(drop_pending_updates=True)
