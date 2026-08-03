"""第18章: p=1 QAOAで2ノードMax-Cutを解く。"""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from scipy.optimize import minimize


def qaoa_state(gamma: float, beta: float) -> Statevector:
    circuit = QuantumCircuit(2)
    circuit.h([0, 1])
    circuit.rzz(-gamma, 0, 1)
    circuit.rx(2 * beta, 0)
    circuit.rx(2 * beta, 1)
    return Statevector.from_instruction(circuit)


def expected_cut(parameters: np.ndarray) -> float:
    probabilities = qaoa_state(*map(float, parameters)).probabilities_dict()
    return probabilities.get("01", 0.0) + probabilities.get("10", 0.0)


def objective(parameters: np.ndarray) -> float:
    return -expected_cut(parameters)


def main() -> None:
    result = minimize(
        objective,
        x0=np.array([0.8, 0.4]),
        method="COBYLA",
        options={"maxiter": 200, "tol": 1e-10},
    )
    probability = expected_cut(result.x)
    probabilities = qaoa_state(*map(float, result.x)).probabilities_dict()

    assert result.success, result.message
    assert probability > 0.999_999, (result.x, probabilities)
    print({"parameters": result.x.tolist(), "probabilities": probabilities})
    print("PASS two-node QAOA Max-Cut")


if __name__ == "__main__":
    main()
