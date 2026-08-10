import os
import re
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

# ---------------------------------------------------------------------------
# English Book（教科书跟读音频）专用切割参数：在 1 分钟附近的静音处切割
# （对齐句间停顿，避免把句子拦腰截断），而不是严格按固定 60 秒切。
# ---------------------------------------------------------------------------
ENGLISH_BOOK_CHUNK_SECONDS = 60.0   # 目标块长：约 1 分钟
ENGLISH_BOOK_SILENCE_TOLERANCE = 20.0  # 在目标时间 ±20s 内找最近的静音中点
ENGLISH_BOOK_SILENCE_NOISE = '-35dB'   # 静音判定的响度阈值
ENGLISH_BOOK_SILENCE_MIN = '0.5'       # 静音最短持续时间（秒）


def is_english_book(source_audio: SourceAudio) -> bool:
    """判断 source_audio 是否属于 English Book 教科书（drama 名包含 "English Book"）。"""
    return 'english book' in (source_audio.drama.name or '').lower()


def _get_audio_duration(audio_path: str) -> float:
    """用 ffprobe 获取音频时长（秒）。"""
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
        check=True, capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def _detect_silences(audio_path: str) -> list:
    """用 ffmpeg silencedetect 检测静音区间，返回 [(start, end), ...]（秒）。"""
    command = [
        'ffmpeg', '-i', audio_path,
        '-af', f'silencedetect=noise={ENGLISH_BOOK_SILENCE_NOISE}:d={ENGLISH_BOOK_SILENCE_MIN}',
        '-f', 'null', '-',
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    silences = []
    start = None
    for line in result.stderr.splitlines():
        m = re.search(r'silence_start:\s*([\d.]+)', line)
        if m:
            start = float(m.group(1))
            continue
        m = re.search(r'silence_end:\s*([\d.]+)', line)
        if m and start is not None:
            silences.append((start, float(m.group(1))))
            start = None
    return silences


def _pick_silence_boundaries(duration: float, silences: list) -> list:
    """对每个 ~1 分钟目标点（60s/120s/...），在容差内选最近的静音中点作为切分点。

    找不到合适静音的目标点直接跳过（该段会并入相邻块）。
    """
    boundaries = []
    target = ENGLISH_BOOK_CHUNK_SECONDS
    while target < duration - 5:
        best_mid, best_dist = None, ENGLISH_BOOK_SILENCE_TOLERANCE
        for start, end in silences:
            mid = (start + end) / 2
            dist = abs(mid - target)
            if dist < best_dist:
                best_dist, best_mid = dist, mid
        if best_mid is not None:
            boundaries.append(best_mid)
        target += ENGLISH_BOOK_CHUNK_SECONDS
    return boundaries


def _silence_aware_segments(audio_path: str) -> list:
    """English Book 专用：返回 [(start, end), ...] 静音切分区间。

    检测/计算失败或没有可用静音时返回 []（调用方回退固定 60s 切割）。
    """
    try:
        duration = _get_audio_duration(audio_path)
        silences = _detect_silences(audio_path)
        boundaries = _pick_silence_boundaries(duration, silences)
        if not boundaries:
            return []
        segments = []
        starts = [0.0] + boundaries
        ends = boundaries + [duration]
        for start, end in zip(starts, ends):
            if end - start >= 1.0:  # 跳过过短的碎片
                segments.append((start, end))
        return segments
    except Exception as exc:
        print(f"[audio_slicer] English Book 静音切割检测失败，回退固定 60s 切割: {exc}")
        return []


def slice_source_to_chunks(source_audio: SourceAudio):
    """
    Slices a SourceAudio file into ~60-second AudioChunks using ffmpeg.

    English Book 教科书跟读音频特殊处理：在 1 分钟附近的静音处切割
    （对齐句间停顿，避免把句子拦腰截断），而不是严格按固定 60 秒切。
    """
    source_file_path = source_audio.file.path

    # English Book：按静音位置切；其余仍走固定 60s
    segments = _silence_aware_segments(source_file_path) if is_english_book(source_audio) else []

    with tempfile.TemporaryDirectory() as temp_dir:
        output_pattern = os.path.join(temp_dir, 'chunk_%03d.mp3')

        try:
            if segments:
                for i, (start, end) in enumerate(segments):
                    chunk_path = os.path.join(temp_dir, f'chunk_{i + 1:03d}.mp3')
                    command = [
                        'ffmpeg', '-i', source_file_path,
                        '-ss', f'{start:.3f}',
                        '-to', f'{end:.3f}',
                        '-c:a', 'libmp3lame',
                        '-b:a', '192k',
                        '-y', chunk_path,
                    ]
                    subprocess.run(command, check=True, capture_output=True, text=True)
            else:
                command = [
                    'ffmpeg',
                    '-i', source_file_path,
                    '-f', 'segment',
                    '-segment_time', '60',
                    '-c:a', 'libmp3lame',
                    '-b:a', '192k',
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