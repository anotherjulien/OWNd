""" OWNd entry point when running it directly from CLI
(as opposed to imported into another project)
"""
import argparse
import asyncio
import logging

from .exceptions import (
    OWNGatewayUnreachableError,
    OWNConnectionRefusedError,
    OWNAuthenticationError,
    OWNNACKException,
)
from .connection import OWNEventSession, OWNCommandSession, OWNGateway
from .message import OWNMessage, OWNEvent


async def main(arguments: dict, connection: OWNEventSession) -> None:
    """Package entry point!"""

    address = (
        arguments["address"]
        if "address" in arguments and isinstance(arguments["address"], str)
        else None
    )
    port = (
        arguments["port"]
        if "port" in arguments and isinstance(arguments["port"], int)
        else None
    )
    password = (
        arguments["password"]
        if "password" in arguments and isinstance(arguments["password"], str)
        else None
    )
    serial_number = (
        arguments["serialNumber"]
        if "serialNumber" in arguments and isinstance(arguments["serialNumber"], str)
        else None
    )
    logger = (
        arguments["logger"]
        if "logger" in arguments and isinstance(arguments["logger"], logging.Logger)
        else None
    )
    logging_mode = arguments["logging_mode"] if "logging_mode" in arguments else False

    gateway = await OWNGateway.build_from_discovery_info(
        {
            "address": address,
            "port": port,
            "password": password,
            "serialNumber": serial_number,
        }
    )
    connection.gateway = gateway

    who_filter_polarity = (
        arguments["who_filter_polarity"] if "who_filter_polarity" in arguments else 0
    )
    who_filter = arguments["who_filter"] if "who_filter" in arguments else []

    where_filter_polarity = (
        arguments["where_filter_polarity"]
        if "where_filter_polarity" in arguments
        else 0
    )
    where_filter = arguments["where_filter"] if "where_filter" in arguments else []

    dimension_filter_polarity = (
        arguments["dimension_filter_polarity"]
        if "dimension_filter_polarity" in arguments
        else 0
    )
    dimension_filter = (
        arguments["dimension_filter"] if "dimension_filter" in arguments else []
    )

    print(f"Filtering {'in' if who_filter_polarity >= 0 else 'out'} WHO {who_filter}")
    print(
        f"Filtering {'in' if where_filter_polarity >= 0 else 'out'} WHERE {where_filter}"
    )

    if logger is not None:
        connection.logger = logger

    await connection.connect()

    while True:
        message = await connection.get_next()
        if (
            message
            and (
                (
                    (who_filter_polarity > 0 and str(message.who) in who_filter)
                    or (who_filter_polarity < 0 and str(message.who) not in who_filter)
                    or who_filter_polarity == 0
                )
                and (
                    (where_filter_polarity > 0 and str(message.where) in where_filter)
                    or (
                        where_filter_polarity < 0
                        and str(message.where) not in where_filter
                    )
                    or where_filter_polarity == 0
                )
                and (
                    (
                        dimension_filter_polarity > 0
                        and str(message.dimension) in dimension_filter
                    )
                    or (
                        dimension_filter_polarity < 0
                        and str(message.dimension) not in dimension_filter
                    )
                    or dimension_filter_polarity == 0
                )
            )
            or (
                who_filter_polarity == 0
                and where_filter_polarity == 0
                and dimension_filter_polarity == 0
            )
        ):
            if not logging_mode:
                logger.debug("Received: %s", message)
                if message.is_event:
                    logger.info(message.human_readable_log)
            else:
                logger.warning(message)


async def send(arguments: dict, connection: OWNCommandSession) -> None:
    """Package entry point!"""

    address = (
        arguments["address"]
        if "address" in arguments and isinstance(arguments["address"], str)
        else None
    )
    port = (
        arguments["port"]
        if "port" in arguments and isinstance(arguments["port"], int)
        else None
    )
    password = (
        arguments["password"]
        if "password" in arguments and isinstance(arguments["password"], str)
        else None
    )
    serial_number = (
        arguments["serialNumber"]
        if "serialNumber" in arguments and isinstance(arguments["serialNumber"], str)
        else None
    )
    logger = (
        arguments["logger"]
        if "logger" in arguments and isinstance(arguments["logger"], logging.Logger)
        else None
    )
    messages = arguments["messages"] if "messages" in arguments else []

    gateway = await OWNGateway.build_from_discovery_info(
        {
            "address": address,
            "port": port,
            "password": password,
            "serialNumber": serial_number,
        }
    )
    connection.gateway = gateway

    if logger is not None:
        connection.logger = logger

    await connection.connect()

    for message in messages:
        try:
            await connection.send(message, logging_mode=True)
        except OWNNACKException:
            pass


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a", "--address", type=str, help="IP address of the OpenWebNet gateway"
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="TCP port to connectect the gateway, default is 20000",
    )
    parser.add_argument(
        "-P",
        "--password",
        type=str,
        help="Password for the OpenWebNet connection, default is 12345",
    )
    parser.add_argument(
        "-m",
        "--mac",
        type=str,
        help="MAC address of the gateway (to be used as ID, if  not found via SSDP)",
    )
    parser.add_argument(
        "-s",
        "--send",
        nargs="+",
        type=str,
        help="Correctly formated OpenWebNet messages to be sent.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        type=int,
        help="Change output verbosity [0 = WARNING; 1 = INFO (default); 2 = DEBUG]",
    )
    parser.add_argument(
        "-l",
        "--logging-mode",
        help="Turn on a logging mode, data output is minimal and tab separated",
        action="store_true",
    )
    parser.add_argument(
        "--who-filter",
        nargs="+",
        type=str,
        help="+/- to indicate include or exclude, then WHO values to filter",
    )
    parser.add_argument(
        "--where-filter",
        nargs="+",
        type=str,
        help="+/- to indicate include or exclude, then WHERE values to filter",
    )
    parser.add_argument(
        "--dimension-filter",
        nargs="+",
        type=str,
        help="+/- to indicate include or exclude, then DIMENSION values to filter",
    )
    args = parser.parse_args()

    # create logger with 'OWNd'
    _logger = logging.getLogger("OWNd")
    _logger.setLevel(logging.DEBUG)

    # create console handler which logs even debug messages
    log_stream_handler = logging.StreamHandler()

    if args.verbose == 2:
        log_stream_handler.setLevel(logging.DEBUG)
    elif args.verbose == 0 or args.logging_mode or args.send is not None:
        log_stream_handler.setLevel(logging.WARNING)
    else:
        log_stream_handler.setLevel(logging.INFO)

    # create formatter and add it to the handlers
    formatter = (
        logging.Formatter("%(asctime)s\t%(message)s")
        if args.logging_mode or args.send is not None
        else logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    log_stream_handler.setFormatter(formatter)
    # add the handlers to the logger
    _logger.addHandler(log_stream_handler)

    if args.send is not None:
        command_session = OWNCommandSession()
        _arguments = {
            "address": args.address,
            "port": args.port,
            "password": args.password,
            "serialNumber": args.mac,
            "logger": _logger,
            "messages": args.send,
        }

        loop = asyncio.get_event_loop()
        send_task = asyncio.gather(send(_arguments, command_session))
        # loop.set_debug(True)

        try:
            _logger.info("Starting OWNd sender.")
            loop.run_until_complete(send_task)
        except KeyboardInterrupt:
            _logger.info("Stoping OWNd sender.")
            send_task.cancel()
            loop.run_until_complete(command_session.close())
            send_task.exception()
            loop.stop()
            loop.close()
        except (
            OWNGatewayUnreachableError,
            OWNConnectionRefusedError,
            OWNAuthenticationError,
        ) as e:
            _logger.error(e)
            _logger.info("Stoping OWNd sender.")
            send_task.cancel()
            loop.run_until_complete(command_session.close())
            send_task.exception()
            loop.stop()
            loop.close()
        finally:
            _logger.info("OWNd sender stopped.")

    else:

        _who_filter_polarity = 0
        _who_filter = []

        if args.who_filter is not None:
            if args.who_filter[0] == "-":
                _who_filter_polarity = -1
                _who_filter = args.who_filter[1:]
            elif args.who_filter[0] == "+":
                _who_filter_polarity = +1
                _who_filter = args.who_filter[1:]
            else:
                _who_filter_polarity = +1
                _who_filter = args.who_filter

        _where_filter_polarity = 0
        _where_filter = []

        if args.where_filter is not None:
            if args.where_filter[0] == "-":
                _where_filter_polarity = -1
                _where_filter = args.where_filter[1:]
            elif args.where_filter[0] == "+":
                _where_filter_polarity = +1
                _where_filter = args.where_filter[1:]
            else:
                _where_filter_polarity = +1
                _where_filter = args.where_filter

        _dimension_filter_polarity = 0
        _dimension_filter = []

        if args.dimension_filter is not None:
            if args.dimension_filter[0] == "-":
                _dimension_filter_polarity = -1
                _dimension_filter = args.dimension_filter[1:]
            elif args.dimension_filter[0] == "+":
                _dimension_filter_polarity = +1
                _dimension_filter = args.dimension_filter[1:]
            else:
                _dimension_filter_polarity = +1
                _dimension_filter = args.dimension_filter

        event_session = OWNEventSession()
        _arguments = {
            "address": args.address,
            "port": args.port,
            "password": args.password,
            "serialNumber": args.mac,
            "logger": _logger,
            "logging_mode": args.logging_mode,
            "who_filter_polarity": _who_filter_polarity,
            "who_filter": _who_filter,
            "where_filter_polarity": _where_filter_polarity,
            "where_filter": _where_filter,
            "dimension_filter_polarity": _dimension_filter_polarity,
            "dimension_filter": _dimension_filter,
        }

        loop = asyncio.get_event_loop()
        main_task = asyncio.gather(main(_arguments, event_session))
        # loop.set_debug(True)

        try:
            _logger.info("Starting OWNd.")
            loop.run_until_complete(main_task)
        except KeyboardInterrupt:
            _logger.info("Stoping OWNd.")
            main_task.cancel()
            loop.run_until_complete(event_session.close())
            main_task.exception()
            loop.stop()
            loop.close()
        except (
            OWNGatewayUnreachableError,
            OWNConnectionRefusedError,
            OWNAuthenticationError,
        ) as e:
            _logger.error(e)
            _logger.info("Stoping OWNd.")
            main_task.cancel()
            loop.run_until_complete(event_session.close())
            main_task.exception()
            loop.stop()
            loop.close()
        finally:
            _logger.info("OWNd stopped.")
