# DICOM Support Matrix

## Services

| Service | Status |
|---|---|
| C-ECHO SCU | Supported |
| MWL C-FIND SCU | Supported |
| C-STORE SCU | Supported |
| C-MOVE / C-GET | Not supported |
| Storage Commitment | Not supported |
| Storage SCP | Not supported (nur Test-SCP in automatisierten Tests) |

## Storage SOP Classes

| SOP Class | Synthetisch | Upload |
|---|---:|---:|
| Secondary Capture Image Storage | Supported | Supported |
| CT Image Storage | Supported | Supported |
| MR Image Storage | Supported | Supported |
| Ultrasound Image Storage | Supported | Supported |
| Computed Radiography Image Storage | Supported | Supported |
| Digital X-Ray Image Storage for Presentation | Supported | Supported |

## Transfer Syntaxes

Explicit VR Little Endian und Implicit VR Little Endian werden für synthetische Objekte unterstützt. Bei Uploads wird die in der Datei deklarierte Transfer Syntax angefordert. Komprimierte Uploads können gesendet werden, wenn pydicom sie lesen kann und der SCP den Context akzeptiert; DCMSim transkodiert nicht.

MWL unterstützt Datum, Modalität, Scheduled Station AE Title, Patient ID, Accession Number und Patient Name sowie eine Broad Query. Query/Retrieve, HL7 und produktive SCP-Dienste gehören nicht zum MVP.

