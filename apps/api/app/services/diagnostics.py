RECOMMENDATIONS = {
    "TCP_CONNECTION_FAILED": "Host, Port, Routing und Firewall der Gegenstelle prüfen.",
    "DICOM_ASSOCIATION_REJECTED": "Called AE, Calling AE und die Freigabe der Quell-IP prüfen.",
    "DICOM_ASSOCIATION_ABORTED": "PACS-/RIS-Log auf einen aktiven Association-Abbruch prüfen.",
    "DICOM_TIMEOUT": "Timeouts und Auslastung der Gegenstelle prüfen und den Test wiederholen.",
    "DICOM_NO_PRESENTATION_CONTEXT": "SOP Class und Transfer Syntax mit der PACS-Freigabe abgleichen.",
    "DICOM_C_FIND_FAILED": "C-FIND-Status und MWL-Berechtigung im RIS/PACS prüfen.",
    "DICOM_STORE_WARNING": "Das Objekt wurde angenommen; Warnstatus im PACS-Log nachschlagen.",
    "DICOM_STORE_FAILED": "C-STORE-Status, Speicherregeln und PACS-Importlog prüfen.",
    "MODALITY_TARGET_MISSING": "Profil bearbeiten und für jeden aktiven Dienst ein Ziel auswählen.",
}


def recommendation_for(code: str | None) -> str | None:
    return RECOMMENDATIONS.get(code or "")
