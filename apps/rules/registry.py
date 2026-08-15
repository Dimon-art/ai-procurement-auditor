from apps.rules.amount_validation import AmountValidationRule
from apps.rules.date_validation import DateValidationRule
from apps.rules.duplicate_document import DuplicateDocumentRule
from apps.rules.duplicate_file import DuplicateFileRule
from apps.rules.file_format import FileFormatRule
from apps.rules.file_integrity import FileIntegrityRule
from apps.rules.ocr_quality import OCRQualityRule
from apps.rules.required_fields import RequiredFieldsRule
from apps.rules.supplier_validation import SupplierValidationRule
from apps.rules.tax_validation import TaxValidationRule


def get_default_rules():
    """
    Return the default MVP rule set in execution order.
    """

    return [
        FileFormatRule(),
        FileIntegrityRule(),
        OCRQualityRule(),
        RequiredFieldsRule(),
        SupplierValidationRule(),
        DuplicateFileRule(),
        DuplicateDocumentRule(),
        AmountValidationRule(),
        DateValidationRule(),
        TaxValidationRule(),
    ]