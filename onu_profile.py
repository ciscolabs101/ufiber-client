import ipaddress


class ONUProfile():
    '''
    Defaults are:
    - Router mode, WAN side access enabled VLAN 1
    - WAN mode PPPoE
    - WAN interface on VLAN 1
    - LAN interface on 192.168.1.1/24, DHCP pool 192.168.1.101-192.168.1.150, 1h lease
    - DNS servers 8.8.8.8, 1.1.1.1; no DNS proxy
    - Management on HTTP port 8080, SSH port 22
    - All firewall traffic helpers enabled
    '''

    # Bandwidth multiplier
    K = 131072

    MODE_ROUTER = 'router'
    MODE_BRIDGE = 'bridge'
    MODE_VALID_RANGE = [MODE_ROUTER, MODE_BRIDGE]
    MODE_ROUTER_DHCP = 'dhcp'
    MODE_ROUTER_PPPOE = 'pppoe'
    MODE_ROUTER_STATIC = 'static'
    MODE_ROUTER_VALID_MODES = [MODE_ROUTER_DHCP,
                               MODE_ROUTER_PPPOE, MODE_ROUTER_STATIC]
    PORT_VALID_RANGE = range(1, 65536)
    VLAN_VALID_RANGE = range(1, 4094)
    MODE_ROUTER_DHCP_SERVER_ENABLED = 'enabled'
    MODE_ROUTER_DHCP_SERVER_DISABLED = 'disabled'
    MODE_ROUTER_DHCP_SERVER_VALID_RANGE = [
        MODE_ROUTER_DHCP_SERVER_ENABLED, MODE_ROUTER_DHCP_SERVER_DISABLED]
    IP_ADDRESS_MASK_VALID_RANGE = range(1, 33)

    def set_configuration(self):
        '''
        Adds profile to OLT config. Can be used to set configuration for an existing profile
        '''
        # If using default, then this is a new profile
        if 'profile-id' in self.profile.keys():
            # Get profiles from config
            profiles = list(self.client.get_onu_profiles().keys())
            # We don't need the 'profile-' part
            profiles = list(
                map(lambda x: str(x).replace('profile-', ''), profiles)
            )
            # Remove default profile
            profiles = list(filter(lambda x: x != 'default', profiles))
            # We need integers to compare
            profiles = list(
                map(lambda x: int(x), profiles)
            )
            # Get last profile id, add 1
            new_profile_id = max(profiles) + 1
            new_profile = f'profile-{str(new_profile_id)}'

            self.profile[new_profile] = self.profile.pop('profile-id')

        if self.profile:
            profile_list = {
                'onu-profiles': self.profile,
            }
            data = {
                "SET": profile_list,
            }
            return self.client.set_configuration(data)
        raise Warning('Profile not initialized')

    def add(self):
        '''
        Adds profile to OLT config. Can be used to set configuration for an existing profile
        '''
        return self.set_configuration()

    def save(self):
        '''
        Adds profile to OLT config. Can be used to set configuration for an existing profile.
        '''
        return self.set_configuration()

    def delete(self):
        '''
        Removes profile to OLT config
        '''
        if self.profile:
            profile_list = {
                'onu-profiles': self.profile,
            }
            data = {
                "DELETE": profile_list,
            }
            return self.client.set_configuration(data)
        raise Warning('Profile not initialized')

    def __init__(self, olt_client, name, admin_password,
                 profile_id='profile-id',
                 mode='router',
                 http_port=8080,
                 ssh_enabled=True, ssh_port=22,
                 telnet_enabled=False, telnet_port=23,
                 ubnt_discovery_enabled=True,
                 bandwidth_limit_enabled=True,
                 bandwidth_limit_up=1,
                 bandwidth_limit_down=1,
                 wan_vlan='1', wan_mode='pppoe',
                 wan_access_blocked=False,
                 gateway='',
                 lan_provisioned=True, lan_address='192.168.1.1/24',
                 dhcp_server='enabled',
                 dhcp_pool='192.168.1.101-192.168.1.150',
                 dhcp_lease_time='3600',
                 dns_resolver=['8.8.8.8', '1.1.1.1'],
                 dns_proxy_enable=False,
                 nat_protocol_ftp=True, nat_protocol_pptp=True, nat_protocol_rtsp=True, nat_protocol_sip=True, upnp_enabled=True,
                 port_1_include_vlan=[],
                 port_1_native_vlan='1',
                 port_2_include_vlan=[],
                 port_2_native_vlan='1',
                 port_3_include_vlan=[],
                 port_3_native_vlan='1',
                 port_4_include_vlan=[],
                 port_4_native_vlan=['1'],
                 wifi_native_vlan='1',
                 ):

        self.client = olt_client

        # Profile name
        assert str(name), 'Profile name cannot be blank'
        # Admin password
        assert str(admin_password), 'admin_password name cannot be blank'
        # Admin password
        assert len(
            admin_password) >= 8, 'admin_password must be at least 8 characters long'
        # ONU mode
        assert mode in self.MODE_VALID_RANGE, f'Invalid mode, {mode}'
        # HTTP
        try:
            http_port = int(http_port)
            assert http_port in self.PORT_VALID_RANGE, f'Invalid port, {http_port}'
        except ValueError as ex:
            raise ValueError(f'Invalid port, {http_port}')
        # SSH
        try:
            ssh_port = int(ssh_port)
            assert ssh_port in self.PORT_VALID_RANGE, f'Invalid port, {ssh_port}'
        except ValueError as ex:
            raise ValueError(f'Invalid port, {http_port}')
        # Enabled services, SSH
        assert isinstance(ssh_enabled, bool), f'ssh_enabled must be True/False'
        # Enabled services, TELNET
        assert isinstance(
            telnet_enabled, bool), f'telnet_enabled must be True/False'
        # Enabled services, DISCOVERY
        assert isinstance(ubnt_discovery_enabled,
                          bool), f'discovery_enabled must be True/False'
        # Bandwidth limit
        assert isinstance(bandwidth_limit_enabled,
                          bool), f'bandwidth_limit must be True/False'
        try:
            bandwidth_limit_up = int(bandwidth_limit_up) * self.K
        except ValueError as ex:
            raise ValueError(f'Invalid range, {ex}')
        try:
            bandwidth_limit_down = int(bandwidth_limit_down) * self.K
        except ValueError as ex:
            raise ValueError(f'Invalid range, {ex}')
        assert bandwidth_limit_up >= self.K, f'Invalid range, {bandwidth_limit_up}'
        assert bandwidth_limit_down >= self.K, f'Invalid range, {bandwidth_limit_down}'

        # Basic profile structure
        profile_base = {
            profile_id: {
                'name': name,
                'mode': mode,
                'admin-password': admin_password,
                'lan-provisioned': lan_provisioned,
                'services': {
                    'http-port': http_port,
                    'ssh-enabled': ssh_enabled,
                    'ssh-port': ssh_port,
                    'telnet-enabled': telnet_enabled,
                    'ubnt-discovery-enabled': ssh_enabled,
                },
                'lan-address': lan_address,
                'port': {
                    '1': {
                        'link-speed': 'auto'
                    },
                    '2': {
                        'link-speed': 'auto'
                    },
                    '3': {
                        'link-speed': 'auto'
                    },
                    '4': {
                        'link-speed': 'auto'
                    }
                },
                'bandwidth-limit-enabled': bandwidth_limit_enabled,
                'bandwidth-limit-down': bandwidth_limit_up,
                'bandwidth-limit-up': bandwidth_limit_down
            }
        }

        # Bridge mode values
        if mode == self.MODE_BRIDGE:
            for vlan in port_1_include_vlan:
                try:
                    int(vlan)
                except ValueError as ex:
                    raise ValueError(f'Invalid tagged VLAN in port 1, {vlan}')
            try:
                int(port_1_native_vlan)
            except ValueError as ex:
                raise ValueError(
                    f'Invalid native VLAN in port 1, {port_1_native_vlan}')
            for vlan in port_2_include_vlan:
                try:
                    int(vlan)
                except ValueError as ex:
                    raise ValueError(f'Invalid tagged VLAN in port 2, {vlan}')
            try:
                int(port_2_native_vlan)
            except ValueError as ex:
                raise ValueError(
                    f'Invalid native VLAN in port 2, {port_2_native_vlan}')
            for vlan in port_3_include_vlan:
                try:
                    int(vlan)
                except ValueError as ex:
                    raise ValueError(f'Invalid tagged VLAN in port 3, {vlan}')
            try:
                int(port_3_native_vlan)
            except ValueError as ex:
                raise ValueError(
                    f'Invalid native VLAN in port 3, {port_3_native_vlan}')
            for vlan in port_4_include_vlan:
                try:
                    int(vlan)
                except ValueError as ex:
                    raise ValueError(f'Invalid tagged VLAN in port 4, {vlan}')
            try:
                int(port_4_native_vlan)
            except ValueError as ex:
                raise ValueError(
                    f'Invalid native VLAN in port 4, {port_4_native_vlan}')
            try:
                int(wifi_native_vlan)
            except ValueError as ex:
                raise ValueError(
                    f'Invalid native VLAN in WiFi port, {wifi_native_vlan}')

            bridge_mode = {
                'port': {
                    '1': {
                        'include-vlan': port_1_include_vlan,
                        'native-vlan': port_1_native_vlan
                    },
                    '2': {
                        'include-vlan': port_2_include_vlan,
                        'native-vlan': port_2_native_vlan
                    },
                    '3': {
                        'include-vlan': port_3_include_vlan,
                        'native-vlan': port_3_native_vlan
                    },
                    '4': {
                        'include-vlan': port_4_include_vlan,
                        'native-vlan': port_4_native_vlan
                    },
                    'wifi': {
                        'native-vlan': wifi_native_vlan
                    }
                }
            }
            profile_base['profile-id']['bridge-mode'] = bridge_mode

        if mode == self.MODE_ROUTER:
            # WAN VLAN
            try:
                int(wan_vlan)
            except ValueError as ex:
                raise ValueError(
                    f'Invalid WAN vlan, {wan_vlan}')
            assert int(
                wan_vlan) in self.VLAN_VALID_RANGE, f'Invalid WAN vlan, {wan_vlan}'
            # WAN MODE
            assert wan_mode in self.MODE_ROUTER_VALID_MODES, f'Invalid WAN mode, {wan_mode}'
            # WAN Access Blocked
            assert isinstance(wan_access_blocked,
                              bool), f'wan_access_blocked must be True/False'
            # LAN Provisioned
            assert isinstance(lan_provisioned,
                              bool), f'lan_provisioned must be True/False'
            # LAN Address
            try:
                address = str(lan_address).split('/')[0]
                ipaddress.ip_address(address)
            except ValueError as ex:
                raise ValueError(
                    f'Invalid LAN IP address')
            # LAN Subnet mask
            try:
                mask = int(str(lan_address).split('/')[1])
            except ValueError as ex:
                raise ValueError(
                    f'Invalid netmask for LAN IP address')
            assert mask in self.IP_ADDRESS_MASK_VALID_RANGE, f'mask must be True/False'
            # DHCP server
            assert dhcp_server in self.MODE_ROUTER_DHCP_SERVER_VALID_RANGE,  f'Invalid DHCP server mode, {dhcp_server}'
            # DHCP pool
            dhcp_pool_range = dhcp_pool.split('-')
            assert len(
                dhcp_pool_range) == 2,  f'Invalid DHCP pool, {dhcp_pool}'
            try:
                for address in dhcp_pool_range:
                    ipaddress.ip_address(address)
            except ValueError as ex:
                raise ValueError(
                    f'Invalid IP address for DHCP pool, {address}')
            # DHCP lease time
            try:
                int(dhcp_lease_time)
            except ValueError as ex:
                raise ValueError(
                    f'Invalid lease time for DHCP, {dhcp_lease_time}')
            # DNS servers
            try:
                for server in dns_resolver:
                    ipaddress.ip_address(server)
            except ValueError as ex:
                raise ValueError(
                    f'Invalid IP address for DNS server, {server}')
            # Enabled services, dns_proxy
            assert isinstance(dns_proxy_enable,
                              bool), f'dns_proxy must be True/False'
            # Enabled services, upnp
            assert isinstance(upnp_enabled,
                              bool), f'upnp must be True/False'
            # Enabled services, nat_ftp
            assert isinstance(nat_protocol_ftp,
                              bool), f'nat_ftp must be True/False'
            # Enabled services, nat_pptp
            assert isinstance(nat_protocol_pptp,
                              bool), f'nat_pptp must be True/False'
            # Enabled services, nat_rtsp
            assert isinstance(nat_protocol_rtsp,
                              bool), f'nat_rtsp must be True/False'
            # Enabled services, nat_sip
            assert isinstance(nat_protocol_sip,
                              bool), f'nat_sip must be True/False'
            router_mode = {
                'wan-vlan': str(wan_vlan),
                'wan-mode': wan_mode,
                'nat-protocol-ftp': nat_protocol_ftp,
                'nat-protocol-pptp': nat_protocol_pptp,
                'nat-protocol-rtsp': nat_protocol_rtsp,
                'nat-protocol-sip': nat_protocol_sip,
                'wan-access-blocked': wan_access_blocked,
                'upnp-enabled': upnp_enabled,
                'dns-resolver': dns_resolver,
                'dhcp-server': dhcp_server,
                'dhcp-pool': dhcp_pool,
                'dhcp-lease-time': str(dhcp_lease_time),
                'dns-proxy-enable': dns_proxy_enable
            }

            profile_base['profile-id']['router-mode'] = router_mode

        self.profile = profile_base

        super().__init__()
