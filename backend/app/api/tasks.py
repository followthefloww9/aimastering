from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from ..celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a background task"""
    try:
        result = AsyncResult(task_id, app=celery_app)
        
        if result.state == 'PENDING':
            response = {
                'task_id': task_id,
                'state': result.state,
                'status': 'Task is waiting to be processed'
            }
        elif result.state == 'PROGRESS':
            response = {
                'task_id': task_id,
                'state': result.state,
                'progress': result.info.get('progress', 0),
                'status': result.info.get('status', 'Processing...')
            }
        elif result.state == 'SUCCESS':
            response = {
                'task_id': task_id,
                'state': result.state,
                'result': result.result,
                'status': 'Task completed successfully'
            }
        elif result.state == 'FAILURE':
            response = {
                'task_id': task_id,
                'state': result.state,
                'error': str(result.info),
                'status': 'Task failed'
            }
        else:
            response = {
                'task_id': task_id,
                'state': result.state,
                'status': f'Unknown state: {result.state}'
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a background task"""
    try:
        celery_app.control.revoke(task_id, terminate=True)
        return {
            'task_id': task_id,
            'status': 'Task cancelled'
        }
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_active_tasks():
    """Get list of active tasks"""
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        if not active_tasks:
            return {'active_tasks': []}
        
        # Flatten the tasks from all workers
        all_tasks = []
        for worker, tasks in active_tasks.items():
            for task in tasks:
                all_tasks.append({
                    'task_id': task['id'],
                    'name': task['name'],
                    'worker': worker,
                    'args': task.get('args', []),
                    'kwargs': task.get('kwargs', {})
                })
        
        return {'active_tasks': all_tasks}
        
    except Exception as e:
        logger.error(f"Error getting active tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
