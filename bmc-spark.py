#!/usr/local/bin/python
"""Script to generate X servers, configure them in a spark cluster."""

import argparse
import sched
import time
import requests
import ast
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from services import bmc_api_auth, bmc_api
from utils.logs import bcolors

scheduler = sched.scheduler(time.time, time.sleep)

REQUEST = requests.Session()
ENVIRONMENT = "prod"
VERBOSE_MODE = False
NOW = datetime.now()


def parse_args():
    """Defines which arguments are needed for the script to run."""
    parser = argparse.ArgumentParser(
        description='BMC-API Demo')
    req_grp = parser.add_argument_group(title='optional arguments')
    req_grp.add_argument(
        '-d',
        '--delete_all',
        help='Delete all servers')
    parsed = parser.parse_args()

    return parsed


def main():
    """Method called from the main entry point of the script to do the required logic."""
    args = parse_args()
    delete_all = args.delete_all

    get_access_token(credentials["client_id"], credentials["client_secret"])
    if delete_all is not None:
        bmc_api.delete_all_servers(REQUEST, ENVIRONMENT)
        return
    servers = list()
    pool = ThreadPoolExecutor()
    futures_requests = []
    print(bcolors.WARNING + "Creating servers..." + bcolors.ENDC)
    bmc_api.create_servers(futures_requests, pool, REQUEST, data["servers"], ENVIRONMENT)
    waiting_provision_servers(futures_requests, pool, servers)
    run_scripts(servers)
    print(bcolors.OKBLUE + bcolors.BOLD + "Setup servers done" + bcolors.ENDC)
    print(bcolors.OKBLUE + bcolors.BOLD + "Master node UI: http://{}:8080".format(data['master_ip']) + bcolors.ENDC)


def run_scripts(servers):
    for server in servers:
        print(bcolors.OKBLUE + bcolors.BOLD + "Running all_host.sh script on {} (Public IP: {})".format(
            server['hostname'], server['publicIpAddresses'][0]) + bcolors.ENDC)
        run_script_on_host(server['publicIpAddresses'][0], "all_hosts.sh {}".format(server['privateIpAddresses'][0]))
        if server['master']:
            print(bcolors.WARNING + bcolors.BOLD + "Running master_host.sh script on {} (Public IP: {})".format(
                server['hostname'], server['publicIpAddresses'][0]) + bcolors.ENDC)
            run_script_on_host(server['publicIpAddresses'][0], "master_host.sh")
            print(bcolors.OKBLUE + bcolors.BOLD + "Master host installed" + bcolors.ENDC)
    for server in servers:
        if not server['master']:
            print(bcolors.WARNING + bcolors.BOLD + "Running worker_host.sh script on {} (Public IP: {})".format(
                server['hostname'], server['publicIpAddresses'][0]) + bcolors.ENDC)
            run_script_on_host(server['publicIpAddresses'][0],
                               "worker_host.sh {} {}".format(data['master_private_ip'], data['master_hostname']))


def waiting_provision_servers(futures_requests, pool, servers):
    futures_setups = []
    requests_counter = 0
    for request in as_completed(futures_requests):
        if request.result() is not None:
            requests_counter += 1
            json_server = request.result()
            print(bcolors.WARNING + "Server created, provisioning {}...".format(json_server['hostname']) + bcolors.ENDC)
            if requests_counter == server_settings['servers_quantity']:
                print(bcolors.WARNING + "Waiting for servers to be provisioned..." + bcolors.ENDC)
            futures_setups.append(pool.submit(__do_setup_host, servers, request.result()))
    wait(futures_setups)


def __do_setup_host(servers, json_server):
    if json_server is not None:
        json_server['master'] = False
        servers.append(json_server)
        setup_host(json_server)
    return json_server


def setup_hosts(servers):
    pool = ThreadPoolExecutor()
    futures = []
    for json_server in servers:
        futures.append(pool.submit(setup_host, json_server))
    wait(futures)
    return futures, pool


def get_master_host(servers):
    for json_server in servers:
        if json_server['master']:
            return json_server['publicIpAddresses'][0]


def get_access_token(client, password):
    print(bcolors.WARNING + "Retrieving token" + bcolors.ENDC)
    # Retrieve an access token using the client Id and client secret provided.
    access_token = bmc_api_auth.get_access_token(client, password, ENVIRONMENT)
    # Add Auth Header by default to all requests.
    REQUEST.headers.update({'Authorization': 'Bearer {}'.format(access_token)})
    REQUEST.headers.update({'Content-Type': 'application/json'})


def setup_host(json_server):
    scheduler.enter(0, 1, wait_server_ready, (scheduler, json_server))
    scheduler.run()


def wait_server_ready(sched, server_data):
    json_server = bmc_api.get_server(REQUEST, server_data['id'], ENVIRONMENT)
    if json_server['status'] == "creating":
        scheduler.enter(2, 1, wait_server_ready, (sched, server_data,))
    elif json_server['status'] == "powered-on" and not data['has_a_master_server']:
        server_data['master'] = True
        data['has_a_master_server'] = True
        data['master_ip'] = json_server['publicIpAddresses'][0]
        data['master_private_ip'] = json_server['privateIpAddresses'][0]
        data['master_hostname'] = json_server['hostname']
        print(bcolors.OKBLUE + bcolors.BOLD + "ASSIGNED MASTER SERVER: {}".format(data['master_hostname']) + bcolors.ENDC)


def run_script_on_host(host_ip: str, script_filename: str):
    run_shell_command([ssh + 'ubuntu@{} \'bash -s\' < ./scripts/{}'.format(host_ip, script_filename)], print_log=True)


def read_dict_file(filename: str) -> dict:
    with open(filename, 'r') as f:
        s = f.read()
        return ast.literal_eval(s)


def run_shell_command(commands: list, print_log: bool = VERBOSE_MODE) -> str:
    proc = subprocess.Popen(commands, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    result = out.decode('UTF-8')
    if print_log:
        if result != "":
            print(bcolors.HEADER + "{}".format(result) + bcolors.ENDC)
        else:
            print(bcolors.HEADER + "Finished: {}".format(commands[0]) + bcolors.ENDC)
    return result


if __name__ == '__main__':
    server_settings = read_dict_file("server-settings.conf")
    credentials = read_dict_file("credentials.conf")
    servers_data = []
    for server in range(server_settings['servers_quantity']):
        server_data = {"hostname": "{}-{}".format(server_settings['hostname'], server),
                       "description": "{}-{}".format(server_settings['description'], server),
                       "public": server_settings['public'],
                       "location": server_settings['location'],
                       "os": server_settings['os'],
                       "type": server_settings['type'],
                       "sshKeys": [server_settings['ssh_key']]}
        servers_data.append(server_data)
    data = {"has_a_master_server": False, "servers": servers_data, "master_ip": "", "master_hostname": ""}
    time = {"now": NOW}
    config = {}
    ssh = "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o LogLevel=ERROR "
    main()
