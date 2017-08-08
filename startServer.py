import logging.config
import ssl
from os.path import isfile
from core.config import config, paths
from apps import *
from gevent.wsgi import WSGIServer

logger = logging.getLogger('startserver')


def get_ssl_context():
    if config.https.lower() == "true":
        # Sets up HTTPS
        if config.tls_version == "1.2":
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        elif config.tls_version == "1.1":
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_1)
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

        if isfile(paths.certificate_path) and isfile(paths.private_key_path):
            context.load_cert_chain(paths.certificate_path, paths.private_key_path)
            return context
        else:
            print('Cannot locate certificates')
    return None


def setup_logger():
    log_config = None
    if isfile(paths.logging_config_path):
        try:
            with open(paths.logging_config_path, 'rt') as log_config_file:
                log_config = json.loads(log_config_file.read())
        except:
            print('Invalid JSON in logging config file')
            pass
    else:
        print('No logging config found')

    if log_config is not None:
        logging.config.dictConfig(log_config)
    else:
        logging.basicConfig()
        logger.info("Basic logging is being used")


def run():
    # The order of these imports matter for initialization (should probably be fixed)
    from server import flaskserver
    import core.case.database as case_database
    case_database.initialize()
    ssl_context = get_ssl_context()
    flaskserver.running_context.init_threads()
    from server.receiver import start_receiver

    start_receiver()
    try:
        port = int(config.port)
    except ValueError:
        print('Invalid port {0}. Port must be an integer'.format(config.port))
    else:
        host = config.host
        if ssl_context:
            server = WSGIServer((host, port), application=flaskserver.app, ssl_context=ssl_context)
            proto = 'https'
        else:
            server = WSGIServer((host, port), application=flaskserver.app)
            proto = 'http'
        setup_logger()
        logger.info('Listening on host {0}://{1}:{2}'.format(proto, host, port))

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info('Shutting down server')

        # app.run()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        logger.info('Caught KeyboardInterrupt!')
    finally:
        from core.controller import shutdown_pool
        from server.receiver import stop_receiver

        stop_receiver()
        shutdown_pool()
        logger.info('Shutting down server')

