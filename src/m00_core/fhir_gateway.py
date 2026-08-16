"""
fhir_gateway.py - M00 HL7 FHIR R4 標準轉換閘道
"""

import json
import sqlite3
from typing import Dict, Any, List, Optional
from src.m00_core.utils_db import get_sqlite_connection


def convert_entity_to_fhir_resource(entity_id: str, db_path: str = "tw-med-db/db/med.db") -> Dict[str, Any]:
    """
    將 M00 實體資料轉換為標準 HL7 FHIR R4 JSON Payload (Patient / MedicationRequest / Observation)
    """
    conn = get_sqlite_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT entity_id, entity_type, title, subtitle FROM m00_entities WHERE entity_id = ?;", (entity_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {
            "resourceType": "OperationOutcome",
            "id": entity_id,
            "issue": [{"severity": "error", "code": "not-found", "diagnostics": f"Entity '{entity_id}' not found"}]
        }

    e_id, e_type, title, subtitle = row[0], row[1], row[2], row[3]

    if e_type == "DRUG":
        fhir_payload = {
            "resourceType": "MedicationRequest",
            "id": e_id,
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "https://twcore.mohw.gov.tw/fhir/CodeSystem/medication-tw",
                    "code": e_id,
                    "display": title
                }],
                "text": f"{title} ({subtitle})"
            }
        }
    elif e_type == "LAB_LOINC":
        fhir_payload = {
            "resourceType": "Observation",
            "id": e_id.replace("-", "_"),
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": e_id,
                    "display": title
                }]
            },
            "valueQuantity": {
                "unit": subtitle
            }
        }
    elif e_type == "HOSPITAL":
        fhir_payload = {
            "resourceType": "Organization",
            "id": e_id,
            "name": title,
            "type": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                    "code": "prov",
                    "display": subtitle
                }]
            }]
        }
    else:
        fhir_payload = {
            "resourceType": "Basic",
            "id": e_id,
            "code": {"text": e_type},
            "subject": {"display": title}
        }

    conn.close()
    return fhir_payload
