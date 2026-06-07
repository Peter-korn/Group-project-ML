import logging
import sys
from pathlib import Path


def setup_logging():
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/scraping.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


setup_logging()
