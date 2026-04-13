import os
import sys
import json
import logging
import whisper
import yt_dlp
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

# Configure standard logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================================
# VAD configuration constants for tuning
# ==========================================
SILENCE_THRESH_OFFSET = -16      # Offset against audio.dBFS to define silence dynamically
MIN_SILENCE_LEN = 700            # ms: The minimum length of silence to constitute a split (reduced to 700ms for more responsive chunking)
SEEK_STEP = 1             # ms: Step size for iterating through the audio

# Whisper configuration
WHISPER_MODEL_NAME = "base"

def download_audio_from_url(url: str, output_dir: str = ".") -> str:
    """Download audio from a URL using yt-dlp and extract as m4a."""
    logger.info(f"Downloading audio from {url}...")
    
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # The FFmpeg postprocessor might change the extension to .m4a
            base_filename = os.path.splitext(filename)[0]
            expected_filename = f"{base_filename}.m4a"
            
            if os.path.exists(expected_filename):
                logger.info(f"Downloaded audio to {expected_filename}")
                return expected_filename
            elif os.path.exists(filename):
                # Fallback if the extension didn't change
                logger.info(f"Downloaded audio to {filename}")
                return filename
            else:
                raise FileNotFoundError(f"Could not find downloaded file around {filename}")
    except Exception as e:
        logger.error(f"Failed to download from URL: {e}")
        raise

def detect_voice_chunks(audio_path: str) -> tuple[list[tuple[int, int]], AudioSegment]:
    """Detect non-silent chunks in an audio file. Returns list of (start_ms, end_ms) and the AudioSegment."""
    logger.info(f"Loading audio {audio_path} for VAD...")
    try:
        audio = AudioSegment.from_file(audio_path)
    except Exception as e:
        logger.error(f"Failed to load audio {audio_path}: {e}")
        raise

    
    dynamic_thresh = audio.dBFS + SILENCE_THRESH_OFFSET
    
    logger.info(f"Audio average dBFS: {audio.dBFS:.2f}")
    logger.info(f"Detecting non-silent chunks (dynamic threshold: {dynamic_thresh:.2f}dB, min_silence: {MIN_SILENCE_LEN}ms)...")
    nonsilent_ranges = detect_nonsilent(
        audio,
        min_silence_len=MIN_SILENCE_LEN,
        silence_thresh=dynamic_thresh,
        seek_step=SEEK_STEP
    )
    logger.info(f"Detected {len(nonsilent_ranges)} chunks via VAD.")
    return nonsilent_ranges, audio

def transcribe_chunks_with_whisper(audio: AudioSegment, nonsilent_ranges: list[tuple[int, int]]) -> list[dict]:
    """Transcribe each non-silent chunk and calculate global timestamps."""
    logger.info(f"Loading Whisper model '{WHISPER_MODEL_NAME}'...")
    try:
        model = whisper.load_model(WHISPER_MODEL_NAME)
    except Exception as e:
        logger.error(f"Failed to load Whisper model: {e}")
        raise

    # Temporary directory for intermediate chunk files
    chunk_dir = "temp_vad_chunks"
    os.makedirs(chunk_dir, exist_ok=True)
    
    global_results = []
    
    try:
        for idx, (start_ms, end_ms) in enumerate(nonsilent_ranges):
            chunk = audio[start_ms:end_ms]
            chunk_file = os.path.join(chunk_dir, f"chunk_{idx}.wav")
            
            # Export chunk so whisper can read it natively
            chunk.export(chunk_file, format="wav")
            
            logger.info(f"Transcribing chunk {idx + 1}/{len(nonsilent_ranges)} ({start_ms}ms to {end_ms}ms)...")
            result = model.transcribe(chunk_file, fp16=False)
            
            # Core Timestamp Restoration
            global_offset_sec = start_ms / 1000.0
            
            merged_text = ""
            merged_start = -1
            
            segments = result.get("segments", [])
            for i, segment in enumerate(segments):
                text = segment.get("text", "").strip()
                if not text:
                    continue
                
                if merged_start == -1:
                    merged_start = global_offset_sec + segment.get("start", 0.0)
                
                merged_text = (merged_text + " " + text).strip() if merged_text else text
                
                # Check if it ends with terminal punctuation OR if it is the very last segment in the chunk
                is_last_segment = (i == len(segments) - 1)
                if merged_text[-1] in '.!?。！？"\'”’' or is_last_segment:
                    merged_end = global_offset_sec + segment.get("end", 0.0)
                    global_results.append({
                        "text": merged_text,
                        "start": round(merged_start, 3),
                        "end": round(merged_end, 3)
                    })
                    merged_text = ""
                    merged_start = -1
                
    finally:
        # Cleanup temporary files
        logger.info("Cleaning up temporary chunk files...")
        for filename in os.listdir(chunk_dir):
            file_path = os.path.join(chunk_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp chunk {file_path}: {e}")
        
        try:
            os.rmdir(chunk_dir)
        except Exception:
            pass

    return global_results

def process_source(source: str):
    """Main pipeline handler."""
    audio_path = source
    is_temp_download = False
    
    # 1. Flexible Input
    if source.startswith("http://") or source.startswith("https://"):
        logger.info("Source identified as URL. Initiating download...")
        audio_path = download_audio_from_url(source)
        is_temp_download = True
    else:
        logger.info("Source identified as local file.")
        if not os.path.exists(audio_path):
            logger.error(f"Local file does not exist: {audio_path}")
            sys.exit(1)

    try:
        # 2. VAD Dynamic Chunking
        nonsilent_ranges, audio = detect_voice_chunks(audio_path)
        
        if not nonsilent_ranges:
            logger.warning("No non-silent chunks found. Is the audio completely silent?")
            sys.exit(0)
            
        # 3 & 4. Whisper Transcription & Timestamp Restoration
        results = transcribe_chunks_with_whisper(audio, nonsilent_ranges)
        
        # 5. Output Results
        output_json = "transcript_2.json"
        output_md = "transcript_2.md"
        
        logger.info(f"Saving results to {output_json} and {output_md}...")
        
        # Save JSON
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        # Save Markdown
        with open(output_md, "w", encoding="utf-8") as f:
            f.write("# Podcast Transcript\n\n")
            for res in results:
                # Formatting: [MM:SS] Text
                mins = int(res['start'] // 60)
                secs = int(res['start'] % 60)
                f.write(f"- **[{mins:02d}:{secs:02d}]** {res['text']}\n")
            
        logger.info("Podcast Miner Pipeline completed successfully.")
        
        # Output Top 5 items
        print("\n" + "="*50)
        print("--- Top 5 Transcribed Segments ---")
        for res in results[:5]:
            print(f"[{res['start']:.3f}s -> {res['end']:.3f}s] {res['text']}")
        print("="*50 + "\n")
            
    except Exception as e:
        logger.error(f"Pipeline failed during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python podcast_miner.py <url_or_filepath>")
        print("Example 1: python podcast_miner.py https://youtube.com/watch?v=...")
        print("Example 2: python podcast_miner.py ./local_episode.mp3")
        sys.exit(1)
        
    source_arg = sys.argv[1]
    process_source(source_arg)
