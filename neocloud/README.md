# Neocloud Redfish Profiles (DRAFT — work in progress)

Working area for the OCP **Scaling AI Clusters at Neoclouds** workgroup: a cross-vendor Redfish
Interoperability Profile family for managing GPU servers, plus the gap analysis that motivates it.

> **Status: early draft (v0.5.0) for workgroup discussion.** Not an approved OCP profile. Names specific
> OEM behaviors and uses the SemiAnalysis ClusterMAX criteria as the evaluation lens.

## Contents

| Path | What it is |
|---|---|
| [`docs/neocloud-redfish-gap-analysis.md`](docs/neocloud-redfish-gap-analysis.md) | Gap analysis of the current OCP profile corpus vs. ClusterMAX — what Redfish/the standard can mandate today (🟢), what needs DMTF/OCP standards work (🟡), and what is out of scope (🔴). Covers the schema gaps, the DSP0266 v1.24 protocol features to leverage, the 7-OEM implementability constraint, and the NVIDIA HMC/AMC aggregation seam. |
| [`profiles/OCPNeocloudServiceCore.v0_5_0.json`](profiles/OCPNeocloudServiceCore.v0_5_0.json) | Service-plane core. Composes the approved OCP base profiles (`RequiredProfiles`) and hardens eventing, RBAC, audit logging, attestation, and the fleet-scale query floor. |
| [`profiles/OCPNeocloudGPUServer.v0_5_0.json`](profiles/OCPNeocloudGPUServer.v0_5_0.json) | GPU server profile. Adds the AI-cluster RAS content missing from the UBB baseline (GPU/HBM ECC, throttle, PCIe AER, NVLink/NVSwitch fabric, active-fault `Conditions`) and a **license-aware conditional telemetry** contract. |
| [`registries/OCPAcceleratorRAS.1.0.0.json`](registries/OCPAcceleratorRAS.1.0.0.json) | Message-registry **stub** giving XID / SXID / row-remap / bus-drop / NVLink events neutral `MessageId`s. The full vendor-code mapping is the open work item. |
| [`profiles/README.md`](profiles/README.md) | How the profiles compose, the Core vs Trusted tiers, how to run the DMTF Redfish-Interop-Validator, and the open issues. |
| [`build_profiles.py`](build_profiles.py) | Generator for the profile/registry JSON. Edit the Python and re-run (`python build_profiles.py` from this folder) rather than hand-editing nested JSON. |

## Relationship to the upstream repo

These build on the approved OCP profiles in the repo root (`OCPServiceBaseline`, `OCPBaselineHardwareManagement`,
`OCPServerHardwareManagement`) and the in-development `gpu/OCP_UBB_BaselineManagement` via `RequiredProfiles`
composition. See the open-items list in [`profiles/README.md`](profiles/README.md) — notably, a few UBB
requirements (hard `TelemetryService` mandate; deprecated `HttpPushUriOptions`) should be refreshed upstream
before this can be enforced cleanly.

## Feedback

Issues / PRs welcome, or raise in the OCP Scaling AI Clusters at Neoclouds workgroup. Contact: jm@farmgpu.com
