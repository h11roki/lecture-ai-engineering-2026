"""第5回: Graph 探索の候補の選び方を、小さな資料・グラフ・固定ベクトルで確かめる。API は呼ばない。

入口の次のページ（質問から遠い）と、用語「メモリ」でつながる別の章のページ（質問に近い）が
同じ枠を争う。演習の質問2で、別の章の根拠（第3回 p.13）が前後ページに押し出された形を小さくしたもの。
"""

import json

import pytest

from app import retrieval
from scripts.build_rag_index import build_index

EMBEDDINGS = {"入口": [1, 0], "次のページ": [0, 1], "その次": [0, 1], "章の始め": [0, 1],
              "別の章の根拠": [0.9, 0.1], "最後": [0, 1]}
TERM = "term:memory"


@pytest.fixture
def small_graph(tmp_path, monkeypatch):
    titles = list(EMBEDDINGS)
    page_ids = [f"lec01-main-p{n:03d}" for n in range(1, len(titles) + 1)]
    source = tmp_path / "lectures.json"
    source.write_text(json.dumps([{"id": "lec01-main", "title": "講義1", "content": [
        {"section": section, "content": [
            {"id": page_ids[n], "title": titles[n], "page": n + 1, "content": titles[n]} for n in numbers]}
        for section, numbers in (("章A", range(0, 3)), ("章B", range(3, 6)))
    ]}], ensure_ascii=False), encoding="utf-8")
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps({
        "nodes": [{"id": page_id, "kind": "page", "title": title} for page_id, title in zip(page_ids, titles)]
        + [{"id": TERM, "kind": "term", "title": "メモリ"}],
        "edges": [{"source": a, "target": b, "relation": "next_page"} for a, b in zip(page_ids, page_ids[1:])]
        + [{"source": page_ids[0], "target": TERM, "relation": "mentions"},
           {"source": page_ids[4], "target": TERM, "relation": "mentions"}],
    }, ensure_ascii=False), encoding="utf-8")
    database = tmp_path / "index.sqlite3"
    build_index(source, database, embedder=lambda text, _: EMBEDDINGS[text.splitlines()[2]])
    for name, value in {"RAG_SOURCE": source, "RAG_GRAPH": graph, "RAG_DB": database,
                        "GRAPH_START_K": 1, "GRAPH_HOPS": 2, "GRAPH_MAX_RESULTS": 2}.items():
        monkeypatch.setattr(retrieval, name, value)
    monkeypatch.setattr(retrieval, "embed_text", lambda *_: [1, 0])
    return page_ids


def test_structural_priority_fills_the_slot_with_the_next_page(small_graph, monkeypatch):
    monkeypatch.setattr(retrieval, "GRAPH_RERANK", False)
    result = retrieval.search_graph("メモリの違い")
    assert [page["page_id"] for page in result["seeds"]] == [small_graph[0]]
    assert [page["page_id"] for page in result["expanded"]] == [small_graph[1]]


def test_rerank_picks_the_closest_page_among_graph_candidates(small_graph, monkeypatch):
    monkeypatch.setattr(retrieval, "GRAPH_RERANK", True)
    [page] = retrieval.search_graph("メモリの違い")["expanded"]
    assert page["page_id"] == small_graph[4]
    assert page["hops"] == 2
    assert [step["id"] for step in page["path"]] == [small_graph[0], TERM, small_graph[4]]
    assert page["distance"] == pytest.approx(1 - 0.9 / (0.9**2 + 0.1**2) ** 0.5, abs=1e-6)
