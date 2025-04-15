import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from app.transcription import transcribe_audio
from app.summarization import summarize_text
from app.database import save_report
import os
import uuid

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    file_path = ""
    try:
        logger.info(f"Received file upload: {file.filename}")
        # Save uploaded file
        file_path = f"voices/{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
        os.makedirs("voices", exist_ok=True)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"File saved to {file_path}")

        # Transcribe
        logger.info("Starting transcription")
        transcript = transcribe_audio(file_path)
        if "error" in transcript.lower():
            logger.error(f"Transcription failed: {transcript}")
            raise HTTPException(status_code=500, detail=transcript)
        logger.info(f"Transcription successful: {transcript}")

        # Summarize
        logger.info("Starting summarization")
        summary = summarize_text(transcript)
        if "error" in summary.lower():
            logger.error(f"Summarization failed: {summary}")
            raise HTTPException(status_code=500, detail=summary)
        logger.info(f"Summarization successful: {summary}")

        # Save to database
        logger.info("Saving to database")
        report_id = save_report(user_id=0, voice_file_path=file_path, transcript=transcript, summary=summary)
        logger.info(f"Saved report with ID {report_id}")

        return {
            "report_id": report_id,
            "transcript": transcript,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error in /transcribe: {str(e)}", exc_info=True)
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
