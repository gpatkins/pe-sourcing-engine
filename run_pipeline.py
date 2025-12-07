from __future__ import annotations

import argparse
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path

from etl.discover.google_places import main as discover_main
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
# Step wrappers
# ---------------------------------------------------------
def run_discover():
    """
    Run the discovery step only (Google Places → companies table).
    """
    logger.info("BEGIN step=discover")
    start = datetime.utcnow()
    try:
        discover_main()
        duration = datetime.utcnow() - start
        logger.info("END step=discover status=success duration=%s", duration)
    except Exception as exc:  # noqa: BLE001
        duration = datetime.utcnow() - start
        logger.exception("END step=discover status=error duration=%s error=%s", duration, exc)
        raise


def run_enrich():
    """
    Run the enrichment step only (enrich_companies.py).
    """
    logger.info("BEGIN step=enrich")
    start = datetime.utcnow()
    try:
        enrich_main()
        duration = datetime.utcnow() - start
        logger.info("END step=enrich status=success duration=%s", duration)
    except Exception as exc:  # noqa: BLE001
        duration = datetime.utcnow() - start
        logger.exception("END step=enrich status=error duration=%s error=%s", duration, exc)
        raise


def run_score():
    """
    Run the scoring step only (calculate_scores.py).
    """
    logger.info("BEGIN step=score")
    start = datetime.utcnow()
    try:
        score_main()
        duration = datetime.utcnow() - start
        logger.info("END step=score status=success duration=%s", duration)
    except Exception as exc:  # noqa: BLE001
        duration = datetime.utcnow() - start
        logger.exception("END step=score status=error duration=%s error=%s", duration, exc)
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


if __name__ == "__main__":
    main()
