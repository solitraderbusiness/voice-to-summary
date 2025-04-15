import logging
import os
from pydub import AudioSegment
import requests
from config.settings import OPENAI_API_KEY

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB safety margin
TARGET_SAMPLE_RATE = 16000  # 16kHz
INITIAL_SEGMENT_MS = 120000  # 2 minutes initial guess

def transcribe_audio(file_path):
    try:
        logger.info(f"Transcribing audio file: {file_path}")
        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size} bytes")

        # Convert to WAV with optimized settings
        if file_path.endswith(".ogg"):
            logger.info("Converting OGG to WAV (16kHz, mono)")
            audio = AudioSegment.from_ogg(file_path)
            audio = audio.set_frame_rate(TARGET_SAMPLE_RATE).set_channels(1)
            wav_path = file_path.replace(".ogg", ".wav")
            audio.export(wav_path, format="wav")
            file_path = wav_path
            file_size = os.path.getsize(file_path)
            logger.info(f"Converted to {file_path}, size: {file_size} bytes")

        # Split if file exceeds 20MB
        transcripts = []
        if file_size > MAX_FILE_SIZE:
            logger.info("File exceeds 20MB, splitting into segments")
            audio = AudioSegment.from_wav(file_path)
            total_ms = len(audio)
            segment_ms = INITIAL_SEGMENT_MS
            segments = []
            start_ms = 0

            # Iteratively adjust segment size
            while start_ms < total_ms:
                end_ms = min(start_ms + segment_ms, total_ms)
                segment = audio[start_ms:end_ms]
                segment_path = f"{file_path[:-4]}_segment_{len(segments)}.wav"
                segment.export(segment_path, format="wav")
                segment_size = os.path.getsize(segment_path)
                logger.info(f"Trial segment: {segment_path}, size: {segment_size} bytes")

                if segment_size > MAX_FILE_SIZE:
                    logger.info("Segment too large, reducing duration")
                    os.remove(segment_path)
                    segment_ms = int(segment_ms * 0.75)  # Reduce by 25%
                    if segment_ms < 10000:  # Minimum 10 seconds
                        logger.error("Cannot create small enough segments")
                        return f"Transcription error: Unable to split audio under 20MB"
                    continue

                segments.append((segment_path, segment_size))
                start_ms += segment_ms

            # Transcribe segments
            for segment_path, segment_size in segments:
                logger.info(f"Processing segment: {segment_path}, size: {segment_size} bytes")
                transcript = transcribe_segment(segment_path)
                if "error" in transcript.lower():
                    logger.error(f"Segment transcription failed: {transcript}")
                    return transcript
                transcripts.append(transcript)
                os.remove(segment_path)

            transcript = " ".join(transcripts)
        else:
            transcript = transcribe_segment(file_path)

        # Clean up WAV file
        if file_path.endswith(".wav") and os.path.exists(file_path):
            logger.info(f"Removing temporary WAV file: {file_path}")
            os.remove(file_path)

        logger.info(f"Final transcription result: {transcript}")
        return transcript

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        return f"Transcription error: {str(e)}"

def transcribe_segment(file_path):
    try:
        logger.info(f"Sending segment {file_path} to OpenAI Whisper API")
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        with open(file_path, "rb") as audio_file:
            files = {"file": audio_file}
            data = {"model": "whisper-1", "language": "fa"}
            response = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data
            )

        if response.status_code == 200:
            transcript = response.json().get("text", "")
            logger.info(f"Segment transcription result: {transcript}")
            return transcript
        else:
            error = response.text
            logger.error(f"OpenAI API error: {error}")
            return f"Transcription error: {error}"

    except Exception as e:
        logger.error(f"Segment transcription error: {str(e)}", exc_info=True)
        return f"Transcription error: {str(e)}"
