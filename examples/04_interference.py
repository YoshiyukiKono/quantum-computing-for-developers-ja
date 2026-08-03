"""第5章: Hゲートを2回適用した干渉を確認する。"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def main() -> None:
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.h(0)
    circuit.measure(0, 0)

    simulator = AerSimulator()
    compiled = transpile(circuit, simulator)
    counts = simulator.run(
        compiled, shots=1_000, seed_simulator=13
    ).result().get_counts()

    assert counts == {"0": 1_000}, counts
    print(counts)
    print("PASS interference")


if __name__ == "__main__":
    main()
