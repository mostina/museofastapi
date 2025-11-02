from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime

# ✅ Connessione a MongoDB Atlas
MONGO_URI = "mongodb+srv://museomagazzino:artwork@cluster0.kedecnn.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["MuseoMagazzino"]
artworks_collection = db["artworks"]
iot_collection = db["iot-data"]

app = FastAPI(title="Museo Smart System API")

# ==========================
# 📦 MODELLI
# ==========================

class ArtWork(BaseModel):
    _id: str
    nome: str
    autore: str
    anno: int
    in_prestito: bool
    in_magazzino: bool

class IoTData(BaseModel):
    _id: str
    latitude: float
    longitude: float
    temperature: float
    humidity: float
    timestamp: str

# ==========================
# 🏛️ ENDPOINT OPERE D’ARTE
# ==========================

@app.get("/artworks")
def get_all_artworks():
    """Ritorna tutte le opere nel database."""
    data = list(artworks_collection.find({}, {"_id": 0}))
    return {"count": len(data), "artworks": data}

@app.post("/artworks/add")
def add_artwork(artwork: ArtWork):
    """Aggiunge una nuova opera."""
    if artworks_collection.find_one({"_id": artwork._id}):
        raise HTTPException(status_code=400, detail="Opera già esistente")
    artworks_collection.insert_one(artwork.dict())
    return {"message": f"Opera '{artwork.nome}' aggiunta con successo!"}

@app.delete("/artworks/{artwork_id}")
def delete_artwork(artwork_id: str):
    """Rimuove un'opera tramite ID."""
    result = artworks_collection.delete_one({"_id": artwork_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Opera non trovata")
    return {"message": f"Opera {artwork_id} rimossa con successo"}

# ==========================
# 🌡️ ENDPOINT IoT (dal simulatore)
# ==========================

@app.get("/iot-data")
def get_iot_data():
    """Ritorna tutti i dati IoT presenti nel database."""
    data = list(iot_collection.find({}, {"_id": 0}))  # esclude l'_id ObjectId generato da MongoDB
    return {"count": len(data), "iot_data": data}

@app.post("/iot-data/update")
def update_iot_data(data: IoTData):
    """Riceve aggiornamenti IoT e aggiorna il database."""
    artwork = artworks_collection.find_one({"_id": data._id})

    # Se l’opera non esiste, ignoriamo l’update
    if not artwork:
        raise HTTPException(status_code=404, detail="Opera non trovata")

    # Se l’opera NON è in magazzino, aggiorniamo i dati IoT
    if not artwork["in_magazzino"]:
        iot_collection.update_one(
            {"_id": data._id},
            {"$set": data.dict()},
            upsert=True
        )
        return {"message": f"Dati IoT aggiornati per {data._id}"}
    else:
        return {"message": f"L’opera {data._id} è in magazzino — GPS non aggiornato."}

# ==========================
# 🧠 TEST ROUTE
# ==========================

@app.get("/")
def root():
    return {"message": "Museo Smart System API attiva 🚀"}

# ==========================
# 🏁 START SERVER
# ==========================
if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)