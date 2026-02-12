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
    time.sleep(5)
    # Run advanced features pipeline (bk toggle via USE_BK_FEATURES=1)
    try:
        use_bk = os.getenv("USE_BK_FEATURES", "0") == "1"
        if use_bk:
            from bk.pipeline_features_master import run_all_features as run_all_features_bk
            run_all_features_bk()
        else:
            from pipeline_features_master import run_all_features as run_all_features_main
            run_all_features_main()
    except Exception as e:
        log.error(f"[SCHED] Error running features pipeline: {e}")
    # Optional paper trader (USE_PAPER_TRADER=1)
    try:
        use_paper = os.getenv("USE_PAPER_TRADER", "0") == "1"
        if use_paper:
            from bk.paper_trader import run as run_paper
            res = run_paper()
            log.info(f"[SCHED] Paper trader opened={len(res.get('opened', []))} closed={len(res.get('closed', []))}")
    except Exception as e:
        log.error(f"[SCHED] Error running paper trader: {e}")
    log.info("[SCHED] Hourly pipeline complete")


if __name__ == "__main__":
    scheduler.start()
