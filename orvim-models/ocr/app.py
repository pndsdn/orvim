from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image
import requests
from io import BytesIO
from transformers import DonutProcessor, VisionEncoderDecoderModel
import torch
import re, os, uvicorn, logging

app = FastAPI()

# Load processor and model
processor = DonutProcessor.from_pretrained("naver-clova-ix/donut-base-finetuned-cord-v2")
model = VisionEncoderDecoderModel.from_pretrained("naver-clova-ix/donut-base-finetuned-cord-v2")

device = os.getenv("DEVICE", 'cuda:0')
model.to(device)


@app.post("/extract_text/")
async def extract_text(url: str):
    try:
        # Download the image
        logging.error("start")
        response = requests.get(url)
        logging.error("get")
        response.raise_for_status()

        # Open the image
        image = Image.open(BytesIO(response.content)).convert("RGB")
        logging.error("open image")

        # Prepare decoder inputs
        task_prompt = "<s_cord-v2>"
        decoder_input_ids = processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids
        logging.error("tokenizing")

        # Preprocess the image
        pixel_values = processor(image, return_tensors="pt").pixel_values
        logging.error("pixel values")

        # Run inference
        outputs = model.generate(
            pixel_values.to(device),
            decoder_input_ids=decoder_input_ids.to(device),
            max_length=model.decoder.config.max_position_embeddings,
            pad_token_id=processor.tokenizer.pad_token_id,
            eos_token_id=processor.tokenizer.eos_token_id,
            use_cache=True,
            bad_words_ids=[[processor.tokenizer.unk_token_id]],
            return_dict_in_generate=True,
        )
        logging.error("generate")

        # Postprocess the output
        sequence = processor.batch_decode(outputs.sequences)[0]
        logging.error("decode")

        sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(processor.tokenizer.pad_token, "")
        sequence = re.sub(r"<.*?>", "", sequence).strip()  # remove first task start token
        result = processor.token2json(sequence)

        return result

    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=500, detail=f"HTTP error occurred: {http_err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
        log_level="debug",
    )
