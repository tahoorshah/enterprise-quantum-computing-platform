"""
Standalone Qiskit sanity check.

Purpose: prove Qiskit + AerSimulator work correctly on this machine
BEFORE any of it gets wired into FastAPI or Docker. Run this directly:

    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python app/quantum/sanity_check.py

Expected output: a roughly 50/50 split between '00' and '11' counts
(a 2-qubit Bell state), proving genuine quantum simulation is running —
not fabricated/hardcoded numbers.
"""

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def build_bell_state_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(2, 2)
    qc.h(0)        # Hadamard on qubit 0 -> superposition
    qc.cx(0, 1)    # CNOT -> entangles qubit 0 and qubit 1
    qc.measure([0, 1], [0, 1])
    return qc


def run_circuit(qc: QuantumCircuit, shots: int = 1024) -> dict:
    simulator = AerSimulator()
    job = simulator.run(qc, shots=shots)
    result = job.result()
    return result.get_counts()


if __name__ == "__main__":
    circuit = build_bell_state_circuit()
    print("Circuit:")
    print(circuit.draw(output="text"))

    counts = run_circuit(circuit)
    print("\nMeasurement counts (should be ~50/50 between '00' and '11'):")
    print(counts)
