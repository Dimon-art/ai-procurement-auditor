from django import template

register = template.Library()

FIELD_LABELS = {
    "supplier_inn": "ИНН поставщика",
    "supplier_kpp": "КПП поставщика",
    "supplier_name": "Поставщик",
    "buyer_inn": "ИНН покупателя",
    "buyer_kpp": "КПП покупателя",
    "document_type": "Тип документа",
    "document_number": "Номер документа",
    "document_date": "Дата документа",
    "amount_without_vat": "Сумма без НДС",
    "total_amount": "Сумма документа",
    "vat_amount": "НДС",
    "currency": "Валюта",
    "supplier_status": "Статус поставщика",
    "duplicate_document_id": "Дубликат документа",
    "missing_fields": "Недостающие поля",
    "file_hash": "Контрольная сумма файла",
    "provider": "Провайдер OCR",
    "confidence": "Уверенность OCR",
    "text_length": "Длина распознанного текста",
    "error_message": "Сообщение об ошибке",
}

# Stable accountant-facing order for «Основные реквизиты».
# Keys match FieldExtractor / DocumentField.field_name only.
MAIN_REQUISITE_ORDER = (
    "document_type",
    "document_number",
    "document_date",
    "supplier_name",
    "supplier_inn",
    "supplier_kpp",
    "buyer_inn",
    "buyer_kpp",
    "amount_without_vat",
    "vat_amount",
    "total_amount",
    "currency",
)

MONEY_KEYS = {
    "total_amount",
    "vat_amount",
    "amount_without_vat",
}

RULE_LABELS = {
    "R001": "Проверка формата файла",
    "R002": "Проверка целостности файла",
    "R003": "Проверка качества OCR",
    "R004": "Проверка обязательных полей",
    "R005": "Проверка поставщика",
    "R006": "Проверка дубликата файла",
    "R007": "Проверка дубликата документа",
    "R008": "Проверка суммы",
    "R009": "Проверка даты",
    "R010": "Проверка НДС",
}

CHECK_STATUS_LABELS = {
    "passed": "Пройдено",
    "failed": "Не пройдено",
    "warning": "Предупреждение",
    "not_applicable": "Не применимо",
    "insufficient_data": "Недостаточно данных",
    "Passed": "Пройдено",
    "Failed": "Не пройдено",
    "Warning": "Предупреждение",
    "Not applicable": "Не применимо",
    "Insufficient data": "Недостаточно данных",
}

CHECK_SEVERITY_LABELS = {
    "low": "Низкий",
    "medium": "Средний",
    "high": "Высокий",
}

# UI-only translations of CheckResult.explanation strings from rules.
CHECK_EXPLANATION_LABELS = {
    "Document file format is supported.": (
        "Формат файла документа поддерживается."
    ),
    "Document file format is not supported.": (
        "Формат файла не поддерживается."
    ),
    "Document file integrity metadata is valid.": (
        "Метаданные целостности файла документа корректны."
    ),
    "Document file integrity metadata is invalid.": (
        "Некорректные метаданные целостности файла."
    ),
    "OCR result quality is acceptable.": (
        "Качество распознавания текста приемлемое."
    ),
    "OCR result is missing.": "Результат OCR отсутствует.",
    "OCR processing completed with an error.": (
        "OCR завершился с ошибкой."
    ),
    "OCR returned empty text.": (
        "OCR не распознал текст в документе."
    ),
    "All required document fields are present.": (
        "Все обязательные поля документа заполнены."
    ),
    "Required document fields are missing.": (
        "Не хватает обязательных полей документа."
    ),
    "Supplier was not found in master data.": (
        "Поставщик не найден в справочнике компании."
    ),
    "Supplier INN is missing.": "Не указан ИНН поставщика.",
    "Supplier is inactive.": "Поставщик неактивен.",
    "Supplier is valid.": "Поставщик проверен и корректен.",
    "Duplicate file was found.": "Найден дубликат файла.",
    "Duplicate file was not found.": "Дубликат файла не найден.",
    "Document file hash is missing.": (
        "Отсутствует хеш файла документа."
    ),
    "Duplicate document was found.": "Найден дубликат документа.",
    "Duplicate document was not found.": (
        "Дубликат документа не найден."
    ),
    (
        "Duplicate document check cannot be completed "
        "because required fields are missing."
    ): (
        "Проверка дубликата документа невозможна: "
        "не хватает обязательных полей."
    ),
    "Total amount is valid.": "Сумма документа корректна.",
    "Total amount is missing.": "Не указана сумма документа.",
    "Total amount is empty.": "Сумма документа пустая.",
    "Total amount is invalid.": "Некорректная сумма документа.",
    "Total amount must be greater than zero.": (
        "Сумма документа должна быть больше нуля."
    ),
    "Document date is valid.": "Дата документа корректна.",
    "Document date is missing.": "Не указана дата документа.",
    "Document date is empty.": "Дата документа пустая.",
    "Document date is invalid.": "Некорректная дата документа.",
    "Document date cannot be in the future.": (
        "Дата документа не может быть в будущем."
    ),
    "VAT amount is valid.": "Сумма НДС корректна.",
    "Total amount is missing or invalid.": (
        "Сумма документа отсутствует или некорректна."
    ),
    "VAT amount is missing or invalid.": (
        "Сумма НДС отсутствует или некорректна."
    ),
    "VAT amount cannot be negative.": (
        "Сумма НДС не может быть отрицательной."
    ),
    "VAT amount cannot exceed total amount.": (
        "Сумма НДС не может превышать сумму документа."
    ),
}


@register.filter
def check_data_label(key):
    """Human-readable label for check evidence keys."""
    if key is None:
        return "Дополнительные данные"
    return FIELD_LABELS.get(str(key), "Дополнительные данные")


@register.filter
def check_rule_label(rule_id):
    """Human-readable rule name for accountant UI."""
    if rule_id is None:
        return "Проверка документа"
    return RULE_LABELS.get(str(rule_id), "Проверка документа")


@register.filter
def check_status_label(status):
    """Translate CheckResult status for accountant UI only."""
    if status is None or status == "":
        return "—"
    return CHECK_STATUS_LABELS.get(str(status), "—")


@register.filter
def check_severity_label(severity):
    """Translate CheckResult severity for accountant UI only."""
    if severity is None or severity == "":
        return "—"
    return CHECK_SEVERITY_LABELS.get(str(severity), "—")


@register.filter
def check_explanation(explanation):
    """Translate known rule explanations for accountant UI only."""
    if explanation is None or explanation == "":
        return "—"
    text = str(explanation)
    return CHECK_EXPLANATION_LABELS.get(text, text)


@register.filter
def document_field_label(field_name):
    """Human-readable label for DocumentField.field_name."""
    if field_name is None:
        return "Поле документа"
    return FIELD_LABELS.get(str(field_name), "Поле документа")


def _format_iso_date(value):
    text = str(value).strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return f"{text[8:10]}.{text[5:7]}.{text[0:4]}"
    return text


def _format_money(value):
    text = str(value).strip().replace(" ", "").replace(",", ".")
    try:
        number = float(text)
    except (TypeError, ValueError):
        return str(value)

    formatted = f"{number:,.2f}"
    # 28,080.00 → 28 080,00
    return (
        formatted
        .replace(",", " ")
        .replace(".", ",")
    )


def _format_scalar(value, key=""):
    if value is None or value == "":
        return "Не указано"

    key = str(key) if key is not None else ""

    if key == "document_date":
        return _format_iso_date(value)

    if key == "document_type":
        text = str(value).strip()
        if text.lower() == "upd":
            return "УПД"
        return text

    if key in MONEY_KEYS:
        return _format_money(value)

    if key == "missing_fields" and isinstance(value, (list, tuple)):
        if not value:
            return "Не указано"
        labels = [
            FIELD_LABELS.get(str(item), "поле документа")
            for item in value
        ]
        return ", ".join(labels)

    if isinstance(value, bool):
        return "Да" if value else "Нет"

    return str(value)


@register.filter
def check_data_value(value, key=""):
    """Format evidence/check values for accountant-facing UI."""
    if isinstance(value, dict):
        # Should be iterated in template; fallback avoids raw dict dump.
        return "Не указано"

    return _format_scalar(value, key)


@register.filter
def document_field_value(value, field_name=""):
    """Format DocumentField values for accountant-facing UI."""
    if value is None or value == "":
        return "—"
    if isinstance(value, dict):
        return "—"
    return _format_scalar(value, field_name)


@register.filter
def is_mapping(value):
    return isinstance(value, dict)


@register.simple_tag
def ordered_main_fields(document_fields):
    """
    Return extracted fields in MAIN_REQUISITE_ORDER.
    Only includes real DocumentField rows that exist.
    """
    by_name = {
        field.field_name: field
        for field in document_fields
    }
    return [
        by_name[name]
        for name in MAIN_REQUISITE_ORDER
        if name in by_name
    ]
