from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
from ftplib import FTP

app = FastAPI()

# FTP Credentials
FTP_HOST = 'ftp.smartcardai.com'  # Replace with your FTP server
FTP_USERNAME = 'wwwsmart'  # Replace with your FTP username
FTP_PASSWORD = 'd7Jso5AOk2a'  # Replace with your FTP password
FTP_TARGET_DIR = '/uploads'  # Directory on the FTP server where files will be stored


def upload_to_ftp(file_path: str, file_name: str):  
    """
    Uploads a file to the FTP server.
    """
    try:
        # Connect to FTP server
        ftp = FTP(FTP_HOST)
        ftp.login(user=FTP_USERNAME, passwd=FTP_PASSWORD)
        ftp.cwd(FTP_TARGET_DIR)  # Change to the target directory

        # Open the file in binary mode and upload it
        with open(file_path, 'rb') as file:
            ftp.storbinary(f'STOR {file_name}', file)
        
        ftp.quit()  # Close the FTP connection
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
        file_path = f"./{file.filename}"  # Temporarily save file locally
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Upload the file to FTP
        try:
            result = upload_to_ftp(file_path, file.filename)
            results.append(result)
        finally:
            # Clean up local temporary file
            import os
            if os.path.exists(file_path):
                os.remove(file_path)

    return {"results": results}
