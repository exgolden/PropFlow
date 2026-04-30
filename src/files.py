import os
import uuid

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "../static/uploads")
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}


def allowed_file(filename: str) -> bool:
    """
    Returns True if the file extension is in the allowed list.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_file(file) -> str:
    """
    Saves an uploaded file to the uploads folder with a unique UUID name.
    Returns the relative URL path to the saved file.
    Raises ValueError if the file type is not allowed.
    """
    if not allowed_file(file.filename):
        raise ValueError(f"Tipo de archivo no permitido — solo se aceptan: {', '.join(ALLOWED_EXTENSIONS)}")
    extension = file.filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{extension}"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file.save(os.path.join(UPLOAD_FOLDER, unique_filename))
    return f"/static/uploads/{unique_filename}"


def delete_file(url_archivo: str) -> None:
    """
    Deletes a file from disk given its relative URL path.
    Silently ignores the error if the file doesn't exist.
    """
    filename = url_archivo.replace("/static/uploads/", "")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)