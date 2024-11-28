# Импорт необходимых библиотек и модулей
import ctypes
import logging
import os
import sys
import librosa
import tempfile
import soundfile as sf
from pathlib import Path
from streamlit.web import cli as stcli
from nexa.utils import SpinningCursorAnimation, nexa_prompt
from nexa.constants import (
    DEFAULT_TEXT_GEN_PARAMS,
    NEXA_RUN_MODEL_MAP_AUDIO_LM,
    NEXA_RUN_AUDIO_LM_PROJECTOR_MAP,
)
from nexa.gguf.lib_utils import is_gpu_available
from nexa.gguf.llama import audio_lm_cpp
from nexa.gguf.llama._utils_transformers import suppress_stdout_stderr
from nexa.general import pull_model


# Функция для проверки, является ли модель QWen
def is_qwen(model_name):
    if "qwen" in model_name.lower():  # Временное решение: жестко задано, может быть небезопасно
        return True
    return False


# Убедиться, что ключи карт модели и проектора совпадают
assert set(NEXA_RUN_MODEL_MAP_AUDIO_LM.keys()) == set(
    NEXA_RUN_AUDIO_LM_PROJECTOR_MAP.keys()
), "Модели, проекторы и обработчики должны иметь одинаковые ключи"


# Класс для работы с моделями Bark и генерацией речи на основе текста
class NexaAudioLMInference:
    """
    Класс для загрузки моделей Bark и выполнения генерации текста на основе аудио.

    Методы:
        run: Запуск цикла генерации аудио на основе текста.

    Аргументы:
        model_path (str): Путь к файлу модели.
        mmproj_path (str): Путь к файлу проектора.
        n_gpu_layers (int): Количество GPU-слоев для обработки. По умолчанию -1.
        output_dir (str): Директория для вывода. По умолчанию "tts".
        verbosity (int): Уровень детализации логирования модели. По умолчанию 0.
    """

    def __init__(self, model_path=None, local_path=None, projector_local_path=None, device="auto", **kwargs):
        # Проверка на наличие пути к модели или локального пути
        if model_path is None and local_path is None:
            raise ValueError("Необходимо указать либо model_path, либо local_path.")

        # Настройка параметров генерации и загрузка модели
        self.params = DEFAULT_TEXT_GEN_PARAMS.copy()
        self.params.update(kwargs)
        self.model = None
        self.projector = None
        self.projector_path = NEXA_RUN_AUDIO_LM_PROJECTOR_MAP.get(model_path, None)
        self.downloaded_path = local_path
        self.projector_downloaded_path = projector_local_path
        self.device = device
        self.context = None
        self.temp_file = None

        # Определение устройства для обработки (CPU или GPU)
        if self.device == "auto" or self.device == "gpu":
            self.n_gpu_layers = -1 if is_gpu_available() else 0
        else:
            self.n_gpu_layers = 0

        # Логика для загрузки модели и проектора в зависимости от доступных путей
        if self.downloaded_path is not None and self.projector_downloaded_path is not None:
            pass
        elif self.downloaded_path is not None:
            if model_path in NEXA_RUN_MODEL_MAP_AUDIO_LM:
                self.projector_path = NEXA_RUN_AUDIO_LM_PROJECTOR_MAP[model_path]
                self.projector_downloaded_path, _ = pull_model(self.projector_path, **kwargs)
        elif model_path in NEXA_RUN_MODEL_MAP_AUDIO_LM:
            self.model_path = NEXA_RUN_MODEL_MAP_AUDIO_LM[model_path]
            self.projector_path = NEXA_RUN_AUDIO_LM_PROJECTOR_MAP[model_path]
            self.downloaded_path, _ = pull_model(self.model_path, **kwargs)
            self.projector_downloaded_path, _ = pull_model(self.projector_path, **kwargs)
        elif Path(model_path).parent.exists():
            local_dir = Path(model_path).parent
            model_name = Path(model_path).name
            tag_and_ext = model_name.split(":")[-1]
            self.downloaded_path = local_dir / f"model-{tag_and_ext}"
            self.projector_downloaded_path = local_dir / f"projector-{tag_and_ext}"
            if not (self.downloaded_path.exists() and self.projector_downloaded_path.exists()):
                logging.error(
                    f"Модель или проектор не найдены в {local_dir}. "
                    "Убедитесь, что они названы 'model-<tag>.gguf' и 'projector-<tag>.gguf'."
                )
                exit(1)
        else:
            logging.error("Модель из VLM хаба пока не поддерживается.")
            exit(1)

        # Проверка на успешную загрузку моделей
        if self.downloaded_path is None or self.projector_downloaded_path is None:
            logging.error(
                f"Модель ({model_path}) недоступна. Пожалуйста, обратитесь к документации.",
                exc_info=True,
            )
            exit(1)

        # Проверка на Qwen
        self.is_qwen = is_qwen(self.downloaded_path)  # Временное решение
        self.ctx_params = audio_lm_cpp.context_default_params(self.is_qwen)
        with suppress_stdout_stderr():
            self._load_model()
