"""第9章: Toffoliゲートを可逆ANDとして実行する。"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def main() -> None:
    circuit = QuantumCircuit(3, 3)
    circuit.x(0)
    circuit.x(1)
    circuit.ccx(0, 1, 2)
    circuit.measure([0, 1, 2], [0, 1, 2])

    simulator = AerSimulator()
    compiled = transpile(circuit, simulator)
    counts = simulator.run(compiled, shots=1).result().get_counts()

    assert counts == {"111": 1}, counts
    print(counts)
    print("PASS Toffoli reversible AND")


if __name__ == "__main__":
    main()
