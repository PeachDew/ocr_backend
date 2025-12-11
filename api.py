from io import BytesIO
from PIL import Image
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
from pathlib import Path
import pytesseract
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

def load_trocr_model():
    processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
    model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')
    return processor, model

def trocr_multiline(processor, model, img, y1: int = 70, y2: int = 120, y3: int = 165, y4: int = 220):
    """Crop image into 5 lines, run TrOCR on each, combine results."""
    width = img.width
    
    crops = [
        img.crop((0, 0, width, y1)),
        img.crop((0, y1, width, y2)),
        img.crop((0, y2, width, y3)),
        img.crop((0, y3, width, y4)),
        img.crop((0, y4, width, img.height))
    ]
    
    lines = []
    for crop in crops:
        pixel_values = processor(images=crop, return_tensors="pt").pixel_values
        generated_ids = model.generate(pixel_values)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        lines.append(text)
    
    return "\n".join(lines)

def OCR_inference(processor, model, image_PIL):
    image = image_PIL.convert("RGB")
    
    # Tesseract (full image)
    try:
        tesseract_output = pytesseract.image_to_string(image).strip()
    except Exception as e:
        tesseract_output = f"Error: {str(e)}"
    
    # TrOCR (multiline)
    try:
        trocr_output = trocr_multiline(processor, model, image)
    except Exception as e:
        trocr_output = f"Error: {str(e)}"
    
    return {
        "Tesseract": {"output": tesseract_output},
        "TrOCR": {"output": trocr_output}
    }
        
processor, model = load_trocr_model()

app = FastAPI()

# 2. Configure CORS
# importand because, svelte frontend (5173) running on different port than backend (8000)

origins = [
    "http://localhost",
    "http://localhost:5173", # Update this if your Svelte frontend uses a different port
    "ocrsharing.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# datastructure for incoming request body
# validate incoming JSON payload
class OCRRequest(BaseModel):
    image: str # Base64 encoded image string

def format_image(
    image_base64_data: str,
    save_image: bool = True,
    save_image_path: Path = Path("./canvas_output.png")
):
    try: 
        image_bytes = base64.b64decode(image_base64_data)
    except Exception as e:
        raise ValueError(f"Base64 decoding failed {e}")
    
    image_stream = BytesIO(image_bytes)
    image_pil = Image.open(image_stream)

    if save_image: 
        image_pil.save(save_image_path)

    return image_pil

def extract_and_parse_data(image: Image.Image):
    mock_ocr_output = """
    Name: John Doe
    Favorite Food: Pizza
    I Agree Checkbox: Checked
    """
    return mock_ocr_output

@app.post("/ocr")
async def process_ocr(request: OCRRequest):
    """
    Handles the POST request, predict with OCR model, and returns results.
    """ 
    try:
        image_pil = format_image(
        request.image,
        save_image=True
    )
    except ValueError as e:
        return str(e)
    
    # predict
    # extracted_data: str = extract_and_parse_data(image_pil)
    mock_results = OCR_inference(processor, model, image_pil)
        
    # Return the data in the structure the frontend expects: {"model_results": {...}}
    return {"model_results": mock_results}
    

