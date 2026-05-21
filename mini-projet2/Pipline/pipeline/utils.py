import os
import logging
from pathlib import Path

# Setup Logger
def get_logger(name="mexora_pipeline"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        fh = logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

DATA_LAKE_ROOT = os.path.abspath("data_lake")
REFERENTIAL_PATH = os.path.abspath("referentiel_competences_it.json")
COMPANIES_PATH = os.path.abspath("entreprises_it_maroc.csv")
