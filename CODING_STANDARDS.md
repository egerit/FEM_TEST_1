# Стандарты кодирования SteelFrame3D

## 1. Общие положения
Настоящий документ устанавливает правила написания, оформления и организации кода для проекта SteelFrame3D. Соблюдение стандартов обязательно для всех участников разработки.

- **Язык кода:** Английский (идентификаторы, комментарии в коде).
- **Язык документации и интерфейса:** Русский (для пользователя), Английский (технические комментарии).
- **Версия Python:** 3.9+.

## 2. Стиль кода (Code Style)
Проект следует стандарту **PEP 8** с следующими дополнениями:

### 2.1. Форматирование
- **Отступы:** 4 пробела. Табуляция запрещена.
- **Длина строки:** Максимум 100 символов.
- **Кодировка:** UTF-8.
- **Импорты:**
  - Группируются по секциям: стандартная библиотека, сторонние библиотеки, локальные модули.
  - Сортируются внутри секций.
  - Используется `import module` вместо `from module import *`.

### 2.2. Именование (Naming Conventions)
| Объект | Стиль | Пример |
| :--- | :--- | :--- |
| Пакеты/Модули | `snake_case` | `matrix_assembler.py`, `core_utils` |
| Классы | `PascalCase` | `BeamElement`, `StructureModel` |
| Функции/Методы | `snake_case` | `calculate_stiffness()`, `get_node_by_id()` |
| Переменные | `snake_case` | `total_force`, `node_index` |
| Константы | `UPPER_CASE` | `MAX_ITERATIONS`, `DEFAULT_MODULUS_E` |
| Приватные атрибуты | `_snake_case` | `_internal_cache` |

### 2.3. Типизация (Type Hinting)
Использование аннотаций типов обязательно для всех функций и методов.
```python
# Правильно
def calculate_distance(start: tuple[float, float, float], end: tuple[float, float, float]) -> float:
    ...

# Неправильно
def calculate_distance(start, end):
    ...
```
Для сложных структур использовать `typing.List`, `typing.Dict`, `typing.Optional` или синтаксис `list[]` (Python 3.9+).

## 3. Структура проекта
Рекомендуемая структура каталогов:

```text
steel_frame_3d/
├── app/                    # Исходный код приложения
│   ├── __init__.py
│   ├── main.py             # Точка входа (GUI)
│   ├── core/               # Расчетное ядро (не зависит от GUI)
│   │   ├── __init__.py
│   │   ├── model.py        # Классы данных (Node, Element, Model)
│   │   ├── solver.py       # Матрицы, решатель
│   │   └── validation.py   # Проверки модели
│   ├── gui/                # Интерфейс (PyQt + VTK)
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── widgets/        # Кастомные виджеты
│   │   └── dialogs/        # Диалоговые окна
│   └── utils/              # Утилиты (сериализация, логгер)
├── tests/                  # Тесты
│   ├── unit/               # Юнит-тесты ядра
│   └── integration/        # Интеграционные тесты
├── data/                   # Статические данные (сечения, материалы)
├── examples/               # Примеры проектов
├── docs/                   # Документация
├── requirements.txt        # Зависимости
├── setup.py                # Настройки установки
└── README.md
```

## 4. Документирование кода
Использовать стиль **Google Style Docstrings** или **NumPy Style**. Предпочтение отдается NumPy style для математических модулей.

### Пример документа функции:
```python
def assemble_global_matrix(elements: list[BeamElement], nodes: list[Node]) -> scipy.sparse.csr_matrix:
    """
    Собирает глобальную матрицу жесткости конструкции.

    Parameters
    ----------
    elements : list[BeamElement]
        Список конечных элементов (стержней).
    nodes : list[Node]
        Список узлов конструкции.

    Returns
    -------
    csr_matrix
        Разреженная глобальная матрица жесткости размера (6*N x 6*N).

    Raises
    ------
    ValueError
        Если индекс узла выходит за пределы диапазона.
    """
    pass
```

## 5. Обработка ошибок и логирование
- **Исключения:** Использовать специфичные типы исключений (`ValueError`, `TypeError`, `RuntimeError`). Избегать голых `try...except:`.
- **Логирование:** Использовать модуль `logging`. Не использовать `print()` в продакшн-коде.
  - Уровень `DEBUG`: Детали вычислений (матрицы, векторы).
  - Уровень `INFO`: Основные этапы работы (файл сохранен, расчет завершен).
  - Уровень `WARNING`: Некритичные проблемы (устаревший формат файла).
  - Уровень `ERROR`: Ошибки, прерывающие операцию.

```python
import logging

logger = logging.getLogger(__name__)

def solve(model):
    try:
        # ... logic
        logger.info("Calculation completed successfully.")
    except SingularMatrixError as e:
        logger.error("System matrix is singular. Check boundary conditions.", exc_info=True)
        raise
```

## 6. Тестирование
- **Фреймворк:** `pytest`.
- **Покрытие:** Критические модули ядра (сборка матриц, решатель) должны иметь покрытие тестами не менее 90%.
- **Именование тестов:** `test_<function_name>_<scenario>.py`.
- **Эталонные данные:** Тесты сверять с аналитическими решениями (папка `tests/data/analytical_solutions.json`).

Пример теста:
```python
def test_cantilever_beam_deflection():
    """Проверка прогиба консольной балки под сосредоточенной силой."""
    model = create_cantilever_model()
    result = run_calculation(model)
    expected_deflection = 0.012 # meters
    assert abs(result.max_deflection - expected_deflection) < 1e-5
```

## 7. Управление версиями и Git
- **Ветвление:** GitHub Flow.
  - `main` — стабильная версия.
  - `feature/<name>` — новые функции.
  - `bugfix/<name>` — исправления ошибок.
- **Коммиты:** Сообщения коммитов на английском в повелительном наклонении.
  - ✅ `Add node selection logic`
  - ❌ `Added node selection logic` / `Fixing bug`
- **Pre-commit хуки:** Обязательно настроить `pre-commit` для проверки:
  - Форматирования (`black`).
  - Линтинга (`flake8` или `ruff`).
  - Типов (`mypy`).

## 8. Безопасность и производительность
- **Численная стабильность:** При работе с плавающей точкой использовать `numpy.allclose` вместо `==`. Избегать деления на ноль.
- **Память:** Для больших моделей использовать разреженные матрицы (`scipy.sparse`). Не хранить полные копии больших массивов без необходимости.
- **GUI Thread:** Тяжелые вычисления (расчет) выполнять только в отдельных потоках (`QThread`), чтобы не блокировать интерфейс.

## 9. Контроль качества
Перед отправкой Pull Request разработчик обязан:
1. Запустить локальные тесты: `pytest tests/`.
2. Проверить стиль: `ruff check .`.
3. Убедиться, что нет предупреждений от статического анализатора типов.
4. Обновить документацию, если изменился публичный API.

---
*Документ действует с:* 2023-10-27
*Ответственный за стандарты:* Tech Lead
