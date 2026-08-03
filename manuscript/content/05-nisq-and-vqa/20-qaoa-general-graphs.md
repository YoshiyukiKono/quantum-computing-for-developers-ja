# 第20章　一般グラフへQAOAを適用する

<!-- 編集元: `docs/14-QAOA-NetworkX-Max-Cut.md` -->

## はじめに

ここまでに扱った内容：

* QAOAの期待値計算
* 測定結果の評価方法
* scipyによるパラメータ最適化
* pパラメータの意味

を扱いました。

この章では **任意のグラフに対してQAOAを適用する方法**

を解説します。

テーマ：

* 3ノード以上のMax-Cut
* 一般グラフのコストハミルトニアン生成
* NetworkXとの連携
* 自動回路生成
* スケール時の注意点

ここから **実問題サイズに近づくQAOA実装** に入っていきます。

---

## 1. なぜ一般グラフ対応が必要なのか？

ここまでに扱った例：

```text
0 --- 1
```

は最小構成でした。

しかし実際の問題は：

```text
0 --- 1
| \   |
2 --- 3
```

のような：

多ノードグラフになります。

つまり：

```text
任意グラフ → 自動でハミルトニアン生成
```

が必要になります。

---

## 2. Max-Cutの一般形

Max-Cutのコストハミルトニアンは：

$$
H_C = \sum_{(i,j)\in E} \frac{1 - Z_i Z_j}{2}
$$

ここで：

* (E)：辺の集合
* (Z_i)：i番目のZ演算子

つまり、**辺の数だけ項を足す** だけです。

---

## 3. Pythonでグラフを扱う：NetworkX

Pythonでは **NetworkX** を使うと便利です。

インストール：

```bash
pip install networkx
```

グラフ作成：

```python
import networkx as nx

G = nx.Graph()

G.add_edges_from([
    (0, 1),
    (1, 2),
    (2, 0)
])
```

これで、**三角形グラフ** が作れます。

---

## 4. グラフからコストハミルトニアンを作る

QAOAでは：

各辺ごとに

```text
exp(-i γ Z_i Z_j)
```

を追加します。

自動生成コード：

```python
def apply_cost_unitary(qc, gamma, graph):

    for i, j in graph.edges():

        qc.cx(i, j)
        qc.rz(2 * gamma, j)
        qc.cx(i, j)
```

これで、**任意グラフ対応** になります。

---

## 5. ミキサーハミルトニアンの一般形

ミキサーは：

すべての量子ビットに適用します：

$$
H_B = \sum_i X_i
$$

コード：

```python
def apply_mixer_unitary(qc, beta, n_qubits):

    for i in range(n_qubits):

        qc.rx(2 * beta, i)
```

---

## 6. 一般グラフ用QAOA回路を作る

まとめると：

```python
from qiskit import QuantumCircuit

def create_qaoa_circuit(graph, gamma, beta):

    n = len(graph.nodes())

    qc = QuantumCircuit(n)

    # 初期状態
    for i in range(n):
        qc.h(i)

    # コスト
    apply_cost_unitary(qc, gamma, graph)

    # ミキサー
    apply_mixer_unitary(qc, beta, n)

    qc.measure_all()

    return qc
```

これで、**任意グラフ対応QAOA** が完成です。

---

## 7. Max-Cut評価関数を一般化する

評価関数も **自動化できます**。

```python
def maxcut_value(bitstring, graph):

    value = 0

    for i, j in graph.edges():

        if bitstring[i] != bitstring[j]:

            value += 1

    return value
```

期待値計算：

```python
def compute_expectation(counts, graph):

    expectation = 0
    shots = sum(counts.values())

    for bitstring, count in counts.items():

        value = maxcut_value(bitstring, graph)

        expectation += value * count

    return expectation / shots
```

---

## 8. 4ノードグラフで実行してみる

例：

```python
G = nx.Graph()

G.add_edges_from([
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 0)
])
```

この場合：

最適Cutは：

```text
0101
```

または

```text
1010
```

のようなビット列になります。

---

## 9. なぜ一般化が重要なのか？

理由：

現実問題は：

```text
100ノード
1000ノード
```

のようなグラフになるからです。

応用例：

| 分野  | 問題       |
| --- | -------- |
| 物流  | 配送ルート    |
| 半導体 | 配線配置     |
| 金融  | ポートフォリオ  |
| AI  | クラスタリング  |
| 通信  | ネットワーク分割 |

---

## 10. スケール時の注意点

ノード数が増えると、**問題が発生します**。

① 回路が深くなる

```text
辺の数 ∝ CNOT数
```

② パラメータ探索が難しくなる

**自由度増加**

③ ノイズの影響が増える

**NISQ制約**

---

## 11. 現実的な対策

典型的な対策：

| 方法          | 内容       |
| ----------- | -------- |
| pを小さくする     | 回路短縮     |
| 局所グラフ分割     | 部分問題化    |
| warm start  | 初期値改善    |
| classical併用 | ハイブリッド強化 |

つまり：

量子単独ではなく

古典と組み合わせる

のが基本戦略です。

---

## まとめ

この章のポイント：

* Max-Cutは任意グラフへ拡張可能
* NetworkXでグラフ生成できる
* 辺ごとにZZ回転を追加する
* ミキサーは全量子ビットにRX
* 評価関数も自動生成できる
* 実問題サイズに近づくほど課題が増える

ここまでで、**実用レベルのQAOA実装の基礎** が完成しました。

---
