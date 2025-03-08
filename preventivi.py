from fastapi import FastAPI, HTTPException, Request, Form
from pydantic import BaseModel
import os
from twilio.rest import Client
import base64
import hashlib
import logging

app = FastAPI()

# Configura logging per debug
logging.basicConfig(level=logging.INFO)

# Recupera credenziali da variabili d'ambiente
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")  # Numero Twilio

if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_WHATSAPP_NUMBER:
    logging.error("Errore: Variabili d'ambiente di Twilio mancanti!")
    raise ValueError("Configurazione Twilio non valida")

# Inizializza il client Twilio
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def hash_protect(data: str) -> str:
    """Genera un hash SHA-256 codificato in base64 per protezione"""
    return base64.b64encode(hashlib.sha256(data.encode()).digest()).decode()

@app.post("/whatsapp/")
async def whatsapp_webhook(request: Request):
    try:
        form_data = await request.form()
        logging.info(f"Data ricevuta: {form_data}")

        sender = form_data.get("From")
        message_body = form_data.get("Body", "").strip().lower()
        
        if not sender:
            logging.error("Parametro 'From' mancante nella richiesta")
            raise HTTPException(status_code=400, detail="Parametro 'From' mancante")

        risposta = "Ciao! 😊 Sono il tuo assistente per i preventivi. Dimmi, di che lavoro hai bisogno? ✨"
        
        if "preventivo" in message_body:
            risposta = (
                "Ottima scelta! 💪 Per darti un preventivo preciso, ho bisogno di alcune info:\n"
                "1️⃣ Quante ore di lavoro pensi siano necessarie?\n"
                "2️⃣ Qual è il costo stimato dei materiali?\n"
                "3️⃣ Il lavoro è semplice, medio o complesso?"
            )

        # Invio del messaggio tramite Twilio
        client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=risposta,
            to=sender
        )

        return {"status": "Messaggio inviato", "hash": hash_protect(risposta)}
    
    except Exception as e:
        logging.error(f"Errore nel webhook: {e}")
        raise HTTPException(status_code=500, detail="Errore interno del server")
