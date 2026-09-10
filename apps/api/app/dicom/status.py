STORE_STATUS = {
    0x0000: ("success", "Success"),
    0xB000: ("warning", "Coercion of data elements"),
    0xB006: ("warning", "Elements discarded"),
    0xB007: ("warning", "Dataset does not match SOP class"),
    0xA700: ("failure", "Out of resources"),
    0xA900: ("failure", "Dataset does not match SOP class"),
    0xC000: ("failure", "Cannot understand"),
}


def status_hex(code: int | None) -> str | None:
    return f"0x{code:04X}" if code is not None else None


def classify_store_status(code: int | None) -> tuple[str, str]:
    if code is None:
        return "failure", "No C-STORE response"
    if code in STORE_STATUS:
        return STORE_STATUS[code]
    if 0xB000 <= code <= 0xBFFF:
        return "warning", "C-STORE completed with warning"
    if code != 0:
        return "failure", "C-STORE failed"
    return "success", "Success"

