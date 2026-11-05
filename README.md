# Этап 1. Минимальный CLI и конфигурация

Реализованы пять параметров командной строки, их проверка и вывод ключ-значение.
Граф, HTTP-загрузка зависимостей и визуализация на этом этапе ещё не выполняются.

## Демонстрация

```powershell
python src/main.py --package requests --repository https://pypi.org/pypi
```

Ожидаемый вывод:

```text
package=requests
repository=https://pypi.org/pypi
test_repo=False
ascii_tree=False
filter=
```

Показать все параметры:

```powershell
python src/main.py --package A --repository examples/repository.json --test-repo --ascii-tree --filter B
```

Для тестового режима файл должен существовать, имя пакета состоит из букв A-Z.
Проверка содержимого графа относится к этапу 3. На этапе 1 файл не изменяется.
Фильтр и режим ASCII пока только сохраняются в конфигурации.

## Демонстрация ошибок

- Без --package или --repository — отсутствует обязательный параметр.
- --package "bad name" — недопустимое имя.
- --repository ftp://host — неподдерживаемый URL.
- --repository missing.json --test-repo — отсутствующий файл.
- --test-repo=maybe — неверное использование флага тестового режима.
- --ascii-tree=maybe — неверное использование флага ASCII.
- --filter без значения либо --filter " " — ошибка фильтра.

Готовые сценарии: scripts/demo.bat и scripts/errors.bat.
Их окна остаются открытыми благодаря pause.
Для Linux/macOS есть scripts/demo.sh и scripts/errors.sh.

## Требования и запуск

Нужен Python 3.10 или новее. Сторонние Python-библиотеки не нужны.
Это консольное приложение, не графическое окно и не эмулятор оболочки.

Открой PowerShell в корне проекта, где находятся src и run.bat.
Справка:

```powershell
python src/main.py --help
```

Проверки:

```powershell
python -m unittest discover -s tests -v
python tests/check_style.py
```

В Linux/macOS используй python3 вместо python либо ./run.sh с параметрами.
В Windows можно использовать .\run.bat с теми же параметрами.

## Параметры

| Опция | Назначение |
|---|---|
| `--package` | Обязательное имя пакета |
| `--repository` | Обязательный URL JSON API или путь к тестовому файлу |
| `--test-repo` | Флаг выбора тестового репозитория |
| `--ascii-tree` | Флаг выбора ASCII-дерева для будущего этапа 5 |
| `--filter` | Подстрока исключаемых пакетов; по умолчанию пустая |

Флаги передаются без значений: --ascii-tree, а не --ascii-tree=true.
Пути с пробелами заключай в двойные кавычки.
Ошибки параметров завершают программу с кодом 2; --help возвращает 0.

## Структура

- src — исходный код.
- tests — автотесты и проверка измеримых ограничений оформления.
- examples — тестовые данные.
- scripts — демонстрации для Windows и Linux/macOS.
- run.bat и run.sh — запуск с переданными пользователем параметрами.

Автоматическая проверка оформления не заменяет официальную проверку преподавателя.
