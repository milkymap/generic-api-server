import logging 

logging.basicConfig(
    format='%(asctime)s - %(filename)s - %(levelname)s - %(lineno)03d - %(message)s',
    level=logging.DEBUG
)

logging.getLogger('httpx').setLevel(logging.INFO)
logger = logging.getLogger(name='api-server')

if __name__ == '__main__':
    logger.info('log was initialized')