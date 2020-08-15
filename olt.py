import ipaddress
import json

import requests
import urllib3

from onu import ONU, ONUWiFi
from onu_profile import ONUProfile
from utils import pythonize

# No warnings for self signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Use a proper user agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'

# Header for urlencoded form data
HEADER_FORM_URLENCODED = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': USER_AGENT,
}

# Header for urlencoded form data
HEADER_JSON = {
    'Content-Type': 'application/json',
    'User-Agent': USER_AGENT,
}


class LoginError(Exception):
    pass


class OLTClient():
    '''
    Client interface to Ubiquiti UFiber OLT. Host can be a hostname or a IP address
    '''
    # Base Client
    client = requests.Session()

    def login(self):
        '''
        Login using credentials. Returns True/False
        '''
        # Build post request to login
        form_data = {
            'username': self.username,
            'password': self.password,
        }
        try:
            # Try to login
            response = self.client.post(
                verify=False,
                url=self.url,
                headers=HEADER_FORM_URLENCODED,
                data=form_data
            )
        except ConnectionError as ex:
            raise LoginError(ex)
        except TimeoutError as ex:
            raise LoginError(ex)
        # HTTP OK ?
        try:
            assert response.status_code, 200
        except AssertionError:
            raise requests.HTTPError('Got wrong reply from OLT HTTP interface')
        # If there is a port list, then we are logged in
        try:
            assert 'Port 0' in response.text, True
        except AssertionError:
            raise LoginError('Failed to log in with specified credentials')
        return True

    def get_configuration(self):
        '''
        Returns OLT general configuration. GPON configuration != here.
        '''
        assert self.logged_in, True
        url = self.url + '/api/edge/get.json'
        response = self.client.get(url)
        if response.status_code != 200:
            return False
        configuration = response.text
        return json.loads(configuration)['GET']

    def set_configuration(self, data):
        '''
        Sets configuration using data dict
        '''
        assert self.logged_in, True
        # Base url
        url = self.url + '/api/edge/batch.json'
        # Build headers, add CSRF token
        headers = HEADER_JSON
        headers['X-CSRF-TOKEN'] = self.client.cookies.get('X-CSRF-TOKEN')
        # Post configuration
        response = self.client.post(
            verify=False,
            url=url,
            headers=HEADER_JSON,
            json=data,
        )
        # Raise error if status != HTTP 200, OK
        if response.status_code != 200:
            raise ConnectionError()
        action = list(data.keys())[0]
        configuration = json.loads(response.text)[action]
        return configuration

    def delete_configuration(self, data):
        '''
        Deletes configuration using data dict
        '''
        assert self.logged_in, True
        # Base url
        url = self.url + '/api/edge/delete.json'
        # Build headers, add CSRF token
        headers = HEADER_JSON
        headers['X-CSRF-TOKEN'] = self.client.cookies.get('X-CSRF-TOKEN')
        # Post configuration
        response = self.client.post(
            verify=False,
            url=url,
            headers=HEADER_JSON,
            json=data,
        )
        # Raise error if status != HTTP 200, OK
        if response.status_code != 200:
            raise ConnectionError()
        configuration = json.loads(response.text)['DELETE']
        return configuration

    def get_onu_profiles(self):
        '''
        Quickly return onu profiles from configuration
        '''
        assert self.logged_in, True
        return self.get_configuration()['onu-profiles']

    def get_bulk_onu_status(self):
        '''
        Returns list and status of provisioned ONUs
        '''
        assert self.logged_in, True
        url = self.url + '/api/edge/data.json?data=gpon_onu_list'
        response = self.client.get(url)
        if response.status_code != 200:
            return False
        response = json.loads(response.text)['output']['GET_ONU_LIST']
        onu_status = {}
        for onu in response:
            serial_number = onu.pop('serial_number')
            onu_status[serial_number] = onu
        return onu_status

    def get_onu_status(self, serial_number):
        '''
        Returns status of provisioned ONU
        '''
        assert self.logged_in, True
        return self.get_bulk_onu_status()[serial_number]

    def get_onu(self, serial_number):
        '''
        Returns status of provisioned ONU
        '''
        assert self.logged_in, True
        try:
            # Get raw config
            onu_raw = self.get_configuration()['onu-list'][serial_number]
        except KeyError:
            raise KeyError(
                'Could not get configutation for onu {serial_number}'.format(serial_number))

        # Get raw wifi
        wifi_raw = json.loads(json.dumps(onu_raw.pop('wifi')))
        # Make it pythonic
        wifi_parsed = pythonize(wifi_raw)
        # Make wifi
        wifi = ONUWiFi(**wifi_parsed)
        # Remove onu id
        onu_raw.pop('lastOnuId')
        # Build onu
        onu_parsed = pythonize(onu_raw)
        onu = ONU(olt_client=self, serial_number=serial_number,
                  wifi=wifi, **onu_parsed)
        return onu

    def get_onu_profile(self, profile_id):
        '''
        Get ONU profile
        '''
        assert self.logged_in, True
        try:
            # Get raw config
            profile_raw = self.get_onu_profiles()[profile_id]
        except KeyError:
            raise KeyError(
                'Could not get configutation for profile {profile_id}'.format(profile_id))
        # Make it pythonic
        profile_parsed = pythonize(profile_raw)

        # Ports are auto by default
        profile_parsed.pop('port')

        # Ports are auto by default
        services_raw = profile_parsed.pop('services')
        # Make it pythonic
        services_parsed = pythonize(services_raw)

        # Get mode
        bridge_mode = profile_parsed.pop('bridge_mode')
        router_mode = profile_parsed.pop('router_mode')

        # No dhcp relay at the moment
        router_mode.pop('dhcp-relay')

        # Router / Bridge
        if profile_parsed['mode'] == ONUProfile.MODE_BRIDGE:
            mode_raw = bridge_mode
        if profile_parsed['mode'] == ONUProfile.MODE_ROUTER:
            mode_raw = router_mode

        # Make it pythonic
        mode_parsed = pythonize(mode_raw)

        # Adjust bw limit
        profile_parsed['bandwidth_limit_up'] = int(
            int(profile_parsed['bandwidth_limit_up']) / ONUProfile.K)
        profile_parsed['bandwidth_limit_down'] = int(
            int(profile_parsed['bandwidth_limit_down']) / ONUProfile.K)

        profile = ONUProfile(self, **profile_parsed, **
                             mode_parsed, **services_parsed)
        return profile

    def __init__(self, host, username, password):
        self.host = host
        self.url = 'https://{host}'.format(host=host)
        self.username = username
        self.password = password
        self.logged_in = self.login()
        super().__init__()
