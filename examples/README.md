# 実行可能コード例

本文の主要なコードを、1ファイルずつ単独で実行できる形にした検証用ディレクトリです。すべてローカルシミュレータまたは状態ベクトル計算で完結し、クラウドアカウントやAPIキーは不要です。

## 対応環境

- CPython 3.12
- Qiskit 2.5.1
- Qiskit Aer 0.17.2

## Windows PowerShellでの準備

リポジトリのルートで実行します。

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r examples/requirements-lock.txt
python examples/run_all.py
```

仮想環境を有効化しない場合は、最後のコマンドを次のように実行できます。

```powershell
.venv\Scripts\python.exe examples/run_all.py
```

## macOS・Linuxでの準備

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r examples/requirements-lock.txt
python examples/run_all.py
```

`run_all.py` は各例を独立したPythonプロセスで実行します。いずれかの期待値検査に失敗すると、全体も非ゼロ終了します。

`requirements-lock.txt` は実際に一括検証した完全固定環境です。直接依存だけを確認したい場合は `requirements.txt` を参照してください。

## 収録例

| ファイル | 対応内容 | 主な検査 |
| --- | --- | --- |
| `01_first_circuit.py` | 第1章 | Hゲートと測定を含む回路構造 |
| `02_superposition.py` | 第2章 | 0と1がほぼ等確率になること |
| `03_bell_state.py` | 第4章 | 00と11だけが観測されること |
| `04_interference.py` | 第5章 | Hを2回適用すると0へ戻ること |
| `05_grover_two_qubit.py` | 第7章 | 2量子ビット探索で11が得られること |
| `06_toffoli.py` | 第9章 | Toffoliゲートの可逆AND動作 |
| `07_qft_round_trip.py` | 第13章 | QFTと逆QFTで入力状態へ戻ること |
| `08_vqe_single_qubit.py` | 第16章 | 変分最適化が基底エネルギーへ収束すること |
| `09_qaoa_two_node_maxcut.py` | 第18章 | QAOAがカット解01・10へ集中すること |
| `10_bit_flip_correction.py` | 第27章 | 3量子ビット反復符号で1ビット誤りを訂正できること |
