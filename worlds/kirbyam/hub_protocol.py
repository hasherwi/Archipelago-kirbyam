"""Fail closed for incompatible Hub item IDs, transport and saved checks."""
HUB_PROTOCOL_VERSION = 2
HUB_MARKER_OFFSET = 0x1000008
HUB_MARKER = b"APHUB02\0"


def hub_slot_version(slot: dict) -> int:
    """Zero denotes a legacy slot without Hub items; drafts must regenerate."""
    version = slot.get("hub_connection_protocol_version")
    if version is not None:
        if type(version) is not int or version != HUB_PROTOCOL_VERSION:
            raise ValueError("unsupported Hub connection protocol")
        return version
    labels = slot.get("unique_items", ())
    if not isinstance(labels, (list, tuple)):
        raise ValueError("invalid Hub item catalog")
    if any(isinstance(label, str) and "Hub Connection" in label for label in labels):
        raise ValueError("old Hub draft slot requires regeneration")
    return 0
