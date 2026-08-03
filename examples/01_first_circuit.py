"""第1章: 最初の量子回路を構築する。"""

import sys

from qiskit import QuantumCircuit


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)

    operations = circuit.count_ops()
    assert operations.get("h") == 1
    assert operations.get("measure") == 1
    print(circuit.draw("text"))
    print("PASS first circuit")


if __name__ == "__main__":
    main()
