# mutbench

AIが書いたテストは、本当にバグを検出できるのか？—— mutbenchはその問いに変異テスト
（mutation testing）で答えるためのハーネスです。小さなPythonモジュールを用意し、複数のLLMと
人間にpytestスイートを書かせ、次に本番コードを意図的に壊して、どのスイートが何件の破壊に
気づけるかを測ります。

ポイントは「欠けている数字」です。テストは100%パスしても何も保証していないことがあり、
カバレッジにはその区別がつきません。変異テストにはつきます: 本番コードを1か所だけ変え、
どのテストが失敗するかを機械的に確かめるからです。

[English](README.md) | 日本語（本ファイル）

## 測定する6つの指標（意図的に分離しています）

| 指標 | 答える問い |
|---|---|
| 生成成功率 (Generation success) | test名の関数・メソッドを含む構文有効なPythonを提出できたか |
| 実行可能性 (Executability) | そのファイルは構文・import・collectionが成立するPythonか |
| baseline有効性 (Baseline validity) | テストは**未変更のコード**で全部通るか |
| 変異スコア (Mutation score) | 固定変異集合のうち何件を検出したか |
| フレーキー率 (Flaky rate) | 繰り返し実行で同じ答えを返すか |
| 実行時間 (Runtime) | 生成秒数・変異評価秒数 |

素のコードで赤になるスイートは **BASELINE_RED** として分類し、黙って「修正」しません:
素のコードで失敗したテストを除いた診断用スコアだけを報告し、**何件除いたか**自体が主要な
数字です（例: 「79テスト中8テストが、コードに存在しない振る舞いを主張していた」）。
実行可能なコードを最後まで提出できなかった経路は **UNSCORABLE** —— スコアの分母には
入らないが、生成成功率の分母には入る。レポートではプロバイダの生成ゲート、collection失敗、
正規化失敗、変異測定失敗を区別し、スコア欠測を0点として扱いません。baseline有効な
スイートと正規化スイートの中央値・採点件数は別々に示し、混合しません。人間の生成欄は
対象外（n/a）、flakyの証拠がない場合は不明（unknown）です。変異の判定は killed / survived / not-covered /
error / timeout に分離され、スコアに混ぜられるのは killed と survived だけです。

## インストール

```bash
pip install -e ".[dev]"     # pytest, pytest-gremlins(バージョン固定), pytest-cov を導入
```

## クイックスタート

```bash
# 0. (任意) サードパーティ対象のステージング —— SHA固定で取得し、リポジトリには同梱しない
mutbench fetch && mutbench verify

# 1. 人間のスイートを固定変異集合で採点
mutbench score targets/concise/concise suites/human-concise \
    --label concise --cov-pkg concise --flaky-runs 20 --drop-failing

# 2. モデルにテストを書かせる（ソースは見せるが、人間のテストは決して見せない）
mutbench generate --target targets/concise/concise --out suites/concise__nim-deepseek__s0 \
    --provider nim --model deepseek-ai/deepseek-v4.1-flash

# 3. 同じ固定変異集合でAIスイートを採点
mutbench score targets/concise/concise suites/human-concise suites/concise__nim-deepseek__s0 \
    --label concise --cov-pkg concise --flaky-runs 20 --drop-failing

# 4. 表を出力
mutbench report results/concise__summary.json
```

`run_experiment.sh` / `run_phase2_gen.sh` が記事で使ったマトリクス全体
（3対象 × 3生成経路 × 3シード ＋ 人間ベースライン）を走らせます。

## 比較を公正に保つ規則

- **固定変異集合は1つ。** pytest-gremlinsの変異IDは対象ファイルの**パス**由来のため、
  同じ絶対パスに対して実行する限り全スイートが同一の変異集合を受けます —— per-mutantの
  対応比較（paired statistics）の前提条件です。ハーネスは各測定の前後で対象の内容を検証し、
  変更があればその実行を無効化します。
- **スコアの目視比較ではなく対応統計。** 同一変異集合なので各変異が
  (人間は殺したか, 候補は殺したか) のペア観測になります。対象の同一性と変異集合全体の一致を
  検証し、両スイートで判定できたペアだけを統計に使い、除外ペアも開示します: 正確McNemar検定＋変異を単位とした
  ブートストラップ信頼区間（変異は独立でないため、二項CIは楽観的すぎます）。等価変異は
  決定不能なので、生存変異は決して手で除外しません: 生存リストを全件公開し、**全スイートが
  見逃した変異（unanimous survivors）**を等価変異の候補としてフラグします。
- **生成メタデータも証拠の一部。** 各スイートは `meta.json` にプロンプト版とハッシュ、
  temperature、seed（エンドポイントが対応する場合）、エンドポイントが報告したモデル版、
  修復ラウンド数、モデルの生の出力を持ちます。
- **CIはオフライン。** `pytest tests/` にLLM APIも秘密情報も不要です。エンドツーエンドの
  スモークテストは同梱（自作コード）対象を、記録済みの固定変異集合に対して再生します。
  プロバイダを呼ぶ実験は別スクリプトで明示的に実行します。

## 構成

```
mutbench/            generate.py | bench.py | report.py | fetch_targets.py | cli.py
targets/<name>/      変異対象コード＋LICENSE（自作コードは同梱、サードパーティは取得）
suites/              生成スイートごとに1ディレクトリ: test_generated.py + meta.json + raw.txt
results/             スイートごとのJSON＋対象ごとのsummary（証拠としてコミット）
fixtures/            固定変異集合の基準ファイル
```

## 現在の実測（`results/` 参照）

- concise-md `core.py`（70変異）: 人間スイート 57.1%、あるフロンティアモデルのスイートは
  **1テスト除去・1 import修正後の正規化診断値として80.0%**
  （正確McNemar p=0.0004）—— ただし6生成経路のうち2経路は最後まで実行可能なPythonを
  提出できませんでした。
- cachetools `keys.py`（12変異）: 上流人間スイート 91.7%、モデルスイートは
  **正規化診断値として66.7%**（79テスト中8テストがコードと不一致のため除去した後の値）。
  ただし、これらの過去のモデル生成はソース入力が空と記録されており、ソースに基づく比較には使えません。
- cachetools パッケージ全体（gremlins基準で291変異）: 上流スイート 96.2%。
- パッケージ全体のGroq生成はプロバイダのトークン上限で停止し、リクエストは未送信です。
  これは生成ゲートであり、生成済みスイートのcollection結果とは区別します。
- 非空のテスト集合でflaky測定記録があるスイートでは、20回の反復でflakyは0件です。
  測定欠落や空のスイートからflakyの有無は判断できません。

解釈の規律: 対象ごとに提示し、対象横断の合算スコアは作らない。単一モデル・単一シードの
観察は記述値として明記する。固定変異集合を実バグのサンプルとして扱わない。

## 限界

- 変異スコアは代理指標です: 一部の変異は元コードと等価で、どんなテストも殺せません
  （フラグして残し、減算はしない）。
- 人間ベースラインは各プロジェクトの既存スイートであり、本実験のために管理された
  コントロールではありません。
- pytest-gremlins は `==1.14.3` に固定 —— 若いエンジンでAPIがまだ動きます。

## ライセンス

MIT。変異対象のサードパーティコード（cachetools, MIT © Thomas Kemmer）はPyPIから取得し、
`mutbench fetch` が固定SHA-256で検証します（リポジトリには同梱しない）。
`targets/concise` は著者自身のMITコード（concise-md）です。
