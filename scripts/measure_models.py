"""第1回 宿題（基礎・発展）: モデルと質問ごとに、回答・応答時間・トークン数を記録する。

使い方:
    uv run python -m scripts.measure_models > results.jsonl
    uv run python -m scripts.measure_models --models gemini-3.5-flash-lite --repeat 5

1回の呼び出しごとに JSON を1行出力する。
無料枠のレート制限（gemini-3.8-flash は毎分5回）にかからないよう、呼び出しの間を空ける。
429 や 503 が返っても止めずに、そのまま記録する。
"""

import argparse
import itertools
import json
import time

from google import genai
from google.genai import errors

from app.ask import DEFAULT_QUESTION
from app.config import get_api_key

MODELS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]
QUESTIONS = ["LoRAとは何ですか？", DEFAULT_QUESTION]


def main() -> None:
    parser = argparse.ArgumentParser(description="モデルと質問ごとに、回答・応答時間・トークン数を記録する")
    parser.add_argument("--models", nargs="+", default=MODELS)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--interval", type=float, default=13.0, help="呼び出しの間隔（秒）")
    args = parser.parse_args()

    client = genai.Client(api_key=get_api_key())
    for model, question, run in itertools.product(args.models, QUESTIONS, range(1, args.repeat + 1)):
        record = {"model": model, "question": question, "run": run}
        start = time.perf_counter()
        try:
            response = client.models.generate_content(model=model, contents=question)
        except errors.APIError as e:
            record["error"] = f"{e.code} {e.message}"
        else:
            record["answer"] = response.text
            usage = response.usage_metadata
            if usage is not None:
                record |= {
                    "input": usage.prompt_token_count,
                    "output": usage.candidates_token_count,
                    "thoughts": usage.thoughts_token_count,
                    "total": usage.total_token_count,
                }
        record["seconds"] = round(time.perf_counter() - start, 2)
        print(json.dumps(record, ensure_ascii=False), flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
