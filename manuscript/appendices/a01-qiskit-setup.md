# 付録A　PythonとQiskitの環境構築

<!-- 編集元: `docs/00.5.md` -->
<!-- 原稿生成時のAI利用に関する注記は、刊行時の開示方針を著者が判断する。 -->

## 検証済み環境

本書の実行可能コードは、次の環境で一括検証しています。

- CPython 3.12
- Qiskit 2.5.1
- Qiskit Aer 0.17.2
- Windows 64ビット

依存ライブラリの完全な組み合わせは、リポジトリの `examples/requirements-lock.txt` に固定しています。コード例はローカルで完結し、IBM QuantumのアカウントやAPIキーを必要としません。

## 仮想環境を作る

量子プログラミング用ライブラリを他のPythonプロジェクトから分離するため、リポジトリのルートに `.venv` を作ります。

macOS・Linuxでは次を実行します。

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShellでは次を実行します。

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

有効化後、次のコマンドで実際に使われるPythonを確認できます。

```bash
python --version
python -m pip --version
```

## 固定した依存関係をインストールする

検証時と同じ組み合わせを再現するには、ロックファイルを指定します。

```bash
python -m pip install -r examples/requirements-lock.txt
```

QiskitとQiskit Aerという直接依存だけを確認したい場合は、`examples/requirements.txt` を参照してください。書籍コードの再現性を優先する場合は、ロックファイルを使用します。

## コード例を一括実行する

最初に、全コードブロックの分類を検査します。ファイル名付きフェンスは単独実行可能コード、言語名だけのフェンスは説明用コード断片、`text`または無指定のフェンスは出力・疑似コード・状態表現として扱います。

```bash
python manuscript/tools/audit_code_blocks.py
```

続いて、原稿とコード例の対応、Python構文、廃止済みAPIの混入を検査します。

```bash
python manuscript/tools/verify_code_examples.py
```

続いて、全コード例を一括実行します。

```bash
python examples/run_all.py
```

各ファイルは別々のPythonプロセスで起動されます。したがって、ある例で定義した変数やimportに別の例が依存することはありません。10例すべてが期待値を満たすと、最後に次の行が表示されます。

```text
PASS all 10 examples
```

## 1ファイルだけ実行する

各コード例は単独でも実行できます。たとえば、Bell状態の例は次のコマンドで起動します。

```bash
python examples/03_bell_state.py
```

仮想環境を有効化していないWindows PowerShellでは、仮想環境内のPythonを直接指定できます。

```powershell
.venv\Scripts\python.exe examples\03_bell_state.py
```

## 仮想環境を終了する

作業が終わったら、次のコマンドで仮想環境を終了します。

```bash
deactivate
```
