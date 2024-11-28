from fastapi import FastAPI, HTTPException
import requests
from io import BytesIO
import re, os, uvicorn, logging
from inference import NexaAudioLMInference
import tempfile

# Инициализация приложения FastAPI
app = FastAPI()

# Устройство для выполнения модели, по умолчанию используется GPU (если доступен)
device = os.getenv("DEVICE", 'cuda:0')

# Инициализация модели NexaAudioLMInference
model = NexaAudioLMInference(
    model_path="Qwen2-Audio-7.8B-Instruct:q2_K",  # Путь к предобученной модели
    device=device  # Указание устройства для вычислений
)

# Тестовое выполнение модели на заранее заданном аудиофайле
outputs = model.inference(
    audio_path="./596a2ad660504b872d9dceb921576f3762a9dd4c.wav",  # Локальный путь к аудиофайлу
    prompt="Provide detailed caption of this audio"  # Пример подсказки для генерации текста
)


@app.post("/audio_caption/")
async def extract_text(url: str, prompt: str = "Provide detailed caption of this audio"):
    """
    Обработчик POST-запроса для извлечения текстового описания из аудиофайла по URL.

    Аргументы:
    - url: Ссылка на аудиофайл
    - prompt: Подсказка для генерации описания

    Возвращает:
    - JSON с извлечённым текстом
    """
    try:
        # Логгирование начала обработки
        logging.error("start")

        # Скачивание аудиофайла по указанному URL
        response = requests.get(url)
        logging.error("get")
        response.raise_for_status()  # Проверка успешности скачивания

        # Сохранение скачанного аудиофайла во временное хранилище
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        logging.error("open aidio")

        # Запуск модели на скачанном аудиофайле
        outputs = model.inference(
            audio_path=temp_file_path,  # Путь к временному файлу
            prompt=prompt  # Пользовательская подсказка
        )

        # Очистка ресурсов модели после выполнения
        model.cleanup()
        logging.error("generate")

        # Возвращение результата
        return {"extracted_text": outputs}

    # Обработка ошибок HTTP
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=500, detail=f"HTTP error occurred: {http_err}")
    # Обработка других ошибок
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

if __name__ == "__main__":
    # Запуск приложения с использованием uvicorn
    uvicorn.run(
        "app:app",  # Указание модуля и переменной приложения
        host=os.getenv("HOST", "0.0.0.0"),  # Хост сервера
        port=int(os.getenv("PORT", "8000")),  # Порт сервера
        reload=True,  # Автоперезагрузка при изменениях кода
        log_level="debug",  # Уровень логирования
    )
