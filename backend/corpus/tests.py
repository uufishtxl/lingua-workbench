"""
#23 验收用 API 测试（Windows venv 运行：python manage.py test corpus）

覆盖：
- 上传 PDF 创建 Textbook（含 name 自动推导、格式/大小校验）
- 教材列表/详情
- 权限（未认证 401）
"""
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
import tempfile
from unittest.mock import patch
from django.test import override_settings

from .models import CorpusTask, Textbook
from .services import (
    _is_overview_page,
    bucket_modules,
    clean_text,
    locate_unit_range,
    locate_words_region,
)
from .tasks import _run_extract_unit, _run_generate_kps, _run_generate_tts, _run_llm_bucket

User = get_user_model()

# 测试写文件隔离到临时目录，防止污染真实 media/（曾覆盖真书 english_book_5a.pdf）
_TEST_MEDIA = tempfile.mkdtemp(prefix="corpus_test_media_")


def make_pdf_bytes(name="fake.pdf"):
    # PDF 最小合法头（仅用于绕过文件类型判断，不真正解析）
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"


@override_settings(MEDIA_ROOT=_TEST_MEDIA)
class TextbookApiTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass12345")
        self.client.force_authenticate(self.user)

    def _upload(self, **overrides):
        data = {
            "pdf_file": SimpleUploadedFile("english_book_5a.pdf", make_pdf_bytes()),
            "grade": "五年级",
            "semester": "上册",
        }
        data.update(overrides)
        return self.client.post("/api/v1/textbooks/", data, format="multipart")

    def test_upload_creates_textbook_with_auto_name(self):
        resp = self._upload()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["name"], "english_book_5a")
        self.assertEqual(resp.data["grade"], "五年级")
        self.assertEqual(resp.data["semester"], "上册")
        self.assertTrue(resp.data["pdf_url"].startswith("/media/textbooks/"))

    def test_upload_with_explicit_name(self):
        resp = self._upload(name="5A新版五上")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["name"], "5A新版五上")

    def test_upload_rejects_non_pdf(self):
        resp = self._upload(pdf_file=SimpleUploadedFile("book.txt", b"hello"))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_textbooks(self):
        self._upload(name="5A新版五上")
        self._upload(name="5A新版五下")
        resp = self.client.get("/api/v1/textbooks/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in resp.data["results"]]
        self.assertIn("5A新版五上", names)

    def test_detail_textbook(self):
        created = self._upload(name="5A新版五上")
        pk = created.data["id"]
        resp = self.client.get(f"/api/v1/textbooks/{pk}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "5A新版五上")

    def test_unauthenticated_rejected(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/v1/textbooks/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_parsed_cache_fields_not_exposed(self):
        resp = self._upload()
        self.assertNotIn("parsed_pages", resp.data)
        self.assertNotIn("words_by_unit", resp.data)


# ===========================================================================
# S2 服务层单测（纯函数，fixture 文本）
# ===========================================================================

FIXTURE_PAGES = [
    {"page": 1, "text": "Contents\nTopic words\nFun time\nTalking time\nStory time\nProject\nWords to use\n1"},
    {"page": 2, "text": "Unit 1 preview\nSome words here.\n2"},
    {"page": 3, "text": "Unit 2\nTopic words\nkite-flying\ntug of war\nhopscotch\n17\nFun time\nWelcome to our garden party!\nSound ar garden\n18"},
    {"page": 4, "text": "Talking time\nAs fast as the wind\nMr Zhong, is this Shaolin kung fu?\nFind the rule\nLook at us.\n19\nStory time\nThe dragon dance\nMinmin runs very fast."},
    {"page": 5, "text": "Project\nA presentation of my favourite game\nStep1 Choose a game.\n20"},
    {"page": 6, "text": "Unit 3\nTopic words\nnew words\n21"},
    {"page": 7, "text": "Words to use\nUnit 1 words\nUnit 2 words\nUnit 3 words\n22"},
]

FIXTURE_PAGE_TEXTS = [p["text"] for p in FIXTURE_PAGES]


class CleanTextTests(APITestCase):
    def test_removes_isolated_page_numbers(self):
        text = "kite-flying\ntug of war\n17\nFun time\n18"
        cleaned, removed = clean_text(text)
        self.assertNotIn("17", cleaned)
        self.assertNotIn("18", cleaned)
        self.assertIn("kite-flying", cleaned)
        self.assertEqual(removed, [17, 18])

    def test_joins_hard_wrapped_lines(self):
        # 上一行以逗号结尾 → 续行
        text = "I use all my strength,\nfor every action."
        cleaned, _ = clean_text(text)
        self.assertIn("strength, for every action.", cleaned)

    def test_joins_content_keeps_title_boundaries(self):
        # 标题后的小写内容被接行；大写开头的下一标题触发新行
        text = "Topic words\nkite-flying\ntug of war\nFun time\nparty"
        cleaned, _ = clean_text(text)
        self.assertIn("Topic words kite-flying tug of war", cleaned)
        self.assertIn("Fun time party", cleaned)

    def test_does_not_remove_inline_numbers(self):
        # 填空占位数字在句子内，不是独立成行，必须保留
        text = "12 kinds of 1\nstand like a 2"
        cleaned, _ = clean_text(text)
        self.assertIn("12 kinds of 1", cleaned)
        self.assertIn("stand like a 2", cleaned)


class BucketModulesTests(APITestCase):
    def test_buckets_six_modules(self):
        text = (
            "Topic words\nkite-flying / tug of war\n\n"
            "Fun time\nWelcome to our garden party!\n\n"
            "Talking time\nAs fast as the wind\n\n"
            "Story time\nThe dragon dance\n\n"
            "Project\nA presentation\n\n"
            "Words to use\nUnit 2 words"
        )
        result = bucket_modules(text)
        self.assertEqual(list(result.keys()), ["topic_words", "fun_time", "talking_time", "story_time", "project", "words_to_use"])
        self.assertIn("kite-flying", result["topic_words"])
        self.assertIn("garden party", result["fun_time"])
        self.assertIn("wind", result["talking_time"])
        self.assertIn("dragon dance", result["story_time"])
        self.assertIn("presentation", result["project"])
        self.assertIn("Unit 2 words", result["words_to_use"])

    def test_missing_module_is_none(self):
        text = "Topic words\nkite-flying\nFun time\nparty"
        result = bucket_modules(text)
        self.assertIsNone(result["story_time"])
        self.assertIsNone(result["words_to_use"])
        self.assertIsNotNone(result["topic_words"])


    def test_bucket_handles_variant_titles(self):
        # 变体标题：Chant time → fun_time，Reading time → story_time
        text = (
            "Topic words\nkite-flying\n\n"
            "Chant time\nWe sing and dance.\n\n"
            "Talking time\nAs fast as the wind\n\n"
            "Reading time\nThe dragon dance\n\n"
            "Project\nA presentation\n\n"
            "Words to use\nUnit 2 words"
        )
        result = bucket_modules(text)
        self.assertIn("sing and dance", result["fun_time"])
        self.assertIn("dragon dance", result["story_time"])
        self.assertIn("kite-flying", result["topic_words"])
        self.assertIn("Unit 2 words", result["words_to_use"])


    def test_bucket_after_clean(self):
        # 真实流程：先清洗（接行）再分桶，锚点必须容忍行首匹配
        raw = "Topic words\nkite-flying / tug of war\n17\nFun time\nWelcome to our garden party!"
        cleaned, _ = clean_text(raw)
        result = bucket_modules(cleaned)
        self.assertIn("kite-flying", result["topic_words"])
        self.assertIn("garden party", result["fun_time"])


class LocateUnitRangeTests(APITestCase):
    def test_finds_range_between_units(self):
        (start, end), err, warnings = locate_unit_range(FIXTURE_PAGE_TEXTS, 2)
        self.assertIsNone(err)
        self.assertEqual((start, end), (2, 5))  # 页 3 到页 5（不含 Unit 3 页）

    def test_missing_start_returns_error(self):
        rng, err, warnings = locate_unit_range(FIXTURE_PAGE_TEXTS, 99)
        self.assertIsNone(rng)
        self.assertIn("未找到起点", err)

    def test_missing_end_warns_and_takes_rest(self):
        pages = ["Unit 5\ncontent", "more content"]
        (start, end), err, warnings = locate_unit_range(pages, 5)
        self.assertEqual((start, end), (0, 2))
        self.assertTrue(any("取到最后一页" in w for w in warnings))

    def test_skips_overview_page(self):
        # 起点页是单元总览页（含多个模块标题+摘要）→ 自动跳到下一页
        pages = [
            "Unit 2\nBig task Topic words Fun time\ntraditional game of war\nProject Story time\nMaking a presentation",
            "Topic words\nkite-flying\ntug of war\n17",
            "Unit 3\nTopic words\nnew words",
        ]
        (start, end), err, warnings = locate_unit_range(pages, 2)
        self.assertEqual((start, end), (1, 2))
        self.assertTrue(any("总览" in w for w in warnings))

    def test_no_overview_no_skip(self):
        # 正文页直接开始（仅 1 个模块标题）→ 不跳过
        pages = ["Unit 2\nTopic words\nkite-flying", "more"]
        (start, end), err, warnings = locate_unit_range(pages, 2)
        self.assertEqual((start, end), (0, 2))
        self.assertFalse(any("总览" in w for w in warnings))

    def test_talking_page_not_misjudged_as_overview(self):
        # Talking time 正文页含 Talking time + Find the rule（子内容）→ 不算总览页
        self.assertFalse(_is_overview_page("Talking time\nAs fast as the wind\nFind the rule\nLook at us."))
        # 总览页含 5 个互斥模块 → 算
        self.assertTrue(_is_overview_page("Unit 2\nBig task Topic words Fun time\nTalking time Story time Project"))


class LocateWordsRegionTests(APITestCase):
    def test_skips_front_quarter_toc(self):
        # 页 1 目录含 "Words to use" 字样，但新算法排除前 1/4 页后从页 6 开始
        region = locate_words_region(FIXTURE_PAGE_TEXTS)
        self.assertEqual(region, (6, 7))  # 页 7 到最后一页

    def test_not_found(self):
        pages = ["a", "b", "c", "d", "e", "f", "g", "h"]
        self.assertIsNone(locate_words_region(pages))

    def test_too_few_pages(self):
        self.assertIsNone(locate_words_region(["a", "b", "c"]))


# ===========================================================================
# S2 extract_unit 任务测试（mock PDF 层）
# ===========================================================================

@override_settings(MEDIA_ROOT=_TEST_MEDIA)
class ExtractTaskTests(APITestCase):
    def setUp(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.user = get_user_model().objects.create_user(username="tester2", password="pass12345")
        self.client.force_authenticate(self.user)
        self.textbook = Textbook.objects.create(
            name="5A新版五上",
            grade="五年级",
            semester="上册",
            pdf_file=SimpleUploadedFile("english_book_5a.pdf", make_pdf_bytes()),
        )

    @patch("corpus.tasks.has_text_layer")
    @patch("corpus.tasks.extract_pages")
    def test_extract_task_success(self, mock_extract, mock_has_layer):
        mock_has_layer.return_value = 5
        mock_extract.return_value = list(FIXTURE_PAGE_TEXTS)

        task = CorpusTask.objects.create(
            name="5A新版五上 · Unit 2", textbook=self.textbook, unit=2
        )
        _run_extract_unit(task.id)

        task.refresh_from_db()
        self.assertEqual(task.extract_status, "done")
        self.assertEqual(task.stage, 1)
        # raw_pages 不可变原始文本
        self.assertEqual(len(task.raw_pages), 3)
        self.assertEqual(task.raw_pages[0]["page"], 3)
        # 清洗后分桶
        self.assertIn("kite-flying", task.cleaned_modules["topic_words"])
        self.assertIsNotNone(task.cleaned_modules["talking_time"])
        # 词表区域缓存
        self.textbook.refresh_from_db()
        self.assertEqual(self.textbook.words_region_pages, {"start_page": 7, "end_page_exclusive": 8})

    @patch("corpus.tasks.has_text_layer")
    @patch("corpus.tasks.extract_pages")
    def test_extract_task_unit_missing(self, mock_extract, mock_has_layer):
        mock_has_layer.return_value = 5
        mock_extract.return_value = list(FIXTURE_PAGE_TEXTS)

        task = CorpusTask.objects.create(
            name="5A新版五上 · Unit 99", textbook=self.textbook, unit=99
        )
        _run_extract_unit(task.id)

        task.refresh_from_db()
        self.assertEqual(task.extract_status, "error")
        self.assertIn("未找到起点", task.extract_error)

    @patch("corpus.tasks.has_text_layer")
    @patch("corpus.tasks.extract_pages")
    def test_extract_text_layer_warning_but_succeeds(self, mock_extract, mock_has_layer):
        # has_text_layer 误报 0（trials 同款检测正则不匹配时）→ 软警告，不拦截
        mock_has_layer.return_value = 0
        mock_extract.return_value = list(FIXTURE_PAGE_TEXTS)

        task = CorpusTask.objects.create(
            name="5A新版五上 · Unit 2", textbook=self.textbook, unit=2
        )
        _run_extract_unit(task.id)

        task.refresh_from_db()
        self.assertEqual(task.extract_status, "done")
        self.assertIn("文本层", task.extract_error)

    @patch("corpus.tasks.has_text_layer")
    @patch("corpus.tasks.extract_pages")
    def test_extract_empty_text_rejected_as_scanned(self, mock_extract, mock_has_layer):
        # 真扫描版：提取结果全空 → 报错
        mock_has_layer.return_value = 0
        mock_extract.return_value = ["", "", ""]

        task = CorpusTask.objects.create(
            name="5A新版五上 · Unit 2", textbook=self.textbook, unit=2
        )
        _run_extract_unit(task.id)

        task.refresh_from_db()
        self.assertEqual(task.extract_status, "error")
        self.assertIn("OCR", task.extract_error)

    @patch("corpus.tasks.has_text_layer")
    @patch("corpus.tasks.extract_pages")
    def test_extract_caches_parsed_pages(self, mock_extract, mock_has_layer):
        mock_has_layer.return_value = 5
        mock_extract.return_value = list(FIXTURE_PAGE_TEXTS)

        task = CorpusTask.objects.create(
            name="5A新版五上 · Unit 2", textbook=self.textbook, unit=2
        )
        _run_extract_unit(task.id)
        self.textbook.refresh_from_db()
        self.assertEqual(len(self.textbook.parsed_pages), 7)
        self.assertIsNotNone(self.textbook.parsed_at)

        # 第二次任务不应重新解析
        mock_extract.reset_mock()
        task2 = CorpusTask.objects.create(
            name="5A新版五上 · Unit 3", textbook=self.textbook, unit=3
        )
        _run_extract_unit(task2.id)
        mock_extract.assert_not_called()


# ===========================================================================
# S2 API 测试
# ===========================================================================

@override_settings(MEDIA_ROOT=_TEST_MEDIA)
class CorpusTaskApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester3", password="pass12345")
        self.client.force_authenticate(self.user)
        self.textbook = Textbook.objects.create(
            name="5A新版五上",
            pdf_file=SimpleUploadedFile("english_book_5a.pdf", make_pdf_bytes()),
        )

    @patch("corpus.views.extract_unit_task")
    def test_create_task_enqueues_extraction(self, mock_task):
        resp = self.client.post("/api/v1/corpus-tasks/", {"textbook": self.textbook.id, "unit": 2})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["name"], "5A新版五上 · Unit 2")
        self.assertEqual(resp.data["stage"], 0)
        self.assertEqual(resp.data["extract_status"], "pending")
        mock_task.assert_called_once()

    def test_create_task_requires_unit(self):
        resp = self.client.post("/api/v1/corpus-tasks/", {"textbook": self.textbook.id})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("corpus.views.extract_unit_task")
    def test_retrieve_task_for_polling(self, mock_task):
        created = self.client.post("/api/v1/corpus-tasks/", {"textbook": self.textbook.id, "unit": 2})
        pk = created.data["id"]
        resp = self.client.get(f"/api/v1/corpus-tasks/{pk}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("extract_status", resp.data)

    def test_list_tasks(self):
        CorpusTask.objects.create(name="t1", textbook=self.textbook, unit=1)
        resp = self.client.get("/api/v1/corpus-tasks/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)


# ===========================================================================
# S3/S4 API 测试：仪表盘统计 + 总览计算字段 + 删除
# ===========================================================================

@override_settings(MEDIA_ROOT=_TEST_MEDIA)
class CorpusStatsAndOverviewTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester4", password="pass12345")
        self.client.force_authenticate(self.user)
        self.textbook = Textbook.objects.create(
            name="5A新版五上",
            pdf_file=SimpleUploadedFile("stats_book.pdf", make_pdf_bytes()),
        )
        self.raw_pages = [
            {"page": 3, "text": "Unit 2\nTopic words\nkite-flying\nFun time\nparty"},
            {"page": 4, "text": "Talking time\nwind\nStory time\ndragon"},
        ]
        self.modules = {
            "topic_words": "Topic words kite-flying tug of war",
            "fun_time": "Welcome to our garden party!",
            "talking_time": "As fast as the wind",
            "story_time": "The dragon dance",
            "project": None,
            "words_to_use": "traditional / Chinese yo-yo / kite-flying / dragon dance",
        }

    def _mk_task(self, unit=2, status_="draft", stage=1, with_data=True):
        return CorpusTask.objects.create(
            name=f"5A新版五上 · Unit {unit}",
            textbook=self.textbook,
            unit=unit,
            status=status_,
            stage=stage,
            raw_pages=self.raw_pages if with_data else None,
            cleaned_modules=self.modules if with_data else None,
            extract_status="done",
        )

    def test_stats_counts(self):
        self._mk_task(unit=2, status_="completed")
        self._mk_task(unit=3, status_="completed")
        self._mk_task(unit=4, status_="proofreading")
        self._mk_task(unit=2)  # 重复 unit 不应计入覆盖单元数
        resp = self.client.get("/api/v1/corpus-tasks/stats/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total"], 4)
        self.assertEqual(resp.data["completed"], 2)
        self.assertEqual(resp.data["in_progress"], 2)
        self.assertEqual(resp.data["units_covered"], 3)  # unit 2,3,4

    def test_stats_empty(self):
        resp = self.client.get("/api/v1/corpus-tasks/stats/")
        self.assertEqual(resp.data, {"total": 0, "completed": 0, "in_progress": 0, "units_covered": 0})

    def test_overview_computed_fields(self):
        task = self._mk_task()
        resp = self.client.get(f"/api/v1/corpus-tasks/{task.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total_chars"], len(self.raw_pages[0]["text"]) + len(self.raw_pages[1]["text"]))
        self.assertEqual(resp.data["page_start"], 3)
        self.assertEqual(resp.data["page_end"], 4)
        self.assertEqual(resp.data["module_count"], 5)  # 6 模块中 5 个非空
        self.assertEqual(resp.data["words_count"], 6)

    def test_overview_computed_fields_without_data(self):
        task = self._mk_task(with_data=False)
        resp = self.client.get(f"/api/v1/corpus-tasks/{task.id}/")
        self.assertEqual(resp.data["total_chars"], 0)
        self.assertEqual(resp.data["page_start"], None)
        self.assertEqual(resp.data["module_count"], 0)
        self.assertEqual(resp.data["words_count"], 0)

    @patch("corpus.views.extract_unit_task")
    def test_delete_task(self, mock_task):
        task = self._mk_task()
        resp = self.client.delete(f"/api/v1/corpus-tasks/{task.id}/")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(CorpusTask.objects.filter(id=task.id).exists())


# ===========================================================================
# S5 LLM 归整测试（#27）：容错解析 + 归整任务 + bucket action
# ===========================================================================

class ParseJsonResponseTests(APITestCase):
    def test_plain_json(self):
        from .llm import parse_json_response
        self.assertEqual(parse_json_response('{"a": 1}'), {"a": 1})

    def test_code_fence(self):
        from .llm import parse_json_response
        content = '```json\n{"a": "b"}\n```'
        self.assertEqual(parse_json_response(content), {"a": "b"})

    def test_surrounding_text(self):
        from .llm import parse_json_response
        content = '好的，结果如下：{"topic_words": "kite-flying"} 完'
        self.assertEqual(parse_json_response(content), {"topic_words": "kite-flying"})

    def test_invalid_raises(self):
        from .llm import parse_json_response
        with self.assertRaises(Exception):
            parse_json_response("不是 JSON")


@override_settings(MEDIA_ROOT=_TEST_MEDIA)
class LlmBucketTaskTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester5", password="pass12345")
        self.client.force_authenticate(self.user)
        self.textbook = Textbook.objects.create(
            name="5A新版五上",
            pdf_file=SimpleUploadedFile("bucket_book.pdf", make_pdf_bytes()),
            parsed_pages=[{"page": i + 1, "text": f"page{i + 1} text"} for i in range(8)],
            words_region_pages={"start_page": 7, "end_page_exclusive": 9},
        )
        self.task = CorpusTask.objects.create(
            name="5A新版五上 · Unit 2",
            textbook=self.textbook,
            unit=2,
            extract_status="done",
            cleaned_modules={
                "topic_words": "kite-flying / tug of war",
                "fun_time": "Welcome to our garden party!",
                "talking_time": "As fast as the wind",
                "story_time": "The dragon dance",
                "project": None,
                "words_to_use": None,
            },
        )
    @patch("corpus.tasks.bucket_modules_with_llm")
    def test_bucket_task_success(self, mock_llm):
        # LLM 返回结构化模块（含标题/列表/语法点/步骤）
        mock_llm.return_value = {
            "topic_words": {"title": "Topic Words", "items": ["kite-flying", "tug of war"]},
            "fun_time": {"title": "Welcome to our garden party!", "content": "party!", "sound": "Sound ar garden"},
            "talking_time": {"title": "As fast as the wind", "content": "wind", "grammar_tip": "Look at us."},
            "story_time": {"title": "The dragon dance", "content": "dragon dance"},
            "project": {"title": "A presentation", "sections": [{"title": "B Introduce", "steps": [{"title": "Step 1", "content": "Choose"}]}]},
            "words_to_use": {"title": "Words to use", "items": ["traditional", "yo-yo"]},
        }
        _run_llm_bucket(self.task.id)

        self.task.refresh_from_db()
        self.assertEqual(self.task.bucket_status, "done")
        self.assertEqual(list(self.task.cleaned_modules.keys()), [
            "topic_words", "fun_time", "talking_time", "story_time", "project", "words_to_use",
        ])
        self.assertEqual(self.task.cleaned_modules["words_to_use"]["items"], ["traditional", "yo-yo"])
        self.assertEqual(self.task.cleaned_modules["talking_time"]["grammar_tip"], "Look at us.")
        self.assertEqual(self.task.cleaned_modules["project"]["sections"][0]["steps"][0]["title"], "Step 1")
    @patch("corpus.tasks.bucket_modules_with_llm")
    def test_bucket_task_missing_module_becomes_none(self, mock_llm):
        # LLM 返回缺键 → 规范化为 None
        mock_llm.return_value = {"topic_words": {"title": "Topic Words", "items": ["kite-flying"]}}
        _run_llm_bucket(self.task.id)
        self.task.refresh_from_db()
        self.assertEqual(self.task.cleaned_modules["project"], None)
        self.assertEqual(self.task.cleaned_modules["topic_words"]["items"], ["kite-flying"])
    @patch("corpus.tasks.bucket_modules_with_llm")
    def test_bucket_task_llm_failure(self, mock_llm):
        mock_llm.side_effect = RuntimeError("API down")
        _run_llm_bucket(self.task.id)
        self.task.refresh_from_db()
        self.assertEqual(self.task.bucket_status, "error")
        self.assertIn("API down", self.task.bucket_error)
    @patch("corpus.tasks.bucket_modules_with_llm")
    def test_bucket_truncates_long_input(self, mock_llm):
        # 输入超限 → 截断 + 提示
        huge = {k: "word " * 10000 for k in ["topic_words", "fun_time"]}
        self.task.cleaned_modules = huge
        self.task.save(update_fields=["cleaned_modules"])
        mock_llm.return_value = {"topic_words": {"title": "T", "items": ["x"]}, "fun_time": {"title": "F", "content": "y"},
                                 "talking_time": None, "story_time": None, "project": None, "words_to_use": None}
        _run_llm_bucket(self.task.id)
        self.task.refresh_from_db()
        self.assertEqual(self.task.bucket_status, "done")
        self.assertIn("截断", self.task.bucket_error)

    def test_bucket_accepts_structured_input(self):
        # 重新归整：cleaned_modules 已是结构化 dict → 拍平成文本输入，不报错
        from .tasks import _module_to_text
        self.task.cleaned_modules = {
            "topic_words": {"title": "Topic Words", "items": ["kite-flying"]},
            "fun_time": {"title": "party", "content": "Welcome!", "sound": "Sound ar"},
            "talking_time": {"title": "wind", "content": "dialogue", "grammar_tip": "rule"},
            "story_time": {"title": "dragon", "content": "story"},
            "project": {"title": "pres", "content": "Kite is my fav.",
                        "sections": [{"title": "B Intro", "steps": [{"title": "Step 1", "content": "choose"}]}]},
            "words_to_use": {"title": "WtU", "items": ["trad"]},
        }
        self.task.save(update_fields=["cleaned_modules"])
        with patch("corpus.tasks.bucket_modules_with_llm") as mock_llm:
            mock_llm.return_value = {
                "topic_words": {"title": "T", "items": ["a"]}, "fun_time": {"title": "F", "content": "x"},
                "talking_time": {"title": "T2", "content": "y"}, "story_time": {"title": "S", "content": "z"},
                "project": None, "words_to_use": {"title": "W", "items": ["b"]},
            }
            _run_llm_bucket(self.task.id)
        self.task.refresh_from_db()
        self.assertEqual(self.task.bucket_status, "done")
        # LLM 收到的输入包含结构化的各个部分
        input_text = mock_llm.call_args[0][0]
        self.assertIn("Kite is my fav.", input_text)
        self.assertIn("Sound ar", input_text)

    @patch("corpus.views.llm_bucket_task")
    def test_bucket_action_triggers(self, mock_task):
        resp = self.client.post(f"/api/v1/corpus-tasks/{self.task.id}/bucket/")
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(resp.data["bucket_status"], "pending")
        mock_task.assert_called_once()
    @patch("corpus.tasks.bucket_modules_with_llm")
    def test_bucket_words_to_use_fallback(self, mock_llm):
        # LLM 未返回 words_to_use（词表提取失败）→ 用 topic_words 兜底，避免空白
        mock_llm.return_value = {
            "topic_words": {"title": "Topic Words", "items": ["kite-flying", "tug of war"]},
            "fun_time": {"title": "F", "content": "party"},
            "talking_time": {"title": "T", "content": "wind"},
            "story_time": {"title": "S", "content": "dragon"},
            "project": None,
            "words_to_use": None,
        }
        _run_llm_bucket(self.task.id)
        self.task.refresh_from_db()
        wtu = self.task.cleaned_modules["words_to_use"]
        self.assertIsNotNone(wtu)
        self.assertEqual(wtu["items"], ["kite-flying", "tug of war"])
    @patch("corpus.tasks.bucket_modules_with_llm")
    def test_bucket_topic_words_fallback_from_mechanical(self, mock_llm):
        # LLM 归整丢 topic_words → 用机械分桶原始值恢复（比词表准确，来自正文）
        mock_llm.return_value = {
            "topic_words": None,
            "fun_time": {"title": "F", "content": "x"},
            "talking_time": {"title": "T", "content": "y"},
            "story_time": {"title": "S", "content": "z"},
            "project": None,
            "words_to_use": {"title": "Words to use", "items": ["root", "stem", "water lily"]},
        }
        _run_llm_bucket(self.task.id)
        self.task.refresh_from_db()
        tp = self.task.cleaned_modules["topic_words"]
        self.assertIsNotNone(tp)
        # 机械分桶原始值（setUp 里 "kite-flying / tug of war" 文本格式）
        self.assertEqual(tp["items"], ["kite-flying", "tug of war"])
    @patch("corpus.tasks.bucket_modules_with_llm")
    def test_bucket_words_to_use_kept_when_present(self, mock_llm):
        # LLM 正常返回 words_to_use → 不覆盖
        mock_llm.return_value = {
            "topic_words": {"title": "Topic Words", "items": ["kite-flying"]},
            "fun_time": {"title": "F", "content": "x"},
            "talking_time": {"title": "T", "content": "y"},
            "story_time": {"title": "S", "content": "z"},
            "project": None,
            "words_to_use": {"title": "Words to use", "items": ["traditional", "dragon dance"]},
        }
        _run_llm_bucket(self.task.id)
        self.task.refresh_from_db()
        self.assertEqual(self.task.cleaned_modules["words_to_use"]["items"], ["traditional", "dragon dance"])


# ===========================================================================
# S5 LLM 调用降级重试（#27）：json_object 失败（含空返回）自动降级
# ===========================================================================

class LlmRetryTests(APITestCase):
    def test_json_mode_empty_then_retry_succeeds(self):
        # 第一次 json_mode 返回空内容（parse 失败）→ 自动降级重试成功
        from types import SimpleNamespace
        from unittest.mock import Mock
        from corpus.llm import bucket_modules_with_llm

        with patch("ai_analysis.services.get_llm") as mock_get_llm:
            first = Mock()
            first.invoke.return_value = SimpleNamespace(content="")
            second = Mock()
            second.invoke.return_value = SimpleNamespace(
                content='{"topic_words": {"title": "T", "items": ["a"]}}'
            )
            mock_get_llm.side_effect = [first, second]

            result = bucket_modules_with_llm("text", "words", 2)

        self.assertEqual(result["topic_words"]["items"], ["a"])
        # 第二次调用不带 json_object
        _, kwargs = mock_get_llm.call_args_list[1]
        self.assertNotIn("model_kwargs", kwargs)

    def test_both_fail_raises_diagnostic(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from corpus.llm import bucket_modules_with_llm

        with patch("ai_analysis.services.get_llm") as mock_get_llm:
            llm = Mock()
            llm.invoke.return_value = SimpleNamespace(content=None)
            mock_get_llm.return_value = llm

            with self.assertRaises(RuntimeError) as ctx:
                bucket_modules_with_llm("text", "words", 2)

        self.assertIn("连续失败", str(ctx.exception))



# ===========================================================================
# S2 双栏分栏提取（#27 增强）：对话页按 x 坐标左→右阅读序
# ===========================================================================

class SplitColumnsTests(APITestCase):
    def test_detects_two_columns_left_to_right(self):
        from .services import split_columns
        words = []
        # 左栏 6 行、右栏 6 行交错（模拟双栏对话页）
        for i in range(6):
            words.append({"text": f"left-{i}", "x0": 50, "x1": 90, "top": 10 + i * 10})
            words.append({"text": f"right-{i}", "x0": 400, "x1": 440, "top": 10 + i * 10})
        left, right = split_columns(words, 600)
        self.assertEqual(left, "\n".join(f"left-{i}" for i in range(6)))
        self.assertEqual(right, "\n".join(f"right-{i}" for i in range(6)))

    def test_single_column_returns_none(self):
        from .services import split_columns
        words = [
            {"text": f"w{i}", "x0": 50 + i * 20, "x1": 70 + i * 20, "top": 10 + i * 10}
            for i in range(10)
        ]
        self.assertIsNone(split_columns(words, 600))

    def test_too_few_words_returns_none(self):
        from .services import split_columns
        self.assertIsNone(split_columns([{"text": "a", "x0": 0, "x1": 10, "top": 0}], 600))


# ===========================================================================
# S6 KP 生成/保存/状态机测试（#28）
# ===========================================================================

@override_settings(MEDIA_ROOT=_TEST_MEDIA)
class GenerateKpsTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester6", password="pass12345")
        self.client.force_authenticate(self.user)
        self.textbook = Textbook.objects.create(
            name="5A新版五上",
            pdf_file=SimpleUploadedFile("kp_book.pdf", make_pdf_bytes()),
        )
        self.task = CorpusTask.objects.create(
            name="5A新版五上 · Unit 2",
            textbook=self.textbook,
            unit=2,
            extract_status="done",
            bucket_status="done",
            cleaned_modules={
                "topic_words": {"title": "Topic Words", "items": ["kite-flying", "tug of war"]},
                "fun_time": {"title": "party", "content": "Welcome!", "sound": "Sound ar garden\nFind a star."},
                "talking_time": {"title": "As fast as the wind", "content": "dialogue", "grammar_tip": "Look at us.\nStand like a pine tree."},
                "story_time": {"title": "The dragon dance", "content": "The students train hard."},
                "project": {"title": "A presentation", "content": "Kite-flying is my favourite game."},
                "words_to_use": {"title": "Words to use", "items": ["traditional", "kite-flying"]},
            },
        )

    @patch("corpus.tasks.generate_kp_summary")
    @patch("corpus.tasks.add_ipa_to_vocabulary")
    def test_kp_generation_rules_and_summary(self, mock_ipa, mock_summary):
        mock_summary.return_value = "舞龙队刻苦训练的故事。"
        mock_ipa.return_value = "kite-flying /ˈkaɪtflaɪɪŋ/\ntug of war\ntraditional /trəˈdɪʃənl/"
        _run_generate_kps(self.task.id)

        self.task.refresh_from_db()
        self.assertEqual(self.task.kp_status, "done")
        kp = self.task.knowledge_points
        # 词汇合并去重（topic_words + words_to_use）→ LLM 补音标
        mock_ipa.assert_called_once_with(["kite-flying", "tug of war", "traditional"])
        self.assertEqual(kp["vocabulary"], "kite-flying /ˈkaɪtflaɪɪŋ/\ntug of war\ntraditional /trəˈdɪʃənl/")
        # 语法来自 Find the rule
        self.assertIn("Look at us.", kp["grammar"])
        # 拼读来自 Sound
        self.assertIn("Sound ar garden", kp["phonics"])
        # Big Task 来自 Project 范文
        self.assertIn("Kite-flying is my favourite", kp["big_task"])
        # 梗概来自 LLM
        self.assertEqual(kp["summary"], "舞龙队刻苦训练的故事。")
        # 短语/句型留空（MVP）
        self.assertEqual(kp["phrases"], "")
        self.assertEqual(kp["sentence_patterns"], "")

    @patch("corpus.tasks.generate_kp_summary")
    @patch("corpus.tasks.add_ipa_to_vocabulary")
    def test_kp_serializer_exposes_and_progress(self, mock_ipa, mock_summary):
        mock_summary.return_value = "梗概"
        mock_ipa.return_value = ""  # IPA 失败 → 回退规则文本
        _run_generate_kps(self.task.id)
        resp = self.client.get(f"/api/v1/corpus-tasks/{self.task.id}/")
        self.assertEqual(resp.data["kp_progress"], 5)  # 词汇/语法/拼读/梗概/范文 = 5（短语/句型空）
        self.assertIn("knowledge_points", resp.data)

    def test_generate_kps_missing_task_silent(self):
        # 任务已被删除 → 静默返回不抛异常
        _run_generate_kps(999999)

    @patch("corpus.tasks.generate_kp_summary")
    @patch("corpus.tasks.add_ipa_to_vocabulary")
    def test_save_kp_and_complete(self, mock_ipa, mock_summary):
        mock_summary.return_value = "梗概"
        mock_ipa.return_value = ""
        _run_generate_kps(self.task.id)

        # 保存 KP（编辑已完成任务 → 退回 proofreading）
        resp = self.client.patch(
            f"/api/v1/corpus-tasks/{self.task.id}/",
            {"knowledge_points": {"vocabulary": "手动修改", "summary": "新梗概"}},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.knowledge_points["vocabulary"], "手动修改")

        # 完成校订
        resp = self.client.post(f"/api/v1/corpus-tasks/{self.task.id}/complete/")
        self.assertEqual(resp.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "completed")

        # 再保存 → 自动退回 proofreading
        resp = self.client.patch(
            f"/api/v1/corpus-tasks/{self.task.id}/",
            {"knowledge_points": {"summary": "再次编辑"}},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "proofreading")


# ===========================================================================
# S7 AI 修复 / 重新生成测试（#29）：预览不落盘 + 应用写库
# ===========================================================================

@override_settings(MEDIA_ROOT=_TEST_MEDIA)
class AiFixTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester7", password="pass12345")
        self.client.force_authenticate(self.user)
        self.textbook = Textbook.objects.create(
            name="5A新版五上",
            pdf_file=SimpleUploadedFile("fix_book.pdf", make_pdf_bytes()),
        )
        self.task = CorpusTask.objects.create(
            name="5A新版五上 · Unit 2",
            textbook=self.textbook,
            unit=2,
            bucket_status="done",
            cleaned_modules={
                "topic_words": {"title": "Topic Words", "items": ["kite-flying", "tug of war"]},
                "fun_time": {"title": "F", "content": "x"},
                "talking_time": {"title": "T", "content": "y"},
                "story_time": {"title": "S", "content": "z"},
                "project": None,
                "words_to_use": {"title": "W", "items": ["trad"]},
            },
            knowledge_points={"vocabulary": "kite-flying / tug of war", "summary": "旧梗概"},
        )

    @patch("corpus.views.fix_module_with_llm")
    def test_fix_module_preview_not_persisted(self, mock_fix):
        mock_fix.return_value = {"title": "Topic Words", "items": ["kite-flying", "tug of war", "hopscotch"]}
        resp = self.client.post(
            f"/api/v1/corpus-tasks/{self.task.id}/fix-module/",
            {"module_key": "topic_words", "instruction": "补上 hopscotch"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["new_content"]["items"][-1], "hopscotch")
        # 预览不落盘
        self.task.refresh_from_db()
        self.assertEqual(self.task.cleaned_modules["topic_words"]["items"], ["kite-flying", "tug of war"])

    @patch("corpus.views.fix_module_with_llm")
    def test_fix_module_apply_persists(self, mock_fix):
        new_content = {"title": "Topic Words", "items": ["kite-flying", "tug of war", "hopscotch"]}
        resp = self.client.post(
            f"/api/v1/corpus-tasks/{self.task.id}/apply-module/",
            {"module_key": "topic_words", "content": new_content},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.cleaned_modules["topic_words"]["items"], ["kite-flying", "tug of war", "hopscotch"])

    def test_fix_module_unknown_key_400(self):
        resp = self.client.post(
            f"/api/v1/corpus-tasks/{self.task.id}/fix-module/",
            {"module_key": "nope"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    @patch("corpus.views.regenerate_kp_with_llm")
    def test_regenerate_kp_preview_and_apply(self, mock_regen):
        mock_regen.return_value = "新梗概：舞龙队……"
        resp = self.client.post(
            f"/api/v1/corpus-tasks/{self.task.id}/regenerate-kp/",
            {"kp_key": "summary", "instruction": "写详细一点"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["new_content"], "新梗概：舞龙队……")
        self.task.refresh_from_db()
        self.assertEqual(self.task.knowledge_points["summary"], "旧梗概")  # 未落盘

        resp = self.client.post(
            f"/api/v1/corpus-tasks/{self.task.id}/apply-kp/",
            {"kp_key": "summary", "content": "新梗概：舞龙队……"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.knowledge_points["summary"], "新梗概：舞龙队……")

    @patch("corpus.views.fix_module_with_llm")
    def test_fix_module_llm_failure_502(self, mock_fix):
        mock_fix.side_effect = RuntimeError("LLM down")
        resp = self.client.post(
            f"/api/v1/corpus-tasks/{self.task.id}/fix-module/",
            {"module_key": "topic_words"},
            format="json",
        )
        self.assertEqual(resp.status_code, 502)
        self.assertIn("LLM down", resp.data["error"])


# ===========================================================================
# S11 TTS 学习音频 + whisper 时间戳测试（#33）
# ===========================================================================



@override_settings(MEDIA_ROOT=_TEST_MEDIA)
class GenerateTtsTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester8", password="pass12345")
        self.client.force_authenticate(self.user)
        self.textbook = Textbook.objects.create(
            name="5A新版五上",
            pdf_file=SimpleUploadedFile("tts_book.pdf", make_pdf_bytes()),
        )
        self.task = CorpusTask.objects.create(
            name="5A新版五上 · Unit 2",
            textbook=self.textbook,
            unit=2,
            bucket_status="done",
            cleaned_modules={
                "topic_words": {"title": "Topic Words", "items": ["kite-flying"]},
                "fun_time": {"title": "party", "content": "Welcome to our garden party!",
                             "sound": "Sound ar garden"},
                "talking_time": {"title": "wind", "content": "Mr Zhong, is this Shaolin kung fu?"},
                "story_time": {"title": "dragon", "content": "The dragon dance. Minmin runs fast."},
                "project": {"title": "pres", "content": "Kite-flying is my favourite."},
                "words_to_use": {"title": "WtU", "items": ["trad"]},
            },
        )

    @patch("corpus.tasks.generate_learning_audio")
    @patch("corpus.tasks.convert_audio_to_mp3")
    def test_tts_generation(self, mock_mp3, mock_tts):
        import os
        from django.conf import settings
        mock_tts.return_value = "english_corner/tts/0/1.wav"
        mock_mp3.return_value = "english_corner/tts/0/1.mp3"
        # mock 音频文件存在性
        fake_path = os.path.join(settings.MEDIA_ROOT, "english_corner", "tts", "0", "1.wav")
        os.makedirs(os.path.dirname(fake_path), exist_ok=True)
        with open(fake_path, "w") as f:
            f.write("fake-wav")

        _run_generate_tts(self.task.id)

        self.task.refresh_from_db()
        self.assertEqual(self.task.tts_status, "done")
        self.assertEqual(self.task.tts_audio_url, "english_corner/tts/0/1.mp3")  # 播放用 MP3
        self.assertIsNone(self.task.tts_timestamps)  # 不做自动切割，时间戳留空
        # TtsText 朗读文本已保存
        from .models import TtsText
        ttstext = TtsText.objects.get(task=self.task)
        self.assertIn("party", ttstext.modules["fun_time"]["text"])

    @patch("corpus.tasks.generate_learning_audio")
    @patch("corpus.tasks.convert_audio_to_mp3")
    def test_tts_cached_skip(self, mock_mp3, mock_tts):
        self.task.tts_audio_url = "already.wav"
        self.task.save(update_fields=["tts_audio_url"])
        _run_generate_tts(self.task.id)
        self.task.refresh_from_db()
        self.assertEqual(self.task.tts_status, "done")
        mock_tts.assert_not_called()
        mock_transcribe.assert_not_called()

    def test_tts_data_action(self):
        # 未生成音频 → 404
        resp = self.client.get(f"/api/v1/corpus-tasks/{self.task.id}/tts-data/")
        self.assertEqual(resp.status_code, 404)
        # 生成音频后 → 返回 URL + 时间戳
        self.task.tts_audio_url = "english_corner/tts/0/9.wav"
        self.task.tts_timestamps = {
            "fun_time": [{"text": "Welcome!", "start": 0.0, "end": 2.0}],
            "story_time": [{"text": "Dragon.", "start": 2.0, "end": 3.0}],
        }
        self.task.tts_status = "done"
        self.task.save(update_fields=["tts_audio_url", "tts_timestamps", "tts_status"])
        resp = self.client.get(f"/api/v1/corpus-tasks/{self.task.id}/tts-data/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["tts_audio_url"], "english_corner/tts/0/9.wav")
        self.assertEqual(resp.data["tts_timestamps"]["fun_time"][0]["start"], 0.0)

    def test_task_serializer_exposes_tts_url(self):
        self.task.tts_audio_url = "x.wav"
        self.task.tts_status = "done"
        self.task.save(update_fields=["tts_audio_url", "tts_status"])
        resp = self.client.get(f"/api/v1/corpus-tasks/{self.task.id}/")
        self.assertEqual(resp.data["tts_audio_url"], "x.wav")

    @patch("corpus.views.generate_tts_task")
    def test_complete_triggers_tts(self, mock_tts):
        resp = self.client.post(f"/api/v1/corpus-tasks/{self.task.id}/complete/")
        self.assertEqual(resp.status_code, 200)
        mock_tts.assert_called_once()



# ===========================================================================
# S11 跟读专用文本分割（#33 增强）：过滤语法点/步骤/-- 占位
# ===========================================================================

class BuildTtsTextTests(APITestCase):
    def test_filters_grammar_sections_and_dash_prefix(self):
        from .tts import build_tts_text
        mods = {
            "fun_time": {"title": "party", "content": "Welcome to our garden party!",
                         "sound": "Sound ar garden"},
            "talking_time": {"title": "As fast as the wind",
                             "content": "-- Mr Zhong, is this Shaolin kung fu?\n-- Yes, it is!",
                             "grammar_tip": "Look at us. Stand like a pine tree."},
            "story_time": {"title": "The dragon dance", "content": "-- Slow down!\nMinmin runs fast."},
            "project": {"title": "A presentation",
                        "content": "Kite-flying is my favourite game.",
                        "sections": [{"title": "B Introduce",
                                      "steps": [{"title": "Step 1", "content": "Choose a game."}]}]},
            "topic_words": {"title": "Topic Words", "items": ["kite-flying"]},
        }
        result = build_tts_text(mods)
        # 四模块都有
        self.assertEqual(set(result.keys()), {"fun_time", "talking_time", "story_time", "project"})
        # grammar_tip 被排除（不在文本中）
        self.assertNotIn("Look at us.", result["talking_time"]["text"])
        # sections 步骤被排除
        self.assertNotIn("Choose a game.", result["project"]["text"])
        self.assertIn("Kite-flying is my favourite game.", result["project"]["text"])
        # "--" 前缀被删除（对话内容保留）
        self.assertNotIn("--", result["talking_time"]["text"])
        self.assertIn("Mr Zhong, is this Shaolin kung fu?", result["talking_time"]["text"])
        self.assertIn("Slow down!", result["story_time"]["text"])
        # Sound 保留（拼读示例句可跟读）
        self.assertIn("Sound ar garden", result["fun_time"]["text"])
        # 句子列表非空
        self.assertTrue(result["talking_time"]["sentences"])

    def test_missing_module_skipped(self):
        from .tts import build_tts_text
        mods = {"fun_time": {"title": "F", "content": "x"}, "project": None}
        result = build_tts_text(mods)
        self.assertEqual(set(result.keys()), {"fun_time"})


class TtsSlicesUpdateTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester9", password="pass12345")
        self.client.force_authenticate(self.user)
        self.textbook = Textbook.objects.create(
            name="5A新版五上",
            pdf_file=SimpleUploadedFile("tts_book.pdf", make_pdf_bytes()),
        )
        self.task = CorpusTask.objects.create(name="U", textbook=self.textbook, unit=1)

    def test_save_slices_rounds_and_validates(self):
        resp = self.client.put(
            f"/api/v1/corpus-tasks/{self.task.id}/tts-slices/",
            {"tts_timestamps": {
                "fun_time": [
                    {"text": "party", "start": 0.1234, "end": 0.5678},
                    {"text": "Welcome!", "start": 0.6, "end": None},
                ],
                "talking_time": "bad",  # 非法
            }},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        # 修正后保存
        resp = self.client.put(
            f"/api/v1/corpus-tasks/{self.task.id}/tts-slices/",
            {"tts_timestamps": {
                "fun_time": [
                    {"text": "party", "start": 0.1234, "end": 0.5678},
                    {"text": "Welcome!", "start": 0.6, "end": None},
                ],
            }},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.task.refresh_from_db()
        ts = self.task.tts_timestamps["fun_time"]
        self.assertEqual(ts[0]["start"], 0.12)  # 0.01 精度
        self.assertEqual(ts[0]["end"], 0.57)
        self.assertIsNone(ts[1]["end"])
        self.assertEqual(ts[1]["text"], "Welcome!")


@override_settings(MEDIA_ROOT=_TEST_MEDIA)
class SlicerSyncTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester10", password="pass12345")
        self.client.force_authenticate(self.user)
        self.textbook = Textbook.objects.create(
            name="5A新版五上",
            pdf_file=SimpleUploadedFile("tts_book.pdf", make_pdf_bytes()),
        )
        self.task = CorpusTask.objects.create(
            name="5A新版五上 · Unit 3",
            textbook=self.textbook, unit=3,
            tts_audio_url="english_corner/tts/0/3.mp3",
            tts_timestamps={
                "fun_time": [{"text": "Parts of plants", "start": 0.0, "end": 1.0},
                             {"text": "The roots hold the plant in place,", "start": 1.0, "end": 2.5},
                             {"text": "No timestamp", "start": None, "end": None}],
                "talking_time": [{"text": "A visit", "start": 3.0, "end": 5.0}],
            },
            tts_status="done",
        )
        # 假 mp3 文件
        import os
        from django.conf import settings
        fake = os.path.join(settings.MEDIA_ROOT, "english_corner", "tts", "0", "3.mp3")
        os.makedirs(os.path.dirname(fake), exist_ok=True)
        with open(fake, "wb") as f:
            f.write(b"fake-mp3")

    def test_sync_creates_drama_source_chunk_slices(self):
        from audio_slicer.models import AudioChunk, AudioSlice, Drama, SourceAudio
        from .services import sync_tts_to_audio_slicer

        self.assertTrue(sync_tts_to_audio_slicer(self.task))
        drama = Drama.objects.get(name="English Book (Grade 5)")
        source = SourceAudio.objects.get(drama=drama, season=1, episode=3)
        self.assertEqual(source.title, "5A新版五上 · Unit 3")
        chunk = AudioChunk.objects.get(source_audio=source, chunk_index=0)
        self.assertTrue(chunk.has_slices)
        self.assertTrue(chunk.file.name.endswith(".mp3"))
        slices = list(chunk.slices.all().order_by("start_time"))
        # None 时间戳的句子被跳过
        self.assertEqual(len(slices), 3)
        self.assertEqual(slices[0].original_text, "Parts of plants")
        self.assertEqual(slices[0].start_time, 0.0)
        self.assertEqual(slices[1].end_time, 2.5)

    def test_sync_idempotent(self):
        from audio_slicer.models import AudioSlice, Drama, SourceAudio
        from .services import sync_tts_to_audio_slicer

        sync_tts_to_audio_slicer(self.task)
        sync_tts_to_audio_slicer(self.task)
        drama = Drama.objects.get(name="English Book (Grade 5)")
        self.assertEqual(SourceAudio.objects.filter(drama=drama, season=1, episode=3).count(), 1)
        self.assertEqual(AudioSlice.objects.count(), 3)  # 不重复

    def test_sync_api_endpoint(self):
        resp = self.client.post(f"/api/v1/corpus-tasks/{self.task.id}/tts-sync-slicer/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("S1E3", resp.data["detail"])
        resp = self.client.post(f"/api/v1/corpus-tasks/{self.task.id}/tts-sync-slicer/")
        self.assertEqual(resp.status_code, 200)  # 幂等
