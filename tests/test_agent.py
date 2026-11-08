"""エージェントの配線テスト。

TestModel は実際のLLMを呼ばない偽モデルで、登録されたツールを全部呼んでから
ダミーの回答を返す。APIキーも利用枠も使わずに、
「ツールが登録され、呼ばれ、結果がモデルに戻るか」を確かめられる。
"""

import pytest
from pydantic_ai import DeferredToolRequests, ToolDenied
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import tools
from app.agent import agent, ask_approvals

BASE_TOOLS = {"search_glossary", "get_lecture_summary"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called():
    model = TestModel()
    with agent.override(model=model):
        result = agent.run_sync("LoRAとは？")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered  # 演習でツールを足しても壊れないよう「含む」で判定

    called = {p.tool_name for p in _parts(result, ToolCallPart)}
    assert BASE_TOOLS <= called
    # 承認が必要なツール（requires_approval=True）は、実行されずに承認待ちになるので戻り値が無い
    waiting = len(result.output.approvals) if isinstance(result.output, DeferredToolRequests) else 0
    assert len(_parts(result, ToolReturnPart)) + waiting == len(_parts(result, ToolCallPart))
    assert result.output


def test_glossary_result_reaches_the_model():
    model = TestModel(call_tools=["search_glossary"])
    with agent.override(model=model):
        result = agent.run_sync("RAGとは？")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_glossary"


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path)
    return tmp_path


def _resume_learning_log_run(approve: bool):
    with agent.override(model=TestModel(call_tools=["save_learning_log"])):
        waiting = agent.run_sync("今日学んだことを記録して")
        assert isinstance(waiting.output, DeferredToolRequests)
        [call] = waiting.output.approvals
        return agent.run_sync(
            message_history=waiting.all_messages(),
            deferred_tool_results=waiting.output.build_results(approvals={call.tool_call_id: approve}),
        )


def test_learning_log_waits_for_approval_before_saving(log_dir):
    with agent.override(model=TestModel(call_tools=["save_learning_log"])):
        result = agent.run_sync("今日学んだことを記録して")
    assert isinstance(result.output, DeferredToolRequests)
    assert not any(log_dir.iterdir())


def test_learning_log_is_saved_when_approved(log_dir):
    result = _resume_learning_log_run(approve=True)
    assert isinstance(result.output, str)
    assert len(list(log_dir.glob("*.md"))) == 1


def test_learning_log_is_not_saved_when_denied(log_dir):
    result = _resume_learning_log_run(approve=False)
    assert isinstance(result.output, str)
    assert not any(log_dir.iterdir())


def _approval_request() -> DeferredToolRequests:
    call = ToolCallPart("save_learning_log", {"title": "LoRA", "body": "要点"}, tool_call_id="call-1")
    return DeferredToolRequests(approvals=[call])


@pytest.mark.parametrize("answer", ["y", "Y", "yes"])
def test_ask_approvals_approves_on_yes(monkeypatch, answer):
    monkeypatch.setattr("builtins.input", lambda _: answer)
    assert ask_approvals(_approval_request()).approvals == {"call-1": True}


@pytest.mark.parametrize("answer", ["", "n", "はい"])
def test_ask_approvals_denies_unless_yes(monkeypatch, answer):
    monkeypatch.setattr("builtins.input", lambda _: answer)
    assert isinstance(ask_approvals(_approval_request()).approvals["call-1"], ToolDenied)


def test_ask_approvals_denies_when_input_is_closed(monkeypatch):
    def closed_input(_):
        raise EOFError

    monkeypatch.setattr("builtins.input", closed_input)
    assert isinstance(ask_approvals(_approval_request()).approvals["call-1"], ToolDenied)
