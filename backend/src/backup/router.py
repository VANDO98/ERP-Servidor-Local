
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import List
import os
from src.auth.security import get_current_user
from src.backup import service as backup_service

router = APIRouter(prefix="/api/backups", tags=["Backup"])

@router.post("/create")
def create_backup(current_user: dict = Depends(get_current_user)):
    """Trigger a manual database backup"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can perform backups")
        
    success, result = backup_service.create_backup()
    if success:
        # Also run cleanup
        backup_service.cleanup_old_backups()
        return {"status": "success", "filename": result}
    else:
        raise HTTPException(status_code=500, detail=f"Backup failed: {result}")

@router.get("")
def get_backups(current_user: dict = Depends(get_current_user)):
    """List available backups"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")
    return backup_service.list_backups()

@router.get("/download/{filename}")
def download_backup(filename: str, current_user: dict = Depends(get_current_user)):
    """Download a specific backup file"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")
        
    path = backup_service.get_backup_path(filename)
    if not path:
        raise HTTPException(status_code=404, detail="Backup file not found")
        
    return FileResponse(path, filename=filename, media_type='application/x-sqlite3')
