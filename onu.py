import ipaddress
import json


class ONUWiFi():
    '''
    Builds WiFi configuration for ONU
    Returns a JSON string
    '''

    AUTH_MODE_OPEN = 'open'
    AUTH_MODE_WPA2PSK = 'wpa2psk'
    AUTH_VALID_RANGE = [
        AUTH_MODE_OPEN,
        AUTH_MODE_WPA2PSK
    ]

    CHANNEL_01 = 1
    CHANNEL_02 = 2
    CHANNEL_03 = 3
    CHANNEL_04 = 4
    CHANNEL_05 = 5
    CHANNEL_06 = 6
    CHANNEL_07 = 7
    CHANNEL_08 = 8
    CHANNEL_09 = 9
    CHANNEL_10 = 10
    CHANNEL_11 = 11
    CHANNEL_12 = 12
    CHANNEL_13 = 13
    CHANNEL_AUTO = 'auto'
    CHANNEL_VALID_RANGE = [
        CHANNEL_01,
        CHANNEL_02,
        CHANNEL_03,
        CHANNEL_04,
        CHANNEL_05,
        CHANNEL_06,
        CHANNEL_07,
        CHANNEL_08,
        CHANNEL_09,
        CHANNEL_10,
        CHANNEL_11,
        CHANNEL_12,
        CHANNEL_13,
        CHANNEL_AUTO,
        CHANNEL_01,
    ]
    CHANNEL_DEFAULT = CHANNEL_AUTO

    CHANNEL_WIDTH_20 = '20'
    CHANNEL_WIDTH_20_40 = '20/40'
    CHANNEL_WIDTH_VALID_RANGE = [
        CHANNEL_WIDTH_20,
        CHANNEL_WIDTH_20_40
    ]
    CHANNEL_WIDTH_DEFAULT = CHANNEL_WIDTH_20_40

    TX_POWER_100 = 100
    TX_POWER_50 = 50
    TX_POWER_25 = 25
    TX_POWER_12 = 12
    TX_POWER_6 = 6
    TX_POWER_VALID_RANGE = [
        TX_POWER_100,
        TX_POWER_50,
        TX_POWER_25,
        TX_POWER_12,
        TX_POWER_6,
    ]
    TX_POWER_DEFAULT = TX_POWER_100
    ENCRYPT_TYPE = 'aes'

    SSID_VALID_RANGE = range(8, 17)
    WPAPSK_VALID_RANGE = range(8, 17)

    SSID_DEFAULT = 'UBNT-ONU'
    WPAPSK_DEFAULT = '12345678'

    def __init__(self,
                 provisioned=False, enabled=False,
                 channel=CHANNEL_DEFAULT, channel_width=CHANNEL_WIDTH_DEFAULT,
                 tx_power=TX_POWER_DEFAULT,
                 hide_ssid=False,
                 auth_mode=AUTH_MODE_WPA2PSK,
                 ssid=SSID_DEFAULT,
                 wpapsk=WPAPSK_DEFAULT,
                 encrypt_type=ENCRYPT_TYPE
                 ):

        assert isinstance(provisioned,
                          bool), 'provisioned has to be True/False'
        assert isinstance(enabled, bool), 'enabled has to be True/False'
        assert str(
            channel) in self.CHANNEL_VALID_RANGE, 'channel out of range'
        assert str(
            channel_width) in self.CHANNEL_WIDTH_VALID_RANGE, 'channel_width out of range'
        assert int(
            tx_power) in self.TX_POWER_VALID_RANGE, 'tx_power out of range 100, 50, 25, 12, 6'
        assert isinstance(
            hide_ssid, bool), 'hide_ssid has to be True/False'
        assert str(auth_mode) in self.AUTH_VALID_RANGE, 'auth_mode invalid'
        if provisioned:
            assert len(str(ssid).strip()
                       ) in self.SSID_VALID_RANGE, 'ssid has to be 8-16 characters'
            assert len(str(wpapsk).strip(
            )) in self.WPAPSK_VALID_RANGE, 'wpapsk has to be 8-16 characters'

        wifi = {
            'provisioned': provisioned,
            'enabled': enabled,
            'channel': channel,
            'channel_width': channel_width,
            'tx_power': tx_power,
            'hide_ssid': hide_ssid,
            'auth_mode': auth_mode,
            'encrypt_type': self.ENCRYPT_TYPE,
            'ssid': ssid,
            'wpapsk': wpapsk,
        }

        self.wifi = json.dumps(wifi)

        super().__init__()


class ONU():
    '''
    ONU Defintion with configuration
    '''
    PPPoE_MAX_LENGTH = range(0, 32)

    def set_configuration(self):
        '''
        Use OLT Client to set ONU configuration
        '''
        if self.onu:
            onu_list = {
                'onu-list': self.onu,
            }
            data = {
                "SET": onu_list,
            }
            return self.client.set_configuration(data)
        raise Warning('ONU not initialized')

    def add(self):
        '''
        Adds an onu. Can be used to set configuration for an existing ONU
        '''
        return self.set_configuration()

    def save(self):
        '''
        Adds an onu. Can be used to set configuration for an existing ONU
        '''
        return self.set_configuration()

    def delete(self):
        '''
        Use OLT Client to delete ONU configuration
        '''
        if self.onu:
            onu_list = {
                'onu-list': self.onu,
            }
            data = {
                "DELETE": onu_list,
            }
            return self.client.set_configuration(data)
        raise Warning('ONU not initialized')

    def status(self):
        '''
        Use OLT Client to retrieve ONU status
        '''
        if self.onu:
            onu_list = self.client.get_onu_status()
            for onu in onu_list:
                if onu['serial_number'] == self.serial_number:
                    return onu
            return False
        raise Warning('ONU not initialized')

    def __init__(self, olt_client,
                 serial_number, profile, name,
                 wifi,
                 wan_address='null',
                 port_forwards='',
                 pppoe_user='',
                 pppoe_password='',
                 pppoe_mode='auto',
                 disable=False):

        # HTTP Client
        self.client = olt_client

        # Serial starts with UBNT
        assert str(serial_number)[
            :3] != 'UBNT', 'Serial has to start with UBNT'
        # Format Serial Number
        # Serial lenght 12 chars
        assert len(str(serial_number)
                   ) == 12, 'Serial has be 12 characters long'
        # Build serial number
        serial_number_prefix = str(serial_number).strip()[:4]
        serial_number_sufix = str(serial_number).strip().lower()[4:]
        serial_number = serial_number_prefix + serial_number_sufix

        # ONU profile starts with 'profile-'
        assert str(
            profile[:7]) != 'profile-', 'ONU profile has to start with "profile-"'
        # Avoid blank ONU name
        assert name, 'ONU name cannot be blank'

        # Keep PPPoE secret under 16 chars for compatibility
        assert len(str(
            pppoe_user)) in self.PPPoE_MAX_LENGTH, 'PPPoE Username length cannot be more than 16 characters'
        assert len(str(
            pppoe_password)) in self.PPPoE_MAX_LENGTH, 'PPPoE Password length cannot be more than 16 characters'

        # Validate IP address
        if wan_address != 'null':
            assert ipaddress.ip_address(
                wan_address), f'Address {wan_address} is not valid'

        self.onu = {
            serial_number: {
                "disable": disable,
                "profile": profile,
                "name": name,
                "wifi": wifi.wifi,
                "pppoe-mode": "auto",
                "pppoe-user": pppoe_user,
                "pppoe-password": pppoe_password,
                "wan-address": "null",
                "port-forwards": []
            }
        }
        super().__init__()
