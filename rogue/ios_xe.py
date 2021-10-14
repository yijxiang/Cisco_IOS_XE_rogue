from ttp import ttp
from .common import show_rogue_detail_ttp_cleanup, show_ap_dot11_x_summary_ttp_cleanup, show_ap_clean_air_ttp_cleanup, show_ap_load_ttp_cleanup
import re


def ios_summary_data(data):
    _data = []
    mac = '[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}'
    rogue_str = re.compile(r'''({m})\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(-\d+)+\s+(\d+)\s+'''.format(m=mac))
    found = re.findall(rogue_str, data)
    for i in found:
        rogue_ap_mac, rssi, channel = i
        _channel = channel
        if "," in channel:
            _channel = channel.split("(")[1].split(",")[0]
        if not _channel.isdigit():
            continue
        _one_data = {
            "rogue_ap_mac": rogue_ap_mac,
            "rssi": int(rssi),
            "channel": int(_channel)
        }
        _data.append(_one_data)
    return _data


def show_rogue_detail_ttp(data):
    ttp_template = """
<group>
Rogue BSSID                            : {{rogue_mac}}
Last heard Rogue SSID                  : {{rogue_ssid | ORPHRASE}}
State                                  : {{rogue_state}}
First Time Rogue was Reported          : {{rogue_first_saw | ORPHRASE}}
<group name="reported_ap*">
  AP Name : {{ap_name}}
    Detecting slot ID                  : {{slot}}
    Radio Type                         : {{radio_type | ORPHRASE}}
    Channel                            : {{channel | ORPHRASE}}
      Channels                         : {{rogue_channels | joinmatches(',')}}
    RSSI                               : {{rogue_rssi | to_int}} dBm
    SNR                                : {{rogue_snr | to_int}} dB
</group>
</group>
"""
    parser = ttp(data=data, template=ttp_template)
    parser.parse()
    return parser.result()[0][0]


def show_ap_dot11_x_summary_ttp(data):
    ttp_template = """
<group>
ap_name                           mac             slot    state          oper_state    width    txpwr           channel                             mode {{ _headers_ }}
</group>"""
    parser = ttp(data=data, template=ttp_template)
    parser.parse()
    return parser.result()[0][0]


def show_ap_load_ttp(data):
    ttp_template = """
<group>
ap_name                           mac             slot  channel_utilization      clients {{ _headers_ }}
</group>"""
    parser = ttp(data=data, template=ttp_template)
    parser.parse()
    return parser.result()[0][0]


def show_ap_clean_air_ttp(data):
    ttp_template = """
<group>
ap_name               channel    avg_aq  min_aq  interferers  spectrum_ap_type {{ _headers_ }}
</group>"""
    parser = ttp(data=data, template=ttp_template)
    parser.parse()
    return parser.result()[0][0]


def ios_version(data):
    ttp_template = """
Cisco IOS XE Software, Version {{os_version}}
{{hostname| ORPHRASE}} uptime is {{ignore| re(".*")}}
System restarted at {{restart_time| ORPHRASE}}
Last reload reason: {{last_reset_reason| ORPHRASE}}
AIR License Level: {{license_level| ORPHRASE}}
Smart Licensing Status: {{license_status| ORPHRASE}}
Installation mode is {{install_mode}}
"""
    parser = ttp(data=data, template=ttp_template)
    parser.parse()
    return [parser.result()[0][0]]


def ios_rogue_data(data):
    _data_1 = show_rogue_detail_ttp(data)
    _data = show_rogue_detail_ttp_cleanup(_data_1)
    return _data


def ios_ap_data(data):
    _data_1 = show_ap_dot11_x_summary_ttp(data)
    _data = show_ap_dot11_x_summary_ttp_cleanup(_data_1)
    return _data


def ios_load_data(data):
    _data_1 = show_ap_load_ttp(data)
    _data = show_ap_load_ttp_cleanup(_data_1)
    return _data


def ios_clean_air_data(data):
    _data_1 = show_ap_clean_air_ttp(data)
    _data = show_ap_clean_air_ttp_cleanup(_data_1)
    return _data


def ios_xe(_ap, _load, _rogue, _clean_air):
    _ap_data = ios_ap_data(_ap)
    _load_data = ios_load_data(_load)
    _rogue_data = ios_rogue_data(_rogue)
    _clean_air_data = ios_clean_air_data(_clean_air)

    print(f'IOS XE - Count of AP/Load/Rogue-AP/Clean_air: {len(_ap_data)}/{len(_load_data)}/{len(_rogue_data)}/{len(_clean_air_data)}')

    return {
        "ap": _ap_data,
        "load": _load_data,
        "rogue": _rogue_data,
        "clean_air": _clean_air_data
    }


def ios_wlan_data(data):
    ttp_template = """
<group>
id   profile_name                     ssid                             status security                            {{ _headers_ }}
</group>"""
    parser = ttp(data=data, template=ttp_template)
    parser.parse()

    _data = []
    for i in parser.result()[0][0]:
        if "UP" not in i.get("status"):
            continue
        i.pop("security")
        _data.append(i)
    return _data
