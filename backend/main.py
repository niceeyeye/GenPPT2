from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .schemas import PPTRequest, PPTContent, Slide
from .services.llm import generate_ppt_content, polish_topic
from .services.ppt import create_pptx
from .services.html_export import create_html_presentation
from .services import history as history_service
import os
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GenPPT API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Static Files for Downloads
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
generated_dir = os.path.join(BASE_DIR, "generated_ppts")
os.makedirs(generated_dir, exist_ok=True)
app.mount("/downloads", StaticFiles(directory=generated_dir), name="downloads")

@app.get("/get-file/{filename}")
async def get_file(filename: str):
    """
    Forces download of a file by setting Content-Disposition.
    """
    file_path = os.path.join(generated_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Setting filename in FileResponse sets Content-Disposition: attachment
    return FileResponse(
        file_path, 
        filename=filename, 
        media_type='application/octet-stream'
    )

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "GenPPT API is running"}

@app.post("/polish")
async def polish(request: PPTRequest):
    """
    Polishes the topic for better results.
    """
    logger.info(f"Received /polish request for topic: {request.topic}")
    try:
        polished = polish_topic(request.topic, request.provider, request.api_key)
        return {"polished_topic": polished}
    except Exception as e:
        logger.error(f"Error in /polish: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate", response_model=PPTContent)
async def generate_preview(request: PPTRequest):
    """
    Generates PPT content (JSON) for preview based on the topic.
    """
    logger.info(f"Received /generate request: topic='{request.topic}', provider='{request.provider}'")
    try:
        content = generate_ppt_content(request.topic, request.provider, request.api_key)
        
        # Automatically generate files and add to history
        pptx_filename = create_pptx(content)
        html_filename = create_html_presentation(content)
        
        history_service.add_history_item(
            title=content.title,
            content=content,
            pptx_filename=pptx_filename,
            html_filename=html_filename
        )
        
        logger.info("Successfully generated PPT content and added to history")
        return content
    except Exception as e:
        logger.error(f"Error in /generate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history():
    return history_service.get_all_history()

@app.delete("/history/{item_id}")
async def delete_history(item_id: str):
    history_service.delete_history_item(item_id)
    return {"status": "success"}

@app.post("/download")
async def generate_file(content: PPTContent, background_tasks: BackgroundTasks):
    """
    Generates the physical PPTX file from the JSON content and returns the download URL.
    """
    try:
        filename = create_pptx(content)
        download_url = f"/downloads/{filename}"
        return {"download_url": download_url, "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download-html")
async def generate_html_file(content: PPTContent):
    """
    Generates a standalone HTML file from the JSON content.
    """
    try:
        filename = create_html_presentation(content)
        download_url = f"/downloads/{filename}"
        return {"download_url": download_url, "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
