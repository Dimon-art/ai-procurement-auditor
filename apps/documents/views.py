from django.shortcuts import render

from apps.companies.models import Company
from apps.documents.models import Document
from apps.documents.services.document_ocr import process_document_ocr
from apps.documents.services.ocr_factory import get_ocr_service


def upload_document(request):
    """
    Upload document and run OCR.
    """

    companies = Company.objects.all()

    if request.method == "POST":
        company_id = request.POST.get("company")
        uploaded_file = request.FILES.get("document")

        company = Company.objects.get(
            id=company_id
        )

        document = Document.objects.create(
            company=company,
            original_file=uploaded_file,
            filename=uploaded_file.name,
        )

        ocr_service = get_ocr_service()

        try:
            process_document_ocr(
                document,
                ocr_service,
            )
        except Exception:
            pass

        document.refresh_from_db()

        return render(
            request,
            "documents/upload.html",
            {
                "companies": companies,
                "uploaded_document": document,
            },
        )

    return render(
        request,
        "documents/upload.html",
        {
            "companies": companies,
        },
    )