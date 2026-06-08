# OCP Neocloud Redfish Profile family (DRAFT v0.5.0)

A layered set of [Redfish Interoperability Profiles](https://www.dmtf.org/dsp/DSP0272) for the OCP
"Scaling AI Clusters at Neoclouds" workgroup. These are **machine-validatable requirement documents**:
run them against a BMC with the [DMTF Redfish-Interop-Validator](https://github.com/DMTF/Redfish-Interop-Validator)
to get a pass/fail conformance report.

They implement the recommendations in [`../docs/neocloud-redfish-gap-analysis.md`](../docs/neocloud-redfish-gap-analysis.md).
Section references below (e.g. "gap 2.1") point into that document.

## The stack (RequiredProfiles composition)

```
OCPNeocloudGPUServer.v0_5_0          <- GPU RAS + conditional telemetry + NVLink fabric
   requires:
   ├─ OCPNeocloudServiceCore.v0_5_0  <- service-plane hardening (eventing, audit, RBAC, attestation)
   │     requires:
   │     ├─ OCPServiceBaseline (1.0.0)            [approved, upstream]
   │     ├─ OCPBaselineHardwareManagement (1.1.0) [approved, upstream]
   │     └─ OCPServerHardwareManagement (1.0.0)   [approved, upstream]
   └─ OCP_UBB_BaselineManagement (1.0.0)          [in-development, upstream]
```

The validator merges all required profiles and applies the **most-restrictive** requirement per property.
So a vendor running the GPU profile is tested against everything in the whole tree at once.

| File | Role |
|---|---|
| `OCPNeocloudServiceCore.v0_5_0.json` | Composes the approved OCP base profiles; promotes the service-plane items the UBB GPU baseline omits — `EventService`, RBAC `Role`s, MFA, a Security-purpose audit `LogService` with actor identity, `MultipartHttpPushUri`, and (Trusted tier) `SecureBoot` + SPDM `ComponentIntegrity`. Also sets the fleet-scale **query-parameter** floor in `Protocol`. |
| `OCPNeocloudGPUServer.v0_5_0.json` | Adds the AI-cluster RAS content: `ProcessorMetrics` (ECC/throttle/PCIe-AER — **absent from UBB**), `MemoryMetrics` HBM ECC (UBB mandates only `BandwidthPercent`), NVLink `Port` health + `Conditions`, `Fabric`/`Switch` (IfImplemented → required where an NVSwitch fabric exists), PCIe bus-drop detection, and a **license-aware conditional telemetry** block. |
| `../registries/OCPAcceleratorRAS.1.0.0.json` | Message-registry **stub** giving XID/SXID/row-remap/bus-drop/NVLink events neutral `MessageId`s (gap 2.2/8.8). The full XID/SXID code→MessageId table is TBD with NVIDIA/AMD. |

## The two conformance tiers

Expressed via `ReadRequirement` level, not separate files (yet):

- **Neocloud-Core** — everything marked `Mandatory`. The floor all 7 OEMs (Supermicro, Dell, Lenovo, HPE,
  Gigabyte, MSI, ASUS) should pass on shipping firmware: inventory, health, **HBM/GPU ECC**, thermal/power,
  multipart update, basic eventing. Uses only direct-GET telemetry (`ProcessorMetrics`/`MemoryMetrics`) that
  needs **no telemetry license**.
- **Neocloud-Trusted** — the `Recommended` items: streaming `TelemetryService` + `Triggers`, SPDM
  `ComponentIntegrity`, enforced `SecureBoot`, full audit log. Pitched at the Tier-1 BMCs
  (Dell iDRAC / HPE iLO / Lenovo XCC3). Operators can demand this contractually.

When the workgroup wants hard tier separation, split into `...-Core` and `...-Trusted` files where Trusted
`RequiredProfiles` Core and raises selected requirements.

## Why telemetry is *conditional* (`IfImplemented`), not Mandatory

Verified OEM constraints (gap 8.3): **HPE iLO implements the Telemetry Service on Intel servers only** (no
AMD/ARM); **Dell** needs an **iDRAC Datacenter license**; **Supermicro** gates Redfish behind **SFT-DCMS**;
**Lenovo** behind **Premier/Platinum**. A hard `TelemetryService=Mandatory` rule is therefore literally
un-implementable on common neocloud nodes. So the GPU profile makes streaming telemetry `IfImplemented`
("if present, the MetricReportDefinitions/MinCollectionInterval/Triggers content is Mandatory") and keeps the
**raw, unlicensed `ProcessorMetrics`/`MemoryMetrics` polling Mandatory** as the Core path.

## How to validate against a BMC (or mockup)

```bash
pip install redfish_interop_validator
# against a live BMC:
rf_interop_validator -i https://<bmc-ip> -u <user> -p <pass> \
    --profile neocloud/profiles/OCPNeocloudGPUServer.v0_5_0.json --schema_directory ./schemas
# the validator merges required profiles; make the upstream ones reachable on its profile path:
# OCPServiceBaseline.v1_0_0.json + OCPBaselineHardwareManagement.v1_1_1.json + OCPServerHardwareManagement.v1_0_0.json
# (repo root) and gpu/OCP_UBB_BaselineManagement.v1.0.0.json.
```
Run it against a real HGX unit from each of the 7 OEMs to set the Core floor *empirically* (gap 4.2).

## Open items the workgroup must resolve (this is a DRAFT)

1. **UBB conflicts inherited by composition.** UBB currently mandates `TelemetryService` (conflicts with the
   license-gating above) and the **deprecated `HttpPushUriOptions`** instead of `MultipartHttpPushUri`
   (open repo issue, Mar 2026). Because most-restrictive wins, requiring UBB re-imposes those. **Fix UBB
   upstream** (schema-refresh pass) or have the neocloud profile selectively re-state UBB's GPU resources
   instead of requiring it wholesale. Until then, treat the conditional-telemetry blocks here as the intended
   end-state.
2. **Conditional / value syntax.** The `Comparison`+`Values` checks (e.g. `ProcessorType AnyOf [GPU,Accelerator]`)
   and `IfImplemented` semantics should be confirmed against your Redfish-Interop-Validator version; some
   releases differ on `CompareProperty`/`CompareType` vs `Comparison`/`Values`.
3. **MinVersion pins** are first-guess (e.g. `ProcessorMetrics 1.6.0` for throttle durations, `MemoryMetrics
   1.7.0`). Confirm against the DSP8010 bundle you standardize on.
4. **OEM/row-remap.** HBM row-remap and NVLink CRC/replay counters are OEM-only today; this profile uses the
   standard `HealthData`/`PortMetrics` proxies and the RAS registry. Drive DMTF schema proposals to make them
   first-class (gap 3, §6 of the analysis).
5. **Rack-scale NVL72 NVLink** is owned by NVIDIA NMX-C / Global Fabric Manager **out-of-band of Redfish**
   (gap 8.7) — the `Fabric`/`Switch` requirements here cover **intra-node** NVLink only.
6. **Registry content.** `OCPAcceleratorRAS` is a stub — the XID/SXID code mapping is the real work item.

## Regenerating

These JSON files are emitted by [`../build_profiles.py`](../build_profiles.py) — edit the Python (it's far more
readable than hand-editing nested JSON) and re-run `python build_profiles.py`.
