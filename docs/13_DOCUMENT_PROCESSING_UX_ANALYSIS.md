# AI Procurement Auditor

**Документ:** Анализ экрана обработки документа (ЭТАП 2)  
**Версия:** 1.1  
**Статус:** Approved analysis  
**Автор:** Solution Architect / Staff Engineer  
**Последнее обновление:** 2026-08-22

---

# 1. Назначение документа

Документ фиксирует утверждённый анализ ЭТАПА 2: путь документа от загрузки до итогового риска и то, что уже показывает текущий frontend.

Код при анализе не изменялся.

Изучены:

- `apps/documents/templates/documents/detail.html`
- `apps/documents/templates/documents/list.html`
- `apps/documents/templates/documents/upload.html`
- `apps/documents/views.py`
- модель `Document`
- модели/структуры результатов проверки и risk score
- существующие rules / `check_results`
- тесты DocumentDetail и pipeline / status

---

# 2. Граница ЭТАПА 2

ЭТАП 2 сначала проектируется **поверх текущей GitHub-версии frontend**.

На этапе проектирования и фиксации анализа:

- не изменяются `.py` файлы;
- не изменяются templates;
- не изменяются API, модели, pipeline, OCR, rules, authentication и URL;
- не добавляются зависимости.

Реализация UI (если будет разрешена отдельно) опирается на уже существующие данные и шаблоны текущей версии.

---

# 3. Утверждённая UX-идея

Понятный путь проверяющего строится по формуле:

> **Статус → что произошло → почему → что делать**

Пользователь после загрузки и на карточке документа должен понимать:

1. документ принят;
2. система работает или проверка уже завершена;
3. что произошло;
4. почему возник риск / замечание (если есть);
5. что делать дальше;
6. нужно ли ему что-либо делать вручную.

Целевая UX-схема этапов:

```
Загрузка → Обработка → OCR → Извлечение данных → Проверка правил → Оценка риска → Итог
```

Этапы показываются только на основе реальных данных проекта. Новые этапы и поля не выдумываются.

---

# 4. Цветовая схема

| Цвет | Смысл |
|---|---|
| Бледно-фиолетовый | система сейчас работает |
| Зелёный | проверка пройдена |
| Жёлтый | требует внимания |
| Красный | высокий риск |
| Серый | ещё не начато |

## Процент прогресса

**Процент прогресса не показываем.**

Backend не предоставляет progress %. Выдумывать процент запрещено.

---

# 5. Текущий реальный путь документа

```
POST /documents/upload/
  → Document(status=uploaded)
  → file_hash / file_size
  → process_document(document)   # синхронно, внутри HTTP-запроса
       → OCR_PROCESSING
       → OCR + fields + line items
       → OCR_COMPLETED
       → Rule Engine → CheckResult (R001–R010)
       → risk_score / decision (вычисляются, в Document не хранятся)
       → status = VERIFIED
       (ошибка OCR → ERROR; upload view не падает)
  → render upload.html с результатом
  → опционально переход на /documents/<pk>/ (detail)
```

Ключевые факты:

1. Document создаётся в `upload_document`.
2. Статус сразу после создания: `uploaded`.
3. `process_document` вызывается **синхронно**.
4. OCR выполняется **внутри того же HTTP-запроса**. Очереди / Celery нет.
5. Пока идёт POST, промежуточный Django-экран не отдаётся.
6. После завершения снова открывается `/documents/upload/` (HTTP 200, без redirect).
7. Карточка документа (`detail`) в потоке загрузки не обязательна, но доступна по ссылке.

---

# 6. Существующие статусы Document

| Статус | Значение | Когда ставится |
|---|---|---|
| `uploaded` | Uploaded | default при создании |
| `ocr_processing` | OCR processing | старт `process_document_ocr` |
| `ocr_completed` | OCR completed | OCR + fields + line items успешно |
| `verified` | Verified | конец `process_document` после Rule Engine; также ручной Approve |
| `error` | Error | ошибка OCR |

Отдельного статуса «правила выполняются» нет.

Нюанс: `verified` означает и «pipeline завершён», и «документ утверждён» (Approve). На detail после успешного pipeline кнопка Approve уже скрыта, а текст может звучать как «утверждён бухгалтером» даже без ручного утверждения.

---

# 7. Decision и risk score

На странице detail контекст формируется во view:

- `risk_score` = сумма `score` последних `CheckResult` по каждому `rule_id` (`calculate_risk_score`);
- `decision` = `determine_document_decision(risk_score)`.

Пороги decision:

| risk_score | decision |
|---|---|
| 0 | `ok` |
| 1–20 | `warning` |
| 21–60 | `risk` |
| > 60 | `manual_review` |

`decision` в модели Document **не хранится**.

---

# 8. Причины риска

Причины риска берутся из `CheckResult`:

- `rule_id`
- `status` (`passed` / `warning` / `failed` / `not_applicable` / `insufficient_data`)
- `severity`
- `score`
- `explanation`
- опционально `actual_value`, `expected_value`, `evidence`

Правила MVP: R001–R010  
(file format, integrity, OCR quality, required fields, supplier, duplicate file, duplicate document, amount, date, VAT).

На detail в блоке проблем показываются результаты со статусом `failed` или `warning` (с русскими формулировками для известных explanation).

---

# 9. Что уже показывает frontend

## 9.1. upload.html

После POST:

- файл загружен / загружен с ошибкой;
- сырой `status`;
- ссылки на карточку документа и список;
- ошибка OCR (если есть);
- извлечённые поля (если есть).

`risk_score` / `decision` в контексте upload **нет**.

## 9.2. detail.html — экран «В обработке»

Условие: `uploaded` / `ocr_processing` / (`ocr_completed` без `check_results`).

Показывает:

- бейдж «В обработке» (бледно-фиолетовый);
- «Документ ещё проходит автоматическую обработку»;
- «Обновите страницу через некоторое время»;
- список проблем ещё недоступен;
- кнопка «Утвердить документ» доступна.

После обычной sync-загрузки этот экран почти не виден: к моменту ответа статус уже `verified` или `error`.

## 9.3. detail.html — после завершения

Типичный happy path pipeline → `verified`:

- бейдж зелёный «Проверен»;
- текст «Документ утверждён бухгалтером»;
- кнопка Approve скрыта;
- ниже могут отображаться failed/warning из `check_results`;
- `risk_score` показывается только если значение truthy (`{% if risk_score %}` скрывает 0).

Ветки по `decision` (`ok` / `warning` / `risk` / `manual_review`) в шаблоне есть, но при `status == verified` срабатывают **после** ветки verified и фактически **не определяют** главный бейдж/итог.

## 9.4. Что увидит пользователь при decision

| decision | Задумано в шаблоне | Фактически после sync-pipeline (`verified`) |
|---|---|---|
| `ok` | «Без существенных рисков» / зелёный | Зелёный «Проверен» + «утверждён бухгалтером» |
| `warning` | «Требует внимания» / жёлтый | То же зелёное «утверждён…» (decision перекрыт) |
| `risk` | «Высокий риск» / красный | То же зелёное «утверждён…» (decision перекрыт) |
| `manual_review` | «Высокий риск» / красный | То же зелёное «утверждён…» (decision перекрыт) |

`risk` и `manual_review` в UI оба подписаны одинаково: «Высокий риск».

## 9.5. list.html

- список документов по `Document.status`;
- счётчики «Требуют внимания» и «Высокий риск» сейчас показывают `—`;
- risk/decision на список **не передаются** ListView.

---

# 10. Какие этапы можно показать на реальных данных

Без выдуманных полей и без %:

| UX-шаг | Чем подтвердить |
|---|---|
| Загрузка | есть `Document` |
| Обработка / OCR | `status=ocr_processing` или наличие OCR-процесса/результата |
| Извлечение данных | есть `document.fields` и/или `status=ocr_completed` |
| Проверка правил | есть `check_results` |
| Оценка риска | вычисленные `risk_score` и `decision` |
| Итог | `decision` + `status` |

---

# 11. Что уже можно показать без изменения backend

На **detail** (уже в контексте view):

- `document.status`
- `document_fields`
- `ocr_result`
- `check_results`
- `risk_score`
- `decision`
- причины R001–R010

На **list** без изменения view:

- только поля `Document` (filename, status, dates);
- полноценный светофор по risk/decision недоступен.

На **upload**:

- filename, status, fields, OCR error;
- risk/decision нет.

---

# 12. Что сейчас непонятно проверяющему

1. После автопроверки документ выглядит как уже утверждённый бухгалтером (`verified` перекрывает `decision`).
2. Высокий риск / warning маскируются зелёным «Проверен».
3. Нет видимой цепочки этапов «Загрузка → … → Итог».
4. В списке нет светофора по риску.
5. `risk` и `manual_review` не различаются по смыслу в UI.
6. При `risk_score == 0` оценка риска скрыта.
7. Живой экран «система сейчас работает» при обычной sync-загрузке почти не наблюдается.

---

# 13. Как реализовать понятный «светофор» на существующих данных

Формула экрана:

> **Статус → что произошло → почему → что делать**

Рекомендуемая логика цвета на detail (данные уже есть):

| Сигнал | Условие |
|---|---|
| Серый / бледно-фиолетовый | ещё не начато / `uploaded` / `ocr_processing` / нет checks |
| Зелёный | `decision == "ok"` (и не `error`) |
| Жёлтый | `decision == "warning"` |
| Красный | `decision == "risk"` или `manual_review` или `status == error` |

Для итогового светофора приоритетнее `decision` / `error`, а не факт `verified`.

`verified` показывать отдельно как признак завершения обработки / утверждения, не подменяя цвет риска.

Полностью честно отделить auto-`verified` (конец pipeline) от ручного Approve **без** audit-контекста или нового поля нельзя.

Пошаговый трек — только по фактам наличия артефактов / статусов. Процент не показывать.

---

# 14. Варианты реализации (из анализа)

## Вариант A — только frontend

Улучшить отображение на существующих templates, опираясь на текущий GitHub-frontend:

- detail: приоритет decision, формула «статус → что произошло → почему → что делать», цвета;
- опционально list/upload — ограничено доступными данными.

Живой промежуточный процесс во время sync-POST одним template не появляется.

## Вариант B — минимальный backend

Нужен только если требуется живой экран «идёт обработка» до конца pipeline (redirect после create, отдельный старт, poll status API).

Для светофора итога на detail backend менять не обязательно: `risk_score` и `decision` уже в контексте.

Рекомендация анализа для понятного итога проверяющему на текущем frontend: начинать с frontend-слоя detail на существующих данных; backend — только если понадобится живой processing flow.

---

# 15. Минимальные frontend-файлы для будущей реализации

1. `apps/documents/templates/documents/detail.html` — обязательно.
2. `apps/documents/templates/documents/list.html` — по желанию (полноценный risk-светофор без изменения ListView невозможен).
3. `apps/documents/templates/documents/upload.html` — не обязателен для светофора на карточке.

На момент фиксации этого документа файлы **не изменялись**.

---

# 16. Тесты, которые нужно сохранить / учесть

Сохранить:

- `DocumentUploadViewTests`
- OCR-тесты смены статусов
- `DocumentPipelineTests`
- тесты `DocumentStatus*`
- `PipelineAPITests` (status / start / restart)
- `DocumentDetailPage*` (template, context: fields / ocr / check_results / risk_score / decision)

При будущей смене потока upload → redirect расширить ожидания HTTP-статуса и URL.

---

# 17. Связанный UX загрузки

Утверждённые формулировки upload (ЭТАП 1):

- «Загрузите счёт, УПД или другой закупочный документ для автоматической проверки.»
- подсказка файла: «Выберите PDF, JPG, JPEG или PNG до 15 МБ.»
