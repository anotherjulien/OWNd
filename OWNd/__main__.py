import time
import logging
import asyncio
import sys

from connection import OWNConnection
from message import *

async def main(connection: OWNConnection):
    """ Package entry point! """

    await connection.connect()
    while True:
        message = await connection.get_next()
        if message:
            logger.debug("Received: {}".format(message))
            if message.is_event():
                print(message.human_readable_log)

if __name__ == "__main__":

    if len(sys.argv) > 1:
        address = sys.argv[1]
        port = sys.argv[2]
        password = sys.argv[3]

    # create logger with 'OWNd'
    logger = logging.getLogger('OWNd')
    logger.setLevel(logging.DEBUG)
    # get AsyncIO logger
    #aio_logger = logging.getLogger('asyncio')
    #aio_logger.setLevel(logging.DEBUG)
    # create console handler which logs even debug messages
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(ch)
    #aio_logger.addHandler(ch)

    connection = OWNConnection(logger, address, port, password)
    
    main_task = asyncio.ensure_future(main(connection))
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    try:
        logger.info("Starting OWNd")
        loop.run_forever()
        #connection.send(OWNLightingCommand.switch_on(32))
    except KeyboardInterrupt:
        print("Stoping OWNd.")
        main_task.cancel()
        loop.run_until_complete(connection.close())
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.stop()
        loop.close()
        exit()
    finally:
        print('OWNd stopped.')