import os
import asyncio
import hashlib
from pathlib import Path
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from yt_dlp import YoutubeDL

TOKEN = '7524843007:AAFT6CuyZ2fNvhB-FA3IfJjBb2AKPxMrlY4'

bot = Bot(token=TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = Path("downloads")
# Простой in-memory кэш: url -> file_path
_cache: dict[str, Path] = {}

YDL_OPTS = {
    'format': 'bestaudio/best',
    'outtmpl': str(DOWNLOAD_DIR / '%(id)s.%(ext)s'),  # id вместо title — короче, без спецсимволов
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '128',   # 128 вместо 192 — в 1.5x быстрее конвертация
    }],
    # === СКОРОСТЬ ===
    'concurrent_fragment_downloads': 8,   # параллельные фрагменты
    'buffersize': 1024 * 16,              # 16 KB буфер
    'http_chunk_size': 1024 * 1024 * 10, # 10 MB чанки
    'socket_timeout': 10,
    'retries': 3,
    'fragment_retries': 3,
    # === НЕ СПАМИТЬ В КОНСОЛЬ ===
    'quiet': True,
    'no_warnings': True,
}


def _download_sync(url: str) -> tuple[Path, str]:
    """Синхронная загрузка — запускается в отдельном потоке."""
    with YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=True)
        raw = ydl.prepare_filename(info)
        # yt-dlp всегда меняет расширение после postprocessor
        file_path = Path(raw).with_suffix('.mp3')
        title = info.get('title', 'Unknown')
    return file_path, title


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! Пришли ссылку на трек из SoundCloud — скачаю мгновенно. 🎵")


@dp.message(F.text.contains("soundcloud.com"))
async def download_track(message: types.Message):
    url = message.text.strip()

    # Проверяем кэш
    cache_key = hashlib.md5(url.encode()).hexdigest()
    if cache_key in _cache and _cache[cache_key].exists():
        cached_path = _cache[cache_key]
        audio = types.FSInputFile(cached_path)
        await message.answer_audio(audio, caption="⚡ Из кэша — мгновенно!")
        return

    msg = await message.answer("Загружаю...")

    try:
        # Не блокируем event loop — скачиваем в потоке
        file_path, title = await asyncio.to_thread(_download_sync, url)

        audio = types.FSInputFile(file_path)
        await message.answer_audio(audio, caption=f"✅ {title}")

        # Кэшируем
        _cache[cache_key] = file_path

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"Ошибка: {e}")


async def main():
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())