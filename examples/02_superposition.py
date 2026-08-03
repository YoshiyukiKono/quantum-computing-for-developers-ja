"""第2章: Hadamardゲートによる重ね合わせを測定する。"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


SHOTS = 2_000


def main() -> None:
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)

    simulator = AerSimulator()
    compiled = transpile(circuit, simulator)
    result = simulator.run(compiled, shots=SHOTS, seed_simulator=7).result()
    counts = result.get_counts()

    assert set(counts) == {"0", "1"}
    probability_zero = counts["0"] / SHOTS
    assert 0.45 <= probability_zero <= 0.55, counts
    print(counts)
    print("PASS superposition")


if __name__ == "__main__":
    main()
