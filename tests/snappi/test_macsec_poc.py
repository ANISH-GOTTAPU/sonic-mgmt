from tests.common.fixtures.conn_graph_facts import conn_graph_facts,\
    fanout_graph_facts
from tests.common.snappi.snappi_fixtures import snappi_api_serv_ip, snappi_api_serv_port,\
    snappi_api, snappi_ixnet_session
from ixnetwork_restpy import Files, PortMapAssistant, StatViewAssistant
import time
from tabulate import tabulate
import logging
import pytest
logger = logging.getLogger(__name__)


def test_mka_functionality(snappi_ixnet_session,
                           conn_graph_facts,
                           fanout_graph_facts,
                           duthost):
    # DUT Config
    duthostMACsecConfigMkaFunctionality(duthost)

    # TGEN Config & Verify Test
    ixNetwork = snappi_ixnet_session.Session.Ixnetwork
    logger.info("Loading Configuration")
    ixNetwork.LoadConfig(Files('Test8.1_mka-functionality_Test_pairWiseCA.ixncfg', local_file=True))
    logger.info('connect the virtual ports to test ports')

    port_map = PortMapAssistant(ixNetwork)
    port_map.Map(Location='10.36.77.157;1;13', Name='Ethernet - 001')
    port_map.Map(Location='10.36.77.157;1;14', Name='Ethernet - 002')
    logger.info(port_map)
    port_map.Connect(ForceOwnership=True)

    test_ports = ixNetwork.Vport.find()
    logger.info('Starting All protocols')
    ixNetwork.StartAllProtocols()
    time.sleep(10)

    logger.info('Verifying Protocol Summary')
    protocols_Summary = StatViewAssistant(ixNetwork, 'Protocols Summary')
    for i in range(0, len(protocols_Summary.Rows)):
        if int(protocols_Summary.Rows[i]['Sessions Down']) != 0:
            logger.info(" {} Sessions are Down".format(protocols_Summary.Rows[i]['Protocol Type']))
        else:
            logger.info(" {} Sessions are UP".format(protocols_Summary.Rows[i]['Protocol Type']))

    printStats(ixNetwork, "Protocols Summary", {"Protocols Summary": {'transpose': False},})
    MACsec_global = StatViewAssistant(ixNetwork, 'MACsec Global Port Statistics')
    MACsec_per_port = StatViewAssistant(ixNetwork, 'MACsec Per Port')
    MKA_per_port = StatViewAssistant(ixNetwork, 'MKA Per Port')
    logger.info('\n')
    for i in range(0, len(test_ports)):
        if int(MACsec_global.Rows[i]['Encrypted Byte Rx']) > 0:
            logger.info('Encrypted Byte Rx is > 0 for {}!!'.format(test_ports[i].Name))
        else:
            if int(MACsec_per_port.Rows[i]['Valid Packet Rx']) > 0:
                logger.info('Valid Packet Rx > 0 for {}!!'.format(test_ports[i].Name))
            else:
                logger.info('!!  Valid Packet Rx = 0 for {}!!'.format(test_ports[i].Name))
            if int(MKA_per_port.Rows[i]['MKPDU Tx']) > 0 and int(MKA_per_port.Rows[i]['MKPDU Rx']) > 0:
                logger.info('MKPDU Tx > 0 and MKPDU Rx > 0 for {}!!'.format(test_ports[i].Name))
            else:
                logger.info('MKPDU Tx = 0 and MKPDU Rx = 0 for {}!!'.format(test_ports[i].Name))
    logger.info('\n')
    printStats(ixNetwork, "MACsec Global Port Statistics",
               {"MACsec Global Port Statistics": {'transpose': False},})
    table = []
    table1 = [MACsec_global.Rows[0]['Stat Name'],
              MACsec_global.Rows[0]['Port Name'],
              MACsec_global.Rows[0]['Protected Packet Tx'],
              MACsec_global.Rows[0]['Encrypted Packet Tx'],
              MACsec_global.Rows[0]['Non-MACsec Packet Tx'],
              MACsec_global.Rows[0]['Protected Packet Rx'],
              MACsec_global.Rows[0]['Encrypted Packet Rx'],
              MACsec_global.Rows[0]['Non-MACsec Packet Rx'],
              MACsec_global.Rows[0]['Unknown SCI/SA Accepted'],
              MACsec_global.Rows[0]['Unknown SCI/SA Discarded']]
    table2 = [MACsec_global.Rows[1]['Stat Name'],
              MACsec_global.Rows[1]['Port Name'],
              MACsec_global.Rows[1]['Protected Packet Tx'],
              MACsec_global.Rows[1]['Encrypted Packet Tx'],
              MACsec_global.Rows[1]['Non-MACsec Packet Tx'],
              MACsec_global.Rows[1]['Protected Packet Rx'],
              MACsec_global.Rows[1]['Encrypted Packet Rx'],
              MACsec_global.Rows[1]['Non-MACsec Packet Rx'],
              MACsec_global.Rows[1]['Unknown SCI/SA Accepted'],
              MACsec_global.Rows[1]['Unknown SCI/SA Discarded']]
    table.append(table1)
    table.append(table2)
    columns = ['Stat Name',
               'Port Name',
               'Protected Packet Tx',
               'Encrypted Packet Tx',
               'Non-MACsec Packet Tx',
               'Protected Packet Rx',
               'Encrypted Packet Rx',
               'Non-MACsec Packet Rx',
               'Unknown SCI/SA Accepted',
               'Unknown SCI/SA Discarded']
    logger.info('MACsec Global Port Statistics')
    logger.info("\n%s" % tabulate(table, headers=columns, tablefmt="psql"))
    printStats(ixNetwork, "MACsec Per Port",
               {"MACsec Per Port": {'transpose': False}})

    logger.info('Generating Traffic Item')
    for i in range(0, len(ixNetwork.Traffic.TrafficItem.find())):
        ixNetwork.Traffic.TrafficItem.find()[i].Generate()
    time.sleep(5)
    logger.info('Applying Traffic')
    ixNetwork.Traffic.Apply()
    time.sleep(5)
    logger.info('Starting Traffic')
    ixNetwork.Traffic.StartStatelessTrafficBlocking()
    time.sleep(20)
    tiStatistics = StatViewAssistant(ixNetwork, 'Traffic Item Statistics')
    for i in range(0, len(tiStatistics.Rows)):
        if float(tiStatistics.Rows[i]['Loss %']) <= 0.3:
            logger.info('PASS, Encrypted {} is flowing with {} percent loss'.format(tiStatistics.Rows[i]['Traffic Item'],float(tiStatistics.Rows[i]['Loss %'])))
        else:
            pytest.fail('FAIL, Encrypted {} is flowing with {} percent loss'.format(tiStatistics.Rows[i]['Traffic Item'],float(tiStatistics.Rows[i]['Loss %'])))

    printStats(ixNetwork, "MACsec Per Port",
               {"MACsec Per Port": {'transpose': False}})
    table = []
    for i in range(0, len(ixNetwork.Traffic.TrafficItem.find())):
        table1 = []
        table1.append(tiStatistics.Rows[i]['Tx Frames'])
        table1.append(tiStatistics.Rows[i]['Rx Frames'])
        table1.append(tiStatistics.Rows[i]['Loss %'])
        table.append(table1)
        columns = ['Tx Frames', 'Rx Frames', 'Loss%']
    logger.info('Traffic Item Statistics')
    logger.info("\n%s" % tabulate(table, headers=columns, tablefmt="psql"))
    logger.info('Done')


def test_macsec_impact(snappi_ixnet_session,
                       conn_graph_facts,
                       fanout_graph_facts,
                       duthost):
    # DUT Config
    duthostMACsecConfigImpact(duthost)

    # Tgen Config and test
    ixNetwork = snappi_ixnet_session.Session.Ixnetwork
    logger.info("Loading Configuration")
    ixNetwork.LoadConfig(Files('Test9.1_macsec_impact_L2_traffic.ixncfg', local_file=True))
    logger.info('connect the virtual ports to test ports')

    port_map = PortMapAssistant(ixNetwork)
    port_map.Map(Location='10.36.77.157;1;13', Name='Ethernet - 001')
    port_map.Map(Location='10.36.77.157;1;14', Name='Ethernet - 002')
    logger.info(port_map)
    port_map.Connect(ForceOwnership=True)

    test_ports = ixNetwork.Vport.find()
    logger.info('Starting All protocols')
    ixNetwork.StartAllProtocols()
    time.sleep(10)

    logger.info('Verifying Protocol Summary')
    protocols_Summary = StatViewAssistant(ixNetwork, 'Protocols Summary')
    for i in range(0, len(protocols_Summary.Rows)):
        if int(protocols_Summary.Rows[i]['Sessions Down']) != 0:
            logger.info(" {} Sessions are Down".format(protocols_Summary.Rows[i]['Protocol Type']))
        else:
            logger.info(" {} Sessions are UP".format(protocols_Summary.Rows[i]['Protocol Type']))

    printStats(ixNetwork, "Protocols Summary",
               {"Protocols Summary": {'transpose': False}})
    MACsec_global = StatViewAssistant(ixNetwork,
                                      'MACsec Global Port Statistics')
    MACsec_per_port = StatViewAssistant(ixNetwork, 'MACsec Per Port')
    MKA_per_port = StatViewAssistant(ixNetwork, 'MKA Per Port')
    logger.info('\n')
    for i in range(0, len(test_ports)):
        if int(MACsec_global.Rows[i]['Encrypted Byte Rx']) > 0:
            logger.info('Encrypted Byte Rx is > 0 for {}!!'.format(test_ports[i].Name))
        else:
            if int(MACsec_per_port.Rows[i]['Valid Packet Rx']) > 0:
                logger.info('Valid Packet Rx > 0 for {}!!'.format(test_ports[i].Name))
            else:
                logger.info('!!  Valid Packet Rx = 0 for {}!!'.format(test_ports[i].Name))
            if int(MKA_per_port.Rows[i]['MKPDU Tx']) > 0 and int(MKA_per_port.Rows[i]['MKPDU Rx']) > 0:
                logger.info('MKPDU Tx > 0 and MKPDU Rx > 0 for {}!!'.format(test_ports[i].Name))
            else:
                logger.info('MKPDU Tx = 0 and MKPDU Rx = 0 for {}!!'.format(test_ports[i].Name))
    logger.info('\n')
    printStats(ixNetwork, "MACsec Global Port Statistics",
               {"MACsec Global Port Statistics": {'transpose': False}})
    table = []
    table1 = [MACsec_global.Rows[0]['Stat Name'],
              MACsec_global.Rows[0]['Port Name'],
              MACsec_global.Rows[0]['Protected Packet Tx'],
              MACsec_global.Rows[0]['Encrypted Packet Tx'],
              MACsec_global.Rows[0]['Non-MACsec Packet Tx'],
              MACsec_global.Rows[0]['Protected Packet Rx'],
              MACsec_global.Rows[0]['Encrypted Packet Rx'],
              MACsec_global.Rows[0]['Non-MACsec Packet Rx'],
              MACsec_global.Rows[0]['Unknown SCI/SA Accepted'],
              MACsec_global.Rows[0]['Unknown SCI/SA Discarded']]
    table2 = [MACsec_global.Rows[1]['Stat Name'],
              MACsec_global.Rows[1]['Port Name'],
              MACsec_global.Rows[1]['Protected Packet Tx'],
              MACsec_global.Rows[1]['Encrypted Packet Tx'],
              MACsec_global.Rows[1]['Non-MACsec Packet Tx'],
              MACsec_global.Rows[1]['Protected Packet Rx'],
              MACsec_global.Rows[1]['Encrypted Packet Rx'],
              MACsec_global.Rows[1]['Non-MACsec Packet Rx'],
              MACsec_global.Rows[1]['Unknown SCI/SA Accepted'],
              MACsec_global.Rows[1]['Unknown SCI/SA Discarded']]
    table.append(table1)
    table.append(table2)
    columns = ['Stat Name',
               'Port Name',
               'Protected Packet Tx',
               'Encrypted Packet Tx',
               'Non-MACsec Packet Tx',
               'Protected Packet Rx',
               'Encrypted Packet Rx',
               'Non-MACsec Packet Rx',
               'Unknown SCI/SA Accepted',
               'Unknown SCI/SA Discarded']
    logger.info('MACsec Global Port Statistics')
    logger.info("\n%s" % tabulate(table, headers=columns, tablefmt="psql"))
    printStats(ixNetwork, "MACsec Per Port", 
               {"MACsec Per Port": {'transpose': False}})

    logger.info('Generating Traffic Item')
    for i in range(0, len(ixNetwork.Traffic.TrafficItem.find())):
        ixNetwork.Traffic.TrafficItem.find()[i].Generate()
    time.sleep(5)
    logger.info('Applying Traffic')
    ixNetwork.Traffic.Apply()
    time.sleep(5)
    logger.info('Starting Traffic')
    ixNetwork.Traffic.StartStatelessTrafficBlocking()
    time.sleep(20)
    tiStatistics = StatViewAssistant(ixNetwork, 'Traffic Item Statistics')
    for i in range(0, len(tiStatistics.Rows)):
        if float(tiStatistics.Rows[i]['Loss %']) <= 0.3:
            logger.info('PASS, Encrypted {} is flowing with {} percent loss'.format(tiStatistics.Rows[i]['Traffic Item'],float(tiStatistics.Rows[i]['Loss %'])))
        else:
            pytest.fail('FAIL, Encrypted {} is flowing with {} percent loss'.format(tiStatistics.Rows[i]['Traffic Item'],float(tiStatistics.Rows[i]['Loss %'])))

    printStats(ixNetwork, "MACsec Per Port",
               {"MACsec Per Port": {'transpose': False}})
    table = []
    for i in range(0, len(ixNetwork.Traffic.TrafficItem.find())):
        table1 = []
        table1.append(tiStatistics.Rows[i]['Tx Frames'])
        table1.append(tiStatistics.Rows[i]['Rx Frames'])
        table1.append(tiStatistics.Rows[i]['Loss %'])
        table.append(table1)
        columns = ['Tx Frames', 'Rx Frames', 'Loss%']
    logger.info('Traffic Item Statistics')
    logger.info("\n%s" % tabulate(table, headers=columns, tablefmt="psql"))
    logger.info('Done')


def duthostMACsecConfigMkaFunctionality(duthost):
    # Enable MACSec Feature
    duthost.shell("sudo config feature state macsec enabled")

    # Add MACSec Profile
    duthost.shell('redis-cli -n 4 hmset "MACSEC_PROFILE|test_profile" "priority" "64" "cipher_suite" "GCM-AES-128" "primary_cak" "0123456789ABCDEF0123456789ABCDEF" "primary_ckn" "6162636465666768696A6B6C6D6E6F707172737475767778797A303132333435" "fallback_cak" "" "fallback_ckn" "" "policy" "security" "enable_replay_protect" "false" "replay_window" "0" "send_sci" "true" "rekey_period" "0"')

    # Enable MACsec profile in Ethernet0
    duthost.shell('redis-cli -n 4 hmset "PORT|Ethernet0" "macsec" "test_profile"')

    # Add a MACsec profile1
    duthost.shell('redis-cli -n 4 hmset "MACSEC_PROFILE|test_profile1" "priority" "64" "cipher_suite" "GCM-AES-128" "primary_cak" "AA23456789ABCDEF0123456789ABCDAA" "primary_ckn" "AA62636465666768696A6B6C6D6E6F707172737475767778797A3031323334AA" "fallback_cak" "" "fallback_ckn" "" "policy" "security" "enable_replay_protect" "false" "replay_window" "0" "send_sci" "true" "rekey_period" "0"')

    # Enable MACsec profile in Ethernet4
    duthost.shell('redis-cli -n 4 hmset "PORT|Ethernet4" "macsec" "test_profile1"')

    try:
        # remove ip setting from interfaces in the previous test if any
        duthost.shell("sudo config interface ip remove Ethernet0 20.1.1.2/24")
        duthost.shell("sudo config interface ip remove Ethernet4 22.1.1.2/24")
        duthost.shell("sudo config vlan member del 4 Ethernet0")
        duthost.shell("sudo config vlan member del 4 Ethernet4")
        duthost.shell("sudo config vlan del 4")
    except:
        pass

    # Configure IP interfaces on the port on both interfaces
    duthost.shell("sudo config interface ip add Ethernet4 22.1.1.2/24")
    duthost.shell("sudo config interface ip add Ethernet0 20.1.1.2/24")

    duthost.shell("ip macsec show")

    time.sleep(10)


def duthostMACsecConfigImpact(duthost):
    # # Enable MACSec Feature
    # duthost.shell("sudo config feature state macsec enabled")

    # # Add MACSec Profile
    # duthost.shell('redis-cli -n 4 hmset "MACSEC_PROFILE|test_profile" "priority" "64" "cipher_suite" "GCM-AES-128" "primary_cak" "0123456789ABCDEF0123456789ABCDEF" "primary_ckn" "6162636465666768696A6B6C6D6E6F707172737475767778797A303132333435" "fallback_cak" "" "fallback_ckn" "" "policy" "security" "enable_replay_protect" "false" "replay_window" "0" "send_sci" "true" "rekey_period" "0"')

    # # Enable MACsec profile in Ethernet0
    # duthost.shell('redis-cli -n 4 hmset "PORT|Ethernet0" "macsec" "test_profile"')

    # # Add a MACsec profile1
    # duthost.shell('redis-cli -n 4 hmset "MACSEC_PROFILE|test_profile1" "priority" "64" "cipher_suite" "GCM-AES-128" "primary_cak" "AA23456789ABCDEF0123456789ABCDAA" "primary_ckn" "AA62636465666768696A6B6C6D6E6F707172737475767778797A3031323334AA" "fallback_cak" "" "fallback_ckn" "" "policy" "security" "enable_replay_protect" "false" "replay_window" "0" "send_sci" "true" "rekey_period" "0"')

    # # Enable MACsec profile in Ethernet4
    # duthost.shell('redis-cli -n 4 hmset "PORT|Ethernet4" "macsec" "test_profile1"')

    try:
        # remove ip setting from interfaces in the previous test if any
        duthost.shell("sudo config interface ip remove Ethernet0 20.1.1.2/24")
        duthost.shell("sudo config interface ip remove Ethernet4 22.1.1.2/24")
        duthost.shell("sudo config vlan member del 4 Ethernet0")
        duthost.shell("sudo config vlan member del 4 Ethernet4")
        duthost.shell("sudo config vlan del 4")
    except:
        pass

    # add vlan and ip interfaces for the current test:
    duthost.shell("sudo config vlan add 4")
    duthost.shell("sudo config vlan member add -u 4 Ethernet0")
    duthost.shell("sudo config vlan member add -u 4 Ethernet4")

    duthost.shell("ip macsec show")

    time.sleep(10)

def printStats(ixNetwork, vName, printoptions={}):
    if isinstance(vName, list):
        [printStats(view, printoptions) for view in vName]
    else:
        transpose = True
        try: transpose = printoptions[vName]["transpose"]
        except: pass
        view = StatViewAssistant(ixNetwork, vName)
        data = view.Rows.RawData
        columnCaptions = view.ColumnHeaders
        cheader = columnCaptions[:]
        
        if vName in printoptions and "toprint" in printoptions[vName]:
            cheader = printoptions[vName]["toprint"]
        if vName in printoptions  and 'nottoprint' in printoptions[vName]:
            [cheader.remove(st) for st in printoptions[vName]['nottoprint']]

        rows = []
        for row in data:
            tmp = [row[columnCaptions.index(col)] for col in cheader]
            rows.append(tmp[:])

        if transpose:
            rows.insert(0, cheader)
            rows = list(zip(*rows))
            cheader = []
        logger.info('\n"%s"\n' % (vName,)+tabulate(rows, headers=cheader, tablefmt="psql"))
        logger.info(len(data))
