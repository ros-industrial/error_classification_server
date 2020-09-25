'''
This program defines and served API endpoint routes for the ERT and ECS tables.
'''

import os
import errno

from sanic import Sanic, response
from databases import Database

app = Sanic(__name__)


@app.route("/ping")
async def get_ping(request):
    """
    Test API Route
    """

    return response.json({'data': 'ECS API is Live!'}, status=200)


@app.route("/ert/error-data")
async def get_ert_errordata(request):
    """
    Primary API that can be used to retrieve ERT row corresponding to a
    robot model/error text combo ERT should be primarily used only in
    development environment, not production.

    :param RobotModel: Model of the Robot which is querying the database
    :param ErrorText: Error String that is queried
    :return result: Matching Row for the queried ErrorText and RobotModel
    :responses
    -- 200 : Successful query
    -- 400 : Insufficient parameters to serve request
    -- 500 : Database issue
    """
    # Get database
    try:
        db_instance = request.app.config['database']
    except Exception as ex:
        return response.json({'data': 'Database ERROR ' + str(ex)}, status=500)

    # Get query parameters
    try:
        query_params = request.args
        robot_model = query_params.get('RobotModel')
        error_text = query_params.get('ErrorText')

        if not (robot_model and error_text):
            raise Exception

    except Exception:
        return response.json({'data': 'Required API parameters missing'}, status=400)

    # Set query
    query = """
            SELECT error_code, cast(error_level as integer) as 'error_level', compounding_flag, error_module, error_source, error_text, error_description, error_resolution
            FROM error_report
            WHERE (:robot_model LIKE robot_model COLLATE NOCASE) AND (:error_text LIKE error_text COLLATE NOCASE);
            """

    # Retrieve query and return results
    try:
        # Retrieve query
        rows = await db_instance.fetch_all(query=query,
                                           values={"robot_model": robot_model,
                                                   "error_text": error_text})
        # Return results
        return response.json({'data': rows_to_list(rows)}, status=200)
    except Exception as ex:
        return response.json({'data': 'Database Query ERROR, ' + str(ex)}, status=500)


@app.route("/ecs/error-data")
async def get_ecs_errordata(request):
    """
    Primary API that can be used to retrieve ECS row corresponding to
    a robot model/error text combo ECS should be the primary choice
    in a production environment.

    :param RobotModel: Model of the Robot which is querying the database
    :param ErrorText: Error String that is queried
    :return result: Matching Row for the queried ErrorText and RobotModel
    :responses
    -- 200 : Successful query
    -- 400 : Insufficient parameters to serve request
    -- 500 : Database issue
    """

    # Get database
    try:
        db_instance = request.app.config['database']
    except Exception as ex:
        return response.json({'data': 'Database ERROR ' + str(ex)}, status=500)

    # Get query parameters
    try:
        query_params = request.args
        robot_model = query_params.get('RobotModel')
        error_text = query_params.get('ErrorText')

        if not (robot_model and error_text):
            raise Exception

    except Exception:
        return response.json({'data': 'Required API parameters missing'}, status=400)

    # Set query
    query = """
            SELECT sub_query.cognicept_error_code, sub_query.severity, sub_query.compounding_flag, sub_query.error_module, sub_query.error_source, sub_query.error_text
            FROM (error_classification EC
            INNER JOIN robot_info RI ON EC.robot_type = RI.robot_id) sub_query
            WHERE :robot_model LIKE sub_query.robot_model COLLATE NOCASE
            AND :error_text LIKE sub_query.error_text COLLATE NOCASE
            """

    # Retrieve query and return results
    try:
        # Retrieve query
        rows = await db_instance.fetch_all(query=query,
                                           values={"robot_model": robot_model,
                                                   "error_text": error_text})
        # Return results
        return response.json({'data': rows_to_list(rows)}, status=200)
    except Exception as ex:
        return response.json({'data': 'Database Query ERROR, ' + str(ex)}, status=500)


@app.listener('before_server_start')
async def register_db(app, loop):
    """
    Connects to the database
    """
    try:
        db_path = os.path.expanduser(os.environ['ECS_DB_LOC'])

        if not os.path.exists(db_path):
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), db_path)

        app.config['database'] = Database(
            'sqlite:///' + db_path)
        await app.config['database'].connect()
    except Exception as ex:
        print('Database Connectivity ERROR, ' + str(ex))


@app.listener('after_server_stop')
async def close_connection(app, loop):
    """
    Disconnects from the database
    """
    await app.config['database'].disconnect()


def rows_to_list(records):
    """
    Parse db record response into list of dicts for JSON format
    """
    raw_list = []
    for record in records:
        items = record.items()
        raw_list.append({i[0]: i[1].rstrip() if type(
            i[1]) == str else i[1] for i in items})

    # Process data for compounding flag to be boolean since SQLite does not have a boolean type
    processed_list = []
    for row in raw_list:
        if 'compounding_flag' in row:
            if row['compounding_flag'] == '1':
                row['compounding_flag'] = True
            else:
                row['compounding_flag'] = False
            processed_list.append(row)

    # If processed list is empty, no processing was done, just assign raw list
    if not processed_list:
        processed_list = raw_list

    return processed_list


if __name__ == "__main__":

    # Parsing API Components
    ecs_api_url = (os.environ['ECS_API']
                   if 'ECS_API' in os.environ else 'http://0.0.0.0:8000')

    # Getting the API port from the URL string
    api_port = (ecs_api_url.split(':'))[2]

    try:
        app.run(host='0.0.0.0', port=api_port,
                access_log=True, debug=True)
    except Exception as ex:
        print('Exception message: ', str(ex))
