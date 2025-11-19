from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from fastapi import WebSocket, WebSocketDisconnect

from models import SessionLocal, Site, Attachment, create_tables
from config import settings
from sync import RemoteDBSync
from download import process_attachment_file
from utils import contains_id_card, contains_phone


# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, ws_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[ws_id] = websocket

    def disconnect(self, ws_id: str):
        if ws_id in self.active_connections:
            del self.active_connections[ws_id]

    async def send_progress(self, ws_id: str, progress_data: dict):
        if ws_id in self.active_connections:
            await self.active_connections[ws_id].send_text(json.dumps(progress_data))

manager = ConnectionManager()

# Create tables on startup
create_tables()

# Create FastAPI app
app = FastAPI(title="Attachment Detection System", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files under /static
app.mount("/static", StaticFiles(directory="static"), name="static")


import asyncio
import threading
from collections import defaultdict

# Global state for pending operations
pending_operations = {}
operation_lock = threading.Lock()

@app.websocket("/ws/{ws_id}")
async def websocket_endpoint(websocket: WebSocket, ws_id: str):
    await manager.connect(ws_id, websocket)
    try:
        # Check if there's a pending operation for this ws_id
        with operation_lock:
            if ws_id in pending_operations:
                # Get the operation details and execute it
                operation = pending_operations[ws_id]
                del pending_operations[ws_id]

                # Execute the operation in a separate thread/task
                # We need to make sure this runs after the WebSocket is connected
                if operation['type'] == 'detect':
                    site_owner = operation['params']['site_owner']
                    detection_type = operation['params']['detection_type']
                    # Run the detection operation
                    from download import process_site_attachments_with_progress
                    from models import SessionLocal
                    db = SessionLocal()
                    try:
                        process_site_attachments_with_progress(site_owner, db, detection_type, ws_id)
                    finally:
                        db.close()

        # Keep the WebSocket connection alive to receive messages
        while True:
            # Keep the connection alive
            data = await websocket.receive_text()
            # Process any messages from frontend if needed
    except WebSocketDisconnect:
        manager.disconnect(ws_id)


# Pydantic models for API
from datetime import datetime

class SiteBase(BaseModel):
    owner: str
    account: str
    name: str
    domain: str
    state: int
    alias_domains: Optional[str] = None
    create_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class SiteResponse(SiteBase):
    id: int


class AttachmentBase(BaseModel):
    site_id: int
    show_name: str
    file_path: str
    url_path: str
    file_ext: str
    create_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class AttachmentResponse(AttachmentBase):
    id: int
    text_content: Optional[str] = None
    ocr_content: Optional[str] = None
    llm_content: Optional[str] = None
    has_id_card: bool
    has_phone: bool
    manual_verified_sensitive: bool
    verification_notes: Optional[str] = None
    create_date: Optional[datetime] = None
    processed_datetime: Optional[datetime] = None
    ocr_score: Optional[float] = None


class SyncRequest(BaseModel):
    site_owner: Optional[str] = None


class SiteStats(BaseModel):
    site_id: int
    site_name: str
    site_account: Optional[str] = None
    site_domain: str
    site_create_date: Optional[datetime] = None
    total_attachments: int
    attachments_with_id_card: int
    attachments_with_phone: int

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_sites: int
    total_attachments: int
    attachments_with_id_card: int
    attachments_with_phone: int
    sites_stats: List[SiteStats]
    sync_sites: Optional[int] = 0

    class Config:
        from_attributes = True


class AttachmentQuery(BaseModel):
    site_id: Optional[int] = None
    site_owner: Optional[str] = None
    site_state: Optional[int] = None
    text_content_search: Optional[str] = None
    ocr_content_search: Optional[str] = None
    has_id_card: Optional[bool] = None
    has_phone: Optional[bool] = None


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Frontend endpoints
@app.get("/", response_class=HTMLResponse)
def read_root():
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")


# API endpoints


@app.get("/api/sites", response_model=List[SiteResponse])
def get_sites(db: Session = Depends(get_db)):
    sites = db.query(Site).all()
    return sites


@app.get("/api/sites/{site_id}", response_model=SiteResponse)
def get_site(site_id: int, db: Session = Depends(get_db)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


class PaginatedAttachmentsResponse(BaseModel):
    items: List[AttachmentResponse]
    total: int

@app.get("/api/attachments", response_model=PaginatedAttachmentsResponse)
def get_attachments(
    site_id: Optional[int] = Query(None),
    site_owner: Optional[str] = Query(None),
    site_state: Optional[int] = Query(None),
    text_content_search: Optional[str] = Query(None),
    ocr_content_search: Optional[str] = Query(None),
    has_id_card: Optional[bool] = Query(None),
    has_phone: Optional[bool] = Query(None),
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = Query(None),  # Field to sort by
    sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$"),  # Sort direction
    db: Session = Depends(get_db)
):
    query = db.query(Attachment)

    # Filter by site - Attachment.site_id corresponds to Site.owner field
    # If both site_id and site_owner are provided, prioritize site_owner
    if site_owner is not None:
        query = query.filter(Attachment.site_id == site_owner)
    elif site_id is not None:
        # If only site_id is provided, we need to find the corresponding owner
        # Find the site by its database ID and get its owner
        site = db.query(Site).filter(Site.id == site_id).first()
        if site:
            query = query.filter(Attachment.site_id == site.owner)

    if text_content_search:
        query = query.filter(Attachment.text_content.contains(text_content_search))

    if ocr_content_search:
        query = query.filter(Attachment.ocr_content.contains(ocr_content_search))

    if has_id_card is not None:
        query = query.filter(Attachment.has_id_card == has_id_card)

    if has_phone is not None:
        query = query.filter(Attachment.has_phone == has_phone)

    # Join with Site table to filter by site state
    if site_state is not None:
        from sqlalchemy import and_
        query = query.join(Site, Attachment.site_id == Site.owner).filter(Site.state == site_state)

    # Apply sorting if specified
    from sqlalchemy import asc, desc
    if sort_by:
        # Map sort field to column (handle potential invalid field names)
        column_map = {
            'id': Attachment.id,
            'site_id': Attachment.site_id,
            'show_name': Attachment.show_name,
            'file_ext': Attachment.file_ext,
            'create_date': Attachment.create_date,
            'text_content': Attachment.text_content,
            'ocr_content': Attachment.ocr_content,
            'has_id_card': Attachment.has_id_card,
            'has_phone': Attachment.has_phone,
            'manual_verified_sensitive': Attachment.manual_verified_sensitive,
            'processed_datetime': Attachment.processed_datetime,
            'ocr_score': Attachment.ocr_score
        }

        if sort_by in column_map:
            if sort_order == "desc":
                query = query.order_by(desc(column_map[sort_by]))
            else:
                query = query.order_by(asc(column_map[sort_by]))

    # Get total count
    total = query.count()

    # Get paginated results
    attachments = query.offset(skip).limit(limit).all()

    return PaginatedAttachmentsResponse(items=attachments, total=total)


@app.get("/api/attachments/{attachment_id}", response_model=AttachmentResponse)
def get_attachment(attachment_id: int, db: Session = Depends(get_db)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return attachment


@app.post("/api/sync-sites")
def sync_sites(db: Session = Depends(get_db)):
    syncer = RemoteDBSync(db)
    try:
        syncer.sync_all_sites()
        return {"message": "Sites sync completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sites sync failed: {str(e)}")
    finally:
        syncer.close()

@app.post("/api/sync-attachments")
def sync_attachments(request: SyncRequest = None, db: Session = Depends(get_db)):
    syncer = RemoteDBSync(db)
    try:
        if request and request.site_owner:
            # Sync attachments for specific site
            syncer.sync_attachments_for_site(request.site_owner)
        else:
            # Sync all attachments
            syncer.sync_all_attachments()
        return {"message": "Attachments sync completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Attachments sync failed: {str(e)}")
    finally:
        syncer.close()

@app.post("/api/sync")
def sync_remote_data(request: SyncRequest = None, db: Session = Depends(get_db)):
    syncer = RemoteDBSync(db)
    try:
        # First sync all sites (always sync sites completely)
        syncer.sync_all_sites()

        # Then sync attachments (all or for specific site)
        if request and request.site_owner:
            syncer.sync_attachments_for_site(request.site_owner)
        else:
            syncer.sync_all_attachments()

        return {"message": "Full sync completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
    finally:
        syncer.close()


@app.post("/api/process-attachment/{attachment_id}")
def process_attachment(attachment_id: int, db: Session = Depends(get_db)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    try:
        # For now, we'll use an empty base URL - in a real system you'd determine the base URL properly
        process_attachment_file(attachment, db, base_url=settings.ATTACHMENT_DEFAULT_BASE_URL, detection_type="normal")
        return {"message": f"Attachment {attachment_id} processed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/api/process-attachment-ai/{attachment_id}")
def process_attachment_ai(attachment_id: int, db: Session = Depends(get_db)):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")

    try:
        # For now, we'll use an empty base URL - in a real system you'd determine the base URL properly
        process_attachment_file(attachment, db, base_url=settings.ATTACHMENT_DEFAULT_BASE_URL, detection_type="ai")
        return {"message": f"Attachment {attachment_id} processed with AI successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Processing failed: {str(e)}")


@app.post("/api/process-site/{site_owner}")
def process_site_attachments(site_owner: str, detection_type: str = "normal", db: Session = Depends(get_db)):
    attachments = db.query(Attachment).filter(Attachment.site_id == site_owner).all()

    processed_count = 0
    for attachment in attachments:
        try:
            if detection_type == "ai" and not settings.OPENAI_API_KEY:
                # Skip AI processing if API key is not configured
                process_attachment_file(attachment, db, base_url=settings.ATTACHMENT_DEFAULT_BASE_URL, detection_type="normal")
            else:
                process_attachment_file(attachment, db, base_url=settings.ATTACHMENT_DEFAULT_BASE_URL, detection_type=detection_type)
            processed_count += 1
        except Exception as e:
            print(f"Error processing attachment {attachment.id}: {str(e)}")
            continue

    return {"message": f"Processed {processed_count} attachments for site {site_owner}"}


@app.post("/api/detect-site/{site_owner}")
def detect_site_attachments(site_owner: str, detection_type: str = "normal", ws_id: str = None, db: Session = Depends(get_db)):
    if detection_type == "ai" and not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured for AI detection")

    # Check if ws_id is provided for progress updates
    if ws_id:
        # Register the operation as pending to be executed when WebSocket connects
        with operation_lock:
            pending_operations[ws_id] = {
                'type': 'detect',
                'params': {
                    'site_owner': site_owner,
                    'detection_type': detection_type
                }
            }
        # Return to allow client to establish WebSocket connection
        return {"message": "Detection will start when WebSocket connection is established", "site_owner": site_owner, "ws_id": ws_id}
    else:
        # Use the original detection without progress tracking
        attachments = db.query(Attachment).filter(Attachment.site_id == site_owner).all()

        processed_count = 0
        sensitive_count = 0

        for attachment in attachments:
            try:
                if detection_type == "ai":
                    process_attachment_file(attachment, db, base_url=settings.ATTACHMENT_DEFAULT_BASE_URL, detection_type="ai")
                else:
                    process_attachment_file(attachment, db, base_url=settings.ATTACHMENT_DEFAULT_BASE_URL, detection_type="normal")

                # Count attachments that were marked as containing sensitive info
                if attachment.has_id_card or attachment.has_phone:
                    sensitive_count += 1

                processed_count += 1
            except Exception as e:
                print(f"Error processing attachment {attachment.id}: {str(e)}")
                continue

        return {
            "message": f"Detected {processed_count} attachments for site {site_owner}, {sensitive_count} with sensitive info",
            "processed_count": processed_count,
            "sensitive_count": sensitive_count
        }


@app.post("/api/download-site/{site_owner}")
def download_site_attachments(site_owner: str, db: Session = Depends(get_db)):
    """
    Download all attachments for a site (without progress tracking).
    This is a synchronous operation that returns results when complete.
    """
    from download import download_site_attachments_simple
    return download_site_attachments_simple(site_owner, db)





@app.get("/api/stats", response_model=StatsResponse)
def get_statistics(db: Session = Depends(get_db)):
    total_sites = db.query(Site).count()
    total_attachments = db.query(Attachment).count()
    attachments_with_id_card = db.query(Attachment).filter(Attachment.has_id_card == True).count()
    attachments_with_phone = db.query(Attachment).filter(Attachment.has_phone == True).count()

    # Count sync sites (sites that have at least one attachment)
    sync_sites = db.query(Site.owner).join(Attachment, Site.owner == Attachment.site_id).distinct().count()

    # Get stats per site
    sites = db.query(Site).all()
    sites_stats = []
    for site in sites:
        site_attachments = db.query(Attachment).filter(Attachment.site_id == site.owner).count()
        site_attachments_with_id = db.query(Attachment).filter(
            Attachment.site_id == site.owner,
            Attachment.has_id_card == True
        ).count()
        site_attachments_with_phone = db.query(Attachment).filter(
            Attachment.site_id == site.owner,
            Attachment.has_phone == True
        ).count()

        sites_stats.append({
            "site_id": site.id,
            "site_name": site.name,
            "site_account": site.account,
            "site_domain": site.domain,
            "site_create_date": site.create_date,
            "total_attachments": site_attachments,
            "attachments_with_id_card": site_attachments_with_id,
            "attachments_with_phone": site_attachments_with_phone
        })

    # Sort sites by total attachments in descending order
    sites_stats.sort(key=lambda x: x["total_attachments"], reverse=True)

    return StatsResponse(
        total_sites=total_sites,
        total_attachments=total_attachments,
        attachments_with_id_card=attachments_with_id_card,
        attachments_with_phone=attachments_with_phone,
        sites_stats=sites_stats,
        sync_sites=sync_sites
    )


@app.get("/{full_path:path}")
def read_frontend(full_path: str, request: Request):
    from fastapi.responses import FileResponse
    import os
    # Serve index.html for any route that doesn't match an API endpoint
    # This enables client-side routing in the Vue frontend
    file_path = os.path.join("static", full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        # If the file exists in static directory, serve it directly
        return FileResponse(file_path)
    else:
        # For any other route, serve index.html (for Vue Router)
        return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)