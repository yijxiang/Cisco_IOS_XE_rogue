"""Python example script showing proper use of the Cisco Sample Code header.
Copyright (c) 2021 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

import os
from datetime import datetime

import click
import pandas as pd
import yaml
from netmiko import ConnectHandler

from rogue.common import channel_5G_24G, co_channel_5G, adj_channel_5G
from rogue.ios_xe import ios_rogue_data, ios_ap_data, ios_load_data, ios_clean_air_data, ios_summary_data, ios_version, \
    ios_wlan_data
from rogue.wlc_ssh import wlc_ap_data, wlc_rogue_data, wlc_clean_air_data, wlc_summary_data, wlc_sysinfo, wlc_wlan_data

cmd_dict = {
    "cisco_wlc_ssh": {
        "rogue_summary": "show rogue ap summary",
        "rogue": "show rogue ap detailed"
    },
    "cisco_ios": {
        "rogue_summary": "show wireless wps rogue ap summary",
        "rogue": "show wireless wps rogue ap detailed"
    }
}

g_device_type = {
    "aireos": "cisco_wlc_ssh",
    "ios": "cisco_ios",
    "cisco_wlc_ssh": "aireos",
    "cisco_ios": "ios"
}


def rogue_channel_data_ios_5G(_load, _ap, _rogue):
    _ap_ = {}
    _load_ = {}
    _rogue_ = []

    for i in _load:
        _load_[f'{i["ap_name"]}_{i["slot"]}'] = i
    for i in _ap:
        ap_key = f'{i["ap_name"]}_{i["slot"]}'
        if ap_key in _load_.keys():
            i.update(_load_[ap_key])
            _ap_[ap_key] = i
    for i in _rogue:
        ap_key = f'{i["ap_name"]}_{i["slot"]}'
        if ap_key in _ap_.keys():
            i.update(_ap_[ap_key])
            # Co/Adj. channel check
            if co_channel_5G(_ap_[ap_key].get("channel"), i.get("rogue_channels")):
                i["check_channel"] = "Co Channel"
            elif adj_channel_5G(_ap_[ap_key].get("channel"), i.get("rogue_channels")):
                i["check_channel"] = "Adjacent Channel"
            else:
                i["check_channel"] = ""

            _rogue_.append(i)
    return _rogue_


def rogue_channel_data_wlc_5G(_ap, _rogue):
    _ap_ = {}
    _rogue_ = []

    for i in _ap:
        _ap_[i["ap_name"]] = i
    for i in _rogue:
        if i.get("ap_name") in _ap_.keys():
            i.update(_ap_[i["ap_name"]])
        # Co/Adj. channel check
        if co_channel_5G(i.get("channel"), i.get("rogue_channels")):
            i["check_channel"] = "Co Channel"
        elif adj_channel_5G(i.get("channel"), i.get("rogue_channels")):
            i["check_channel"] = "Adjacent Channel"
        else:
            i["check_channel"] = ""

        _rogue_.append(i)
    return _rogue_


data_f_map = {
    "cisco_ios": {
        "show wireless wps rogue ap summary": ios_summary_data,
        "show wireless wps rogue ap detailed": ios_rogue_data,
        "show ap dot11 5ghz cleanair air-quality summary": ios_clean_air_data,
        "show ap dot11 24ghz cleanair air-quality summary": ios_clean_air_data,
        "show ap dot11 5ghz load-info": ios_load_data,
        "show ap dot11 24ghz load-info": ios_load_data,
        "show ap dot11 5ghz summary": ios_ap_data,
        "show ap dot11 24ghz summary": ios_ap_data,
        "show version": ios_version,
        "5G": rogue_channel_data_ios_5G,
        "show wlan summary": ios_wlan_data
    },
    "cisco_wlc_ssh": {
        "show 802.11a cleanair air-quality summary": wlc_clean_air_data,
        "show advanced 802.11a summary": wlc_ap_data,
        "show rogue ap detailed": wlc_rogue_data,
        "show rogue ap summary": wlc_summary_data,
        "show sysinfo": wlc_sysinfo,
        "5G": rogue_channel_data_wlc_5G,
        "show wlan summary": wlc_wlan_data
    }
}


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if not ctx.invoked_subcommand:
        ctx.invoke(run)


@click.command()
@click.option("--client", prompt="??????????????? WLC ???????????????????????? - client_name_location", help="Client_name_location of WLC.")
@click.option("--host", prompt="??????????????? WLC ??????????????????IP??????", help="host or IP of WLC.")
@click.option("--username", prompt="??????????????? WLC ???????????????????????????", help="username of WLC.")
@click.password_option(prompt="??????????????? WLC ????????????????????????", help="password of WLC.")
@click.option("--port", default=22, prompt="??????????????? WLC ?????????????????? SSH port", help="SSH port of WLC.")
# @click.option('--channel', default="5G", type=click.Choice(['5G', '2.4G', 'all']), prompt="???????????????????????????")
@click.option('--device_type', default="ios", type=click.Choice(['ios', 'aireos']), prompt="??????????????? WLC ?????????????????? OS", help="??????OS???????????????C9800=ios???35/55/85 WLC=aireos")
@click.option("--rssi", default=-80, prompt="?????????rogue AP RSSI-dBm ?????????", help="Min RSSI of Rogue AP.")
def init(client, host, username, password, port, rssi, device_type="ios", channel="5G"):
    """ ??????????????????????????? config.yml ??????????????????????????????????????????: rogue init??????????????????????????????????????????????????? config.yml???????????????????????????????????????????????????????????????????????????????????????config.yml????????????????????????????????????"""
    _wlc = {}
    channels_5G = False
    channels_24G = False
    if channel == "all":
        channels_5G = True
        channels_24G = True
    elif channel == "5G":
        channels_5G = True
    elif channel == "2.4G":
        channels_24G = True

    all_commands_dict = {
        "cisco_ios": {
            "5G": ["show ap dot11 5ghz cleanair air-quality summary", "show ap dot11 5ghz load-info",
                   "show ap dot11 5ghz summary"],
            "2.4G": ["show ap dot11 24ghz cleanair air-quality summary", "show ap dot11 24ghz load-info",
                     "show ap dot11 24ghz summary"],
            "common": ["show version", "show wlan summary"]
        },
        "cisco_wlc_ssh": {
            "5G": ["show 802.11a cleanair air-quality summary", "show advanced 802.11a summary"],
            "2.4G": ["show 802.11b cleanair air-quality summary", "show advanced 802.11b summary"],
            "common": ["show sysinfo", "show wlan summary"]
        }
    }

    _wlc[client] = {
        "host": host,
        "username": username,
        "password": password,
        "port": port,
        "capture": True,
        "device_type": g_device_type.get(device_type)
    }
    _config = {
            "channels_5G": channels_5G,
            "channels_24G": channels_24G,
            "rssi_min_dBm": rssi,
            "devices": _wlc,
            "commands": all_commands_dict
        }
    # print(_config)
    if not os.path.isfile('config.yml'):
        # new config.yml file
        with open(f'config.yml', "w") as file:
            yaml.dump(_config, file)
            print("config.yml file created successfully, next step run command: rogue")
    else:
        # modify the old config.yml file and make sure the new config refreshed
        with open(f'config.yml', "r") as file:
            _old_config = yaml.load(file, Loader=yaml.FullLoader)
        _devices = _old_config.pop("devices")
        _old_host = {v.get("host"): k for k, v in _devices.items()}
        if host in _old_host.keys():
            _devices.pop(_old_host.get(host))
            _devices[client] = _wlc[client]
        _config.pop("devices")
        _config["devices"] = _devices
        with open(f'config.yml', "w") as file:
            yaml.dump(_config, file)
            print("config.yml file changed successfully, please check sure this file correctly, then to run command: rogue")
    return


def rogue_detail(_cmd, _mac_list, _netmiko,  _folder, _device_type, _file_write=True):
    _detail_str = ""
    for i in _mac_list:
        _detail_str += f'-------- {_cmd} {i} --------\n\n'
        _detail_str += _netmiko.send_command(f'{_cmd} {i}')
        _detail_str += "\n"

    if _file_write:
        with open(f'{_folder}/{_cmd}.txt', "w") as file:
            file.write(_detail_str)
    if _cmd in data_f_map[_device_type].keys():
        return data_f_map[_device_type][_cmd](_detail_str)
    else:
        return []


def one_command_data(_cmd, _netmiko, _folder, _device_type, _file_write=True):
    # all command functions
    output = _netmiko.send_command(_cmd)
    if _file_write:
        with open(f'{_folder}/{_cmd}.txt', "w") as file:
            file.write(output)
    if _cmd in data_f_map[_device_type].keys():
        return data_f_map[_device_type][_cmd](output)
    else:
        return []


@click.command()
@click.option('--conf', default="config.yml", prompt="please input the config filename", help="????????? config.yml file??????????????????????????????")
def run(conf):
    """ ?????????????????????????????? - WLC ????????? Rogue AP ?????????????????????????????????rogue ?????? rogue run
    ??????config.yml???????????????devices ??????????????????"""
    config = {}
    if not os.path.isfile(conf):
        print(f"{conf} ??????????????????please run it first: rogue init")
        return

    with open(conf) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    if not config.get("channels_5G") and not config.get("channels_24G"):
        print(f"???????????????????????? 5G???2.4G?????? {conf} ????????? channels_5G???channels_24G?????????????????? yes or true")
        return
    if not isinstance(config.get("rssi_min_dBm"), int):
        print("rssi_min_dBm ??????????????????????????????????????????-80 ")
        return

    print("Start to collect.......")
    # add device type for consumed by netmiko
    # C9800 type: cisco_ios
    _wlcs = {}
    for name, device in config["devices"].items():
        if device.get("capture"):
            device.pop("capture")
            _wlcs[name] = device

    if not _wlcs:
        print("?????? WLC ???????????????????????????devices???????????? WLC ?????????capture: yes")
        return

    now = datetime.now()
    # now_time = now.strftime("%Y%m%d_%H%M%S")
    # now_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # Show command that we execute
    rogue_ap_all = []
    _header_list = []
    for name, device in _wlcs.items():
        print(f'    start to collect info from device/host: {name}/{device.get("host")}')
        with ConnectHandler(**device) as net_connect:
            _folder = f'{FOLDER}/{name}_{device.get("host")}'
            if not os.path.exists(_folder):
                os.makedirs(_folder)

            # -------------------------- 1: for rogue ap summary --------------------------
            _summary = one_command_data(cmd_dict[device["device_type"]].get("rogue_summary"), net_connect, _folder, device["device_type"], config.get("write_file", True))
            channel = channel_5G_24G(_summary, config["rssi_min_dBm"])

            _mac_list = []
            if config.get("channels_5G"):
                _mac_list.extend([i.get("rogue_ap_mac") for i in channel.get("5G")])
            elif config.get("channels_24G"):
                _mac_list.extend([i.get("rogue_ap_mac") for i in channel.get("24G")])

            if not _mac_list:
                print(f'For WLC - {name} {device.get("host")}: No Rogue AP found')
                continue
            # print(f'???????????? Rogue APs ????????? {len(_mac_list)}')

            # -------------------------- 2: for rogue ap detailed --------------------------

            _rogue_detail = rogue_detail(cmd_dict[device["device_type"]].get("rogue"), _mac_list, net_connect, _folder, device["device_type"], config.get("write_file", True))
            # print(f'rogue dtailed : {len(_rogue_detail)}')
            # print(_rogue_detail)
            # print(_rogue_detail)

            # run commands capture
            # -------------------------- 3: for all other commands --------------------------
            _commands_list = []
            if config.get("channels_5G"):
                _commands_list.extend(config["commands"][device["device_type"]]["5G"])
                _commands_list.extend(config["commands"][device["device_type"]]["common"])
            elif config.get("channels_24G"):
                _commands_list.extend(config["commands"][device["device_type"]]["2.4G"])
                _commands_list.extend(config["commands"][device["device_type"]]["common"])

            _data = {}
            for i in _commands_list:
                _data[i] = one_command_data(i, net_connect, _folder, device["device_type"], config.get("write_file", True))

        # -------------------------- 4: data relationship and output to table --------------------------

        if device.get("device_type") == "cisco_ios":
            _rogue = rogue_channel_data_ios_5G(_data.get("show ap dot11 5ghz load-info"),  _data.get("show ap dot11 5ghz summary"), _rogue_detail)
        elif device.get("device_type") == "cisco_wlc_ssh":
            _rogue = rogue_channel_data_wlc_5G(_data.get("show advanced 802.11a summary"), _rogue_detail)

        for i in _rogue:
            i.update({
                "client_name": name,
                "WLC_host": device.get("host"),
                "captured_date": now.strftime("%Y-%m-%d %H:%M:%S")
            })
            rogue_ap_all.append(i)
        # print(json.dumps(rogue_ap_all, indent=4))
        print(
            f'    For {name}/{device.get("host")}: rogue AP count in channels 5G/2.4G: {len(channel.get("5G"))}/{len(channel.get("24G"))}')
        print("    --------------------------------------------------")
        _header_list.extend(rogue_ap_all[0].keys())

    # -------------------------- 5: final to csv --------------------------

    # print(rogue_ap_all)
    _header = []
    _header_missing_data = []
    for _c_name in ["rogue_mac", "rogue_ssid", "rogue_rssi", "ap_name", "check_channel",
                    "channel", "rogue_channels", "channel_utilization", "clients", "txpwr", "client_name",
                    "WLC_host", "captured_date"]:
        if _c_name in list(set(_header_list)):
            _header.append(_c_name)
        else:
            _header_missing_data.append(_c_name)
    if _header_missing_data:
        print(f'Missing data for this columns: {_header_missing_data}')
    df = pd.DataFrame(rogue_ap_all)
    df.sort_values(by=['rogue_rssi'], ascending=False).to_csv(
        f'{FOLDER}/rogue ap {now.strftime("%Y%m%d-%H%M%S")}.csv', index=False, columns=_header)

    print(f"??????????????????-{FOLDER} ????????????show????????????????????????????????????????????????????????????????????????")


if __name__ == '__main__':
    # raw data folder
    FOLDER = "output"
    if not os.path.exists(FOLDER):
        os.makedirs(FOLDER)

    cli.add_command(init)
    cli.add_command(run)
    cli()
