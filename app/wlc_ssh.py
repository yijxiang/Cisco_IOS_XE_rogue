from ttp import ttp
from datetime import datetime
from common import show_rogue_detail_ttp_cleanup, show_ap_clean_air_ttp_cleanup
import re


def wlc_summary_data(data):
    # print(data)
    _data = []
    mac = '[0-9a-fA-F]{2}\:[0-9a-fA-F]{2}\:[0-9a-fA-F]{2}\:[0-9a-fA-F]{2}\:[0-9a-fA-F]{2}\:[0-9a-fA-F]{2}'
    rogue_str = re.compile(r'''({m})\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(-\d+)+\s+(\S+)\s+'''.format(m=mac))
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


def show_rogue_detail_wlc_ttp(data):
    ttp_template = """
<group>
Rogue BSSID...................................... {{rogue_mac}}
State............................................ {{rogue_state}}
First Time Rogue was Reported.................... {{rogue_first_saw | ORPHRASE}}
<group name="reported_ap*">
        MAC Address.............................. {{ap_mac}}  
        Name..................................... {{ap_name}}
        Radio Type............................... {{radio_type | ORPHRASE}}
        SSID..................................... {{rogue_ssid | ORPHRASE}}
        Channel.................................. {{channel | ORPHRASE}}
        RSSI..................................... {{rogue_rssi | to_int}} dBm
        SNR...................................... {{rogue_snr | to_int}} dB
</group>
</group>
"""
    parser = ttp(data=data, template=ttp_template)
    parser.parse()
    return parser.result()[0][0]


def ap_ttp(data):
    ttp_template = """
<group>
ap_name                          mac               slot state    oper_state  channel            txpwr         bss       {{ _headers_ }}
</group>"""
    parser = ttp(data=data, template=ttp_template)
    parser.parse()
    return parser.result()[0][0]


def show_ap_clean_air_wlc_ttp(data):
    ttp_template = """
<group>
ap_name            channel avg_aq min_aq interferers {{ _headers_ }}
</group>"""
    parser = ttp(data=data, template=ttp_template)
    parser.parse()
    return parser.result()[0][0]


def wlc_sysinfo(data):
    ttp_template = """
Product Version.................................. {{os_version}}
System Name...................................... {{hostname| ORPHRASE}}
System Location.................................. {{location| ORPHRASE}}
Redundancy Mode.................................. {{ha_mode| ORPHRASE}}
IP Address....................................... {{ip}}
Last Reset....................................... {{last_reset_reason| ORPHRASE}} 
System Up Time................................... {{uptime| ORPHRASE}}
Configured Country............................... {{country| ORPHRASE}}
Fan Status....................................... {{fan_status}}
Fan Speed Mode................................... {{fan_speed_mode}}
State of 802.11b Network......................... {{802_11b_state}}
State of 802.11a Network......................... {{802_11a_state}}
Number of WLANs.................................. {{wlan_count| to_int}}
Number of Active Clients......................... {{client_count| to_int}}
Maximum number of APs supported.................. {{max_ap| to_int}}
Licensing Type................................... {{license_type| ORPHRASE}}
"""
    parser = ttp(data=data, template=ttp_template)
    parser.parse()
    return parser.result()[0][0]


def ap_ttp_cleanup(data):
    _data_ = []
    _ap_name = []
    for ap in data:
        if ap.get("ap_name") in _ap_name:
            continue
        if "ENABLED" not in ap.pop("state"):
            continue
        if not ap.get("slot").isdigit():
            continue
        _txpwr = ap.pop("txpwr")
        _channel = ap.pop("channel")
        ap["ap_mac"] = ap.pop("mac")
        # if "*" in _txpwr:
        #     ap["TPC"] = "*"
        # else:
        #     ap["TPC"] = ""
        # ap["DCA"] = _channel.split(")")[1]
        if "(Monitor)" in _channel:
            continue
        if "(" in _channel:
            ap["channel"] = _channel.split("(")[1].split(")")[0]
        elif "*" in _channel:
            ap["channel"] = _channel.split("*")[0]
        else:
            ap["channel"] = _channel
        ap["txpwr"] = int(_txpwr.split("(")[1].split()[0])
        # ignore some data
        ap.pop("oper_state")
        if "mode" in ap.keys():
            ap.pop("mode")
        if "bss" in ap.keys():
            ap.pop("bss")
        _data_.append(ap)
        _ap_name.append(ap.get("ap_name"))
    return _data_


def wlc_rogue_data(data):
    _data_1 = show_rogue_detail_wlc_ttp(data)
    _data = show_rogue_detail_ttp_cleanup(_data_1)
    return _data


def wlc_ap_data(data):
    _data_1 = ap_ttp(data)
    _data = ap_ttp_cleanup(_data_1)
    return _data


def wlc_clean_air_data(data):
    _data_1 = show_ap_clean_air_wlc_ttp(data)
    _data = show_ap_clean_air_ttp_cleanup(_data_1)
    return _data


def wlc_ssh(_ap, _rogue, _clean_air):
    _ap_data = wlc_ap_data(_ap)
    _rogue_data = wlc_rogue_data(_rogue)
    _clean_air_data = wlc_clean_air_data(_clean_air)

    print(f'WLC_SSH - Count of AP/Rogue-AP/Clean_air: {len(_ap_data)}/{len(_rogue_data)}/{len(_clean_air_data)}')

    return {
        "ap": _ap_data,
        "rogue": _rogue_data,
        "clean_air": _clean_air_data
    }
