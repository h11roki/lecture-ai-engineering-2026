# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：第1回の `app.ask` は「レベル1 基礎・入門」「レベル2 応用・実践」「レベル3 発展・挑戦」と一般論で答え、2つ目を「応用」とし、「どれか1つで完了」とも言わなかった（第1回の宿題で試した6回すべて）。エージェントは `search_glossary` で `homework-levels` を引いてから、「基礎（講義内容の確認）」「実装（自分でコードを書く）」「発展（調査や試行）」の3段階で、どれか1つに取り組めば完了、原則として採点しない、と `data/glossary.json` の定義どおりに答えた。回答の最後には「関連する回：第1回」が付いた。make_quiz を足したあとに3回試しても同じだった
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - 「3レベル」の質問：`search_glossary({'query': '3レベル'})` の1回
  - 「LoRAとQLoRAの違いは？」：`search_glossary({'query': 'LoRA'})` と `search_glossary({'query': 'QLoRA'})`。`[tool call]` の2行が `[tool return]` より先に並んでおり、1回の応答で2つの検索をまとめて依頼していた
  - 「第2回の内容から確認問題を1問出して」：`make_quiz({'lecture': 2})` の1回（3回とも）
- 1つの質問での LLM 呼び出し回数（`requests`）：どの質問も 2。1回目でツールを依頼し、2回目でツールの結果を見て答える。LoRA と QLoRA は検索が2回でも、依頼が1回の応答にまとまっているので 2 のままだった。`input_tokens` は2回分の合計で、ツールが2つの時点では「3レベル」が 783、「LoRAとQLoRA」が 1196。make_quiz を足すと、make_quiz を使わない質問でもそれぞれ 957、1370 に増えた（1回の呼び出しあたり約 87 トークン）。ツールの一覧（名前・説明文・引数）は呼び出しのたびに送られるため
- 追加したツールと、docstring に書いた説明：`app/tools.py` に `make_quiz(lecture: int) -> str` を足し、`app/agent.py` の TODO の場所で `agent.tool_plain(tools.make_quiz)` と登録した。用語集から `lecture` が一致する用語を集めて `random.choice` で1つ選び、`{"question": "「PEFT」の意味は？", "answer": "<定義>"}` を JSON で返す。用語の無い回では「第0回の用語は用語集にありません。用語がある回: 1, 2, 3, 4, 6」を返す（`pytest` の TestModel は `lecture=0` で呼ぶため）。docstring は次のとおり

  ```text
  指定した回（1始まりの整数）の用語から1つを選び、確認問題と答え（用語の定義）を返す。

  「第2回の確認問題を出して」のように、復習用の問題を求められたときに使う。
  ```

  - `--list-tools` に make_quiz とこの docstring が出た。`uv run pytest -q` は全部通った（用語のある回と無い回のテストを `tests/test_tools.py` に2件足した）
- 気づいたこと：確認問題の3回とも、答えは伏せて問題だけを出した。ただし1回目は「第2回（モデルの基礎と事前学習）」と、どのツールも返していない回の題名を書いた（正しくは「ファインチューニングとLoRA」）。3回目は「ヒント：モデルの大部分を固定し、ごく一部のパラメータだけを効率よく学習する手法の総称です」と、PEFT の定義をほぼそのまま言っていた。INSTRUCTIONS の「宿題の答えそのものは書かず、考え方のヒントで導く」を確認問題にも当てはめた可能性があるが、確かめていない

## 宿題

- 取り組んだレベル：基礎・実装・発展（a）の3つ
- やったこと・結果・気づき：レベルごとに下に書く

### 基礎：INSTRUCTIONS と docstring を1か所ずつ変えて比べる

- やったこと：make_quiz を登録した状態を基準にして、1か所ずつ書き換え、同じ質問を `--trace` 付きで3回ずつ実行した。書き換えは比べ終わるたびに元に戻した（コミットには残していない）。①は動きが変わらなかったので、docstring も重ねて変えた
- 結果：ツール呼び出しが3回とも同じだったものは1行にまとめた。`input_tokens` は `requests` 回分の合計

| 変えたこと | 質問 | ツール呼び出し | `requests` | `input_tokens` |
|---|---|---|---|---|
| なし（基準） | LoRAとQLoRAの違いは？ | `LoRA`、`QLoRA` を1つずつ検索 | 2 | 1370 |
| なし（基準） | 「3レベル」とは何ですか？ | `3レベル` を検索 | 2 | 957 |
| ① INSTRUCTIONS から「必ず search_glossary で用語集を確認する」の行を消す | LoRAとQLoRA | 基準と同じ | 2 | 1322 |
| ① | 3レベル | 基準と同じ | 2 | 909 |
| ①に加えて、docstring の「答える前に使うこと」を「調べるときに使う」にする | LoRAとQLoRA | 基準と同じ | 2 | 1320 |
| 同上 | 3レベル | 基準と同じ | 2 | 907 |
| ② docstring の「1つだけ入れる」を「まとめて入れる」にする | LoRAとQLoRA | `LoRA QLoRA` で1回だけ検索 | 2 | 1059 |
| なし（基準） | LoRA、QLoRA、PEFT、量子化の関係を教えて | 4語を1つずつ検索 | 2 | 1797 |
| ② | 同上 | `LoRA QLoRA PEFT 量子化` で1回だけ検索 | 2 | 1146 |
| ③ INSTRUCTIONS の「回答の最後に、関係する回（第N回）を示す」を「回答の最後に、確認問題を1問出す」にする | LoRAとQLoRA | 2回は検索2つと `make_quiz({'lecture': 2})`、1回は検索2つだけ | 3、3、2 | 2407、2404、1362 |

- ①：検索を促す文を2か所とも消しても、12回すべて検索してから答え、最後に第N回も付いた。残っている「用語集に見つからないことは…「用語集にはない」と伝える」や「関係する回（第N回）を示す」が、用語集を引く理由になっている可能性があるが、そこまでは確かめていない
- ②：検索は1回になり、`input_tokens` は 1370 → 1059 に減った。`search_glossary` は「用語名が検索語に含まれる」ときも当たる部分一致なので、`LoRA QLoRA` でも2つとも返った。ところが結果は最大3件（`MAX_RESULTS`）なので、4語の質問では `PEFT`・`LoRA`・`QLoRA` だけが返り、「量子化」は返らなかった。それでも3回とも量子化を説明し、うち2回は用語集に無い「32ビット浮動小数点数」を元の形式の例に挙げた。「用語集にはない」とは言わなかった。1語ずつ検索した基準では、3回とも用語集どおり「16ビットから4ビット」だった
- ③：3回中2回は make_quiz を呼び、`requests` が 3、`input_tokens` が基準の約1.8倍になった。make_quiz は回しか受け取らないので、LoRA の質問に「事前学習」の問題が出た回もあった。残りの1回はツールを使わず、LoRA のランクについて自分で問題を作った。最後の「関係する回」の行は無くなったが、3回とも問題の見出しに「第2回」を入れた
- 気づき・疑問：
  - 指示を1行消しても動きは変わらなかったのに、docstring の引数の説明を1語変えただけで、検索の回数と引数がすぐ変わった。「いつ使うか」は複数の文から決まり、「どう呼ぶか」は docstring の引数の説明にそのまま従っているように見えた
  - ②は入力が減る代わりに、検索結果の上限で用語が黙って落ち、モデルはそれに気づかず自分の知識で埋めた。ツールが「上位3件だけを返した」と伝えない限り、モデルには落ちたことが分からない。まとめて検索させるなら、件数の上限を語の数に合わせるか、見つからなかった語を返す必要がありそう
  - 疑問：①で検索が止まらなかったのは、どの文のためか。INSTRUCTIONS を1行ずつ消していけば分かるが、今回は試していない

### 実装：保存の前に利用者の承認を挟む

- やったこと：
  - `app/tools.py` に `save_learning_log(title: str, body: str) -> str` を作った。`learning_log/YYYY-MM-DD.md` に `## HH:MM 見出し` を付けて追記する（1日1ファイル）。日付は日本時間（UTC+9 の固定。日本には夏時間が無い）で決める。Codespaces の時計は UTC なので、そのままだと日本の朝9時前の記録が前日のファイルに入るため。`learning_log/` は講座の `.gitignore` で共有しない設定になっている
  - `app/agent.py` で `agent.tool_plain(requires_approval=True)(tools.save_learning_log)` と登録し、`output_type=[str, DeferredToolRequests]` にした。`tool_plain(関数, requires_approval=True)` でも動くが、型定義ではキーワードを付けるときは `tool_plain(...)(関数)` の形なので、そちらにした
  - CLI は、出力が `DeferredToolRequests` の間、`approvals` の呼び出しごとにツール名と引数を見せて `実行してよいですか？ [y/N]` と聞く。引数の中の改行以外の制御文字（`\r` や端末のエスケープ）は、`\r`・`\x1b` のような見える形にして表示する。見えていない内容を承認させないため。`y` / `yes` 以外と、入力が閉じている（EOF）ときは `ToolDenied("利用者が実行を断りました。")` にする。答えを `DeferredToolResults` にし、`message_history=result.all_messages()` と `usage=result.usage` と一緒に渡して続きを実行する。`usage` を渡すのは、`--trace` の `requests` を最初からの合計にするため。断られた保存をモデルが求め直し続けると終わらないので、この往復は3回（`MAX_APPROVAL_ROUNDS`）までにした
  - テストを足した：承認待ちで止まってファイルが無いこと、承認すると1ファイルできること、断るとできないこと、断られても保存を求め続けるモデルでは聞くのが3回で止まること、`ask_approvals` が `y`・`Y`・`yes` だけを承認し、空・`n`・`はい`・EOF を断ること、引数に隠した制御文字が見える形で表示されること、日付が日本時間で決まること（時計を UTC 15:30 に固定すると翌日のファイルになる）、同じ日の記録が1ファイルに順に追記されること。`requires_approval=True` を外すと、承認まわりのテストが落ちることも確かめた
- 結果：
  - 承認した場合（`echo y | uv run python -m app.agent --trace "LoRAについて今日学んだことを、用語集の定義をもとに記録して"`）。`requests` は 3 で、検索を依頼 → 保存を依頼して承認待ちで止まる → 承認後に保存の結果を見て答える、の順だった。`learning_log/2026-11-08.md` には `## 20:37 LoRAについての学習記録` の下に body がそのまま入った

    ```text
    [approval] save_learning_log
      title: LoRAについての学習記録
      body: - **LoRAの定義**: 事前学習済みの重みは固定したまま、（略）
        - **特徴**: 学習するパラメータが少なく、（略）
    実行してよいですか？ [y/N] 本日のLoRAについての学びを用語集の定義をもとに記録いたしました。

    （第2回）

    --- trace ---
    [tool call]   search_glossary({'query': 'LoRA'})
    [tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, （略）
    [tool call]   save_learning_log({'title': 'LoRAについての学習記録', 'body': （略）})
    [tool return] save_learning_log -> learning_log/2026-11-08.md に保存しました。…
    [usage] RunUsage(（略）requests=3, tool_calls=2)
    ```

  - 断った場合（`n`）：保存されず、ツールの結果として「利用者が実行を断りました。」がモデルに返った。モデルは「許可されなかったため保存は行いませんでした」と伝え、用語集の定義を見せた。`[usage]` の `tool_calls` は 1 で、断った呼び出しは数えられていなかった
  - 入力が閉じている場合（`< /dev/null`）：断ったのと同じ扱いになり、保存されなかった。モデルは「操作が完了しませんでした」と伝え、記録の内容を手でメモに残すよう勧めた
  - 記録を頼んでいない「LoRAとQLoRAの違いは？」では、2回とも save_learning_log は呼ばれず、検索2回だけだった。ただし `input_tokens` は 1370 → 1628 に増えた
- 気づき・疑問：
  - 承認が要るかどうかは、ツールの関数ではなく、登録するときの `requires_approval=True` で決まる。関数は普通にファイルに書くだけで、「止める・聞く・続きを実行する」はエージェントと CLI の側にある
  - 承認は利用者だけでなく、テストも守っていた。`requires_approval=True` を外して試したとき、既存のテスト（TestModel が全部のツールをダミーの引数で呼ぶ）が、本物の `learning_log/` に `## 20:36 a` という記録を書いた。そこで `tests/conftest.py` で、すべてのテストの保存先を一時フォルダに向けるようにした
  - 断られたあとにモデルが同じ保存をもう一度依頼すると、CLI はもう一度聞く。入力が閉じていると自動で断り続けて空回りするので、往復を3回までにした。実際の実行では、断られたあとに求め直した回は無かった
  - 疑問：上限で止める代わりに、断った内容を覚えておいて、同じ依頼は聞かずに断るほうがよいか

### 発展（a）：ADK で組み立て直す

- やったこと：`adk_agent/glossary_agent/agent.py` と `__init__.py`（`from . import agent` の1行）を作った。INSTRUCTIONS と search_glossary・get_lecture_summary・make_quiz は `app/` から import し、`app/` は変えていない。モデル名は `app.config.MODEL`（既定は gemini-3.5-flash-lite）を使い、Pydantic AI 版と同じモデルにした。google-adk 2.14.0 を `uv run --with google-adk` で足して動かした。比べやすいよう、`adk run --in_memory --jsonl adk_agent/glossary_agent "質問"` で1問ずつ流し、JSONL のイベントからツール呼び出し、LLM の呼び出し回数、トークン数を数えた。演習と同じ3問を3回ずつと、対話モードで2ターンの会話を試した

  ```python
  root_agent = Agent(
      model=MODEL,
      name="glossary_agent",
      instruction=INSTRUCTIONS,
      tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz],
  )
  ```

- 結果（書き方の違い）：

| | Pydantic AI（`app/agent.py`） | ADK（`adk_agent/glossary_agent/agent.py`） |
|---|---|---|
| 指示 | `Agent(instructions=INSTRUCTIONS)` | `Agent(instruction=INSTRUCTIONS)` |
| ツールの渡し方 | 作ったあとに `agent.tool_plain(関数)` で1つずつ登録 | 作るときに `tools=[関数, …]` で渡す |
| モデル | 実行するときに `run_sync(..., model=...)` で渡す（テストで TestModel に差し替えるため） | 作るときに `model="モデル名"` で渡す |
| ツールの説明文 | docstring | docstring（ADK の `FunctionTool` の宣言で、同じ文になることを確かめた） |
| 動かし方と会話 | 自分で書いた CLI（`python -m app.agent`）。1問で終わる | `adk run` が CLI とセッションを用意する。対話モードでは会話が続く |
| モデルに渡る指示 | INSTRUCTIONS だけ | INSTRUCTIONS の後ろに `You are an agent. Your internal name is "glossary_agent".` が自動で付く（`--log_level debug` のログで確認） |
| ツール呼び出しの見方 | 自分で書いた `--trace` | `--jsonl` のイベントと、`--log_level debug` のログ |

- 結果（回答の違い）：Pydantic AI 版の数字は、make_quiz を足したあと、save_learning_log を足す前のもの（ツールが ADK 版と同じ3つの時点）

| 質問 | Pydantic AI のツール呼び出し | ADK のツール呼び出し | `requests` | 入力トークン（Pydantic AI → ADK） |
|---|---|---|---|---|
| LoRAとQLoRAの違いは？ | `LoRA`、`QLoRA` を検索（3回とも） | 同じ（3回とも） | どちらも 2 | 1370 → 1494 |
| 「3レベル」とは何ですか？ | `3レベル` を検索（3回とも） | 同じ（3回とも） | どちらも 2 | 957 → 1083 |
| 第2回の内容から確認問題を1問出して | `make_quiz({'lecture': 2})`（3回とも） | 同じ（3回とも） | どちらも 2 | 885〜899 → 1020〜1059 |

- 回答の中身も同じ形だった。LoRA と 3レベルは用語集の定義どおりに答え、最後に第N回を付けた。確認問題は答えを伏せて出題した
- ADK のほうが、1つの質問あたり入力が 120〜170 トークン多かった。自動で付く1文の分はあるが、ほかに何が増えたのかは確かめていない
- 対話モードで「第2回の内容から確認問題を1問出して」→「わかりません。答えを教えてください」と続けると、2ターン目はツールを呼ばず、1回の呼び出しで、1ターン目に make_quiz が返した答え（「事前学習」の定義）を答えた。2ターン目の入力は 592 トークンで、1ターン目のやり取りが含まれていた
- 対話モードの別の回では、1ターン目に「第2回（LoRAとファインチューニング）」と、ツールが返していない題名を書き、答えに近いヒントも付けた。演習の Pydantic AI 版で見た癖と同じで、フレームワークを変えても起きた
- 気づき・疑問：
  - 指示と docstring が同じなら、ツールの選び方も回数も同じだった。ふるまいを決めているのはモデルと指示・説明文で、フレームワークが変えるのは、モデルを渡す場所、会話を誰が持つか、CLI を自分で書くかどうかだった
  - Pydantic AI はモデルを実行時に渡すので、API キー無しで TestModel に差し替えたテストが書きやすい。ADK は `adk run` だけで会話の続く CLI が手に入る代わりに、モデルに渡る指示に自分の書いていない文が足される。また、ドキュメントによると `instruction` の `{名前}` はセッションの状態で置き換えられ、その状態が無いとエラーになる。INSTRUCTIONS に JSON の例などで `{}` を書くと、Pydantic AI 版では動くのに ADK 版では動かなくなりそう
  - 疑問：実装レベルの承認付きツールを ADK で書くとどうなるか（今回の範囲外で、試していない）
