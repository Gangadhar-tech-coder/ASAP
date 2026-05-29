import os
import shutil
import numpy as np
import librosa
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from predict import DistressDetector

# Initialize FastAPI App
app = FastAPI(title="ASAAP Model API", version="1.0.0")

# Configure CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the ML Model
print("Loading ASAAP Model...")
detector = DistressDetector()

@app.get("/health")
def health_check():
    status = detector.get_status()
    return {"status": "ok", "model_loaded": status["model_loaded"]}

@app.post("/api/v1/model/predict")
async def predict_audio(file: UploadFile = File(...)):
    """
    Receives an audio chunk (e.g., from Web Audio API), processes it,
    and returns the distress confidence score.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Save the uploaded file temporarily
    temp_filepath = f"temp_{file.filename}"
    try:
        with open(temp_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Load audio using librosa (handles various formats and resamples to target rate)
        # target_sr should match SAMPLE_RATE from config (usually 22050)
        from utils.config import SAMPLE_RATE
        audio_chunk, sr = librosa.load(temp_filepath, sr=SAMPLE_RATE, mono=True)
        
        # Run inference
        label, confidence = detector.predict_chunk(audio_chunk)
        
        return {
            "success": True,
            "label": label,
            "confidence": confidence,
            "is_distress": label == "Distress"
        }
        
    except Exception as e:
        print(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

if __name__ == "__main__":
    import uvicorn
    # Run the server on port 8000
    uvicorn.run("model_server:app", host="0.0.0.0", port=8000, reload=True)
