import pytest

from app import retrieval, tools


@pytest.fixture(autouse=True)
def log_dir(tmp_path, monkeypatch):
    path = tmp_path / "learning_log"
    monkeypatch.setattr(tools, "LOG_DIR", path)
    return path


@pytest.fixture(autouse=True)
def retrieval_defaults(monkeypatch):
    monkeypatch.setattr(tools, "RAG_NEIGHBOR_PAGES", 0)
    monkeypatch.setattr(retrieval, "GRAPH_RERANK", False)
