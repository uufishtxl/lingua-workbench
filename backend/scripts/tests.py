from unittest.mock import patch

from django.test import TestCase

from .models import RoughSliceTask, ScriptLine, ScriptTask
from .tasks import (
    ROUGH_SLICE_SOURCE,
    _match_line,
    _translate_script_lines,
    align_lines_to_segments,
    rough_slice_chunk,
)
from audio_slicer.models import AudioChunk, AudioSlice, Drama, SourceAudio


class TranslateScriptLinesTests(TestCase):
    """_translate_script_lines：批量翻译未翻译的 ScriptLine（English Book 与 fanfr 共用）。"""

    def setUp(self):
        drama = Drama.objects.create(name="Friends")
        self.source = SourceAudio.objects.create(drama=drama, season=1, episode=1, title="t")
        self.chunk = AudioChunk.objects.create(source_audio=self.source, chunk_index=1)
        self.line = ScriptLine.objects.create(
            chunk=self.chunk, index=0, order=0.0, text="Hello there.", raw_text="Hello there."
        )
        self.script_task = ScriptTask.objects.create(
            source_audio=self.source, status='ingesting', message='x'
        )

    @patch('ai_analysis.services.batch_translate_texts')
    def test_translates_untranslated_lines(self, mock_batch):
        mock_batch.return_value = [{'id': self.line.id, 'translation': '你好。'}]
        result = _translate_script_lines(self.script_task)
        self.assertEqual(result, 1)
        self.line.refresh_from_db()
        self.assertEqual(self.line.text_zh, '你好。')
        self.script_task.refresh_from_db()
        self.assertEqual(self.script_task.status, 'completed')
        self.assertEqual(self.script_task.translate_count, 1)

    @patch('ai_analysis.services.batch_translate_texts')
    def test_all_already_translated_skips(self, mock_batch):
        self.line.text_zh = '已有'
        self.line.save()
        result = _translate_script_lines(self.script_task)
        self.assertEqual(result, 0)
        mock_batch.assert_not_called()
        self.script_task.refresh_from_db()
        self.assertEqual(self.script_task.status, 'completed')

    @patch('ai_analysis.services.batch_translate_texts', side_effect=RuntimeError('LLM down'))
    def test_failure_propagates(self, mock_batch):
        from django.db.models import Q
        with self.assertRaises(RuntimeError):
            _translate_script_lines(self.script_task)


class AlignLinesToSegmentsTests(TestCase):
    """纯逻辑：script 行 ↔ whisper segments 粗略对齐。"""

    def test_line_per_segment_full_match(self):
        segments = [
            {"text": "Hello, boys and girls!", "start": 0.0, "end": 2.0},
            {"text": "Today we talk about animals.", "start": 2.2, "end": 5.0},
            {"text": "A visit to the zoo.", "start": 5.2, "end": 7.0},
        ]
        lines = ["Hello, boys and girls!", "Today we talk about animals.", "A visit to the zoo."]
        ranges = align_lines_to_segments(lines, segments)
        self.assertEqual(ranges[0], (0.0, 2.0))
        self.assertAlmostEqual(ranges[1][0], 2.2, places=1)
        self.assertAlmostEqual(ranges[1][1], 5.0, places=1)
        self.assertAlmostEqual(ranges[2][0], 5.2, places=1)
        self.assertAlmostEqual(ranges[2][1], 7.0, places=1)

    def test_two_lines_inside_one_segment(self):
        # 一个 whisper 段含两个短句 → 按字符比例拆开，且保持顺序
        segments = [{"text": "Hello there. How are you today?", "start": 0.0, "end": 4.0}]
        lines = ["Hello there.", "How are you today?"]
        ranges = align_lines_to_segments(lines, segments)
        self.assertIsNotNone(ranges[0])
        self.assertIsNotNone(ranges[1])
        self.assertLessEqual(ranges[0][1], ranges[1][0] + 0.01)
        self.assertAlmostEqual(ranges[1][1], 4.0, places=1)

    def test_whisper_noise_tolerance(self):
        segments = [
            {"text": "Okay, hello everyone.", "start": 0.0, "end": 1.8},
            {"text": "Um, today's topic is about healthy food.", "start": 2.0, "end": 5.5},
        ]
        lines = ["Hello everyone.", "Today's topic is about healthy food."]
        ranges = align_lines_to_segments(lines, segments)
        self.assertIsNotNone(ranges[0])
        self.assertIsNotNone(ranges[1])
        self.assertLess(ranges[0][0], ranges[1][0])  # 顺序保持

    def test_unmatched_line_returns_none(self):
        segments = [{"text": "Apple banana cherry.", "start": 0.0, "end": 3.0}]
        lines = ["Apple banana cherry.", "This line does not exist in audio"]
        ranges = align_lines_to_segments(lines, segments)
        self.assertEqual(ranges[0], (0.0, 3.0))
        self.assertIsNone(ranges[1])

    def test_empty_inputs(self):
        self.assertEqual(align_lines_to_segments([], []), [])
        self.assertEqual(align_lines_to_segments(["hello"], []), [None])

    def test_punctuation_and_case_normalized(self):
        segments = [{"text": "I can't believe it!", "start": 0.0, "end": 2.0}]
        self.assertIsNotNone(align_lines_to_segments(["I can't believe it"], segments)[0])
        self.assertIsNotNone(align_lines_to_segments(["I cant believe it"], segments)[0])
        self.assertIsNotNone(align_lines_to_segments(["I CAN'T BELIEVE IT"], segments)[0])

    def test_match_line_leftmost_after_pos(self):
        full = "hi bye hi there"
        m = _match_line(full, "hi", 0)
        self.assertEqual(m, (0, 2))
        m = _match_line(full, "hi", 3)  # 跳过一次后匹配第二次出现
        self.assertEqual(m, (7, 9))


class RoughSliceChunkTests(TestCase):
    """rough_slice_chunk：whisper 转写 → 对齐 → 生成 rough AudioSlice 并绑定 ScriptLine。"""

    def setUp(self):
        drama = Drama.objects.create(name="Friends")
        self.source = SourceAudio.objects.create(drama=drama, season=1, episode=1, title="t")
        self.chunk = AudioChunk.objects.create(source_audio=self.source, chunk_index=1)
        self.lines = [
            ScriptLine.objects.create(chunk=self.chunk, index=0, order=0.0, text="Hello there.", raw_text="Hello there."),
            ScriptLine.objects.create(chunk=self.chunk, index=1, order=1.0, text="How are you today?", raw_text="How are you today?"),
            ScriptLine.objects.create(chunk=self.chunk, index=2, order=2.0, text="Goodbye.", raw_text="Goodbye."),
        ]

    @patch('scripts.tasks._whisper_transcribe')
    def test_creates_rough_slices_and_binds_lines(self, mock_transcribe):
        mock_transcribe.return_value = [
            {"text": "Hello there. How are you today?", "start": 0.0, "end": 4.0},
            {"text": "Goodbye!", "start": 4.5, "end": 6.0},
        ]
        result = rough_slice_chunk(self.chunk.id)
        self.assertEqual(result['created'], 3)

        slices = list(AudioSlice.objects.filter(audio_chunk=self.chunk).order_by('start_time'))
        self.assertEqual(len(slices), 3)
        self.assertTrue(all(s.source == ROUGH_SLICE_SOURCE for s in slices))
        # 每行都绑定了自己的 slice
        for line in ScriptLine.objects.filter(chunk=self.chunk).order_by('index'):
            self.assertIsNotNone(line.slice)
        self.assertEqual(slices[0].original_text, "Hello there.")

        self.chunk.refresh_from_db()
        self.assertTrue(self.chunk.has_slices)

        task_obj = RoughSliceTask.objects.get(chunk=self.chunk)
        self.assertEqual(task_obj.status, 'completed')
        self.assertEqual(task_obj.slice_count, 3)

    @patch('scripts.tasks._whisper_transcribe')
    def test_rerun_is_idempotent(self, mock_transcribe):
        mock_transcribe.return_value = [
            {"text": "Hello there. How are you today?", "start": 0.0, "end": 4.0},
            {"text": "Goodbye!", "start": 4.5, "end": 6.0},
        ]
        rough_slice_chunk(self.chunk.id)
        rough_slice_chunk(self.chunk.id)
        # 不会重复堆积（source 标记的旧 rough slices 先删再建）
        self.assertEqual(AudioSlice.objects.filter(audio_chunk=self.chunk).count(), 3)

    @patch('scripts.tasks._whisper_transcribe')
    def test_no_script_lines_fails_cleanly(self, mock_transcribe):
        ScriptLine.objects.all().delete()
        rough_slice_chunk(self.chunk.id)  # 抛异常但任务状态记录为 failed
        task_obj = RoughSliceTask.objects.get(chunk=self.chunk)
        self.assertEqual(task_obj.status, 'failed')

    @patch('scripts.tasks._whisper_transcribe', side_effect=RuntimeError('whisper down'))
    def test_whisper_failure_marks_task_failed(self, mock_transcribe):
        with self.assertRaises(RuntimeError):
            rough_slice_chunk(self.chunk.id)
        task_obj = RoughSliceTask.objects.get(chunk=self.chunk)
        self.assertEqual(task_obj.status, 'failed')
        self.assertIn('whisper down', task_obj.message)
