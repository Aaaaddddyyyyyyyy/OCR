import os
import sys
from pathlib import Path
from datetime import datetime

from supabase_client import supabase


def upload_document(file_path: str):
    file = Path(file_path)

    if not file.exists():
        raise FileNotFoundError(f"File not found: {file}")

    file_name = file.name
    file_extension = file.suffix.lower()

    if file_extension == ".pdf":
        file_type = "pdf"
        mime_type = "application/pdf"

    elif file_extension in [".jpg", ".jpeg", ".png", ".webp"]:
        file_type = "image"
        mime_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }[file_extension]

    else:
        raise ValueError(
            f"Unsupported file type: {file_extension}"
        )

    storage_path = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"

    with open(file, "rb") as file_data:

        supabase.storage.from_("documents").upload(
            storage_path,
            file_data,
            {
                "content-type": mime_type
            }
        )

    print("File uploaded to Supabase Storage.")
    print(f"Storage path: {storage_path}")

    document_data = {
        "file_name": file_name,
        "file_type": file_type,
        "storage_path": storage_path,
        "processing_status": "uploaded",
    }

    response = (
        supabase
        .table("documents")
        .insert(document_data)
        .execute()
    )

    print("Document record created in database.")
    print("Database response:")
    print(response.data)

    return response.data


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Please provide the file path.")
        print(
            "Example:"
            " python backend\\upload_document.py "
            "\"E:\\OCR_Project\\test.pdf\""
        )
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        upload_document(file_path)

    except Exception as error:
        print("Upload failed!")
        print(error)