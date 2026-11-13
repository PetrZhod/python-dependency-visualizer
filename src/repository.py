"""Чтение объявленных зависимостей напрямую из JSON API PyPI."""

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from config import PACKAGE_PATTERN, validate_package, validate_url

REQUEST_TIMEOUT = 15
MAX_METADATA_BYTES = 8 * 1024 * 1024
HTTP_NOT_FOUND = 404
REQUIREMENT_PATTERN = re.compile(
    rf"^\s*({PACKAGE_PATTERN})(?=$|\s|\[|\(|[<>=!~;@])"
)


def canonical_name(name):
    """Нормализовать имя пакета по правилам Python Package Index."""
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_name(declaration):
    """Извлечь имя из Requires-Dist без сторонних библиотек."""
    if not isinstance(declaration, str):
        raise ValueError("Requires-Dist должен содержать строки")
    match = REQUIREMENT_PATTERN.match(declaration)
    if match is None:
        raise ValueError(f"Некорректная зависимость: {declaration!r}")
    return match.group(1)


def repository_base(value):
    """Принять базовый JSON API и короткий адрес официального PyPI."""
    validate_url(value)
    value = value.rstrip("/")
    parsed = urlsplit(value)
    if parsed.hostname == "pypi.org" and not parsed.path:
        return value + "/pypi"
    if parsed.path.rstrip("/").endswith("/simple"):
        raise ValueError("Нужен JSON API /pypi, а не Simple API /simple")
    return value


def read_json(url):
    """Загрузить ограниченный по размеру JSON с обработкой сетевых ошибок."""
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "python-dependency-visualizer/0.1",
    })
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            raw = response.read(MAX_METADATA_BYTES + 1)
    except HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            raise ValueError(f"Пакет или JSON API не найден: {url}") from error
        raise ValueError(f"Ошибка HTTP {error.code}: {url}") from error
    except (URLError, OSError) as error:
        raise ValueError(
            f"Не удалось обратиться к репозиторию: {error}"
        ) from error
    if len(raw) > MAX_METADATA_BYTES:
        raise ValueError("Ответ репозитория превышает допустимый размер")
    try:
        return json.loads(raw.decode("utf-8-sig"))
    except (ValueError, UnicodeError) as error:
        raise ValueError("Репозиторий вернул некорректный JSON") from error


def metadata_dependencies(data, expected_name):
    """Проверить структуру метаданных и вернуть все объявления Requires-Dist."""
    if not isinstance(data, dict) or not isinstance(data.get("info"), dict):
        raise ValueError("В JSON отсутствует объект info")
    info = data["info"]
    name = info.get("name")
    if not isinstance(name, str):
        raise ValueError("В метаданных отсутствует имя пакета")
    if canonical_name(name) != canonical_name(expected_name):
        raise ValueError("Имя пакета в ответе не совпадает с запрошенным")
    dependencies = info.get("requires_dist")
    if dependencies is None:
        return []
    if not isinstance(dependencies, list):
        raise ValueError("Поле requires_dist должно быть списком или null")
    for declaration in dependencies:
        requirement_name(declaration)
    return sorted(set(dependencies), key=str.casefold)


def metadata_version(data):
    """Прочитать версию метаданных или отметить отсутствие поля."""
    version = data["info"].get("version")
    if version is None:
        return None
    if not isinstance(version, str) or not version.strip():
        raise ValueError("Поле version должно содержать непустую строку")
    if any(not char.isprintable() for char in version):
        raise ValueError("Поле version содержит управляющие символы")
    return version.strip()


class PyPIRepository:
    """Получать декларации зависимостей последней версии и кешировать их."""

    def __init__(self, base_url):
        """Запомнить базовый URL и создать кеш текущего запуска."""
        self.base_url = repository_base(base_url)
        self.cache = {}
        self.versions = {}

    def normalize(self, name):
        """Проверить и нормализовать имя реального пакета."""
        validate_package(name)
        return canonical_name(name)

    def dependencies(self, name):
        """Запросить /имя/json один раз и вернуть копию списка деклараций."""
        name = self.normalize(name)
        if name not in self.cache:
            url = f"{self.base_url}/{quote(name, safe='')}/json"
            data = read_json(url)
            dependencies = metadata_dependencies(data, name)
            version = metadata_version(data)
            self.cache[name] = dependencies
            self.versions[name] = version
        return list(self.cache[name])

    def version(self, name):
        """Получить версию из того же ответа, не повторяя сетевой запрос."""
        name = self.normalize(name)
        if name not in self.cache:
            self.dependencies(name)
        return self.versions[name]
