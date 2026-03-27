import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from yt_dlp import YoutubeDL

# Твой токен
TOKEN = '7524843007:AAFT6CuyZ2fNvhB-FA3IfJjBb2AKPxMrlY4'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Настройки для скачивания (только аудио)
ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s', # Папка для сохранения
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! Пришли мне ссылку на трек из SoundCloud, и я его скачаю.")

@dp.message(F.text.contains("soundcloud.com"))
async def download_track(message: types.Message):
    msg = await message.answer("Начинаю загрузку... Подожди немного. ⏳")
    url = message.text
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

        # Отправка файла пользователю
        audio = types.FSInputFile(file_path)
        await message.answer_audio(audio, caption=f"Готово: {info.get('title')}")
        
        # Удаляем файл после отправки, чтобы не занимать место
        os.remove(file_path)
        await msg.delete()

    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")

async def main():
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
