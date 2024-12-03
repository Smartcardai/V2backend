from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
import shutil

app = FastAPI()

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    "mp3", "mp4", "png", "jpeg", "jpg", "pdf", "doc", "docx", "txt"
}

def validate_file_type(file: UploadFile):
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

@app.post("/upload/")
async def upload_file(files: List[UploadFile] = File(...)):
    """
    Accept multiple files and validate their types.
    """
    for file in files:
        validate_file_type(file)

        # Save file locally
        with open(f"./uploads/{file.filename}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    return {"message": f"Successfully uploaded {len(files)} file(s)."}

