"""PETS integration primitives: evidence, governance and portable task interfaces."""
from .evidence_store import EvidenceStore
from .permissions import Role, Permission, authorize
from .adapters import AdapterRegistry, ReadOnlyAdapter
from .platforms import PlatformProfile, PlatformAdapterRegistry, detect_platform, supported_targets
from .sacred_atom import SacredAtomGraph
from .compute_engine import ComputeEngine
from .auto_assembly import AssemblyPlanner, Component
from .sacred_atom_engine import SacredAtomEngine, AtomNode, Layer, ComponentSpec, CPUBackend
from .qbyte_format_scanner import FormatProfile, scan_bytes, scan_file
from .universal_ir import UniversalOperation, build_operation
from .compatibility_switch import CompatibilitySwitch, RuntimeDescriptor
from .audio_contracts import (
    AudioProviderDescriptor, AudioProviderRegistry, TranscriptSegment,
    TranscriptionResult, TranslationResult, build_transcription,
    build_translation, normalize_language_tag,
)

__all__ = [
    "EvidenceStore", "Role", "Permission", "authorize",
    "AdapterRegistry", "ReadOnlyAdapter", "PlatformProfile",
    "PlatformAdapterRegistry", "detect_platform", "supported_targets",
    "SacredAtomGraph", "ComputeEngine", "AssemblyPlanner", "Component",
    "SacredAtomEngine", "AtomNode", "Layer", "ComponentSpec", "CPUBackend",
    "FormatProfile", "scan_bytes", "scan_file", "UniversalOperation",
    "build_operation", "CompatibilitySwitch", "RuntimeDescriptor",
    "AudioProviderDescriptor", "AudioProviderRegistry", "TranscriptSegment",
    "TranscriptionResult", "TranslationResult", "build_transcription",
    "build_translation", "normalize_language_tag",
]
