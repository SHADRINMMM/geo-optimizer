"""
Email notification tasks.
"""
import asyncio
from app.worker import celery_app


@celery_app.task(name="app.tasks.notify.send_completion_email")
def send_completion_email(site_id: str, user_email: str):
    return asyncio.run(_send_completion(site_id, user_email))


@celery_app.task(name="app.tasks.notify.send_weekly_report")
def send_weekly_report(site_id: str, user_email: str):
    return asyncio.run(_send_weekly(site_id, user_email))


async def _send_completion(site_id: str, user_email: str):
    from app.services.monitor.metrics_builder import get_site_metrics
    metrics = await get_site_metrics(site_id)
    # TODO: integrate SendGrid
    print(f"[notify] Completion email to {user_email} for site {site_id}")
    return {"sent": True}


async def _send_weekly(site_id: str, user_email: str):
    from app.services.monitor.metrics_builder import get_full_report
    report = await get_full_report(site_id)
    # TODO: integrate SendGrid with HTML template
    print(f"[notify] Weekly report to {user_email} for site {site_id}")
    return {"sent": True}
