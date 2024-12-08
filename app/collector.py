from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from ftplib import FTP
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

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


def validate_file_type(file):
    """
    Validates the file type based on its extension.
    """
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type: {file_extension}"
    return True, None


@app.route('/createfolder/', methods=['POST'])
def create_folder():
    """
    Create a folder on the FTP server.
    """
    folder_name = request.json.get('folder_name')
    if not folder_name:
        return jsonify({"error": "Folder name is required"}), 400

    try:
        ftp = connect_ftp()
        target_path = f"{FTP_BASE_DIR}/{folder_name}"
        ftp.mkd(target_path)
        ftp.quit()
        return jsonify({"message": f"Folder '{folder_name}' created successfully."})
    except Exception as e:
        return jsonify({"error": f"Failed to create folder: {str(e)}"}), 500


@app.route('/upload/', methods=['POST'])
def upload_file():
    """
    Upload files to a specific folder on the FTP server.
    """
    folder_name = request.form.get('folder_name')
    files = request.files.getlist('files')
    results = []

    if not folder_name or not files:
        return jsonify({"error": "Folder name and files are required"}), 400

    for file in files:
        valid, error_message = validate_file_type(file)
        if not valid:
            return jsonify({"error": error_message}), 400

        # Save the file locally first
        file_path = f"./{file.filename}"
        file.save(file_path)

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

    return jsonify({"results": results})


@app.route('/deletefolder/', methods=['DELETE'])
def delete_folder():
    """
    Delete a folder from the FTP server.
    """
    folder_name = request.json.get('folder_name')
    if not folder_name:
        return jsonify({"error": "Folder name is required"}), 400

    try:
        ftp = connect_ftp()
        ftp.rmd(f"{FTP_BASE_DIR}/{folder_name}")
        ftp.quit()
        return jsonify({"message": f"Folder '{folder_name}' deleted successfully."})
    except Exception as e:
        return jsonify({"error": f"Failed to delete folder: {str(e)}"}), 500


@app.route('/selectfolder/', methods=['GET'])
def select_folder():
    """
    List all folders in the base directory on the FTP server.
    """
    try:
        ftp = connect_ftp()
        ftp.cwd(FTP_BASE_DIR)
        folders = ftp.nlst()
        ftp.quit()
        return jsonify({"folders": folders})
    except Exception as e:
        return jsonify({"error": f"Failed to list folders: {str(e)}"}), 500


@app.route('/deletefiles/', methods=['DELETE'])
def delete_files():
    """
    Delete specific files from a folder on the FTP server.
    """
    folder_name = request.json.get('folder_name')
    file_names = request.json.get('file_names')

    if not folder_name or not file_names:
        return jsonify({"error": "Folder name and file names are required"}), 400

    try:
        ftp = connect_ftp()
        ftp.cwd(f"{FTP_BASE_DIR}/{folder_name}")
        for file_name in file_names:
            ftp.delete(file_name)
        ftp.quit()
        return jsonify({"message": f"Files {file_names} deleted successfully from folder '{folder_name}'."})
    except Exception as e:
        return jsonify({"error": f"Failed to delete files: {str(e)}"}), 500


@app.route('/selectfiles/', methods=['GET'])
def select_files():
    """
    List all files in a specific folder on the FTP server.
    """
    folder_name = request.args.get('folder_name')
    if not folder_name:
        return jsonify({"error": "Folder name is required"}), 400

    try:
        ftp = connect_ftp()
        ftp.cwd(f"{FTP_BASE_DIR}/{folder_name}")
        files = ftp.nlst()
        ftp.quit()
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": f"Failed to list files: {str(e)}"}), 500


@app.route('/viewfile/', methods=['GET'])
def view_file():
    """
    Get the URL of a specific file.
    """
    folder_name = request.args.get('folder_name')
    file_name = request.args.get('file_name')

    if not folder_name or not file_name:
        return jsonify({"error": "Folder name and file name are required"}), 400

    try:
        return jsonify({
            "file_url": f"http://{FTP_HOST}/{FTP_BASE_DIR}/{folder_name}/{file_name}",
            "folder_name": folder_name
        })
    except Exception as e:
        return jsonify({"error": f"Failed to get file URL: {str(e)}"}), 500


@socketio.on('message')
def handle_message(data):
    """
    Handle real-time socket messages.
    """
    print('Message received:', data)
    socketio.emit('response', {'data': f"Server received: {data}"})


if __name__ == '__main__':
    socketio.run(app, debug=True)
