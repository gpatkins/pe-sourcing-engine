from __future__ import annotations

import argparse
import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from etl.discover.google_places import run_discovery

from enrich_companies import main as enrich_main
from etl.score.calculate_scores import main as score_main

# ---------------------------------------------------------
# Logging setup (console + file)
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

log_file = LOGS_DIR / "pipeline.log"

logger = logging.getLogger("pipeline")
logger.setLevel(logging.INFO)

# Avoid adding handlers multiple times (e.g. in reloads)
if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


# ---------------------------------------------------------
# Progress tracking (v5.2)
# ---------------------------------------------------------
PROGRESS_FILE = BASE_DIR / "pipeline_progress.json"

def update_progress(
    stage: str,
    status: str,
    current: int = 0,
    total: int = 0,
    message: str = ""
):
    """
    Update pipeline progress for the UI.

    Args:
        stage: "discover", "enrich", "score", or "idle"
        status: "running", "complete", "error"
        current: Current item count
        total: Total item count
        message: Status message
    """
    progress = {
        "stage": stage,
        "status": status,
        "current": current,
        "total": total,
        "message": message,
        "updated_at": datetime.utcnow().isoformat()
    }

    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump(progress, f)
    except Exception as e:
        logger.warning(f"Failed to update progress: {e}")


def clear_progress():
    """Clear progress (set to idle)."""
    update_progress("idle", "idle", 0, 0, "System idle")


# ---------------------------------------------------------
# Step wrappers
# ---------------------------------------------------------
def run_discover(user_id: Optional[int] = None):
    """
    Run the discovery step only (Google Places → companies table).
    
    Args:
        user_id: User ID to assign discovered companies to. If None, uses admin.
    """
    logger.info("BEGIN step=discover user_id=%s", user_id)
    start = datetime.utcnow()

    # Update progress
    update_progress("discover", "running", 0, 0, "Starting discovery...")

    try:
        run_discovery(user_id)
        duration = datetime.utcnow() - start
        duration_sec = int(duration.total_seconds())
        logger.info("END step=discover status=success duration=%s", duration)
        update_progress("discover", "complete", 0, 0, f"Discovery complete ({duration_sec}s)")
    except Exception as exc:  # noqa: BLE001
        duration = datetime.utcnow() - start
        logger.exception("END step=discover status=error duration=%s error=%s", duration, exc)
        update_progress("discover", "error", 0, 0, f"Discovery failed: {str(exc)[:100]}")
        raise


def run_enrich():
    """
    Run the enrichment step only (enrich_companies.py).
    """
    logger.info("BEGIN step=enrich")
    start = datetime.utcnow()

    # Update progress
    update_progress("enrich", "running", 0, 0, "Starting enrichment...")

    try:
        enrich_main()
        duration = datetime.utcnow() - start
        duration_sec = int(duration.total_seconds())
        logger.info("END step=enrich status=success duration=%s", duration)
        update_progress("enrich", "complete", 0, 0, f"Enrichment complete ({duration_sec}s)")
    except Exception as exc:  # noqa: BLE001
        duration = datetime.utcnow() - start
        logger.exception("END step=enrich status=error duration=%s error=%s", duration, exc)
        update_progress("enrich", "error", 0, 0, f"Enrichment failed: {str(exc)[:100]}")
        raise


def run_score():
    """
    Run the scoring step only (calculate_scores.py).
    """
    logger.info("BEGIN step=score")
    start = datetime.utcnow()

    # Update progress
    update_progress("score", "running", 0, 0, "Starting scoring...")

    try:
        score_main()
        duration = datetime.utcnow() - start
        duration_sec = int(duration.total_seconds())
        logger.info("END step=score status=success duration=%s", duration)
        update_progress("score", "complete", 0, 0, f"Scoring complete ({duration_sec}s)")
    except Exception as exc:  # noqa: BLE001
        duration = datetime.utcnow() - start
        logger.exception("END step=score status=error duration=%s error=%s", duration, exc)
        update_progress("score", "error", 0, 0, f"Scoring failed: {str(exc)[:100]}")
        raise


# ---------------------------------------------------------
# Main pipeline runner
# ---------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(
        description="PE Sourcing Engine pipeline runner"
    )
    parser.add_argument(
        "step",
        choices=["discover", "enrich", "score", "full"],
        help=(
            "Which step to run:\n"
            "  discover = run discovery only\n"
            "  enrich   = run enrichment only\n"
            "  score    = run scoring only\n"
            "  full     = discover → enrich → score"
        ),
    )

    args = parser.parse_args(argv)
    step = args.step

    logger.info("Pipeline invoked with step=%s", step)
    overall_start = datetime.utcnow()

    if step == "discover":
        run_discover()
    elif step == "enrich":
        run_enrich()
    elif step == "score":
        run_score()
    elif step == "full":
        run_discover()
        run_enrich()
        run_score()
    else:
        logger.error("Unknown step: %s", step)
        sys.exit(1)

    duration = datetime.utcnow() - overall_start
    logger.info("Pipeline step '%s' finished in %s", step, duration)

    # Clear progress back to idle (v5.2)
    clear_progress()


if __name__ == "__main__":
    main()
