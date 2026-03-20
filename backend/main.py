from fastapi import FastAPI, HTTPException, Body, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Any
import os
import uuid
import time
import shutil

from .schemas import PPTContent, ModifyOutlineRequest
from .services.llm import generate_ppt_content, polish_topic, modify_ppt_content
from .services.ppt import create_pptx
from .services.html_export import create_html_presentation
from .services.history import add_history_item, get_all_history, delete_history_item
from .services.stt import save_and_transcribe

app = FastAPI(title="GenPPT API")

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    print(f"--- Incoming Request: {request.method} {request.url.path} ---")
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    print(f"--- Finished Request: {request.method} {request.url.path} (Status: {response.status_code}, Time: {process_time:.2f}ms) ---")
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Ensure the generated_ppts directory exists
GENERATED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_ppts")
os.makedirs(GENERATED_DIR, exist_ok=True)

class TopicRequest(BaseModel):
    topic: str
    provider: str = "openai"
    api_key: Optional[str] = None

@app.post("/generate")
async def generate_ppt(request: TopicRequest):
    try:
        content = generate_ppt_content(request.topic, request.provider, request.api_key)
        
        # Pre-generate both files and save to history
        pptx_filename = create_pptx(content)
        html_filename = create_html_presentation(content)
        
        # Save to history
        add_history_item(
            title=content.title,
            content=content,
            pptx_filename=pptx_filename,
            html_filename=html_filename
        )
        
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/polish")
async def polish(request: TopicRequest):
    try:
        polished = polish_topic(request.topic, request.provider, request.api_key)
        return {"polished_topic": polished}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/modify-outline", response_model=PPTContent)
async def modify_outline(request: ModifyOutlineRequest):
    try:
        print(f"--- Modifying Outline ---")
        print(f"Instruction: {request.instruction}")
        print(f"Slides before: {len(request.content.slides)}")
        
        updated_content_dict = modify_ppt_content(
            current_content=request.content.dict(),
            instruction=request.instruction,
            provider=request.provider,
            api_key=request.api_key
        )
        
        print(f"Slides after: {len(updated_content_dict.get('slides', []))}")
        
        # Ensure we return a valid PPTContent object to avoid validation errors
        return PPTContent(**updated_content_dict)
    except Exception as e:
        import traceback
        print("Error in /modify-outline:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    """
    Endpoint to receive an audio file and return transcribed text.
    """
    print(f"--- STT Request: Received file {file.filename} ---")
    try:
        # Get the file extension
        extension = file.filename.split(".")[-1] if "." in file.filename else "wav"
        
        # Read the audio bytes
        audio_bytes = await file.read()
        
        # Save and transcribe
        text = save_and_transcribe(audio_bytes, extension)
        
        print(f"Transcribed Text: {text}")
        return {"text": text}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Speech to text failed: {str(e)}")

@app.get("/history")
async def get_history():
    return get_all_history()

@app.delete("/history/{item_id}")
async def delete_history(item_id: str):
    delete_history_item(item_id)
    return {"status": "success"}

@app.post("/download")
async def download_pptx(content: PPTContent):
    try:
        filename = create_pptx(content)
        return {
            "filename": filename,
            "download_url": f"/get-file/{filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download-html")
async def download_html(content: PPTContent):
    try:
        filename = create_html_presentation(content)
        return {
            "filename": filename,
            "download_url": f"/get-file/{filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-file/{filename}")
async def get_file(filename: str, mode: Optional[str] = "preview"):
    file_path = os.path.join(GENERATED_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # If mode is download, we want it to be downloaded (attachment)
    # If mode is preview and it's HTML, we want it to open in the browser (inline)
    if mode == "download":
        content_disposition = "attachment"
    else:
        content_disposition = "inline" if filename.endswith(".html") else "attachment"
    
    return FileResponse(
        file_path, 
        filename=filename if content_disposition == "attachment" else None,
        media_type="text/html" if filename.endswith(".html") else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
