import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def info(message: str):
    logger.info(message)

def error(message: str):
    logger.error(message)
