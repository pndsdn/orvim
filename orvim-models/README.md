# Сборка и запуск
## CPU версия
```
docker compose -f docker-compose.cpu.yaml up -d --build
```
## GPU версия
```
docker compose -f docker-compose.gpu.yaml up -d --build
```

# Сервисы

## CLAP
Извлечение текстового описания из аудиофайла по URL.

Доступен по `28001` порту

### Endpoint
**[POST]/audio_caption**

Запрос:
```
{
    "url": "Ссылка на аудиофайл",
    "prompt": "Подсказка для генерации описания"
}
```

Ответ:
```
{
    "extracted_text": "text"
}
```

## CLIP
Извлечение текстового описания из изображения по URL.

Доступен по `28002` порту

### Endpoint
**[POST]/image_caption**

Запрос:
```
{
    "url": "Ссылка на изображение"
}
```

Ответ:
```
{
    "extracted_texts": "text"
}
```

## Embedder
Генерация эмбеддинга для переданного текста.

Доступен по `28003` порту

### Endpoint
**/embed**

Запрос:
```
["text1", "text2", ...]
```

Ответ:
```
["embedding1", "embedding2", ...]
```

## OCR
Извлечение текста из документа по URL.

Доступен по `28004` порту

### Endpoint
**/extract_text**

Запрос:
```
{
    "url": "Ссылка на изображение"
}
```

Ответ:
```
{

}
```