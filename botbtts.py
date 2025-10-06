from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import aiohttp
import os
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("FOOTBALL_API_KEY")

if not BOT_TOKEN or not CHAT_ID or not API_KEY:
    raise ValueError("❌ Error: No se pudieron leer correctamente las variables del archivo .env")

# Función para obtener partidos con alta probabilidad BTTS
async def obtener_partidos_btts():
    url = f"https://v3.football.api-sports.io/fixtures?date={datetime.now().strftime('%Y-%m-%d')}"
    headers = {"x-apisports-key": API_KEY}
    partidos_btts = []

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            if not data.get("response"):
                return partidos_btts

            for partido in data["response"]:
                equipos = partido["teams"]
                liga = partido["league"]["name"]
                hora_utc = partido["fixture"]["date"]
                try:
                    dt = datetime.fromisoformat(hora_utc.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=dt_timezone.utc)
                    hora_col = dt.astimezone(ZoneInfo("America/Bogota"))
                    hora_formateada = hora_col.strftime("%H:%M")
                except:
                    hora_formateada = "?"
                
                # Ejemplo de probabilidad simulada (puedes reemplazarlo por tu fórmula real)
                prob_btts = ((equipos["home"]["id"] + equipos["away"]["id"]) % 5) * 20
                if prob_btts > 50:
                    partidos_btts.append({
                        "local": equipos["home"]["name"],
                        "visitante": equipos["away"]["name"],
                        "liga": liga,
                        "hora": hora_formateada,
                        "probabilidad": prob_btts
                    })

    partidos_btts.sort(key=lambda x: x["probabilidad"], reverse=True)
    return partidos_btts

# Comando /btts
async def btts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Buscando los mejores pronósticos BTTS...")
    partidos = await obtener_partidos_btts()
    if not partidos:
        await update.message.reply_text("⚽ No se encontraron partidos con alta probabilidad hoy.")
        return

    mensaje = "🔥 *Partidos con alta probabilidad BTTS (Hoy — Hora Colombia)* 🔥\n\n"
    for p in partidos:
        mensaje += f"🏆 *{p['liga']}*\n"
        mensaje += f"⚔️ {p['local']} vs {p['visitante']}\n"
        mensaje += f"🕒 {p['hora']} (Hora Colombia)\n"
        mensaje += f"📊 Probabilidad: *{p['probabilidad']}%*\n\n"

    await update.message.reply_text(mensaje, parse_mode="Markdown")

# Iniciar bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("btts", btts))
    print("✅ Bot iniciado y escuchando comandos de Telegram.")
    app.run_polling()
