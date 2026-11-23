"""第5回: 検索結果の加工のテスト（API キーも検索 DB も使わない）。"""

from app.retrieval import load_pages, with_neighbor_pages

PAGES = {page["page_id"]: page for page in load_pages()}


def _hits(*page_ids: str) -> list[dict]:
    return [{**PAGES[page_id], "distance": 0.1} for page_id in page_ids]


def _ids(results: list[dict]) -> list[str]:
    return [result["page_id"] for result in results]


def test_neighbors_follow_each_hit_in_page_order():
    results = with_neighbor_pages(_hits("lec02-main-p052"), span=1)
    assert _ids(results) == ["lec02-main-p052", "lec02-main-p051", "lec02-main-p053"]
    assert [result.get("neighbor_of") for result in results] == [None, "lec02-main-p052", "lec02-main-p052"]


def test_pages_already_returned_are_not_repeated():
    results = with_neighbor_pages(_hits("lec02-main-p052", "lec02-main-p051"), span=1)
    assert _ids(results) == ["lec02-main-p052", "lec02-main-p053", "lec02-main-p051", "lec02-main-p050"]


def test_neighbors_stay_within_the_same_document():
    results = with_neighbor_pages(_hits("lec02-main-p001", "lec01-main-p073"), span=1)
    assert _ids(results) == ["lec02-main-p001", "lec02-main-p002", "lec01-main-p073", "lec01-main-p072"]


def test_no_neighbors_when_span_is_zero():
    hits = _hits("lec02-main-p052")
    assert with_neighbor_pages(hits, span=0) == hits
