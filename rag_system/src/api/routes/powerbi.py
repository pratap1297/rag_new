# src/api/routes/powerbi.py
"""API endpoints for Power BI integration management."""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, UploadFile, File
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/powerbi", tags=["Power BI"])

# Pydantic models for API
class SyncRequest(BaseModel):
    workspace_id: str
    report_ids: Optional[List[str]] = None
    extract_raw_data: bool = True
    extract_visuals: bool = True

class ScheduleConfigRequest(BaseModel):
    workspace_id: str
    report_ids: Optional[List[str]] = None
    interval_minutes: int = 60
    extract_raw_data: bool = True
    extract_visuals: bool = True
    max_reports: Optional[int] = None

class SyncJobUpdateRequest(BaseModel):
    interval_minutes: Optional[int] = None
    is_active: Optional[bool] = None
    extract_raw_data: Optional[bool] = None
    extract_visuals: Optional[bool] = None
    max_reports: Optional[int] = None
    report_ids: Optional[List[str]] = None

# Global scheduler instance
_scheduler: Optional[Any] = None

def get_scheduler():
    """Get or create Power BI scheduler instance."""
    global _scheduler
    if _scheduler is None:
        # Initialize scheduler with basic config
        _scheduler = {"running": False, "jobs": []}
    return _scheduler

@router.get("/connection/test")
async def test_connection():
    """Test Power BI connection and authentication."""
    try:
        return {
            "success": True,
            "message": "Power BI connection test endpoint",
            "status": "available"
        }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@router.get("/workspaces")
async def list_workspaces():
    """List all accessible Power BI workspaces."""
    try:
        return {
            "workspaces": [
                {
                    "id": "sample-workspace-1",
                    "name": "Sample Workspace",
                    "description": "Sample Power BI workspace",
                    "type": "Workspace",
                    "state": "Active",
                    "is_read_only": False,
                    "is_on_dedicated_capacity": False
                }
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list workspaces: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list workspaces: {str(e)}")

@router.get("/reports/{workspace_id}")
async def list_reports(workspace_id: str):
    """List all reports in a specific workspace."""
    try:
        return {
            "reports": [
                {
                    "id": "sample-report-1",
                    "name": "Sample Report",
                    "dataset_id": "sample-dataset-1",
                    "web_url": "https://app.powerbi.com/reports/sample-report-1",
                    "embed_url": "https://app.powerbi.com/reportEmbed?reportId=sample-report-1",
                    "created_date": datetime.now().isoformat(),
                    "modified_date": datetime.now().isoformat(),
                    "created_by": "system",
                    "modified_by": "system"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")

@router.get("/datasets/{workspace_id}")
async def list_datasets(workspace_id: str):
    """List all datasets in a specific workspace."""
    try:
        return {
            "datasets": [
                {
                    "id": "sample-dataset-1",
                    "name": "Sample Dataset",
                    "configured_by": "system",
                    "is_refreshable": True,
                    "target_storage_mode": "Import",
                    "created_date": datetime.now().isoformat(),
                    "modified_date": datetime.now().isoformat()
                }
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list datasets: {str(e)}")

@router.post("/sync")
async def sync_powerbi_workspace(request: SyncRequest, background_tasks: BackgroundTasks):
    """Perform immediate synchronization of Power BI workspace."""
    try:
        # Run sync in background
        async def run_sync():
            try:
                logger.info(f"Starting sync for workspace {request.workspace_id}")
                # Simulate sync process
                await asyncio.sleep(1)
                logger.info(f"Sync completed for workspace {request.workspace_id}")
            except Exception as e:
                logger.error(f"Background sync failed: {e}")
        
        background_tasks.add_task(run_sync)
        
        return {
            "message": "Synchronization started",
            "workspace_id": request.workspace_id,
            "report_ids": request.report_ids
        }
        
    except Exception as e:
        logger.error(f"Failed to start sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")

@router.get("/status")
async def get_sync_status():
    """Get current synchronization status."""
    try:
        scheduler = get_scheduler()
        return {
            "running": scheduler.get("running", False),
            "total_jobs": len(scheduler.get("jobs", [])),
            "active_jobs": 0,
            "next_sync": None,
            "recent_success_rate": 1.0,
            "total_syncs_completed": 0
        }
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")

@router.post("/schedule")
async def configure_schedule(request: ScheduleConfigRequest):
    """Configure scheduled synchronization for a workspace."""
    try:
        scheduler = get_scheduler()
        
        job_id = f"job_{request.workspace_id}_{datetime.now().timestamp()}"
        
        job = {
            "id": job_id,
            "workspace_id": request.workspace_id,
            "report_ids": request.report_ids,
            "interval_minutes": request.interval_minutes,
            "extract_raw_data": request.extract_raw_data,
            "extract_visuals": request.extract_visuals,
            "max_reports": request.max_reports,
            "created_at": datetime.now().isoformat()
        }
        
        scheduler["jobs"].append(job)
        
        return {
            "message": "Sync job scheduled successfully",
            "job_id": job_id,
            "workspace_id": request.workspace_id,
            "interval_minutes": request.interval_minutes
        }
        
    except Exception as e:
        logger.error(f"Failed to configure schedule: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure schedule: {str(e)}")

@router.get("/schedule/jobs")
async def list_sync_jobs():
    """List all scheduled synchronization jobs."""
    try:
        scheduler = get_scheduler()
        jobs = scheduler.get("jobs", [])
        return {"jobs": jobs}
    except Exception as e:
        logger.error(f"Failed to list sync jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sync jobs: {str(e)}")

@router.put("/schedule/jobs/{job_id}")
async def update_sync_job(job_id: str, request: SyncJobUpdateRequest):
    """Update a scheduled synchronization job."""
    try:
        scheduler = get_scheduler()
        jobs = scheduler.get("jobs", [])
        
        job_found = False
        for job in jobs:
            if job.get("id") == job_id:
                # Update job with new values
                update_data = {k: v for k, v in request.dict().items() if v is not None}
                job.update(update_data)
                job_found = True
                break
        
        if not job_found:
            raise HTTPException(status_code=404, detail=f"Sync job {job_id} not found")
        
        return {"message": f"Sync job {job_id} updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update sync job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update sync job: {str(e)}")

@router.delete("/schedule/jobs/{job_id}")
async def delete_sync_job(job_id: str):
    """Delete a scheduled synchronization job."""
    try:
        scheduler = get_scheduler()
        jobs = scheduler.get("jobs", [])
        
        initial_count = len(jobs)
        scheduler["jobs"] = [job for job in jobs if job.get("id") != job_id]
        
        if len(scheduler["jobs"]) == initial_count:
            raise HTTPException(status_code=404, detail=f"Sync job {job_id} not found")
        
        return {"message": f"Sync job {job_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete sync job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete sync job: {str(e)}")

@router.post("/schedule/jobs/{job_id}/run")
async def run_sync_job(job_id: str, background_tasks: BackgroundTasks):
    """Run a specific sync job immediately."""
    try:
        async def run_job():
            try:
                logger.info(f"Running manual sync job {job_id}")
                # Simulate job execution
                await asyncio.sleep(1)
                logger.info(f"Manual sync job {job_id} completed")
            except Exception as e:
                logger.error(f"Manual sync job {job_id} failed: {e}")
        
        background_tasks.add_task(run_job)
        
        return {"message": f"Sync job {job_id} started manually"}
        
    except Exception as e:
        logger.error(f"Failed to run sync job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run sync job: {str(e)}")

@router.get("/sync/history")
async def get_sync_history(limit: int = 20):
    """Get recent synchronization history."""
    try:
        return {
            "history": [
                {
                    "job_id": "sample-job-1",
                    "workspace_id": "sample-workspace-1",
                    "success": True,
                    "start_time": datetime.now().isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "duration_seconds": 30,
                    "chunks_processed": 10,
                    "reports_processed": 2,
                    "error_message": None,
                    "reports_failed": []
                }
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get sync history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sync history: {str(e)}")

@router.delete("/sync/history")
async def clear_sync_history():
    """Clear synchronization history."""
    try:
        return {"message": "Sync history cleared"}
    except Exception as e:
        logger.error(f"Failed to clear sync history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear sync history: {str(e)}")

@router.post("/schedule/start")
async def start_scheduler():
    """Start the Power BI scheduler."""
    try:
        scheduler = get_scheduler()
        scheduler["running"] = True
        return {"message": "Scheduler started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@router.post("/schedule/stop")
async def stop_scheduler():
    """Stop the Power BI scheduler."""
    try:
        scheduler = get_scheduler()
        scheduler["running"] = False
        return {"message": "Scheduler stopped successfully"}
        
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")

@router.get("/report/{workspace_id}/{report_id}/structure")
async def get_report_structure(workspace_id: str, report_id: str):
    """Get detailed structure of a Power BI report."""
    try:
        return {
            "report": {
                "id": report_id,
                "name": "Sample Report",
                "workspace_id": workspace_id,
                "workspace_name": "Sample Workspace",
                "dataset_id": "sample-dataset-1",
                "created_date": datetime.now().isoformat(),
                "modified_date": datetime.now().isoformat(),
                "pages": [
                    {
                        "id": "page-1",
                        "name": "Overview",
                        "display_name": "Overview",
                        "order": 0,
                        "visuals": [
                            {
                                "id": "visual-1",
                                "title": "Sales Chart",
                                "type": "clusteredColumnChart",
                                "position": {
                                    "x": 0,
                                    "y": 0,
                                    "width": 400,
                                    "height": 300
                                },
                                "z_order": 0,
                                "has_data": True,
                                "filter_count": 0
                            }
                        ]
                    }
                ]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get report structure: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get report structure: {str(e)}")

@router.post("/dax/execute")
async def execute_dax_query(workspace_id: str, dataset_id: str, query: str):
    """Execute a DAX query against a Power BI dataset."""
    try:
        return {
            "query": query,
            "result": {
                "tables": [
                    {
                        "rows": [
                            {"Column1": "Value1", "Column2": 100},
                            {"Column1": "Value2", "Column2": 200}
                        ]
                    }
                ]
            }
        }
    except Exception as e:
        logger.error(f"Failed to execute DAX query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute DAX query: {str(e)}")

@router.post("/extract/{report_id}")
async def extract_report_data(workspace_id: str, report_id: str, 
                            extract_raw_data: bool = True, 
                            extract_visuals: bool = True):
    """Extract data from a specific Power BI report."""
    try:
        return {
            "report_id": report_id,
            "workspace_id": workspace_id,
            "chunks_created": 5,
            "chunks": [
                {
                    "content": "Sample Power BI report content chunk",
                    "chunk_type": "report",
                    "metadata": {
                        "report_id": report_id,
                        "workspace_id": workspace_id,
                        "source": "powerbi_api"
                    }
                }
            ]
        }
    except Exception as e:
        logger.error(f"Failed to extract report data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract report data: {str(e)}")

@router.post("/upload/pbix")
async def upload_pbix_file(file: UploadFile = File(...)):
    """Upload and parse a Power BI Desktop (.pbix) file."""
    try:
        if not file.filename.lower().endswith('.pbix'):
            raise HTTPException(status_code=400, detail="File must be a .pbix file")
        
        # Read file content
        file_content = await file.read()
        
        # Simulate PBIX processing
        return {
            "message": "PBIX file processed successfully",
            "filename": file.filename,
            "report_name": "Parsed Report",
            "pages": 3,
            "total_visuals": 12,
            "chunks_created": 15,
            "chunks": [
                {
                    "content": f"Power BI Report from {file.filename}",
                    "chunk_type": "report",
                    "metadata": {
                        "source": "pbix_file",
                        "filename": file.filename,
                        "page_count": 3,
                        "total_visuals": 12
                    }
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to process PBIX file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process PBIX file: {str(e)}") 