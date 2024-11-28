from fastapi import FastAPI, HTTPException
import requests
import re, os, uvicorn, logging
import tempfile, librosa
from transformers import WhisperTokenizer, WhisperFeatureExtractor, WhisperForConditionalGeneration

# Инициализация приложения FastAPI
app = FastAPI()

# Имя модели для генерации аудиописаний
NAME = "MU-NLPC/whisper-small-audio-captioning"
# Устройство для выполнения модели, по умолчанию CPU
device = os.getenv("DEVICE", 'cpu')

# Загрузка предобученной модели генерации текста
model = WhisperForConditionalGeneration.from_pretrained(NAME)
model.eval()  # Установка режима оценки модели

# Загрузка токенизатора и извлекателя признаков
tokenizer = WhisperTokenizer.from_pretrained(NAME, language="en", task="transcribe")
feature_extractor = WhisperFeatureExtractor.from_pretrained(NAME)


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

        # Скачивание аудиофайла по URL
        response = requests.get(url)
        logging.error("get")
        response.raise_for_status()  # Проверка успешности скачивания

        # Сохранение скачанного аудиофайла во временное хранилище
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        logging.error("open aidio")

        # Загрузка аудиоданных с использованием librosa
        audio_data, sr = librosa.load(temp_file_path, sr=None)

        # Преобразование многоканального аудио в моно
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)
            logging.error("channels")

        # Ресэмплинг аудио до частоты 16 кГц, если это необходимо
        if sr != 16000:
            audio_data = librosa.resample(y=audio_data, orig_sr=sr, target_sr=16000)
            logging.error("resample")

        # Извлечение признаков из аудиоданных
        features = feature_extractor(audio_data, sampling_rate=16000, return_tensors="pt").input_features
        logging.error("features")

        # Формирование префикса стиля для генерации текста
        style_prefix = "clotho > caption: "
        style_prefix_tokens = tokenizer("", text_target=style_prefix, return_tensors="pt", add_special_tokens=False).labels
        logging.error("tokenize")

        # Генерация текстового описания аудио
        outputs = model.generate(
            inputs=features,
            forced_decoder_ids=style_prefix_tokens,
            max_length=300,
        )
        logging.error("generate")

        # Возвращение результата
        return {"extracted_text": tokenizer.batch_decode(outputs, skip_special_tokens=True)}

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
