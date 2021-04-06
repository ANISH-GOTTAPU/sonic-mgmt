"""
This module contains the necessary fixtures for running test cases with
Ixia devices and IxNetwork. If more fixtures are required, they should be
included in this file.
"""

import pytest
from ixnetwork_restpy import SessionAssistant
from tests.common.fixtures.conn_graph_facts import conn_graph_facts,\
    fanout_graph_facts
from tests.common.ixia.common_helpers import get_vlan_subnet, get_addrs_in_subnet,\
    get_peer_ixia_chassis
from tests.common.ixia.ixia_helpers import IxiaFanoutManager, get_tgen_location
import snappi

# TODO: remove abstract imports after all tests are migrated to snappi.
try:
    from abstract_open_traffic_generator.port import Port
    from abstract_open_traffic_generator.config import Options, Config
    from abstract_open_traffic_generator.layer1 import Layer1, FlowControl,\
        Ieee8021qbb, AutoNegotiation
    from abstract_open_traffic_generator.device import Device, Ethernet, Ipv4,\
        Pattern
    from ixnetwork_open_traffic_generator.ixnetworkapi import IxNetworkApi
    from abstract_open_traffic_generator.port import Options as PortOptions

except ImportError as e:
    raise pytest.skip.Exception("Test case is skipped: " + repr(e), allow_module_level=True)

@pytest.fixture(scope = "module")
def ixia_api_serv_ip(tbinfo):
    """
    In an Ixia testbed, there is no PTF docker.
    Hence, we use ptf_ip field to store Ixia API server.
    This fixture returns the IP address of the Ixia API server.

    Args:
       tbinfo (pytest fixture): fixture provides information about testbed

    Returns:
        Ixia API server IP
    """
    return tbinfo['ptf_ip']


@pytest.fixture(scope = "module")
def ixia_api_serv_user(duthosts, rand_one_dut_hostname):
    """
    Return the username of Ixia API server.

    Args:
        duthost (pytest fixture): The duthost fixture.

    Returns:
        Ixia API server username.
    """
    duthost = duthosts[rand_one_dut_hostname]
    return duthost.host.options['variable_manager']._hostvars[duthost.hostname]['secret_group_vars']['ixia_api_server']['user']


@pytest.fixture(scope = "module")
def ixia_api_serv_passwd(duthosts, rand_one_dut_hostname):
    """
    Return the password of Ixia API server.

    Args:
        duthost (pytest fixture): The duthost fixture.

    Returns:
        Ixia API server password.
    """
    duthost = duthosts[rand_one_dut_hostname]
    return duthost.host.options['variable_manager']._hostvars[duthost.hostname]['secret_group_vars']['ixia_api_server']['password']


@pytest.fixture(scope = "module")
def ixia_api_serv_port(duthosts, rand_one_dut_hostname):
    """
    This fixture returns the TCP port for REST API of the ixia API server.

    Args:
        duthost (pytest fixture): The duthost fixture.

    Returns:
        Ixia API server REST port.
    """
    duthost = duthosts[rand_one_dut_hostname]
    return duthost.host.options['variable_manager']._hostvars[duthost.hostname]['secret_group_vars']['ixia_api_server']['rest_port']


@pytest.fixture(scope = "module")
def ixia_api_serv_session_id(duthosts, rand_one_dut_hostname):
    """
    Ixia API server can spawn multiple session on the same REST port.
    Optional for LINUX, required for windows return the session ID.

    Args:
        duthost (pytest fixture): The duthost fixture.

    Returns:
        Ixia API server session id.
    """
    duthost = duthosts[rand_one_dut_hostname]
    return duthost.host.options['variable_manager']._hostvars[duthost.hostname]['secret_group_vars']['ixia_api_server']['session_id']


@pytest.fixture(scope = "module")
def ixia_dev(duthosts, rand_one_dut_hostname, fanouthosts):
    """
    Returns the Ixia chassis IP. This fixture can return multiple IPs if
    multiple Ixia chassis are present in the test topology.

    Args:
        duthost (pytest fixture): The duthost fixture.
        fanouthosts (pytest fixture): The fanouthosts fixture.

    Returns:
        Dictionary of Ixia Chassis IP/IPs.
    """
    duthost = duthosts[rand_one_dut_hostname]
    result = dict()
    ixia_dev_hostnames = fanouthosts.keys()
    for hostname in ixia_dev_hostnames:
        result[hostname] = duthost.host.options['inventory_manager'].get_host(hostname).get_vars()['ansible_host']
    return result


@pytest.fixture(scope = "function")
def ixia_api_server_session(
        ixia_api_serv_ip,
        ixia_api_serv_user,
        ixia_api_serv_passwd,
        ixia_api_serv_port,
        ixia_api_serv_session_id) :
    """
    Ixia session manager fixture.

    Args:
        ixia_api_serv_ip (pytest fixture): ixia_api_serv_ip fixture
        ixia_api_serv_user (pytest fixture): ixia_api_serv_user fixture.
        ixia_api_serv_passwd (pytest fixture): ixia_api_serv_passwd fixture.
        ixia_api_serv_port (pytest fixture): ixia_api_serv_port fixture.
        ixia_api_serv_session_id (pytest fixture): ixia_api_serv_session_id
            fixture.

    Returns:
        IxNetwork Session
    """

    if (ixia_api_serv_session_id.lower() != 'none') :
        session = SessionAssistant(IpAddress=ixia_api_serv_ip,
                                   UserName=ixia_api_serv_user,
                                   Password=ixia_api_serv_passwd,
                                   RestPort=ixia_api_serv_port,
                                   SessionId=ixia_api_serv_session_id)
    else :
        session = SessionAssistant(IpAddress=ixia_api_serv_ip,
                                   UserName=ixia_api_serv_user,
                                   Password=ixia_api_serv_passwd,
                                   RestPort=ixia_api_serv_port)
    ixNetwork = session.Ixnetwork
    ixNetwork.NewConfig()

    yield session

    ixNetwork.NewConfig()
    session.Session.remove()

@pytest.fixture(scope = "module")
def ixia_api(ixia_api_serv_ip,
             ixia_api_serv_port,
             ixia_api_serv_user,
             ixia_api_serv_passwd):

    """
    Ixia session fixture for Tgen API

    Args:
        ixia_api_serv_ip (pytest fixture): ixia_api_serv_ip fixture
        ixia_api_serv_port (pytest fixture): ixia_api_serv_port fixture.
        ixia_api_serv_user (pytest fixture): ixia_api_serv_user fixture.
        ixia_api_serv_passwd (pytest fixture): ixia_api_serv_passwd fixture.

    Returns:
        IxNetwork Session

    """
    api_session = IxNetworkApi(address=ixia_api_serv_ip,
                               port=ixia_api_serv_port,
                               username=ixia_api_serv_user,
                               password=ixia_api_serv_passwd)

    yield api_session

    if api_session:
        api_session.assistant.Session.remove()


@pytest.fixture(scope='module')
def snappi_api(ixia_api_serv_ip,
               ixia_api_serv_port):
    """
    Snappi session fixture for snappi Tgen API
    Args:
        ixia_api_serv_ip (pytest fixture): ixia_api_serv_ip fixture
        ixia_api_serv_port (pytest fixture): ixia_api_serv_port fixture.
    """
    host = "https://" + ixia_api_serv_ip + ":" + str(ixia_api_serv_port)
    # TODO: Currently extension is defaulted to ixnetwork.
    # Going forward, we should be able to specify extension
    # from command line while running pytest.
    api = snappi.api(host=host, ext="ixnetwork")

    yield api

    if getattr(api, 'assistant', None) is not None:
        api.assistant.Session.remove()


@pytest.fixture(scope = "function")
def ixia_testbed(conn_graph_facts,
                 fanout_graph_facts,
                 duthosts,
                 rand_one_dut_hostname,
                 snappi_api):

    """
    L2/L3 Tgen API config for the T0 testbed

    Args:
        conn_graph_facts (pytest fixture)
        fanout_graph_facts (pytest fixture)
        duthosts (pytest fixture): list of DUTs
        rand_one_dut_hostname (pytest fixture): DUT hostname

    Returns:
        L2/L3 config for the T0 testbed
    """
    duthost = duthosts[rand_one_dut_hostname]
    ixia_fanout = get_peer_ixia_chassis(conn_data=conn_graph_facts,
                                        dut_hostname=duthost.hostname)

    if ixia_fanout is None:
        return None

    ixia_fanout_id = list(fanout_graph_facts.keys()).index(ixia_fanout)
    ixia_fanout_list = IxiaFanoutManager(fanout_graph_facts)
    ixia_fanout_list.get_fanout_device_details(device_number=ixia_fanout_id)

    ixia_ports = ixia_fanout_list.get_ports(peer_device=duthost.hostname)

    port_names = list()
    port_speed = None

    """ L1 config """
    config = snappi_api.config()
    for i in range(len(ixia_ports)):
        config.ports.port(name='Port {}'.format(i),
                          location=get_tgen_location(ixia_ports[i]))

        if port_speed is None:
            port_speed = int(ixia_ports[i]['speed'])

        elif port_speed != int(ixia_ports[i]['speed']):
            """ All the ports should have the same bandwidth """
            return None

    port_names = [port.name for port in config.ports]
    config.options.port_options.location_preemption = True
    l1_config = config.layer1.layer1()[-1]
    l1_config.name = 'port settings'
    l1_config.port_names = [port.name for port in config.ports]
    l1_config.speed = 'speed_%d_gbps' % int(port_speed/1000)
    l1_config.auto_negotiate = False
    l1_config.auto_negotiation.link_training = True
    l1_config.auto_negotiation.rs_fec = True
    l1_config.ieee_media_defaults = False

    pfc = l1_config.flow_control.ieee_802_1qbb
    pfc.pfc_delay = 0
    pfc.pfc_class_0 = 0
    pfc.pfc_class_1 = 1
    pfc.pfc_class_2 = 2
    pfc.pfc_class_3 = 3
    pfc.pfc_class_4 = 4
    pfc.pfc_class_5 = 5
    pfc.pfc_class_6 = 6
    pfc.pfc_class_7 = 7

    l1_config.flow_control.choice = l1_config.flow_control.IEEE_802_1QBB

    """ L2/L3 config """
    vlan_subnet = get_vlan_subnet(duthost)
    if vlan_subnet is None:
        return None

    vlan_ip_addrs = get_addrs_in_subnet(vlan_subnet, len(ixia_ports))
    gw_addr = vlan_subnet.split('/')[0]
    prefix = vlan_subnet.split('/')[1]

    for i in range(len(ixia_ports)):
        dev = config.devices.device(name='Device {}'.format(i),
                                    container_name=port_names[i])[-1]

        eth = dev.ethernet
        eth.name = 'Ethernet {}'.format(i)
        ipv4 = eth.ipv4
        ipv4.name = 'Ipv4 {}'.format(i)
        ipv4.address = vlan_ip_addrs[i]
        ipv4.prefix = prefix
        ipv4.gateway = gw_addr

    return config
