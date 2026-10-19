"""
Задание 2. Реальный I/O и обработка ошибок

Замеры:
    robust (20 картинок + 2 битых URL): 19.80 s
    Результат: успешно 20, ошибок 2
        https://no-such-site.invalid -> ConnectError
        https://httpbin.org/delay/10 -> ReadTimeout

Почему ~20 секунд:
    Дольше всех работает httpbin.org/delay/10: 3 попытки по 5 с таймаута
    плюс паузы 1 с и 2 с между ними = 5 + 1 + 5 + 2 + 5 = 18 с.
    Остальные картинки за это время успевают скачаться параллельно.

Что сделано:
    - Таймаут: timeout=5 на каждый запрос, дольше ответа не ждём.
    - Ретраи: максимум 3 попытки, пауза между ними растёт вдвое
      (2 ** attempt: 1 с, 2 с), после последней ошибка пробрасывается.
    - Устойчивость: gather(..., return_exceptions=True) возвращает ошибку
      как обычный результат, поэтому один битый URL не роняет остальные.
      robust_main возвращает кортеж (результаты, ошибки).
"""

import asyncio
import time

import httpx
import requests

URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]
URLS += [
    "https://no-such-site.invalid",
    "https://httpbin.org/delay/10",
]

TIMEOUT = 5
MAX_ATTEMPTS = 3


def timed(label, fn, *args):
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")


async def robust_fetch(client: httpx.AsyncClient, url: str) -> int:
    for attempt in range(MAX_ATTEMPTS):
        try:
            resp = await client.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.status_code
        except httpx.HTTPError as e:
            if attempt == MAX_ATTEMPTS - 1:
                raise
            delay = 2 ** attempt
            print(f"{url}: попытка {attempt + 1} не удалась ({type(e).__name__}), жду {delay} с")
            await asyncio.sleep(delay)


async def robust_main():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        outcomes = await asyncio.gather(
            *(robust_fetch(client, url) for url in URLS),
            return_exceptions=True,
        )

    results = []
    errors = []
    for url, outcome in zip(URLS, outcomes):
        if isinstance(outcome, Exception):
            errors.append((url, type(outcome).__name__))
        else:
            results.append((url, outcome))
    return results, errors


def run():
    results, errors = asyncio.run(robust_main())
    print(f"успешно: {len(results)}")
    print(f"ошибок: {len(errors)}")
    for url, err in errors:
        print(f"  {url} -> {err}")


if __name__ == "__main__":
    timed("robust", run)