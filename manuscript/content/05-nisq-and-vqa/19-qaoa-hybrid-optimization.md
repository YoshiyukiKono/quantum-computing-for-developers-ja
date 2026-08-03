# 第19章　QAOAの古典・量子ハイブリッド最適化

<!-- 編集元: `docs/13-QAOA-classic-quantum-hybrid.md` -->

## はじめに

ここまでに扱った内容：

* Max-Cutの量子化
* コストハミルトニアンの回路化
* ミキサーハミルトニアンの回路化
* 最小構成QAOA回路（p=1）

を実装しました。

この章では **QAOAを「アルゴリズムとして動かす」**

段階に進みます。

テーマ：

* 期待値とは何か？
* コスト関数の定義
* 測定結果の評価方法
* scipyによるパラメータ最適化
* p=2以上への拡張

がこの章の対象です。

---

## 1. QAOAはなぜパラメータ最適化が必要なのか？

QAOAは：

```text
U(B, β) U(C, γ)
```

という回路を実行しますが、

ここで重要なのは：

γ（ガンマ）
β（ベータ）

の値です。

この値によって、**量子干渉のパターン** が変わります。

つまり、 **どの解が強調されるか** が変わります。

---

## 2. 最適化の目的：期待値を最小化する

QAOAでは **コストハミルトニアンの期待値** を最小化します。

直感：

| 状態      | 意味     |
| ------- | ------ |
| 期待値が大きい | 悪い解が多い |
| 期待値が小さい | 良い解が多い |

つまり：

```text
期待値最小化 = 最適解探索
```

という対応になります。

---

## 3. 測定結果から期待値を計算する方法

測定結果は：

```text
00
01
10
11
```

のようなビット列です。

Max-Cut（2ノード）の場合：

| 状態 | Cut数 |
| -- | ---- |
| 00 | 0    |
| 11 | 0    |
| 01 | 1    |
| 10 | 1    |

と評価できます。

つまり：

```text
期待値 = Σ (確率 × Cut数)
```

という計算です。

---

## 4. Qiskit Aerで回路を実行する

まず必要なライブラリ：

```python
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
from qiskit import transpile
```

シミュレータ準備：

```python
simulator = AerSimulator()
```

---

## 5. QAOA回路を関数化する

先に示した回路を関数として整理します：

```python
def create_qaoa_circuit(gamma, beta):

    qc = QuantumCircuit(2)

    # 初期状態
    qc.h(0)
    qc.h(1)

    # コストハミルトニアン
    qc.cx(0, 1)
    qc.rz(2 * gamma, 1)
    qc.cx(0, 1)

    # ミキサーハミルトニアン
    qc.rx(2 * beta, 0)
    qc.rx(2 * beta, 1)

    qc.measure_all()

    return qc
```

---

## 6. 回路を実行する関数を書く

次に：

測定結果を取得する関数：

```python
def run_circuit(gamma, beta):

    qc = create_qaoa_circuit(gamma, beta)

    compiled = transpile(qc, simulator)

    job = simulator.run(compiled, shots=1024)

    result = job.result()

    counts = result.get_counts()

    return counts
```

---

## 7. 期待値を計算する関数を書く

Max-Cut評価関数：

```python
def compute_expectation(counts):

    expectation = 0

    for bitstring, count in counts.items():

        if bitstring in ["01", "10"]:
            value = 1
        else:
            value = 0

        expectation += value * count

    return expectation / 1024
```

これが **QAOAの目的関数** になります。

---

## 8. scipyでパラメータ最適化する

古典最適化には **scipy** を使います。

```python
from scipy.optimize import minimize
import numpy as np
```

目的関数：

```python
def objective(params):

    gamma, beta = params

    counts = run_circuit(gamma, beta)

    return -compute_expectation(counts)
```

ここで：

最大化問題 → 最小化問題

に変換するため：

マイナスを付けています。

---

## 9. 最適化を実行する

初期値設定：

```python
initial_guess = np.array([0.5, 0.5])
```

最適化実行：

```python
result = minimize(objective, initial_guess, method="COBYLA")
```

結果：

```python
print(result.x)
```

ここで：

最適な

```text
γ
β
```

が得られます。

---

## 10. 最適パラメータで回路を実行する

最適値で回路を再実行：

```python
optimal_gamma, optimal_beta = result.x

counts = run_circuit(optimal_gamma, optimal_beta)

print(counts)
```

理想的には：

```text
01
10
```

の確率が最大になります。

---

## 11. p=2以上に拡張する方法

QAOAは：

```text
p = 1
```

だけではありません。

一般形：

```text
U(B, β_2) U(C, γ_2)
U(B, β_1) U(C, γ_1)
```

という積になります。

つまり：

```text
γ_1, γ_2
β_1, β_2
```

を最適化します。

拡張例：

```python
params = [gamma1, beta1, gamma2, beta2]
```

のように扱えます。

特徴：

| p   | 精度  |
| --- | --- |
| 小さい | 高速  |
| 大きい | 高精度 |

---

## 12. なぜpを増やすと性能が上がるのか？

理由は **干渉パターンの自由度が増える** からです。

直感：

| p   | 状態    |
| --- | ----- |
| 1   | 粗い探索  |
| 2   | 改善    |
| 3以上 | 高精度探索 |

ただし、**回路深さ** が増えます。

---

## まとめ

この章のポイント：

* QAOAは期待値最小化問題として解く
* 測定結果から評価関数を作れる
* scipyでパラメータ最適化できる
* 最適パラメータで正解確率が最大化される
* pを増やすと精度が上がる

これで、**QAOAが実際に動くアルゴリズム** として理解できました。

---
