import os
import uuid
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.files import File

from .models import SourceAudio, AudioChunk

def slice_audio(source_audio: SourceAudio, start_time: str, end_time: str) -> str:
    """
    Slices an audio file using ffmpeg without re-encoding. / 无需重新编码，即可利用 ffmpeg切割音频

    :param source_audio: The SourceAudio model instance.
    :param start_time: The start time in HH:MM:SS format.
    :param end_time: The end time in HH:MM:SS format.
    :return: The relative path to the sliced audio file, or None if failed.
    """
    input_path = source_audio.file.path

    # Define output directory and create it if it doesn't exist
    output_dir = os.path.join(settings.MEDIA_ROOT, 'slices')
    os.makedirs(output_dir, exist_ok=True)

    # Generate a unique filename for the slice
    original_filename = os.path.basename(input_path)
    name, ext = os.path.splitext(original_filename)
    slice_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    output_path = os.path.join(output_dir, slice_filename)

    # Construct the ffmpeg command
    command = [
        'ffmpeg',
        '-i', input_path,
        '-ss', start_time,
        '-to', end_time,
        '-c', 'copy',      # Crucial for speed: stream copy, no re-encoding
        '-y',              # Overwrite output file if it exists
        output_path
    ]

    try:
        # Execute the command
        print(f"Running ffmpeg command: {' '.join(command)}")
        result = subprocess.run(
            command, 
            check=True,        # Raise CalledProcessError if ffmpeg returns a non-zero exit code
            capture_output=True, # Capture stdout and stderr
            text=True          # Decode stdout/stderr as text
        )
        print(f"ffmpeg stdout: {result.stdout}")
        print(f"ffmpeg stderr: {result.stderr}")

        # Return the path relative to MEDIA_ROOT for URL generation
        relative_path = os.path.join('slices', slice_filename)
        return relative_path

    except FileNotFoundError:
        print("Error: ffmpeg command not found. Make sure it's installed and in your system's PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error during ffmpeg execution: {e}")
        print(f"ffmpeg stderr: {e.stderr}")
        return None

def slice_source_to_chunks(source_audio: SourceAudio):
    """
    Slices a SourceAudio file into 60-second AudioChunks using ffmpeg.
    """
    source_file_path = source_audio.file.path

    with tempfile.TemporaryDirectory() as temp_dir:
        output_pattern = os.path.join(temp_dir, 'chunk_%03d.mp3')

        try:
            command = [
                'ffmpeg',
                '-i', source_file_path,
                '-f', 'segment',
                '-segment_time', '60',
                '-c', 'copy',
                output_pattern
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
        except FileNotFoundError:
            raise Exception("ffmpeg is not installed or not in the system's PATH.")
        except subprocess.CalledProcessError as e:
            raise Exception(f"ffmpeg processing failed: {e.stderr}")

        chunk_files = sorted(Path(temp_dir).glob('chunk_*.mp3'))
        for i, chunk_path in enumerate(chunk_files):
            with open(chunk_path, 'rb') as f:
                AudioChunk.objects.create(
                    source_audio=source_audio,
                    chunk_index=i + 1,
                    file=File(f, name=chunk_path.name)
                )