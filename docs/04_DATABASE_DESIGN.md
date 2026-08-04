# AI Procurement Auditor

**Документ:** Database Design  
**Версия:** 1.0  
**Статус:** Draft  
**Автор:** Solution Architect / Senior Django Engineer  
**Последнее обновление:** 2026-08-04

---

# 1. Назначение документа

Этот документ определяет логическую структуру базы данных AI Procurement Auditor.

Цель документа — зафиксировать:

- перечень таблиц MVP;
- назначение каждой таблицы;
- ключевые поля;
- связи;
- ограничения;
- индексы;
- правила удаления и хранения данных;
- соответствие будущим Django-моделям.

Документ описывает PostgreSQL как целевую базу данных. На раннем локальном этапе допускается SQLite, но структура моделей должна проектироваться с учетом последующего перехода на PostgreSQL.

---

# 2. Общие принципы

## 2.1. Multi-tenancy

Все бизнес-данные должны быть связаны с компанией через `company_id`.

Это относится к:

- пользователям;
- поставщикам;
- документам;
- правилам;
- задачам ручной проверки;
- журналу аудита.

Поиск и выборки должны всегда ограничиваться текущей компанией.

## 2.2. Неизменяемость исходного файла

Оригинал документа после загрузки не изменяется.

В базе хранятся:

- путь к файлу;
- имя файла;
- размер;
- MIME type;
- hash;
- дата загрузки.

Ручные исправления относятся только к извлеченным данным.

## 2.3. Raw и normalized values

Исходное OCR-значение и нормализованное значение хранятся отдельно.

```
raw_value: "1 250 000,00 руб."
normalized_value: "1250000.00"
```

## 2.4. Audit First

Критические изменения должны создавать запись в `audit_logs`.

## 2.5. Soft Delete

Для основных бизнес-сущностей предпочтительно использовать статус или `is_active`, а не физическое удаление.

---

# 3. Список таблиц MVP

```
companies
users
suppliers
documents
document_pages
document_fields
document_relations
rules
check_results
risk_assessments
review_tasks
audit_logs
llm_runs
```

---

# 4. companies

Хранит компании-клиентов SaaS.


| Поле       | Тип          | Обязательное | Назначение                  |
| ---------- | ------------ | ------------ | --------------------------- |
| id         | bigint       | да           | первичный ключ              |
| name       | varchar(255) | да           | название                    |
| status     | varchar(32)  | да           | active, suspended, archived |
| created_at | timestamptz  | да           | дата создания               |
| updated_at | timestamptz  | да           | дата изменения              |


Индексы:

- `status`.

---

# 5. users

Хранит пользователей.


|            |              |              |                |
| ---------- | ------------ | ------------ | -------------- |
| Поле       | Тип          | Обязательное | Назначение     |
| id         | bigint       | да           | первичный ключ |
| company_id | FK           | да           | компания       |
| email      | varchar(254) | да           | логин          |
| full_name  | varchar(255) | да           | имя            |
| role       | varchar(32)  | да           | роль           |
| is_active  | boolean      | да           | доступ         |
| is_staff   | boolean      | да           | Django Admin   |
| created_at | timestamptz  | да           | дата создания  |
| updated_at | timestamptz  | да           | дата изменения |


Ограничения:

- email уникален;
- пользователь принадлежит одной компании.

Индексы:

- `email`;
- `company_id`;
- `(company_id, role)`.

---

# 6. suppliers

Хранит поставщиков компании.


|                 |              |              |                          |
| --------------- | ------------ | ------------ | ------------------------ |
| Поле            | Тип          | Обязательное | Назначение               |
| id              | bigint       | да           | первичный ключ           |
| company_id      | FK           | да           | компания                 |
| legal_name      | varchar(255) | да           | юридическое название     |
| normalized_name | varchar(255) | да           | нормализованное название |
| inn             | varchar(12)  | нет          | ИНН                      |
| kpp             | varchar(9)   | нет          | КПП                      |
| bank_account    | varchar(34)  | нет          | расчетный счет           |
| bik             | varchar(9)   | нет          | БИК                      |
| status          | varchar(32)  | да           | статус                   |
| created_at      | timestamptz  | да           | дата создания            |
| updated_at      | timestamptz  | да           | дата изменения           |


Индексы:

- `company_id`;
- `(company_id, inn)`;
- `(company_id, normalized_name)`.

---

# 7. documents

Центральная таблица системы.


|                   |               |              |                |
| ----------------- | ------------- | ------------ | -------------- |
| Поле              | Тип           | Обязательное | Назначение     |
| id                | bigint        | да           | первичный ключ |
| company_id        | FK            | да           | компания       |
| supplier_id       | FK            | нет          | поставщик      |
| uploaded_by_id    | FK            | да           | пользователь   |
| document_type     | varchar(32)   | да           | тип            |
| status            | varchar(32)   | да           | статус         |
| original_filename | varchar(255)  | да           | имя файла      |
| storage_path      | varchar(1024) | да           | путь           |
| mime_type         | varchar(100)  | да           | MIME type      |
| file_hash         | varchar(64)   | да           | SHA-256        |
| file_size         | bigint        | да           | размер         |
| page_count        | integer       | нет          | страницы       |
| processing_error  | text          | нет          | ошибка         |
| created_at        | timestamptz   | да           | дата загрузки  |
| updated_at        | timestamptz   | да           | дата изменения |


Ограничения:

- исходный файл неизменяем;
- документ всегда принадлежит компании;
- `file_size > 0`.

Индексы:

- `company_id`;
- `(company_id, status)`;
- `(company_id, document_type)`;
- `(company_id, file_hash)`;
- `created_at`.

---

# 8. document_pages

Хранит страницы и OCR-текст.


|                |               |              |
| -------------- | ------------- | ------------ |
| Поле           | Тип           | Обязательное |
| id             | bigint        | да           |
| document_id    | FK            | да           |
| page_number    | integer       | да           |
| image_path     | varchar(1024) | нет          |
| ocr_text       | text          | нет          |
| ocr_confidence | numeric(5,4)  | нет          |
| created_at     | timestamptz   | да           |


Ограничения:

- `page_number > 0`;
- уникальность `(document_id, page_number)`.

---

# 9. document_fields

Хранит извлеченные поля.


|                       |              |              |
| --------------------- | ------------ | ------------ |
| Поле                  | Тип          | Обязательное |
| id                    | bigint       | да           |
| document_id           | FK           | да           |
| field_name            | varchar(64)  | да           |
| raw_value             | text         | нет          |
| normalized_value      | text         | нет          |
| corrected_value       | text         | нет          |
| confidence            | numeric(5,4) | нет          |
| source_page           | integer      | нет          |
| bounding_box          | jsonb        | нет          |
| extraction_method     | varchar(32)  | да           |
| is_manually_corrected | boolean      | да           |
| corrected_by_id       | FK           | нет          |
| corrected_at          | timestamptz  | нет          |
| created_at            | timestamptz  | да           |
| updated_at            | timestamptz  | да           |


Ограничения:

- `raw_value` не изменяется;
- confidence находится в диапазоне 0..1;
- уникальность `(document_id, field_name)` для одиночных полей MVP.

---

# 10. document_relations

Хранит связи между документами.


|                    |              |              |
| ------------------ | ------------ | ------------ |
| Поле               | Тип          | Обязательное |
| id                 | bigint       | да           |
| source_document_id | FK           | да           |
| target_document_id | FK           | да           |
| relation_type      | varchar(32)  | да           |
| confidence         | numeric(5,4) | нет          |
| created_at         | timestamptz  | да           |


Ограничения:

- документ не ссылается сам на себя;
- оба документа принадлежат одной компании;
- уникальность `(source_document_id, target_document_id, relation_type)`.

---

# 11. rules

Хранит правила проверки.


|               |              |              |
| ------------- | ------------ | ------------ |
| Поле          | Тип          | Обязательное |
| id            | bigint       | да           |
| company_id    | FK           | нет          |
| code          | varchar(64)  | да           |
| name          | varchar(255) | да           |
| description   | text         | нет          |
| category      | varchar(64)  | да           |
| severity      | varchar(16)  | да           |
| score         | integer      | да           |
| configuration | jsonb        | да           |
| is_enabled    | boolean      | да           |
| version       | integer      | да           |
| created_at    | timestamptz  | да           |
| updated_at    | timestamptz  | да           |


Ограничения:

- `score` от 0 до 100;
- `version > 0`.

---

# 12. check_results

Хранит результаты правил.


|                |             |              |
| -------------- | ----------- | ------------ |
| Поле           | Тип         | Обязательное |
| id             | bigint      | да           |
| document_id    | FK          | да           |
| rule_id        | FK          | да           |
| status         | varchar(32) | да           |
| severity       | varchar(16) | да           |
| score          | integer     | да           |
| actual_value   | jsonb       | нет          |
| expected_value | jsonb       | нет          |
| explanation    | text        | нет          |
| evidence       | jsonb       | да           |
| rule_version   | integer     | да           |
| created_at     | timestamptz | да           |


Ограничения:

- score неотрицательный;
- evidence обязательно для warning и failed.

---

# 13. risk_assessments

Хранит итоговый риск.


|                     |             |              |
| ------------------- | ----------- | ------------ |
| Поле                | Тип         | Обязательное |
| id                  | bigint      | да           |
| document_id         | FK          | да           |
| total_score         | integer     | да           |
| risk_level          | varchar(16) | да           |
| summary             | text        | нет          |
| calculation_version | integer     | да           |
| created_at          | timestamptz | да           |


Ограничения:

- `total_score` от 0 до 100;
- LLM не изменяет итоговый балл.

---

# 14. review_tasks

Хранит задачи ручной проверки.


|                    |             |              |
| ------------------ | ----------- | ------------ |
| Поле               | Тип         | Обязательное |
| id                 | bigint      | да           |
| company_id         | FK          | да           |
| document_id        | FK          | да           |
| status             | varchar(32) | да           |
| priority           | varchar(16) | да           |
| assigned_to_id     | FK          | нет          |
| resolution         | varchar(32) | нет          |
| resolution_comment | text        | нет          |
| resolved_by_id     | FK          | нет          |
| created_at         | timestamptz | да           |
| resolved_at        | timestamptz | нет          |


Ограничения:

- не более одной активной задачи на документ;
- закрытая задача содержит resolution.

---

# 15. audit_logs

Хранит неизменяемую историю.


|                |             |              |
| -------------- | ----------- | ------------ |
| Поле           | Тип         | Обязательное |
| id             | bigint      | да           |
| company_id     | FK          | да           |
| user_id        | FK          | нет          |
| document_id    | FK          | нет          |
| action         | varchar(64) | да           |
| entity_type    | varchar(64) | да           |
| entity_id      | varchar(64) | нет          |
| previous_value | jsonb       | нет          |
| new_value      | jsonb       | нет          |
| metadata       | jsonb       | нет          |
| created_at     | timestamptz | да           |


Ограничения:

- записи не редактируются;
- обычный пользователь не удаляет аудит.

---

# 16. llm_runs

Хранит статистику LLM.


|                |               |              |
| -------------- | ------------- | ------------ |
| Поле           | Тип           | Обязательное |
| id             | bigint        | да           |
| company_id     | FK            | да           |
| document_id    | FK            | нет          |
| task_type      | varchar(64)   | да           |
| provider       | varchar(64)   | да           |
| model          | varchar(128)  | да           |
| input_tokens   | integer       | да           |
| output_tokens  | integer       | да           |
| estimated_cost | numeric(12,6) | да           |
| latency_ms     | integer       | нет          |
| status         | varchar(32)   | да           |
| prompt_version | varchar(32)   | да           |
| created_at     | timestamptz   | да           |


---

# 17. Связи

```
Company
 ├── Users
 ├── Suppliers
 ├── Documents
 ├── Rules
 ├── ReviewTasks
 ├── AuditLogs
 └── LlmRuns

Document
 ├── DocumentPages
 ├── DocumentFields
 ├── DocumentRelations
 ├── CheckResults
 ├── RiskAssessments
 ├── ReviewTask
 └── AuditLogs
```

---

# 18. Правила удаления

- Company архивируется.
- User деактивируется.
- Supplier архивируется.
- Document архивируется или soft-deleted.
- AuditLog не удаляется обычным пользователем.
- Техническое каскадное удаление допускается только для дочерних сущностей документа.

---

# 19. Django mapping

Рекомендуемые типы:

- primary key: `BigAutoField`;
- строки: `CharField`;
- длинный текст: `TextField`;
- JSON: `JSONField`;
- суммы: `DecimalField`;
- время: `DateTimeField`;
- связи: `ForeignKey`;
- статусы: `TextChoices`;
- файлы: `FileField`.

Для MVP UUID не обязателен.

---

# 20. Порядок создания моделей

1. `Company`
2. custom `User`
3. `Supplier`
4. `Document`
5. `DocumentPage`
6. `DocumentField`
7. `DocumentRelation`
8. `Rule`
9. `CheckResult`
10. `RiskAssessment`
11. `ReviewTask`
12. `AuditLog`
13. `LlmRun`

---

# 21. Риски

## Избыточная нормализация

Мера: JSONB для evidence и configuration.

## Нарушение изоляции компаний

Мера: обязательный `company_id`.

## Потеря OCR-источника

Мера: хранить raw value, страницу и bounding box.

## Сложные удаления

Мера: архивирование и soft delete.

---

# 22. Implementation Impact

После утверждения документа разработчик может:

- создать Django apps;
- реализовать модели;
- настроить ForeignKey;
- определить `TextChoices`;
- написать миграции;
- создать индексы;
- зарегистрировать модели в Django Admin;
- написать тесты ограничений;
- подготовить переход с SQLite на PostgreSQL.

---

# 23. Definition of Done

Документ считается утвержденным, если согласованы:

- таблицы MVP;
- поля;
- связи;
- индексы;
- ограничения;
- правила удаления;
- порядок миграций;
- соответствие Django ORM.

