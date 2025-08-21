import streamlit as st
from qiskit import QuantumCircuit
from qiskit import transpile
from qiskit_aer import Aer
from qiskit_ibm_runtime import SamplerV2 as Sampler
import matplotlib.pyplot as plt
import numpy as np


# initiating a session
if 'circuit_ops' not in st.session_state:
    st.session_state.circuit_ops = []
if 'num_qubits' not in st.session_state:
    st.session_state.num_qubits = 2
if 'run_trigger' not in st.session_state:
    st.session_state.run_trigger = False
if 'result_counts' not in st.session_state:
    st.session_state.result_counts = None


# sidebar controls
st.sidebar.title("QubSim Controls")
st.session_state.num_qubits = st.sidebar.number_input(
    "Number of Qubits", min_value=1, max_value=10, 
    value=st.session_state.num_qubits, step=1
)

col1, col2, col3 = st.sidebar.columns(3)
with col1:
    if st.button("Add H Gate"):
        target = st.number_input(
            "Target Qubit (H)", min_value=0, max_value=st.session_state.num_qubits - 1, value=0, key="h_tgt"
        )
        st.session_state.circuit_ops.append({"gate": "h", "target": target})
with col2:
    if st.button("Add X Gate"):
        target = st.number_input(
            "Target Qubit (X)", min_value=0, max_value=st.session_state.num_qubits - 1, value=0, key="x_tgt"
        )
        st.session_state.circuit_ops.append({"gate": "x", "target": target})
with col3:
    if st.button("Add CNOT"):
        control = st.number_input(
            "Control Qubit", min_value=0, max_value=st.session_state.num_qubits - 1, value=0, key="cx_ctrl"
        )
        target = st.number_input(
            "Target Qubit", min_value=0, max_value=st.session_state.num_qubits - 1, value=1, key="cx_tgt"
        )
        if control != target:
            st.session_state.circuit_ops.append({"gate": "cx", "control": control, "target": target})
        else:
            st.warning("Control and target must differ for CNOT")


if st.sidebar.button("Run Circuit"):
    st.session_state.run_trigger = True

# main display
st.title("QubSim — Qiskit on Streamlit")
st.subheader("Circuit Operations")
if st.session_state.circuit_ops:
    op_strings = []
    for op in st.session_state.circuit_ops:
        if op["gate"] == "cx":
            op_strings.append(f"CX({op['control']}, {op['target']})")
        else:
            op_strings.append(f"{op['gate'].upper()}({op['target']})")
    st.code(" → ".join(op_strings), language="text")
else:
    st.info("No gates added yet.")


# grpahical circuit plot
st.subheader("Circuit Visualization")
fig, ax = plt.subplots(figsize=(10, st.session_state.num_qubits))
for i in range(st.session_state.num_qubits):
    ax.hlines(i, 0, len(st.session_state.circuit_ops) * 2, color="gray")
    ax.text(-0.5, i, f"q[{i}]", fontsize=12)

for idx, op in enumerate(st.session_state.circuit_ops):
    x = idx * 2 + 1
    if op["gate"] == "cx":
        ax.vlines(x, op["control"], op["target"], color="blue")
        ax.scatter(x, [op["control"], op["target"]], color=["black", "red"], s=100)
    else:
        ax.scatter(x, op["target"], color="green", s=120)
        ax.text(x, op["target"] + 0.2, op["gate"].upper(), ha="center", fontsize=12)

ax.axis("off")
st.pyplot(fig)

# simulation logic
def run_circuit_qiskit():
    qc = QuantumCircuit(st.session_state.num_qubits, st.session_state.num_qubits)
    for op in st.session_state.circuit_ops:
        if op["gate"] == "h":
            qc.h(op["target"])
        elif op["gate"] == "x":
            qc.x(op["target"])
        elif op["gate"] == "cx":
            qc.cx(op["control"], op["target"])
    qc.measure_all()

    simulator = Aer.get_backend('qasm_simulator')
    transpiled_circuit = transpile(qc, simulator)
    job = simulator.run(transpiled_circuit, shots=1024)
    result = job.result()
    return result.get_counts()

# results
st.subheader("Measurement Results")
if st.session_state.run_trigger:
    try:
        st.session_state.result_counts = run_circuit_qiskit()
    except Exception as e:
        st.error(f"Simulation failed: {e}")
    finally:
        st.session_state.run_trigger = False

if st.session_state.result_counts:
    st.bar_chart(st.session_state.result_counts)
