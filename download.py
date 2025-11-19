import os
import requests
import tempfile
from urllib.parse import urlparse
from config import settings
import hashlib
from models import Attachment
from sqlalchemy.orm import Session
from utils import extract_text_from_file, contains_id_card, contains_phone, detect_sensitive_info_ai, extract_zip_content
import zipfile
import rarfile


def get_file_hash(file_path):
    """Generate a hash for a file to use as cache key"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def download_file(url, local_path, timeout=30):
    """Download a file from URL to local path"""
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False


def get_cached_file_path(url):
    """Get the local cache path for a URL"""
    # Create cache directory if it doesn't exist
    os.makedirs(settings.ATTACHMENT_CACHE_DIR, exist_ok=True)

    # Parse the URL and use the path directly for cache organization
    parsed_url = urlparse(url)
    path = parsed_url.path

    # Remove leading slash to make it relative
    if path.startswith('/'):
        path = path[1:]

    # Create the full cache path
    cache_path = os.path.join(settings.ATTACHMENT_CACHE_DIR, path)

    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    return cache_path


def update_progress(ws_id: str, current: int, total: int, message: str):
    """Send progress update via WebSocket"""
    import asyncio
    from main import manager
    import json

    async def send_update():
        progress_data = {
            "current": current,
            "total": total,
            "message": message,
            "status": "processing" if current < total else "completed"
        }
        try:
            # Check if connection exists before sending
            if ws_id in manager.active_connections:
                await manager.send_progress(ws_id, progress_data)
            else:
                print(f"WebSocket connection {ws_id} not found, skipping progress update")
        except Exception as e:
            print(f"Error sending WebSocket progress: {e}")

    # Get the current event loop and schedule the task
    try:
        loop = asyncio.get_running_loop()
        # Schedule the task in the running event loop
        loop.create_task(send_update())
    except RuntimeError:
        # No running event loop, create one
        asyncio.run(send_update())


def process_attachment_file(attachment: Attachment, db: Session, base_url: str = "", detection_type="normal", progress_callback=None):
    """Process an attachment: download, extract content, and update database"""
    # Construct full URL for the attachment
    if attachment.url_path.startswith(('http://', 'https://')):
        full_url = attachment.url_path
    else:
        # Use provided base_url, otherwise use the default from settings
        effective_base_url = base_url if base_url else settings.ATTACHMENT_DEFAULT_BASE_URL
        full_url = effective_base_url.rstrip('/') + attachment.url_path if effective_base_url else attachment.url_path

    if not full_url or full_url == attachment.url_path and not full_url.startswith(('http://', 'https://')):
        print(f"Invalid URL for attachment {attachment.id}: {full_url}")
        return

    # Extract file extension from URL path for more accurate detection
    from urllib.parse import urlparse
    parsed_url = urlparse(full_url)
    _, extracted_ext = os.path.splitext(parsed_url.path)
    if extracted_ext:
        # Remove the leading dot for consistency
        extracted_ext = extracted_ext[1:].lower()
    else:
        # If no extension in URL, fall back to the stored file_ext
        extracted_ext = attachment.file_ext.lower() if attachment.file_ext else ""

    # Update the attachment's file_ext field to the extracted extension if different
    if attachment.file_ext != extracted_ext:
        attachment.file_ext = extracted_ext
        db.commit()  # Commit the change to the database

    # Get cached file path
    cached_path = get_cached_file_path(full_url)

    # Download file if not already cached
    if not os.path.exists(cached_path):
        print(f"Downloading {full_url} to {cached_path}")
        if not download_file(full_url, cached_path):
            print(f"Failed to download {full_url}")
            return

    # If the file is an archive, extract it and process the contents
    if extracted_ext in ['zip', 'rar']:
        # Create a temporary directory for extracted files
        extract_dir = cached_path + "_extracted"

        if not os.path.exists(extract_dir):
            print(f"Extracting archive {cached_path} to {extract_dir}")
            extract_zip_content(cached_path, extract_dir)

        # Process each file in the extracted directory
        text_content = ""
        ocr_content = ""

        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                _, file_ext = os.path.splitext(file)
                if file_ext:
                    file_ext = file_ext[1:].lower()  # Remove leading dot and lowercase
                # Extract content from each file in the archive
                file_text = extract_text_from_file(file_path)
                text_content += file_text + "\n"

                if file_ext in ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'pdf']:
                    file_ocr = extract_text_from_file(file_path)
                    ocr_content += file_ocr + "\n"
    else:
        # Extract content from the file directly
        text_content = extract_text_from_file(cached_path)

        # Determine if we need OCR content (for images and image-based PDFs)
        ocr_content = ""
        if extracted_ext in ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'pdf']:
            ocr_content = extract_text_from_file(cached_path)  # This will use OCR for images

    # Process based on detection type
    if detection_type == "ai" and settings.OPENAI_API_KEY:
        # Use AI for content analysis
        has_id_card_normal = contains_id_card(text_content) or contains_id_card(ocr_content)
        has_phone_normal = contains_phone(text_content) or contains_phone(ocr_content)

        # Perform AI analysis
        ai_has_id_card, ai_has_phone, ai_analysis = detect_sensitive_info_ai(text_content + " " + ocr_content)

        # Use AI results if they detect sensitive info, otherwise use normal detection
        has_id_card = ai_has_id_card or has_id_card_normal
        has_phone = ai_has_phone or has_phone_normal
        llm_content = ai_analysis
    else:
        # Use normal detection
        has_id_card = contains_id_card(text_content) or contains_id_card(ocr_content)
        has_phone = contains_phone(text_content) or contains_phone(ocr_content)
        llm_content = ""

    # Update the attachment in the database
    attachment.text_content = text_content
    attachment.ocr_content = ocr_content
    attachment.llm_content = llm_content
    attachment.has_id_card = has_id_card
    attachment.has_phone = has_phone

    # If sensitive info is detected, mark for manual verification
    if has_id_card or has_phone:
        attachment.manual_verified_sensitive = True
        attachment.verification_notes = f"Auto-detected: ID card={has_id_card}, Phone={has_phone}"

    db.commit()
    print(f"Processed attachment {attachment.id}: ID card={has_id_card}, Phone={has_phone}, Manual verification required={has_id_card or has_phone}, File extension: {extracted_ext}")

    # Call progress callback if provided
    if progress_callback:
        progress_callback()


def process_site_attachments_with_progress(site_owner: str, db: Session, detection_type: str = "normal", ws_id: str = None):
    """
    Process all attachments for a site with progress updates
    """
    # Get all attachments for the site
    attachments = db.query(Attachment).filter(Attachment.site_id == site_owner).all()

    total_attachments = len(attachments)

    # Send initial progress
    if ws_id:
        update_progress(ws_id, 0, total_attachments, f"Starting detection for {total_attachments} attachments...")

    processed_count = 0
    sensitive_count = 0

    for i, attachment in enumerate(attachments, 1):
        try:
            # Process the attachment
            process_attachment_file(
                attachment,
                db,
                base_url=settings.ATTACHMENT_DEFAULT_BASE_URL,
                detection_type=detection_type
            )

            # Count attachments that were marked as containing sensitive info
            if attachment.has_id_card or attachment.has_phone:
                sensitive_count += 1

            processed_count += 1

            # Send progress update
            if ws_id:
                update_progress(
                    ws_id,
                    processed_count,
                    total_attachments,
                    f"Processing attachment {processed_count}/{total_attachments}..."
                )

        except Exception as e:
            print(f"Error processing attachment {attachment.id}: {str(e)}")
            continue

    # Send final progress
    if ws_id:
        update_progress(
            ws_id,
            processed_count,
            total_attachments,
            f"Detection completed. {sensitive_count} attachments with sensitive info detected out of {processed_count}."
        )

    return {
        "message": f"Detected {processed_count} attachments for site {site_owner}, {sensitive_count} with sensitive info",
        "processed_count": processed_count,
        "sensitive_count": sensitive_count
    }


def download_site_attachments_simple(site_owner: str, db: Session):
    """
    Download all attachments for a site without progress tracking
    """
    # Get all attachments for the site
    attachments = db.query(Attachment).filter(Attachment.site_id == site_owner).all()

    total_attachments = len(attachments)
    downloaded_count = 0

    for i, attachment in enumerate(attachments, 1):
        try:
            # Construct full URL for the attachment
            if attachment.url_path.startswith(('http://', 'https://')):
                full_url = attachment.url_path
            else:
                # Use the default base URL
                effective_base_url = settings.ATTACHMENT_DEFAULT_BASE_URL
                full_url = effective_base_url.rstrip('/') + attachment.url_path if effective_base_url else attachment.url_path

            if not full_url or full_url == attachment.url_path and not full_url.startswith(('http://', 'https://')):
                print(f"Invalid URL for attachment {attachment.id}: {full_url}")
                continue

            # Get cached file path
            cached_path = get_cached_file_path(full_url)

            # Download file if not already cached
            if not os.path.exists(cached_path):
                print(f"Downloading {full_url} to {cached_path}")
                if download_file(full_url, cached_path):
                    downloaded_count += 1
                else:
                    print(f"Failed to download {full_url}")
            else:
                # File already exists in cache, count as downloaded
                downloaded_count += 1

        except Exception as e:
            print(f"Error downloading attachment {attachment.id}: {str(e)}")
            continue

    return {
        "message": f"Download completed. {downloaded_count} of {total_attachments} attachments downloaded for site {site_owner}",
        "downloaded_count": downloaded_count,
        "total_count": total_attachments
    }




