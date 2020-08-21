#!/usr/local/bin/python
"""Module providing calls available on BMC api."""
import json
import time
from utils.logs import bcolors

environment = {'dev': {'url_path': 'https://api-dev.phoenixnap.com/bmc/v1beta/'},
               'prod': {'url_path': ' https://api.phoenixnap.com/bmc/v1beta/'}}


def get_servers(session, env='dev') -> str:
    """List all servers owned by account."""
    response = session.get(environment[env]['url_path'] + 'servers')
    while response.status_code == 502:
        handle_error_502(response)
        response = session.get(environment[env]['url_path'] + 'servers')
    if response.status_code != 200:
        raise Exception(print_error(response))
    return response.json()


def get_server(session, server_id: str, env='dev') -> str:
    """Get server by ID."""
    response = session.get(environment[env]['url_path'] + 'servers/{}'.format(server_id))
    while response.status_code == 502:
        handle_error_502(response)
        response = session.get(environment[env]['url_path'] + 'servers/{}'.format(server_id))
    if response.status_code != 200:
        raise Exception(print_error(response))

    return response.json()


def __do_create_server(session, server, env):
    response = session.post((environment[env]['url_path'] + 'servers'),
                            data=json.dumps(server))
    while response.status_code == 502:
        handle_error_502(response)
        response = session.post((environment[env]['url_path'] + 'servers'),
                                data=json.dumps(server))
    if response.status_code != 200:
        print(bcolors.FAIL + "Error creating server: {}".format(json.dumps(response.json())) + bcolors.ENDC)
    else:
        print(bcolors.OKBLUE + "{}".format(json.dumps(response.json(), indent=2)) + bcolors.ENDC)
        return response.json()


def create_servers(futures, pool, session, servers: list, env="dev") -> list:
    """Create (request) new server for account."""
    for server in servers:
        futures.append(pool.submit(__do_create_server, session, server, env))


def delete_all_servers(session, env):
    """Delete all servers."""
    servers = get_servers(session, env)

    for server in servers:
        response = session.delete(environment[env]['url_path'] + 'servers/{}'.format(server['id']))
        while response.status_code == 502:
            handle_error_502(response)
            response = session.delete(environment[env]['url_path'] + 'servers/{}'.format(server['id']))
        if response.status_code != 200:
            # raise Exception(utils.print_error(response))
            print(bcolors.FAIL + "Error deleting server" + bcolors.ENDC)
        print(bcolors.FAIL + json.dumps(response.json()) + bcolors.ENDC)


def handle_error_502(response):
    print(bcolors.WARNING + "Error 502, trying again" + bcolors.ENDC)
    print(response.headers)
    time.sleep(0.5)


def print_error(response) -> str:
    """Prints the error returned from an API call"""
    return 'Error: {}. \n {}'.format(response.status_code, response.json())
