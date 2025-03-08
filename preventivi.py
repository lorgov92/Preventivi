from fastapi import FastAPI, HTTPException, Request, Form
from pydantic import BaseModel
import datetime
import os
from twilio.rest import Client
import base64
import hashlib
import logging

app = FastAPI()

# Configura logging per vedere i dati in entrata
logging.basicConfig(level=logging.INFO)

TWILIO_ACCOUNT_SID = "your_account_sid"
TWILIO_AUTH_TOKEN = "your_auth_token"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Numero Twilio
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def hash_protect(data):
    return base64.b64encode(hashlib.sha256(data.encode()).digest()).decode()

@app.post("/whatsapp/")
async def whatsapp_webhook(request: Request):
    try:
        form_data = await request.form()
        
        # Log per debug
        logging.info(f"Data ricevuta: {form_data}")

        sender = form_data.get("From")
        message_body = form_data.get("Body", "").strip().lower()
        
        if not sender:
            raise HTTPException(status_code=400, detail="Parametro 'From' mancante")
        
        risposta = "Ciao! 😊 Sono il tuo assistente per i preventivi. Dimmi, di che lavoro hai bisogno? ✨"
        
        if "preventivo" in message_body:
            risposta = "Ottima scelta! 💪 Per darti un preventivo preciso, ho bisogno di alcune info:\n1️⃣ Quante ore di lavoro pensi siano necessarie?\n2️⃣ Qual è il costo stimato dei materiali?\n3️⃣ Il lavoro è semplice, medio o complesso?"

        client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=risposta,
            to=sender
        )

        return {"status": "Messaggio inviato", "hash": hash_protect(risposta)}
    
    except Exception as e:
        logging.error(f"Errore nel webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
