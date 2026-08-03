"""第4章: Bell状態を作り、相関を測定する。"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


SHOTS = 2_000


def main() -> None:
    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])

    simulator = AerSimulator()
    compiled = transpile(circuit, simulator)
    counts = simulator.run(
        compiled, shots=SHOTS, seed_simulator=11
    ).result().get_counts()

    assert set(counts) == {"00", "11"}, counts
    probability_00 = counts["00"] / SHOTS
    assert 0.45 <= probability_00 <= 0.55, counts
    print(counts)
    print("PASS Bell state")


if __name__ == "__main__":
    main()
