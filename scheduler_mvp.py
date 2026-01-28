import time
import os
from dotenv import load_dotenv
load_dotenv()
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from ingestion_market_mvp import run_ingestion_cycle
from narrative_stream_openai_v4 import run_narrative_stream
from regimes_mvp import compute_features_and_classify_regimes

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("scheduler")

scheduler = BlockingScheduler()


@scheduler.scheduled_job("interval", minutes=60)
def hourly_pipeline():
    log.info("[SCHED] Starting hourly pipeline")
    run_ingestion_cycle()
    time.sleep(10)
    run_narrative_stream()
    time.sleep(10)
    compute_features_and_classify_regimes()
    log.info("[SCHED] Hourly pipeline complete")


if __name__ == "__main__":
    scheduler.start()
