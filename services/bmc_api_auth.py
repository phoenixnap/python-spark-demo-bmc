#!/usr/local/bin/python
"""Module providing anything related to authenticating with BMC api."""
import requests
from base64 import standard_b64encode
from utils.logs import bcolors


environment = {'dev': {'url_path': 'https://auth-dev.phoenixnap.com/auth/realms/BMC/protocol/openid-connect/token'},
               'prod': {'url_path': ' https://auth.phoenixnap.com/auth/realms/BMC/protocol/openid-connect/token'}}


def get_access_token(client_id: str, client_secret: str, env: str) -> str:
    """Retrieves an access token from BMC auth by using the client ID and the client Secret."""
    string_data = "%s:%s" % (client_id, client_secret)
    basic_auth = standard_b64encode(string_data.encode("utf-8"))
    result = requests.post(
        environment[env]['url_path'],
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic %s' % basic_auth.decode("utf-8")},
        data={
            'grant_type': 'client_credentials'})

    if result.status_code != 200:
        raise Exception('Error: {}. \n {}'
                        .format(result.status_code, result.json()))
    print(bcolors.OKBLUE + 'Successfully retrieved API token' + bcolors.ENDC)
    return result.json()['access_token']


def refresh_access_token(refresh_token: str, env: str) -> str:
    """Retrieves an access token from BMC auth by using the refresh token."""
    result = requests.post(
        environment[env]['url_path'],
        headers={
            'Content-Type': 'application/x-www-form-urlencoded'},
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token})

    if result.status_code != 200:
        raise Exception('Error: {}. \n {}'
                        .format(result.status_code, result.json()))

    print('Successfully retrieved access token from refresh token')
    return result.json()['access_token']


