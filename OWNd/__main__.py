import argparse
import asyncio
import logging
import time

from .connection import (OWNEventSession, OWNGateway)


async def main(arguments: dict, connection: OWNEventSession) -> None:
    """ Package entry point! """
    
    address = arguments["address"] if "address" in arguments and isinstance(arguments["address"], str) else None
    port = arguments["port"] if "port" in arguments and isinstance(arguments["port"], int) else None
    password = arguments["password"] if "password" in arguments and isinstance(arguments["password"], str) else None
    serialNumber = arguments["serialNumber"] if "serialNumber" in arguments and isinstance(arguments["serialNumber"], str) else None
    logger = arguments["logger"] if "logger" in arguments and isinstance(arguments["logger"], logging.Logger) else None

    gateway = await OWNGateway.build_from_discovery_info({"address": address, "port": port, "password": password, "serialNumber": serialNumber})
    connection.gateway = gateway
    
    if logger is not None:
        connection.logger = logger

    await connection.connect()

    while True:
        message = await connection.get_next()
        if message:
            logger.debug("Received: %s", message)
            if message.is_event:
                logger.info(message.human_readable_log)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", type=str, help="IP address of the OpenWebNet gateway")
    parser.add_argument("-p", "--port", type=int, help="TCP port to connectect the gateway, default is 20000")
    parser.add_argument("-P", "--password", type=str, help="Numeric password for the OpenWebNet connection, default is 12345")
    parser.add_argument("-m", "--mac", type=str, help="MAC address of the gateway (to be used as ID, if  not found via SSDP)")
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

    event_session = OWNEventSession()
    arguments = {"address": args.address, "port": args.port, "password": args.password, "serialNumber": args.mac, "logger": logger}

    loop = asyncio.get_event_loop()
    main_task = asyncio.ensure_future(main(arguments, event_session))
    #loop.set_debug(True)

    try:
        logger.info("Starting OWNd.")
        loop.run_forever()
        #asyncio.run(main(arguments))
    except KeyboardInterrupt:
        logger.info("Stoping OWNd.")
        main_task.cancel()
        loop.run_until_complete(event_session.close())
        loop.stop()
        loop.close()
    finally:
        logger.info('OWNd stopped.')