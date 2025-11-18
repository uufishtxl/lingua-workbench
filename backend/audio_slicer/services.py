import os
import uuid
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.files import File

from .models import SourceAudio, AudioChunk, AudioSlice

# def slice_audio(source_audio: SourceAudio, start_time: str, end_time: str) -> str:
#     """
#     Slices an audio file using ffmpeg without re-encoding. / 无需重新编码，即可利用 ffmpeg切割音频

#     :param source_audio: The SourceAudio model instance.
#     :param start_time: The start time in HH:MM:SS format.
#     :param end_time: The end time in HH:MM:SS format.
#     :return: The relative path to the sliced audio file, or None if failed.
#     """
#     input_path = source_audio.file.path

#     # Define output directory and create it if it doesn't exist
#     output_dir = os.path.join(settings.MEDIA_ROOT, 'slices')
#     os.makedirs(output_dir, exist_ok=True)

#     # Generate a unique filename for the slice
#     original_filename = os.path.basename(input_path)
#     name, ext = os.path.splitext(original_filename)
#     slice_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
#     output_path = os.path.join(output_dir, slice_filename)

#     # Construct the ffmpeg command
#     command = [
#         'ffmpeg',
#         '-i', input_path,
#         '-ss', start_time,
#         '-to', end_time,
#         '-c', 'copy',      # Crucial for speed: stream copy, no re-encoding
#         '-y',              # Overwrite output file if it exists
#         output_path
#     ]

#     try:
#         # Execute the command
#         print(f"Running ffmpeg command: {' '.join(command)}")
#         result = subprocess.run(
#             command, 
#             check=True,        # Raise CalledProcessError if ffmpeg returns a non-zero exit code
#             capture_output=True, # Capture stdout and stderr
#             text=True          # Decode stdout/stderr as text
#         )
#         print(f"ffmpeg stdout: {result.stdout}")
#         print(f"ffmpeg stderr: {result.stderr}")

#         # Return the path relative to MEDIA_ROOT for URL generation
#         relative_path = os.path.join('slices', slice_filename)
#         return relative_path

#     except FileNotFoundError:
#         print("Error: ffmpeg command not found. Make sure it's installed and in your system's PATH.")
#         return None
#     except subprocess.CalledProcessError as e:
#         print(f"Error during ffmpeg execution: {e}")
#         print(f"ffmpeg stderr: {e.stderr}")
#         return None

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

def slice_chunk_to_slice(chunk: AudioChunk, start_time: float, end_time: float, original_text: str, notes: str, tags: list) -> 'AudioSlice':
    """
    Creates a new AudioSlice from a given AudioChunk and time range, including all metadata.

    This function uses ffmpeg to cut a segment, creates a new AudioSlice instance,
    saves it with all provided data, sets the tags, and returns the final instance.

    :param chunk: The AudioChunk to slice.
    :param start_time: The start time in seconds.
    :param end_time: The end time in seconds.
    :param original_text: The original text for the slice.
    :param notes: Notes for the slice.
    :param tags: A list of tags to associate with the slice.
    :return: A new, saved AudioSlice instance.
    """
    input_path = chunk.file.path

    with tempfile.TemporaryDirectory() as temp_dir:
        original_filename = os.path.basename(input_path)
        name, ext = os.path.splitext(original_filename)
        slice_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        output_path = os.path.join(temp_dir, slice_filename)

        command = [
            'ffmpeg',
            '-i', str(input_path),
            '-ss', str(start_time),
            '-to', str(end_time),
            '-c', 'copy',
            '-y',
            str(output_path)
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except FileNotFoundError:
            raise Exception("ffmpeg is not installed or not in the system's PATH")
        except subprocess.CalledProcessError as e:
            raise Exception(f'ffmpeg processing failed: {e.stderr}')

        slice_path = Path(output_path)
        with open(slice_path, 'rb') as f:
            audio_slice = AudioSlice.objects.create(
                audio_chunk=chunk,
                start_time=start_time,
                end_time=end_time,
                original_text=original_text,
                notes=notes,
                file=File(f, name=slice_path.name)
            )
            if tags:
                audio_slice.tags.set(tags)
            
            return audio_slice
    
    # # Define the output directory relative to MEDIA_ROOT
    # output_dir_name = 'audio_slicer/slices'
    # output_dir_abs = os.path.join(settings.MEDIA_ROOT, output_dir_name)
    # os.makedirs(output_dir_abs, exist_ok=True)

    # # Generate a unique filename for the slice
    # original_filename = os.path.basename(input_path)
    # name, ext = os.path.splitext(original_filename)
    # slice_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    # output_path_abs = os.path.join(output_dir_abs, slice_filename)

    # # Construct the ffmpeg command
    # command = [
    #     'ffmpeg',
    #     '-i', str(input_path),
    #     '-ss', str(start_time),
    #     '-to', str(end_time),
    #     '-c', 'copy',
    #     '-y',
    #     str(output_path_abs)
    # ]

    # try:
    #     print(f"Executing ffmpeg command: {' '.join(command)}") # For debugging
    #     result = subprocess.run(
    #         command,
    #         check=True,
    #         capture_output=True,
    #         text=True
    #     )
    #     # Always print stdout/stderr for debugging
    #     print(f"ffmpeg stdout:\n{result.stdout}")
    #     print(f"ffmpeg stderr:\n{result.stderr}")

    # except FileNotFoundError:
    #     raise Exception("ffmpeg is not installed or not in the system's PATH.")
    # except subprocess.CalledProcessError as e:
    #     # Provide a more informative error message
    #     # Also print stdout/stderr on failure
    #     print(f"ffmpeg stdout on error:\n{e.stdout}")
    #     print(f"ffmpeg stderr on error:\n{e.stderr}")
    #     raise Exception(f"ffmpeg processing failed for chunk {chunk.id}. Stderr: {e.stderr}")

    # # The path to be stored in the FileField must be relative to MEDIA_ROOT
    # relative_slice_path = os.path.join(output_dir_name, slice_filename)

    # # Create an unsaved AudioSlice instance
    # # The file object is not directly associated here. Instead, the path is
    # # assigned to the FileField, and Django handles it upon saving.
    # audio_slice = AudioSlice(
    #     audio_chunk=chunk,
    #     start_time=start_time,
    #     end_time=end_time,
    # )
    # audio_slice.file.name = relative_slice_path
    
    # return audio_slice