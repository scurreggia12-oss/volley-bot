import os
import sqlite3
from database import crea_tabelle
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# ---------------- DATABASE ----------------

def aggiungi_atleta_db(nome, cognome, data_nascita):
    conn = sqlite3.connect("volley.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO atleti (nome, cognome, data_nascita)
        VALUES (?, ?, ?)
    """, (nome, cognome, data_nascita))

    conn.commit()
    conn.close()


def lista_atleti_db():
    conn = sqlite3.connect("volley.db")
    cursor = conn.cursor()

    cursor.execute("SELECT nome, cognome, data_nascita FROM atleti")
    dati = cursor.fetchall()

    conn.close()
    return dati


# ---------------- COMANDI ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message:
        await message.reply_text("🏐 Bot volley attivo!")


async def aggiungi_atleta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message is None:
        return

    try:
        args = context.args or []

        if len(args) < 3:
            await message.reply_text("❌ Usa: /aggiungi_atleta Nome Cognome 2005-06-21")
            return

        nome = args[0]
        cognome = args[1]
        data_nascita = args[2]

        aggiungi_atleta_db(nome, cognome, data_nascita)

        await message.reply_text(f"✅ Atleta {nome} {cognome} aggiunto!")

    except Exception as e:
        await message.reply_text(f"❌ Errore: {e}")


async def lista_atleti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message is None:
        return

    print("LISTA ATLETI CHIAMATO")  # DEBUG

    atleti = lista_atleti_db()

    if not atleti:
        await message.reply_text("❌ Nessun atleta presente")
        return

    testo = "🏐 Lista atleti:\n\n"

    for a in atleti:
        testo += f"- {a[0]} {a[1]} ({a[2]})\n"

    await message.reply_text(testo)


# ---------------- BOT ----------------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("aggiungi_atleta", aggiungi_atleta))
app.add_handler(CommandHandler("lista_atleti", lista_atleti))

crea_tabelle()

print("BOT AVVIATO")  # IMPORTANTISSIMO

app.run_polling()
