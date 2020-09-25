"""
A python script to pull the latest data from centralized ECS to the local file database ECS.
"""

import os
import sys
import time
import sqlite3
import requests
import pandas as pd


class BColors:
    """
    Simple class to print text in color on terminal
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_ecs_data():
    """
    Method that calls a REST API to get the latest ECS data in a JSON format
    """
    # Set API to get data
    ecs_basic_uri = "https://ert.cognicept.systems/update/basic"
    try:
        # Get data. Retry a few times if it fails
        total_retries = 3
        while True:
            total_retries -= 1
            try:
                resp = requests.get(ecs_basic_uri, timeout=5.0)
                break
            except Exception:
                if total_retries == 0:
                    raise
                else:
                    print(f"{BColors.WARNING}Retrying...{BColors.ENDC}")
                    time.sleep(0.5)

        if resp.status_code != 200:
            print(
                f"{BColors.FAIL}REST API returned code: {BColors.ENDC}", resp.status_code)
            sys.exit()
        else:
            # Return JSON data
            return resp.json()

    except requests.exceptions.Timeout:
        print(f"{BColors.FAIL}REST API error: time out.{BColors.ENDC}")
        sys.exit()
    except requests.exceptions.TooManyRedirects:
        print(f"{BColors.FAIL}REST API error: Wrong endpoint.{BColors.ENDC}")
        sys.exit()
    except:
        print(f"{BColors.FAIL}REST API error.{BColors.ENDC}")
        sys.exit()


def update_db():
    """
    Primary update method that calls an API to get JSON data and populates a local
    database using sqlite3.
    """
    # Get ECS data
    json_data = get_ecs_data()

    # Convert ECS data to DataFrame for easy processing + some necessary conversions
    ecs_db_dump = pd.DataFrame(json_data["error_classification"])
    ert_db_dump = pd.DataFrame(json_data["error_report"])
    ri_db_dump = pd.DataFrame(json_data["robot_info"])
    ecs_db_dump["error_type"] = ecs_db_dump["error_type"].astype(str)
    ecs_db_dump["error_resolution"] = ecs_db_dump["error_resolution"].astype(
        str)

    # Get only necessary columns for db population
    ecs_db_dump = pd.DataFrame(
        ecs_db_dump, columns=['classification_id', 'client_error_code',
                              'cognicept_error_code', 'compounding_flag',
                              'error_id', 'error_module', 'error_resolution',
                              'error_source', 'error_text', 'error_type',
                              'error_uuid', 'robot_type', 'severity'])
    ert_db_dump = pd.DataFrame(
        ert_db_dump, columns=['compounding_flag', 'error_code', 'error_description',
                              'error_id', 'error_level', 'error_module',
                              'error_resolution', 'error_source', 'error_text',
                              'robot_make', 'robot_model', 'robot_site'])
    ri_db_dump = pd.DataFrame(
        ri_db_dump, columns=['robot_id', 'robot_make', 'robot_model', 'robot_site'])

    try:
        with sqlite3.connect(db_path) as conn:
            try:
                # Establish connection
                cur = conn.cursor()

                # Begin transaction
                cur.execute('BEGIN')

                # Unparameterized sql commands - DROP and CREATE TABLE
                sqls = [
                    'DROP TABLE IF EXISTS error_classification',
                    'DROP TABLE IF EXISTS error_report',
                    'DROP TABLE IF EXISTS robot_info',
                    '''CREATE TABLE error_classification
                        (classification_id integer,
                         client_error_code text,
                         cognicept_error_code text,
                         compounding_flag booleantext,
                         error_id integer,
                         error_module text,
                         error_resolution json,
                         error_source text,
                         error_text text,
                         error_type json,
                         error_uuid text,
                         robot_type integer,
                         severity text)''',
                    '''CREATE TABLE error_report
                        (compounding_flag booleantext,
                         error_code text,
                         error_description text,
                         error_id integer,
                         error_level text,
                         error_module text,
                         error_resolution text,
                         error_source text,
                         error_text text,
                         robot_make text,
                         robot_model text,
                         robot_site text)''',
                    '''CREATE TABLE robot_info
                        (robot_id integer,
                         robot_make text,
                         robot_model text,
                         robot_site text)''', ]

                # Execute unparameterized sql commands
                for sql in sqls:
                    cur.execute(sql)

                # Execute parameterized sql commands - INSERT
                cur.executemany(
                    'INSERT INTO error_classification VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    ecs_db_dump.values.tolist())

                cur.executemany(
                    'INSERT INTO error_report VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                    ert_db_dump.values.tolist())

                cur.executemany(
                    'INSERT INTO robot_info VALUES (?,?,?,?)', ri_db_dump.values.tolist())

                # End transaction
                cur.execute('END')

                # Save changes
                conn.commit()
                print(f"{BColors.OKGREEN}ECS basic update successful.{BColors.ENDC}")

            except sqlite3.OperationalError:
                # Rollback in case of any exception
                if conn:
                    conn.rollback()
                print(
                    f"{BColors.FAIL}Error during update. Rolling back any changes.{BColors.ENDC}")
                raise

    except sqlite3.OperationalError as err:
        # Convey actual error
        print(f"{BColors.FAIL}Database ERROR: {BColors.ENDC}", err)


if __name__ == "__main__":

    # pull ECS basic version
    db_path = os.path.expanduser(os.environ['ECS_DB_LOC'])
    if os.path.exists(db_path):
        print(f"{BColors.WARNING}ECS db already exists here: {BColors.ENDC}")
        print(db_path)
        user_choice = input(
            "Are you sure you want to overwrite the existing db? \
You will lose any local changes: (Y/N) ")

        if user_choice in ["Y", 'y']:
            update_db()
        else:
            print(
                f"{BColors.OKBLUE}Exiting. \
                    Please rename existing db to keep local changes \
and retry update.{BColors.ENDC}")
    else:
        print(
            f"{BColors.WARNING}ECS db does not exist. Creating one here: {BColors.ENDC}")
        print(db_path)
        update_db()
