from apscheduler.schedulers.background import BackgroundScheduler
from config import SCAN_INTERVAL_MINUTES

scheduler = BackgroundScheduler()

def start_scheduler(scan_function):
    if not scheduler.running:
        scheduler.add_job(
            scan_function,
            "interval",
            minutes=SCAN_INTERVAL_MINUTES,
            id="jussend_scan",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.start()

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)

def is_running():
    return scheduler.running
