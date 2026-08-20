from dataclasses import dataclass

from apps.documents.models import Document, OCRResult
from apps.documents.services.document_ocr import process_document_ocr
from apps.documents.services.ocr_factory import get_ocr_service
from apps.rules.service import run_rule_engine


@dataclass
class PipelineResult:
    document: Document
    ocr_result: OCRResult
    risk_score: int
    decision: str


def process_document(document: Document) -> PipelineResult:
    """
    Run the complete document processing pipeline.

    Pipeline:

        Document
            ↓
        OCR
            ↓
        Document Fields
            ↓
        Document Line Items
            ↓
        Rule Engine
            ↓
        Risk Score
            ↓
        Decision
            ↓
        VERIFIED
    """

    ocr_service = get_ocr_service()

    ocr_result = process_document_ocr(
        document,
        ocr_service,
    )

    report = run_rule_engine(
        document,
    )

    document.refresh_from_db()

    document.status = Document.Status.VERIFIED
    document.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return PipelineResult(
        document=document,
        ocr_result=ocr_result,
        risk_score=report.risk_score,
        decision=report.decision,
    )