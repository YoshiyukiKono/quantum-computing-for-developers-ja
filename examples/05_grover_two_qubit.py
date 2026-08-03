"""第7章: 2量子ビットGrover探索で|11>を見つける。"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def main() -> None:
    circuit = QuantumCircuit(2, 2)
    circuit.h([0, 1])

    # Oracle: mark |11> by reversing its phase.
    circuit.cz(0, 1)

    # Diffusion operator.
    circuit.h([0, 1])
    circuit.z([0, 1])
    circuit.cz(0, 1)
    circuit.h([0, 1])
    circuit.measure([0, 1], [0, 1])

    simulator = AerSimulator()
    compiled = transpile(circuit, simulator)
    counts = simulator.run(
        compiled, shots=1_000, seed_simulator=17
    ).result().get_counts()

    assert counts == {"11": 1_000}, counts
    print(counts)
    print("PASS Grover search")


if __name__ == "__main__":
    main()
