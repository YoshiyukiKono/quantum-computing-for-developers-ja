"""第13章: QFTと逆QFTを連続適用して入力状態へ戻す。"""

from math import pi

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


def qft(num_qubits: int) -> QuantumCircuit:
    circuit = QuantumCircuit(num_qubits, name="QFT")
    for target in reversed(range(num_qubits)):
        circuit.h(target)
        for control in reversed(range(target)):
            angle = pi / (2 ** (target - control))
            circuit.cp(angle, control, target)
    for left in range(num_qubits // 2):
        circuit.swap(left, num_qubits - left - 1)
    return circuit


def main() -> None:
    num_qubits = 3
    circuit = QuantumCircuit(num_qubits)
    circuit.x(0)
    circuit.x(2)  # Prepare |101> = |5>.

    transform = qft(num_qubits)
    circuit.compose(transform, inplace=True)
    circuit.compose(transform.inverse(), inplace=True)

    probabilities = Statevector.from_instruction(circuit).probabilities_dict()
    assert probabilities.get("101", 0.0) > 1.0 - 1e-12, probabilities
    print(probabilities)
    print("PASS QFT round trip")


if __name__ == "__main__":
    main()
