"""第16章: 1量子ビットの最小VQEを古典最適化と組み合わせる。"""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Pauli, Statevector
from scipy.optimize import minimize


HAMILTONIAN = Pauli("Z")


def energy(parameters: np.ndarray) -> float:
    circuit = QuantumCircuit(1)
    circuit.ry(float(parameters[0]), 0)
    state = Statevector.from_instruction(circuit)
    return float(np.real(state.expectation_value(HAMILTONIAN)))


def main() -> None:
    result = minimize(energy, x0=np.array([0.2]), method="COBYLA")
    assert result.success, result.message
    assert result.fun < -0.999_999, result.fun
    print({"energy": result.fun, "theta": float(result.x[0])})
    print("PASS minimal VQE")


if __name__ == "__main__":
    main()
