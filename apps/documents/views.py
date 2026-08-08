from django.shortcuts import redirect, render

from apps.companies.models import Company
from apps.documents.models import Document


def upload_document(request):
    """
    Upload document and save it.
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