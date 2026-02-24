import openpyxl
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================

TOKEN = "TU_TOKEN_AQUI"
EXCEL_FILE = "./avance.xlsx"

META_ENLACES = 266
META_BALANCEADORES = 266


# =========================
# CARGAR DATOS
# =========================

def cargar_datos():

    wb = openpyxl.load_workbook(EXCEL_FILE)
    sheet = wb.active

    datos = []

    for row in sheet.iter_rows(min_row=2, values_only=True):

        if row[0]:

            datos.append({

                "fecha": row[0],

                "enlaces": int(row[1] or 0),
                "enlaces_telmex": int(row[2] or 0),
                "enlaces_totalplay": int(row[3] or 0),

                "balanceadores": int(row[4] or 0),
                "bal_telmex": int(row[5] or 0),
                "bal_totalplay": int(row[6] or 0),

            })

    datos.sort(key=lambda x: x["fecha"])

    return datos


# =========================
# BARRA
# =========================

def barra(p):

    llenos = int(p / 5)
    vacios = 20 - llenos

    return "█" * llenos + "░" * vacios


# =========================
# HOY
# =========================

def comando_hoy():

    d = cargar_datos()[-1]

    porc_enlaces = d["enlaces"] / META_ENLACES * 100
    porc_bal = d["balanceadores"] / META_BALANCEADORES * 100

    return f"""
📅 {d["fecha"].strftime("%d-%b-%Y")}

🔹 ENLACES
Total: {d["enlaces"]}
📡 Telmex: {d["enlaces_telmex"]}
🌐 Totalplay: {d["enlaces_totalplay"]}
Avance: {porc_enlaces:.2f}%

⚖️ BALANCEADORES
Total: {d["balanceadores"]}
📡 Telmex: {d["bal_telmex"]}
🌐 Totalplay: {d["bal_totalplay"]}
Avance: {porc_bal:.2f}%
"""


# =========================
# AVANCE
# =========================

def comando_avance():

    d = cargar_datos()[-1]

    porc_enlaces = d["enlaces"] / META_ENLACES * 100
    porc_bal = d["balanceadores"] / META_BALANCEADORES * 100

    return f"""
📊 AVANCE ENLACES
{d["enlaces"]}/{META_ENLACES}
{barra(porc_enlaces)}
{porc_enlaces:.2f}%

⚖️ AVANCE BALANCEADORES
{d["balanceadores"]}/{META_BALANCEADORES}
{barra(porc_bal)}
{porc_bal:.2f}%
"""


# =========================
# DASHBOARD
# =========================

def comando_dashboard():

    d = cargar_datos()[-1]

    porc_enlaces = d["enlaces"] / META_ENLACES * 100
    porc_bal = d["balanceadores"] / META_BALANCEADORES * 100

    faltan_enlaces = META_ENLACES - d["enlaces"]
    faltan_bal = META_BALANCEADORES - d["balanceadores"]

    return f"""
📊 DASHBOARD MIGRACIONES

Fecha: {d["fecha"].strftime("%d-%b-%Y")}

━━━━━━━━━━━━━━━━━━━

ENLACES
{d["enlaces"]}/{META_ENLACES}
{barra(porc_enlaces)}
Avance: {porc_enlaces:.2f}%
Faltan: {faltan_enlaces}

Telmex: {d["enlaces_telmex"]}
Totalplay: {d["enlaces_totalplay"]}

━━━━━━━━━━━━━━━━━━━

BALANCEADORES
{d["balanceadores"]}/{META_BALANCEADORES}
{barra(porc_bal)}
Avance: {porc_bal:.2f}%
Faltan: {faltan_bal}

Telmex: {d["bal_telmex"]}
Totalplay: {d["bal_totalplay"]}
"""


# =========================
# FALTAN
# =========================

def comando_faltan():

    d = cargar_datos()[-1]

    return f"""
Faltan enlaces: {META_ENLACES - d["enlaces"]}
Faltan balanceadores: {META_BALANCEADORES - d["balanceadores"]}
"""


# =========================
# SEMANA ACTUAL
# =========================

def comando_semana():

    datos = cargar_datos()

    hoy = datetime.now()

    inicio = hoy - timedelta(days=hoy.weekday())

    texto = "📅 SEMANA ACTUAL\n\n"

    for d in datos:

        if d["fecha"] >= inicio:

            texto += f'{d["fecha"].strftime("%d-%b")} | E:{d["enlaces"]} B:{d["balanceadores"]}\n'

    return texto


# =========================
# SEMANA PASADA
# =========================

def comando_semana_pasada():

    datos = cargar_datos()

    hoy = datetime.now()

    inicio = hoy - timedelta(days=hoy.weekday()+7)
    fin = inicio + timedelta(days=6)

    texto = "📅 SEMANA PASADA\n\n"

    for d in datos:

        if inicio <= d["fecha"] <= fin:

            texto += f'{d["fecha"].strftime("%d-%b")} | E:{d["enlaces"]} B:{d["balanceadores"]}\n'

    return texto


# =========================
# DETALLE SEMANA
# =========================

def comando_detalle_semana():

    datos = cargar_datos()

    hoy = datetime.now()

    inicio = hoy - timedelta(days=hoy.weekday())

    primero = None
    ultimo = None

    for d in datos:

        if d["fecha"] >= inicio:

            if primero is None:
                primero = d

            ultimo = d

    if primero and ultimo:

        enlaces = ultimo["enlaces"] - primero["enlaces"]
        bal = ultimo["balanceadores"] - primero["balanceadores"]

        return f"""
DETALLE SEMANA

Enlaces migrados: {enlaces}
Balanceadores migrados: {bal}
"""

    return "Sin datos semana"


# =========================
# PROYECCION
# =========================

def comando_proyeccion():

    datos = cargar_datos()

    inc_enlaces = []
    inc_bal = []

    for i in range(1, len(datos)):

        inc_enlaces.append(datos[i]["enlaces"] - datos[i-1]["enlaces"])
        inc_bal.append(datos[i]["balanceadores"] - datos[i-1]["balanceadores"])

    prom_enlaces = sum(inc_enlaces)/len(inc_enlaces)
    prom_bal = sum(inc_bal)/len(inc_bal)

    faltan_enlaces = META_ENLACES - datos[-1]["enlaces"]
    faltan_bal = META_BALANCEADORES - datos[-1]["balanceadores"]

    dias_enlaces = faltan_enlaces/prom_enlaces if prom_enlaces else 0
    dias_bal = faltan_bal/prom_bal if prom_bal else 0

    fecha_enlaces = datetime.now()+timedelta(days=dias_enlaces)
    fecha_bal = datetime.now()+timedelta(days=dias_bal)

    return f"""
PROYECCION

Enlaces: {fecha_enlaces.strftime("%d-%b-%Y")}
Balanceadores: {fecha_bal.strftime("%d-%b-%Y")}
"""


# =========================
# GRAFICA
# =========================

def generar_grafica():

    datos = cargar_datos()

    fechas = [d["fecha"] for d in datos]
    enlaces = [d["enlaces"] for d in datos]
    bal = [d["balanceadores"] for d in datos]

    plt.figure()

    plt.plot(fechas, enlaces)
    plt.plot(fechas, bal)

    plt.title("Avance")
    plt.grid()

    archivo="grafica.png"

    plt.savefig(archivo)
    plt.close()

    return archivo


# =========================
# TELEGRAM
# =========================

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):

    t = update.message.text.lower()

    if t=="hoy":
        await update.message.reply_text(comando_hoy())

    elif t=="avance":
        await update.message.reply_text(comando_avance())

    elif t=="dashboard":
        await update.message.reply_text(comando_dashboard())

    elif t=="faltan":
        await update.message.reply_text(comando_faltan())

    elif t=="semana":
        await update.message.reply_text(comando_semana())

    elif t=="semana pasada":
        await update.message.reply_text(comando_semana_pasada())

    elif t=="detalle semana":
        await update.message.reply_text(comando_detalle_semana())

    elif t=="proyeccion":
        await update.message.reply_text(comando_proyeccion())

    elif t=="grafica":

        archivo=generar_grafica()

        await update.message.reply_photo(photo=open(archivo,"rb"))

    else:

        await update.message.reply_text(
"""
Comandos:

dashboard
hoy
avance
semana
semana pasada
detalle semana
faltan
proyeccion
grafica
"""
)


# =========================
# RUN
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT,responder))

print("BOT MIGRACIONES ACTIVO")

app.run_polling(drop_pending_updates=True)
