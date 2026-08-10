from unittest.mock import patch

from django.test import TestCase

from .models import AudioChunk, Drama, SourceAudio
from .services import _pick_silence_boundaries, _silence_aware_segments, is_english_book
from .signals import _get_tts_script_lines


class EnglishBookSilenceBoundaryTests(TestCase):
    """English Book 特殊切割：在 1 分钟附近静音处切（纯逻辑测试，不需要 ffmpeg）。"""

    def test_picks_nearest_silence_to_each_minute_target(self):
        silences = [
            (8.0, 9.0), (30.0, 32.0), (58.0, 61.0),   # 58-61s 静音 → 切在 59.5
            (90.0, 92.0), (122.0, 125.0),             # 122-125s 静音 → 切在 123.5
            (150.0, 151.0), (178.0, 182.0),           # 178-182s 静音 → 切在 180.0
        ]
        boundaries = _pick_silence_boundaries(240.0, silences)
        self.assertEqual([round(b, 1) for b in boundaries], [59.5, 123.5, 180.0])

    def test_skips_target_without_nearby_silence(self):
        # 只有 10s 和 200s 处有静音，60/120/180 目标点都够不着 → 不切割
        silences = [(10.0, 12.0), (200.0, 205.0)]
        self.assertEqual(_pick_silence_boundaries(240.0, silences), [])

    def test_no_boundaries_for_short_audio(self):
        self.assertEqual(_pick_silence_boundaries(50.0, [(10.0, 12.0)]), [])

    def test_fallback_when_detection_fails(self):
        # ffprobe/ffmpeg 不可用等异常 → 返回 []（调用方回退固定 60s 切割）
        with patch('audio_slicer.services._get_audio_duration', side_effect=FileNotFoundError):
            self.assertEqual(_silence_aware_segments('/nonexistent/audio.mp3'), [])


class EnglishBookScriptTests(TestCase):
    """English Book 脚本：从 corpus.TtsText（task.unit == episode）拼接清洁文本。"""

    def setUp(self):
        self.drama = Drama.objects.create(name="English Book (Grade 5)")

        from corpus.models import CorpusTask, Textbook, TtsText

        textbook = Textbook.objects.create(name="5A新版五上", pdf_file="textbooks/x.pdf")
        task = CorpusTask.objects.create(name="5A新版五上 · Unit 3", textbook=textbook, unit=3)
        TtsText.objects.create(task=task, modules={
            "fun_time": {"text": "Fun time\nHello, boys and girls!", "sentences": []},
            "talking_time": {"text": "Talking time\nA visit", "sentences": []},
            "story_time": {},
            "project": {"text": "Project\nMy week", "sentences": []},
        })

    def _source(self, episode):
        return SourceAudio(drama=self.drama, season=1, episode=episode)

    def test_english_book_detection(self):
        friends = Drama.objects.create(name="Friends")
        self.assertTrue(is_english_book(self._source(3)))
        self.assertFalse(is_english_book(SourceAudio(drama=friends, season=1, episode=3)))

    def test_script_lines_from_tts_text(self):
        lines = _get_tts_script_lines(self._source(3))
        self.assertEqual(lines, [
            "Fun time", "Hello, boys and girls!",
            "Talking time", "A visit",
            "Project", "My week",
        ])

    def test_no_tts_text_returns_empty(self):
        self.assertEqual(_get_tts_script_lines(self._source(9)), [])


class TriggerAudioSlicingEnglishBookTests(TestCase):
    """English Book 上传时：脚本来自 TtsText，不走 fanfr.com ingest_and_translate_script。"""

    def setUp(self):
        from corpus.models import CorpusTask, Textbook, TtsText

        self.drama = Drama.objects.create(name="English Book (Grade 5)")
        textbook = Textbook.objects.create(name="5A新版五上", pdf_file="textbooks/x.pdf")
        task = CorpusTask.objects.create(name="5A新版五上 · Unit 2", textbook=textbook, unit=2)
        TtsText.objects.create(task=task, modules={
            "fun_time": {"text": "Fun time\nHello!", "sentences": []},
            "story_time": {"text": "Story time\nOnce upon a time", "sentences": []},
        })

    @patch('scripts.tasks.translate_script_lines_task')
    @patch('audio_slicer.signals.slice_source_to_chunks')
    def test_english_book_uses_tts_text_script(self, mock_slice, mock_translate):
        # mock 切块：真实切块需要 ffmpeg，这里直接建一个 chunk
        def fake_slice(sa):
            AudioChunk.objects.create(source_audio=sa, chunk_index=1)
        mock_slice.side_effect = fake_slice

        source = SourceAudio.objects.create(drama=self.drama, season=1, episode=2, title="t")

        from scripts.models import ScriptLine, ScriptTask

        lines = ScriptLine.objects.filter(chunk__source_audio=source).order_by('index')
        self.assertEqual([l.text for l in lines], ["Fun time", "Hello!", "Story time", "Once upon a time"])

        task = ScriptTask.objects.get(source_audio=source)
        self.assertEqual(task.status, 'ingesting')  # 翻译由 Huey 任务异步推进
        self.assertEqual(task.ingest_count, 4)
        # 没走 fanfr 的 ingest_and_translate_script，但入队了 TtsText 翻译任务
        mock_translate.assert_called_once_with(task.id)

    @patch('scripts.tasks.ingest_and_translate_script')
    @patch('audio_slicer.signals.slice_source_to_chunks')
    def test_non_english_book_still_schedules_fanfr_task(self, mock_slice, mock_ingest):
        friends = Drama.objects.create(name="Friends")

        source = SourceAudio.objects.create(drama=friends, season=10, episode=13, title="t")

        from scripts.models import ScriptTask
        task = ScriptTask.objects.get(source_audio=source)
        self.assertEqual(task.status, 'pending')
        mock_ingest.assert_called_once_with(task.id)
