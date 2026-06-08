#!/usr/bin/env python3
"""Generates the OCP Neocloud Redfish Interoperability Profile family.

Outputs (Redfish Interop Profile format, RedfishInteroperabilityProfile.v1_6_0):
  profiles/OCPNeocloudServiceCore.v0_5_0.json   - composition + service-plane hardening
  profiles/OCPNeocloudGPUServer.v0_5_0.json     - GPU RAS + conditional telemetry + fabric
  registries/OCPAcceleratorRAS.1.0.0.json       - XID/SXID/RAS message registry (stub)

Run: python build_profiles.py
"""
import json, os

os.makedirs("profiles", exist_ok=True)
os.makedirs("registries", exist_ok=True)

def M(**kw):  d = {"ReadRequirement": "Mandatory"};   d.update(kw); return d
def R(**kw):  d = {"ReadRequirement": "Recommended"};  d.update(kw); return d
def IfImpl(**kw): d = {"ReadRequirement": "IfImplemented"}; d.update(kw); return d


# =====================================================================
# FILE 1: OCPNeocloudServiceCore - composition + service-plane hardening
# =====================================================================
service_core = {
  "SchemaDefinition": "RedfishInteroperabilityProfile.v1_6_0",
  "ProfileName": "OCPNeocloudServiceCore",
  "ProfileVersion": "0.5.0",
  "Purpose": ("Neocloud service-plane core. Composes the approved OCP base profiles and tightens the "
              "service-plane (eventing, audit, security, fleet-scale query) requirements neoclouds need. "
              "Intended to be required by domain profiles (GPU, Fabric, Storage, Rack)."),
  "OwningEntity": "Open Compute Project",
  "ContributedBy": "OCP Scaling AI Clusters at Neoclouds workgroup (DRAFT)",
  "ContactInfo": "jm@farmgpu.com",
  "RequiredProfiles": {
     "OCPServiceBaseline":            {"MinVersion": "1.0.0"},
     "OCPBaselineHardwareManagement": {"MinVersion": "1.1.0"},
     "OCPServerHardwareManagement":   {"MinVersion": "1.0.0"}
  },
  "Protocol": {
     "MinVersion": "1.16",
     "ExpandQuery":  "Recommended",
     "SelectQuery":  "Recommended",
     "FilterQuery":  "Recommended",
     "ExcerptQuery": "Recommended",
     "OnlyQuery":    "Mandatory",
     "DeepPATCH":    "None",
     "DeepPOST":     "None"
  },
  "Resources": {
    "ServiceRoot": {
      "ReadRequirement": "Mandatory",
      "PropertyRequirements": {
        "EventService":       M(),
        "CertificateService": M(),
        "SessionService":     M(),
        "UpdateService":      M(),
        "TelemetryService":   R(Purpose="License/platform-gated on several OEMs (HPE telemetry is Intel-only; Dell needs a Datacenter license). Required at Neocloud-Trusted; conditional content lives in the GPU profile."),
        "AggregationService": R(Purpose="Enables a node/rack/pod aggregator to unify subordinate BMCs and the NVIDIA HGX controller into one event+telemetry stream (gap analysis 7.1).")
      }
    },
    "EventService": {
      "ReadRequirement": "Mandatory",
      "Purpose": "Push eventing is the backbone of monitoring + SIEM forwarding; absent from the GPU baseline today.",
      "PropertyRequirements": {
        "ServiceEnabled":                    M(),
        "Subscriptions":                     M(),
        "ServerSentEventUri":                R(Purpose="SSE streaming of events/metric reports."),
        "IncludeOriginOfConditionSupported": R(Purpose="Lets subscribers receive the faulting resource state inline with the event (DSP0266 1.22)."),
        "RegistryPrefixes":                  R(),
        "ResourceTypes":                     R()
      },
      "ActionRequirements": {"SubmitTestEvent": R()}
    },
    "EventDestination": {
      "ReadRequirement": "IfPopulated",
      "PropertyRequirements": {
        "Destination":              M(),
        "Protocol":                 M(),
        "SubscriptionType":         M(),
        "EventFormatType":          R(Purpose="Allow MetricReport format for telemetry streaming."),
        "IncludeOriginOfCondition": R(),
        "DeliveryRetryPolicy":      R(),
        "SyslogFilters":            R(Purpose="Forward security/audit events to a SIEM via syslog.")
      }
    },
    "AccountService": {
      "ReadRequirement": "Mandatory",
      "Purpose": "RBAC + external identity + MFA for the management plane (ClusterMAX Security / RBAC-SSO).",
      "PropertyRequirements": {
        "Accounts":                M(),
        "Roles":                   M(),
        "LDAP":                    R(),
        "ActiveDirectory":         R(),
        "OAuth2":                  R(Purpose="Delegated auth / SSO (DSP0266 13.4.4)."),
        "MultiFactorAuth":         R(Purpose="TOTP/MFA for session creation (DSP0266 13.5.5)."),
        "AccountLockoutThreshold": R(),
        "MinPasswordLength":       R()
      }
    },
    "Role": {
      "ReadRequirement": "Mandatory",
      "PropertyRequirements": {"RoleId": M(), "AssignedPrivileges": M(), "IsPredefined": R()}
    },
    "SessionService": {
      "ReadRequirement": "Mandatory",
      "PropertyRequirements": {"SessionTimeout": M(), "Sessions": M()}
    },
    "Session": {
      "ReadRequirement": "Mandatory",
      "Purpose": "Audit identity: who connected, from where, when.",
      "PropertyRequirements": {
        "UserName":              M(),
        "ClientOriginIPAddress": R(),
        "CreatedTime":           R()
      }
    },
    "LogService": {
      "ReadRequirement": "Mandatory",
      "Purpose": "Require a Security-purpose audit log capturing privileged actions with actor identity.",
      "PropertyRequirements": {
        "Entries":        M(),
        "LogPurposes":    R(Purpose="At least one LogService with LogPurposes containing 'Security' for audit (ClusterMAX audit-log criteria)."),
        "ServiceEnabled": R()
      },
      "ActionRequirements": {"ClearLog": R()}
    },
    "LogEntry": {
      "ReadRequirement": "Mandatory",
      "PropertyRequirements": {
        "Created":           M(),
        "Severity":          M(),
        "Message":           M(),
        "MessageId":         M(),
        "Originator":        R(Purpose="Actor identity on privileged actions (audit)."),
        "OriginatorType":    R(),
        "OriginOfCondition": R()
      }
    },
    "UpdateService": {
      "ReadRequirement": "Mandatory",
      "Purpose": "Modern multipart push (deprecates HttpPushUriOptions); component-targeted firmware update.",
      "PropertyRequirements": {
        "ServiceEnabled":       M(),
        "FirmwareInventory":    M(),
        "MultipartHttpPushUri": M(Purpose="Component-targeted push update; preferred over deprecated HttpPushUri (open UBB issue).")
      },
      "ActionRequirements": {
        "SimpleUpdate": R(Parameters={"ImageURI": M(), "Targets": R(), "TransferProtocol": R()})
      }
    },
    "SecureBoot": {
      "ReadRequirement": "Recommended",
      "Purpose": "Neocloud-Trusted tier. Boot integrity (ClusterMAX Security; CoreWeave-Platinum cited Secure/Measured Boot).",
      "PropertyRequirements": {"SecureBootEnable": R(), "SecureBootCurrentBoot": R(), "SecureBootMode": R()}
    },
    "ComponentIntegrity": {
      "ReadRequirement": "Recommended",
      "Purpose": "Neocloud-Trusted tier. SPDM/TPM device attestation of GPUs/NICs/baseboards (gap analysis 4.1; OCP Security WG).",
      "PropertyRequirements": {
        "ComponentIntegrityType":    R(),
        "ComponentIntegrityEnabled": R(),
        "TargetComponentURI":        R(),
        "SPDM":                      R()
      },
      "ActionRequirements": {"SPDMGetSignedMeasurements": R()}
    }
  },
  "Registries": {
    "Base": {"MinVersion": "1.0.0", "Repository": "redfish.dmtf.org/registries", "Messages": {}}
  }
}


# =====================================================================
# FILE 2: OCPNeocloudGPUServer - GPU RAS + conditional telemetry + fabric
# =====================================================================
gpu_server = {
  "SchemaDefinition": "RedfishInteroperabilityProfile.v1_6_0",
  "ProfileName": "OCPNeocloudGPUServer",
  "ProfileVersion": "0.5.0",
  "Purpose": ("Neocloud GPU server profile. Builds on OCPNeocloudServiceCore and the UBB GPU baseline and "
              "adds the AI-cluster RAS signals ClusterMAX weights most: GPU/HBM ECC, throttle, PCIe AER, "
              "NVLink/NVSwitch fabric health, active health Conditions, and a license-aware (conditional) "
              "telemetry contract plus an accelerator-RAS message registry for XID/SXID."),
  "OwningEntity": "Open Compute Project",
  "ContributedBy": "OCP Scaling AI Clusters at Neoclouds workgroup (DRAFT)",
  "ContactInfo": "jm@farmgpu.com",
  "RequiredProfiles": {
     "OCPNeocloudServiceCore":   {"MinVersion": "0.5.0"},
     "OCP_UBB_BaselineManagement": {"MinVersion": "1.0.0"}
  },
  "Protocol": {"MinVersion": "1.16"},
  "Resources": {

    # ---- GPU as Processor: require live metrics + active conditions ----
    "Processor": {
      "MinVersion": "1.16.0",
      "ReadRequirement": "Mandatory",
      "PropertyRequirements": {
        "ProcessorType": M(Comparison="AnyOf", Values=["GPU", "Accelerator"],
                           Purpose="Scope GPU requirements to accelerator processors."),
        "Metrics":          M(Purpose="Raise from UBB-Recommended: GPU telemetry must be reachable."),
        "EnvironmentMetrics": M(),
        "Ports":            M(),
        "Status": M(PropertyRequirements={
            "Health":     M(),
            "State":      M(),
            "Conditions": R(Purpose="Active-fault list (XID/ECC/NVLink conditions) without log scraping; gap analysis 8.4.")
        })
      }
    },

    # ---- NEW vs UBB: ProcessorMetrics with ECC + throttle + PCIe AER ----
    "ProcessorMetrics": {
      "MinVersion": "1.6.0",
      "ReadRequirement": "Mandatory",
      "Purpose": "Absent from the UBB baseline. Carries the GPU health signals ClusterMAX requires.",
      "PropertyRequirements": {
        "BandwidthPercent":   M(),
        "OperatingSpeedMHz":  R(),
        "ThrottlingCelsius":  R(Purpose="Thermal-throttle margin."),
        "PowerLimitThrottleDuration":   R(),
        "ThermalLimitThrottleDuration": R(),
        "CacheMetricsTotal": R(PropertyRequirements={
            "LifeTime": M(PropertyRequirements={
                "CorrectableECCErrorCount":   M(),
                "UncorrectableECCErrorCount": M()
            })
        }),
        "PCIeErrors": R(Purpose="PCIe AER - link instability / 'GPU fell off the bus' (gap analysis 2.1).",
            PropertyRequirements={
                "CorrectableErrorCount": M(),
                "NonFatalErrorCount":    M(),
                "FatalErrorCount":       M(),
                "L0ToRecoveryCount":     R(),
                "ReplayCount":           R()
        })
      }
    },

    # ---- MemoryMetrics: raise UBB (BandwidthPercent-only) to mandate ECC ----
    "MemoryMetrics": {
      "MinVersion": "1.7.0",
      "ReadRequirement": "Mandatory",
      "Purpose": "UBB requires only BandwidthPercent. Mandate HBM ECC counts and health data.",
      "PropertyRequirements": {
        "BandwidthPercent": M(),
        "CurrentPeriod": R(PropertyRequirements={
            "CorrectableECCErrorCount":   M(),
            "UncorrectableECCErrorCount": M()
        }),
        "LifeTime": M(PropertyRequirements={
            "CorrectableECCErrorCount":   M(),
            "UncorrectableECCErrorCount": M()
        }),
        "HealthData": R(Purpose="HBM health incl. spare-block/row-remap proxies.",
            PropertyRequirements={
                "PredictedMediaLifeLeftPercent": R(),
                "RemainingSpareBlockPercentage": R(),
                "AlarmTrips": R(PropertyRequirements={
                    "CorrectableECCError":   R(),
                    "UncorrectableECCError": R(),
                    "SpareBlock":            R(),
                    "Temperature":           R()
                })
        })
      }
    },

    # ---- NVLink ports (under Processor): link health + flap + errors ----
    "Port": {
      "MinVersion": "1.16.0",
      "ReadRequirement": "Mandatory",
      "PropertyRequirements": {
        "LinkState":  M(Purpose="Raise from UBB-Recommended."),
        "LinkStatus": M(Purpose="Raise from UBB-Recommended. NOTE: trust with care on GB200 - NVIDIA fw bug can misreport (gap analysis 8.7)."),
        "LinkTransitionIndicator": R(Purpose="Link-flap signal (no standard cumulative flap counter yet - gap 2.4)."),
        "CurrentSpeedGbps": M(),
        "Metrics":          M(),
        "Status": M(PropertyRequirements={"Health": M(), "State": M(), "Conditions": R()})
      }
    },
    "PortMetrics": {
      "MinVersion": "1.5.0",
      "ReadRequirement": "Mandatory",
      "Purpose": "UBB requires only RX/TXBytes. Add error counters where available (NVLink CRC/replay are OEM today).",
      "PropertyRequirements": {
        "RXBytes":  M(),
        "TXBytes":  M(),
        "RXErrors": R(),
        "TXErrors": R()
      }
    },

    # ---- NVSwitch fabric: IfImplemented (Mandatory where an NVLink fabric exists) ----
    "Fabric": {
      "MinVersion": "1.3.0",
      "ReadRequirement": "IfImplemented",
      "Purpose": "Single-node HGX may not expose a fabric; an NVSwitch/NVL72 fabric MUST (gap analysis 2.3/8.7). Rack-scale NVL72 NVLink is owned by NVIDIA GFM out-of-band - see README.",
      "PropertyRequirements": {
        "FabricType": M(Comparison="AnyOf", Values=["NVLink", "InfiniBand", "Ethernet", "PCIe"]),
        "Switches":   M(),
        "Status": M(PropertyRequirements={"Health": M(), "State": M(), "Conditions": R()})
      }
    },
    "Switch": {
      "MinVersion": "1.9.0",
      "ReadRequirement": "IfImplemented",
      "PropertyRequirements": {
        "SwitchType":      M(),
        "FirmwareVersion": R(),
        "Ports":           M(),
        "Metrics":         R(),
        "Status": M(PropertyRequirements={"Health": M(), "State": M(), "Conditions": R()})
      }
    },

    # ---- PCIe bus-presence (bus-drop detection) ----
    "PCIeDevice": {
      "MinVersion": "1.0.0",
      "ReadRequirement": "Mandatory",
      "PropertyRequirements": {
        "Status": M(Purpose="State=Absent/UnavailableOffline is the standard 'device left the bus' signal.",
            PropertyRequirements={"Health": M(), "State": M()})
      }
    },

    # ---- Conditional telemetry: required ONLY IF TelemetryService is implemented ----
    "TelemetryService": {
      "MinVersion": "1.3.0",
      "ReadRequirement": "IfImplemented",
      "Purpose": ("License/platform-gated (HPE Intel-only; Dell Datacenter license; Supermicro SFT-DCMS). "
                  "Do NOT hard-require streaming. IF implemented, the content below is Mandatory. "
                  "NOTE: requiring UBB currently inherits its hard TelemetryService mandate - see README open issue."),
      "PropertyRequirements": {
        "MetricReportDefinitions": M(),
        "MetricReports":           M(),
        "MinCollectionInterval":   M(),
        "Triggers": R(Purpose="Threshold alerting on temp/power/ECC.")
      }
    },
    "MetricReportDefinition": {
      "MinVersion": "1.4.0",
      "ReadRequirement": "IfImplemented",
      "PropertyRequirements": {
        "MetricReport":               M(),
        "MetricReportDefinitionType": R(Comparison="AnyOf", Values=["Periodic", "OnChange", "OnRequest"]),
        "Metrics":                    R()
      }
    },
    "Triggers": {
      "MinVersion": "1.0.0",
      "ReadRequirement": "IfImplemented",
      "Purpose": "If telemetry is present, threshold triggers enable out-of-band alerting (temp/power/ECC).",
      "PropertyRequirements": {"MetricType": R(), "NumericThresholds": R()}
    }
  },

  "Registries": {
    "OCPAcceleratorRAS": {
      "MinVersion": "1.0.0",
      "Repository": "github.com/jmhands/HWMgmt-OCP-Profiles/tree/neocloud-profiles/neocloud/registries",
      "Messages": {
        "GPUXidError":            {},
        "NVSwitchSxidError":      {},
        "GPURowRemappingPending": {},
        "GPURowRemappingFailure": {},
        "GPUFellOffBus":          {},
        "NVLinkError":            {}
      }
    }
  }
}


# =====================================================================
# FILE 3: OCPAcceleratorRAS message registry (DSP8011 format) - STUB
# =====================================================================
ras_registry = {
  "@Redfish.Copyright": "Copyright 2026 Open Compute Project. Released under CC-BY-SA-4.0.",
  "@odata.type": "#MessageRegistry.v1_6_2.MessageRegistry",
  "Id": "OCPAcceleratorRAS.1.0.0",
  "Name": "OCP Accelerator RAS Message Registry",
  "Language": "en",
  "Description": ("Standardized Redfish messages for accelerator (GPU/NVSwitch) RAS events, mapping vendor "
                  "error codes (NVIDIA XID/SXID; AMD equivalents) onto neutral MessageIds for use in "
                  "LogEntry.MessageId and Event payloads. DRAFT stub for OCP workgroup review - the full "
                  "XID/SXID code-to-MessageId mapping table is TBD and must be developed with NVIDIA/AMD."),
  "RegistryPrefix": "OCPAcceleratorRAS",
  "RegistryVersion": "1.0.0",
  "OwningEntity": "Open Compute Project",
  "Messages": {
    "GPUXidError": {
      "Description": "A GPU reported an NVIDIA XID error.",
      "Message": "GPU '%1' reported XID error %2: %3.",
      "Severity": "Critical",
      "MessageSeverity": "Critical",
      "NumberOfArgs": 3,
      "ParamTypes": ["string", "number", "string"],
      "Resolution": "Correlate the XID code with the NVIDIA XID reference. Drain and diagnose the node; replace the GPU if the fault is persistent or uncorrectable."
    },
    "NVSwitchSxidError": {
      "Description": "An NVSwitch reported an SXID error.",
      "Message": "NVSwitch '%1' reported SXID error %2: %3.",
      "Severity": "Critical",
      "MessageSeverity": "Critical",
      "NumberOfArgs": 3,
      "ParamTypes": ["string", "number", "string"],
      "Resolution": "Assess NVLink fabric blast radius; drain affected GPUs and diagnose the NVSwitch."
    },
    "GPURowRemappingPending": {
      "Description": "A GPU has a pending HBM row remapping that requires a reset to take effect.",
      "Message": "GPU '%1' has a pending memory row remapping.",
      "Severity": "Warning",
      "MessageSeverity": "Warning",
      "NumberOfArgs": 1,
      "ParamTypes": ["string"],
      "Resolution": "Schedule a GPU reset during the next maintenance window to apply the remapping."
    },
    "GPURowRemappingFailure": {
      "Description": "A GPU HBM row remapping operation failed.",
      "Message": "GPU '%1' memory row remapping failed.",
      "Severity": "Critical",
      "MessageSeverity": "Critical",
      "NumberOfArgs": 1,
      "ParamTypes": ["string"],
      "Resolution": "Drain the node and replace the GPU."
    },
    "GPUFellOffBus": {
      "Description": "A GPU is no longer present on the PCIe bus.",
      "Message": "GPU '%1' is no longer responding on the PCIe bus.",
      "Severity": "Critical",
      "MessageSeverity": "Critical",
      "NumberOfArgs": 1,
      "ParamTypes": ["string"],
      "Resolution": "Drain the node; check PCIe AER counters and reseat/replace the GPU."
    },
    "NVLinkError": {
      "Description": "An NVLink port reported an error or link-state change.",
      "Message": "NVLink port '%1' on '%2' reported error condition: %3.",
      "Severity": "Warning",
      "MessageSeverity": "Warning",
      "NumberOfArgs": 3,
      "ParamTypes": ["string", "string", "string"],
      "Resolution": "Inspect NVLink error counters and link status; if persistent, drain and diagnose."
    }
  }
}


def write(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"wrote {path}: {os.path.getsize(path)} bytes")

write("profiles/OCPNeocloudServiceCore.v0_5_0.json", service_core)
write("profiles/OCPNeocloudGPUServer.v0_5_0.json", gpu_server)
write("registries/OCPAcceleratorRAS.1.0.0.json", ras_registry)
print("done.")
