"""
Scheduler Module
Schedule daily video generation and upload
"""
import logging
import schedule
import time
from datetime import datetime
from main import VideoAutomation, setup_logging

logger = setup_logging()

def scheduled_job():
    """Job to run daily"""
    try:
        logger.info(f"\n{'='*70}")
        logger.info(f"SCHEDULED JOB TRIGGERED AT {datetime.now()}")
        logger.info(f"{'='*70}\n")
        
        automation = VideoAutomation()
        automation.run_daily_job()
        
    except Exception as e:
        logger.error(f"Error in scheduled job: {e}", exc_info=True)

def run_scheduler():
    """Run the scheduler"""
    from config import Config
    
    # Schedule daily job
    schedule_time = Config.DAILY_RUN_TIME  # e.g., "08:00"
    schedule.every().day.at(schedule_time).do(scheduled_job)
    
    logger.info(f"Scheduler started - Daily job scheduled at {schedule_time}")
    logger.info("Press Ctrl+C to stop the scheduler\n")
    
    # Run immediately on start (optional)
    # scheduled_job()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        run_scheduler()
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user")
