import time
import logging
import asyncio
import argparse

from OWNd.connection import OWNConnection
from OWNd.message import *

async def main(connection: OWNConnection):
    """ Package entry point! """

    await connection.connect()
    while True:
        message = await connection.get_next()
        if message:
            logger.debug("Received: {}".format(message))
            if message.is_event():
                logger.info(message.human_readable_log)

async def office_on(connection: OWNConnection):
    await asyncio.sleep(1)
    await connection.send(OWNLightingCommand.switch_on(32))

async def office_off(connection: OWNConnection):
    await asyncio.sleep(2)
    await connection.send(OWNLightingCommand.switch_off(32))

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", type=str, help="IP address of the OpenWebNet gateway")
    parser.add_argument("-p", "--port", type=int, help="TCP port to connectect the gateway, default is 20000")
    parser.add_argument("-P", "--password", type=int, help="Numeric password for the OpenWebNet connection, default is 12345 (HMAC passwords are not supported)")
    parser.add_argument("-v", "--verbose", type=int, help="Change output verbosity [0 = WARNING; 1 = INFO (default); 2 = DEBUG]")
    args = parser.parse_args()

    # create logger with 'OWNd'
    logger = logging.getLogger('OWNd')
    logger.setLevel(logging.DEBUG)

    # create console handler which logs even debug messages
    log_stream_handler = logging.StreamHandler()

    if args.verbose == 2:
        log_stream_handler.setLevel(logging.DEBUG)
    elif args.verbose == 0:
        log_stream_handler.setLevel(logging.WARNING)
    else:
        log_stream_handler.setLevel(logging.INFO)
    
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_stream_handler.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(log_stream_handler)

    if args.address is None:
        logger.critical("Please provide an IP address!")
        exit()
    else:
        address = args.address
    
    if args.port is None:
        logger.warning("Port was not provided, using default: 20000.")
        port = 20000
    else:
        port = args.port
    
    if args.password is None:
        logger.warning("No password was provided, default will be used only if required.")
        password = 12345
    else:
        password = args.password

    connection = OWNConnection(logger, address, port, password)
    
    main_task = asyncio.ensure_future(main(connection))
    
    switch_on_task = asyncio.ensure_future(office_on(connection))
    switch_off_task = asyncio.ensure_future(office_off(connection))

    loop = asyncio.get_event_loop()
    #loop.set_debug(True)

    try:
        logger.info("Starting OWNd.")
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Stoping OWNd.")
        main_task.cancel()
        loop.run_until_complete(connection.close())
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.stop()
        loop.close()
        exit()
    finally:
        logger.info('OWNd stopped.')