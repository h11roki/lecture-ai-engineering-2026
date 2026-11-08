"""ツールのテスト（LLMもAPIキーも使わない）。"""

import json
from datetime import datetime

from app import tools


def test_glossary_ids_are_unique_and_related_links_exist():
    terms = tools.load_glossary()
    ids = [t["id"] for t in terms]
    assert len(ids) == len(set(ids))
    for t in terms:
        for r in t["related"]:
            assert r in ids, f"{t['id']} の related に存在しない id: {r}"


def test_search_finds_term_by_name_and_alias():
    for query in ["LoRA", "lora", "Low-Rank Adaptation"]:
        hits = json.loads(tools.search_glossary(query))
        assert hits[0]["term"] == "LoRA", query


def test_search_finds_course_specific_term():
    hits = json.loads(tools.search_glossary("lecNN-start"))
    assert hits[0]["term"] == "lecNN-start タグ"


def test_search_limits_number_of_results():
    hits = json.loads(tools.search_glossary("エージェント"))
    assert 1 <= len(hits) <= tools.MAX_RESULTS


def test_search_reports_not_found():
    assert "見つかりませんでした" in tools.search_glossary("存在しない用語xyz")


def test_lecture_summary():
    assert "エージェント" in tools.get_lecture_summary(3)
    assert "まだありません" in tools.get_lecture_summary(99)


def test_quiz_asks_meaning_of_a_term_from_the_lecture():
    quiz = json.loads(tools.make_quiz(2))
    entry = next(t for t in tools.load_glossary() if t["definition"] == quiz["answer"])
    assert entry["lecture"] == 2
    assert quiz["question"] == f"「{entry['term']}」の意味は？"


def test_quiz_reports_lecture_without_terms():
    assert "用語集にありません" in tools.make_quiz(0)


def test_learning_log_appends_entries_to_todays_file(tmp_path, monkeypatch):
    log_dir = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LOG_DIR", log_dir)
    tools.save_learning_log("LoRA", "低ランク行列だけを学習する")
    tools.save_learning_log("QLoRA", "量子化したモデルに LoRA をかける")

    [log] = log_dir.iterdir()
    assert log.name == f"{datetime.now(tools.LOG_TIMEZONE):%Y-%m-%d}.md"
    text = log.read_text(encoding="utf-8")
    assert text.index("LoRA\n\n低ランク行列") < text.index("QLoRA\n\n量子化")


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"
