from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from typing import List, Optional
from ftplib import FTP
import os

app = FastAPI()

# FTP Credentials
FTP_HOST = 'ftp.smartcardai.com'
FTP_USERNAME = 'wwwsmart'
FTP_PASSWORD = 'd7Jso5AOk2a'
FTP_BASE_DIR = '/uploads'

# Allowed file extensions
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "txt", "pdf", "docx"}

def connect_ftp():
    """
    Establish and return an FTP connection.
    """
    ftp = FTP(FTP_HOST)
    ftp.login(user=FTP_USERNAME, passwd=FTP_PASSWORD)
    return ftp

def validate_file_type(file: UploadFile):
    """
    Validates the file type based on its extension.
    """
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")

@app.post("/createfolder/")
def create_folder(folder_name: str):
    """
    Create a folder on the FTP server.
    """
    try:
        ftp = connect_ftp()
        target_path = f"{FTP_BASE_DIR}/{folder_name}"
        ftp.mkd(target_path)
        ftp.quit()
        return {"message": f"Folder '{folder_name}' created successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create folder: {str(e)}")

@app.post("/upload/")
async def upload_file(
    folder_name: str = Query(..., description="Folder to upload files into"),
    files: List[UploadFile] = File(...)
):
    """
    Upload files to a specific folder on the FTP server.
    """
    results = []
    for file in files:
        validate_file_type(file)

        # Save the file locally first
        file_path = f"./{file.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        try:
            ftp = connect_ftp()
            ftp.cwd(f"{FTP_BASE_DIR}/{folder_name}")
            with open(file_path, 'rb') as f:
                ftp.storbinary(f"STOR {file.filename}", f)
            ftp.quit()
            results.append({"file": file.filename, "status": "uploaded"})
        except Exception as e:
            results.append({"file": file.filename, "status": f"failed: {str(e)}"})
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    return {"results": results}

@app.delete("/deletefolder/")
def delete_folder(folder_name: str):
    """
    Delete a folder from the FTP server.
    """
    try:
        ftp = connect_ftp()
        ftp.rmd(f"{FTP_BASE_DIR}/{folder_name}")
        ftp.quit()
        return {"message": f"Folder '{folder_name}' deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete folder: {str(e)}")

@app.get("/selectfolder/")
def select_folder():
    """
    List all folders in the base directory on the FTP server.
    """
    try:
        ftp = connect_ftp()
        ftp.cwd(FTP_BASE_DIR)
        folders = ftp.nlst()
        ftp.quit()
        return {"folders": folders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list folders: {str(e)}")

@app.delete("/deletefiles/")
def delete_files(folder_name: str, file_names: List[str]):
    """
    Delete specific files from a folder on the FTP server.
    """
    try:
        ftp = connect_ftp()
        ftp.cwd(f"{FTP_BASE_DIR}/{folder_name}")
        for file_name in file_names:
            ftp.delete(file_name)
        ftp.quit()
        return {"message": f"Files {file_names} deleted successfully from folder '{folder_name}'."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete files: {str(e)}")

@app.get("/selectfiles/")
def select_files(folder_name: str):
    """
    List all files in a specific folder on the FTP server.
    """
    try:
        ftp = connect_ftp()
        ftp.cwd(f"{FTP_BASE_DIR}/{folder_name}")
        files = ftp.nlst()
        ftp.quit()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@app.get("/viewfile/")
def view_file(folder_name: str, file_name: str):
    """
    Get the URL of a specific file.
    """
    try:
        return {
            "file_url": f"http://{FTP_HOST}/{FTP_BASE_DIR}/{folder_name}/{file_name}",
            "folder_name": folder_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file URL: {str(e)}")
