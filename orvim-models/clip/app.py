from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image
import requests
from io import BytesIO
from transformers import BlipProcessor, BlipForConditionalGeneration

import torch
import re, os, uvicorn, logging

app = FastAPI()

# Load processor and model
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")

device = os.getenv("DEVICE", 'cpu')
model.to(device)


@app.post("/image_caption/")
async def image_caption(url: str):
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
        inputs = processor(image, return_tensors="pt").to(device)
        logging.error("inputs")

        # Run inference
        out = model.generate(**inputs)
        logging.error("generate")

        # Postprocess the output
        sequence = processor.decode(out[0], skip_special_tokens=True)
        logging.error("decode")

        return {"extracted_texts": sequence}

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
