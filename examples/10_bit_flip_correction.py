"""第27章: 3量子ビット反復符号で単一bit-flip誤りを訂正する。"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def corrected_counts(error_qubit: int) -> dict[str, int]:
    circuit = QuantumCircuit(3, 1)
    circuit.x(0)  # Encode the logical state |1>.
    circuit.cx(0, 1)
    circuit.cx(0, 2)

    circuit.x(error_qubit)

    # Decode, then correct the logical qubit by majority vote.
    circuit.cx(0, 1)
    circuit.cx(0, 2)
    circuit.ccx(1, 2, 0)
    circuit.measure(0, 0)

    simulator = AerSimulator()
    compiled = transpile(circuit, simulator)
    return simulator.run(compiled, shots=32).result().get_counts()


def main() -> None:
    results = {qubit: corrected_counts(qubit) for qubit in range(3)}
    assert all(counts == {"1": 32} for counts in results.values()), results
    print(results)
    print("PASS bit-flip correction")


if __name__ == "__main__":
    main()
