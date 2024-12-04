from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
from ftplib import FTP
import os

app = FastAPI()

# FTP Credentials
FTP_HOST = 'ftp.smartcardai.com'
FTP_USERNAME = 'wwwsmart'
FTP_PASSWORD = 'd7Jso5AOk2a'
FTP_TARGET_DIR = '/uploads'

# Allowed file extensions
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "txt", "pdf", "docx"}

def validate_file_type(file: UploadFile):
    """
    Validates the file type based on its extension.
    """
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")

def upload_to_ftp(file_path: str, file_name: str):
    """
    Uploads a file to the FTP server.
    """
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(user=FTP_USERNAME, passwd=FTP_PASSWORD)
        ftp.cwd(FTP_TARGET_DIR)

        with open(file_path, 'rb') as file:
            ftp.storbinary(f'STOR {file_name}', file)
        
        ftp.quit()
        return {"message": f"File '{file_name}' uploaded successfully to {FTP_TARGET_DIR}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FTP upload failed: {str(e)}")

@app.post("/upload/")
async def upload_file(files: List[UploadFile] = File(...)):
    """
    Accepts multiple files and uploads them to the FTP server.
    """
    results = []
    for file in files:
        validate_file_type(file)
        
        file_path = f"./{file.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        try:
            result = upload_to_ftp(file_path, file.filename)
            results.append(result)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    return {"results": results}
