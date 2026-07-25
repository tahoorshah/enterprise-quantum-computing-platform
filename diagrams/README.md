# Architecture Diagrams

The 15 mandatory architecture and engineering diagrams required by Section 7
of the project specification. Each is numbered to match the specification's
ordering. All are exported as PNG.

| # | Diagram | File | Shows |
|---|---------|------|-------|
| 1 | Enterprise Quantum Computing Architecture | `01-enterprise-quantum-architecture.png` | Full layered view: QFT Bank business actors, presentation/application/simulation/data layers, and the infrastructure & operations tier (Terraform, Kubernetes, Prometheus/Grafana, Jenkins). |
| 2 | High-Level Solution Architecture | `02-high-level-solution-architecture.png` | Three actor types and their high-level data exchanges with the platform. |
| 3 | Detailed System Architecture | `03-detailed-system-architecture.png` | Container-level internals: nginx frontend, FastAPI routers, business-logic modules, persistence layer with graceful fallback, and Prometheus scraping. |
| 4 | Quantum Computing Platform Architecture | `04-quantum-platform-architecture.png` | The quantum simulation layer: Qiskit Aer, PennyLane, and Cirq behind the application modules. |
| 5 | Quantum Circuit Workflow | `05-quantum-circuit-workflow.png` | End-to-end circuit execution: validation, circuit build, Aer execution, persistence with in-memory fallback, UI render. |
| 6 | Portfolio Optimization Architecture | `06-portfolio-optimization-architecture.png` | Module 2 pipeline: market data → QUBO/QAOA optimization → risk calculation → dashboard aggregation. |
| 7 | Enterprise Network Architecture | `07-enterprise-network-architecture.png` | Kubernetes network zones: external, exposed boundary (NodePort), internal ClusterIP-only network, and observability. |
| 8 | Network Flow | `08-network-flow.png` | Numbered request lifecycle from browser through NodePort, nginx, backend, to PostgreSQL/Redis and back. |
| 9 | Data Flow Diagram (Level 0) | `09-data-flow-level-0.png` | Context diagram: the platform as a single process exchanging data with three external actors and the execution store. |
| 10 | Data Flow Diagram (Level 1) | `10-data-flow-level-1.png` | Decomposition into the five numbered functional processes, two datastores, and their labelled data flows. |
| 11 | Quantum Algorithm Execution Workflow | `11-quantum-algorithm-execution-workflow.png` | Algorithm selection and execution path for Grover, QFT, QAOA, and VQE. |
| 12 | Post-Quantum Cryptography Readiness Architecture | `12-pqc-readiness-architecture.png` | Module 5: quantum threat model, NIST PQC catalogue, inventory scan, and migration planning. |
| 13 | Financial Analytics Workflow | `13-financial-analytics-workflow.png` | Analytics pipeline from simulated data through QAOA allocation and risk to executive dashboard metrics. |
| 14 | Database Entity Relationship Diagram | `14-database-erd.png` | The unified `executions` table and the logical shape of its JSON result payload. |
| 15 | Sequence Diagram | `15-sequence-portfolio-to-reports.png` | Portfolio optimization via quantum simulation (with the COBYLA optimization loop) and subsequent executive-report generation. |

All diagrams are explained during both the presentation and the viva voce
examination, as required by the specification.
