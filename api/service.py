from flask import Flask, Response, request
import json
import sys
from re import findall

#local imports
from oracle_connection import OracleDB
import handlers

#sesamutils
from sesamutils.variables import VariablesConfig
from sesamutils.sesamlogger import sesam_logger
from sesamutils.flask import serve

app = Flask(__name__)


def stream_json(testing):
    first = True
    yield '['
    for i, row in enumerate(testing):
        if not first:
            yield ','
        else:
            first = False
        yield json.dumps(row)
    yield ']'

@app.route('/transform', methods=['POST'])
def receiver():
    """This function iterates over input entities and returns the handled version.
    You can use the generic_handler if you just want the query result appended to your entity.
    Otherwise you can create your own handler in handlers.py to customize your handling...

    Make sure to append entities on their way in here with 'do_query': true/false. Unless you want to overload me
    """
    # get entities from request
    req_entities = request.get_json()
    output = []
    query_keys = findall('\{(.*?)\}', variables.query)#Regex to find all keys inside curly brackets in the query
    if len(query_keys) == 0:
        logger.warning('Query does not have keys enclosed in curly braces eg "{"_id"}"')
    try:
        for entity in req_entities:
            do_query = True  # If do_query is missing from the entity we will do the query anyways.
            if 'do_query' in entity:  # Check if entity has do_query key
                do_query = entity['do_query']
            if do_query:
                handler = getattr(handlers, variables.handler)
                entity = handler(databaseConnection, variables, logger, entity, query_keys)
            logger.debug(f'Appending entity: {json.dumps(entity)} to output!')
            output.append(entity)
    except TypeError as e:
        logger.critical('Wrong type gave error: {}'.format(e))
    except Exception as e:
        logger.critical(f'Error when handling entities:\n{json.dumps(req_entities)}\nError message:\n{e}')

    # Generate the response
    try:
        return Response(stream_json(output),
                        mimetype='application/json')
    except BaseException as e:
        return Response(status=500, response=f"An error occured during transform of input. Error: {e}")


if __name__ == '__main__':
    variables = VariablesConfig(
        ['db_host', 'db_port', 'db_database', 'db_username', 'db_password', 'handler', 'query', 'LOG_LEVEL'])
    if not variables.validate():
        sys.exit(-1)

    databaseConnection = OracleDB(host=variables.db_host, port=variables.db_port, database=variables.db_database,
                                  username=variables.db_username,
                                  password=variables.db_password)
    logger = sesam_logger(logger_name='SQL_TRANSFORM', timestamp=True, app=app)
    serve(app=app)
