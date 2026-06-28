# BRING v2 — Диагностика (Фаза 0)

**Дата:** 2026-06-28 23:10 MSK
**Ревизия:** e907dee (оригинальный main)

---

## 1. Окружение

| Компонент | Статус | Версия |
|-----------|--------|--------|
| Python | ✅ | 3.11 |
| FAISS-cpu | ✅ Установлен | 1.14.3 |
| networkx | ✅ | 3.6.1 |
| numpy | ✅ | 1.24+ |
| openai | ✅ | 2.44.0 |
| python-multipart | ✅ Установлен | 0.0.32 |

---

## 2. Импорты

Все 9 модулей импортируются без ошибок:
- ✅ world_cli
- ✅ world_config
- ✅ world_builder
- ✅ world_core
- ✅ world_engine
- ✅ world_intelligence
- ✅ world_narrative
- ✅ world_director
- ✅ world_explorer

---

## 3. CLI

`world_cli.py --help` работает. Все команды парсятся:
- builder, explore, intel, narrative
- memory (maintenance, status, forget, export, import)
- birth, romance (6 подкоманд)

---

## 4. Обнаруженные проблемы

### 🔴 P0 — Нет LLM конфига (БЛОКЕР)
```
ValueError: No base URL provided. Set WORLD_LLM_BASE_URL environment variable.
```
**Причина:** `.env` не создан. `.env.example` есть, но не скопирован.
**Исправление:** создать `.env` с Ollama (локальный) или Mistral API.

### 🔴 P1 — FAISS отключен в коде
```
world_core/memory/world_memory.py:304: self._faiss_disabled = True
```
**Причина:** Разработчик отключил из-за dimension mismatch.
**Факт:** FAISS 1.14.3 работает, 384-dim индекс создаётся, размерный mismatch ловится AssertionError.
**Исправление:** убрать `_faiss_disabled = True`, добавить нормализацию embeddings.

### 🟡 P2 — test_integration.py сломан
```
NameError: name 'api_app' is not defined. Did you mean: 'cli_app'?
```
**Причина:** Опечатка в тесте. Импортируется `cli_app`, но используется `api_app`.
**Исправление:** заменить `api_app` → `cli_app` в test_integration.py:51.

### 🟡 P3 — AVX-предупреждения FAISS (не критично)
```
Could not load library with AVX512 support
Could not load library with AVX2 support
Successfully loaded faiss.
```
**Причина:** Сервер без AVX2/AVX512.
**Влияние:** Нет. FAISS работает на базовом уровне.

---

## 5. Что работает без исправлений

- ✅ Все импорты
- ✅ CLI со всеми командами
- ✅ FAISS создание индекса
- ✅ FAISS поиск
- ✅ FAISS ловит dimension mismatch
- ✅ Graph Manager
- ✅ World Builder (до вызова LLM)
- ✅ Probability Engine
- ✅ Birth/Isekai Wizard (до вызова LLM)

---

## 6. План исправлений (Фаза 1)

| # | Что | Время |
|---|-----|-------|
| 1 | Создать `.env` с Ollama localhost | 5 мин |
| 2 | Исправить `test_integration.py` (api_app→cli_app) | 2 мин |
| 3 | Убрать `_faiss_disabled = True` | 1 мин |
| 4 | Добавить нормализацию embeddings в embedding_queue.py | 1 час |
| 5 | Запустить полный build тестового мира | 30 мин |
| 6 | Бенчмарк FAISS vs линейный поиск | 30 мин |
| **Итого** | | **~2.5 часа** |

---

*Диагностика завершена: 2026-06-28 23:10 MSK*
