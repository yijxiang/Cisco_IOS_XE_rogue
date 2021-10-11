import os
from datetime import datetime

import click
import pandas as pd
import yaml
from netmiko import ConnectHandler

from common import channel_5G_24G, co_channel_5G, adj_channel_5G
from ios_xe import ios_rogue_data, ios_ap_data, ios_load_data, ios_clean_air_data, ios_summary_data, ios_version
from wlc_ssh import wlc_ap_data, wlc_rogue_data, wlc_clean_air_data, wlc_summary_data, wlc_sysinfo

# raw data folder
FOLDER = "output"
if not os.path.exists(FOLDER):
    os.makedirs(FOLDER)

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


data_f_map = {
    "show ap dot11 5ghz cleanair air-quality summary": ios_clean_air_data,
    "show ap dot11 24ghz cleanair air-quality summary": ios_clean_air_data,
    "show 802.11a cleanair air-quality summary": wlc_clean_air_data,
    "show ap dot11 5ghz load-info": ios_load_data,
    "show ap dot11 24ghz load-info": ios_load_data,
    "show ap dot11 5ghz summary": ios_ap_data,
    "show ap dot11 24ghz summary": ios_ap_data,
    "show advanced 802.11a summary": wlc_ap_data,
    "show wireless wps rogue ap detailed": ios_rogue_data,
    "show rogue ap detailed": wlc_rogue_data,
    "show rogue ap summary": wlc_summary_data,
    "show wireless wps rogue ap summary": ios_summary_data,
    "show version": ios_version,
    "show sysinfo": wlc_sysinfo
}


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if not ctx.invoked_subcommand:
        ctx.invoke(run)


@click.command()
@click.option("--client", prompt="请输入访问 WLC 无线控制器的名称 - client_name_location", help="Client_name_location of WLC.")
@click.option("--host", prompt="请输入访问 WLC 无线控制器的IP地址", help="host or IP of WLC.")
@click.option("--username", prompt="请输入访问 WLC 无线控制器的用户名", help="username of WLC.")
@click.password_option(prompt="请输入访问 WLC 无线控制器的密码", help="password of WLC.")
@click.option("--port", default=22, prompt="请输入访问 WLC 无线控制器的 SSH port", help="SSH port of WLC.")
# @click.option('--channel', default="5G", type=click.Choice(['5G', '2.4G', 'all']), prompt="请输入无线信道频段")
@click.option('--device_type', default="ios", type=click.Choice(['ios', 'aireos']), prompt="请输入访问 WLC 无线控制器的 OS", help="运行OS选择方法：C9800=ios、35/55/85 WLC=aireos")
@click.option("--rssi", default=-80, prompt="请输入rogue AP RSSI-dBm 最低值", help="Min RSSI of Rogue AP.")
def init(client, host, username, password, port, rssi, device_type="ios", channel="5G"):
    """ 步骤一：交互式生成 config.yml 文件，第一次使用请先运行命令: rogue init，运行该命令，将删除同目录中的 config.yml文件。对于熟练使用者，可以直接修改config.yml实现多个控制器的信息获取"""
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

    if device_type == "aireos":
        _device_type = "cisco_wlc_ssh"
    elif device_type == "ios":
        _device_type = "cisco_ios"

    all_commands_dict = {
        "cisco_ios": {
            "5G": ["show ap dot11 5ghz cleanair air-quality summary", "show ap dot11 5ghz load-info",
                   "show ap dot11 5ghz summary"],
            "2.4G": ["show ap dot11 24ghz cleanair air-quality summary", "show ap dot11 24ghz load-info",
                     "show ap dot11 24ghz summary"],
            "common": ["show version"]
        },
        "cisco_wlc_ssh": {
            "5G": ["show 802.11a cleanair air-quality summary", "show advanced 802.11a summary"],
            "2.4G": ["show 802.11b cleanair air-quality summary", "show advanced 802.11b summary"],
            "common": ["show sysinfo"]
        }
    }

    _wlc[client] = {
        "host": host,
        "username": username,
        "password": password,
        "port": port,
        "capture": True,
        "device_type": _device_type
    }
    _config = {
            "channels_5G": channels_5G,
            "channels_24G": channels_24G,
            "rssi_min_dBm": rssi,
            "devices": _wlc,
            "commands": all_commands_dict
        }
    # print(_config)
    with open(f'config.yml', "w") as file:
        yaml.dump(_config, file)
        print("config.yml file created successfully, next step run command: rogue")
    return


def rogue_detail(_cmd, _mac_list, _netmiko,  _folder, _file_write):
    _detail_str = ""
    for i in _mac_list:
        _detail_str += f'-------- {_cmd} {i} --------\n\n'
        _detail_str += _netmiko.send_command(f'{_cmd} {i}')
        _detail_str += "\n"

    if _file_write:
        with open(f'{_folder}/{_cmd}.txt', "w") as file:
            file.write(_detail_str)
    return data_f_map[_cmd](_detail_str)


def one_command_data(_cmd, _netmiko, _folder, _file_write):
    output = _netmiko.send_command(_cmd)
    if _file_write:
        with open(f'{_folder}/{_cmd}.txt', "w") as file:
            file.write(output)
    return data_f_map[_cmd](output)


@click.command()
def run():
    """ 步骤二：从无线控制器 - WLC 中抓取 Rogue AP 信息，命令格式可以是：rogue 或者 rogue run"""
    config = {}
    if not os.path.isfile('config.yml'):
        print("config.yml 文件不存在，please run it first: rogue init")
        return

    with open('config.yml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    if not config.get("channels_5G") and not config.get("channels_24G"):
        print("至少需要一个频段 5G、2.4G：在 config.yml 中设置 channels_5G、channels_24G，其中一个是 yes or true")
        return
    if not isinstance(config.get("rssi_min_dBm"), int):
        print("rssi_min_dBm 需要设置为数值，其默认值为：-80 ")
        return

    # add device type for consumed by netmiko
    # C9800 type: cisco_ios
    _wlcs = {}
    for name, device in config["devices"].items():
        if device.get("capture"):
            device.pop("capture")
            _wlcs[name] = device

    if not _wlcs:
        print("没有 WLC 需要信息抓取，检查devices至少一个 WLC 里面：capture: yes")
        return

    now = datetime.now()
    now_time = now.strftime("%Y%m%d_%H%M%S")

    # Show command that we execute
    for name, device in _wlcs.items():
        with ConnectHandler(**device) as net_connect:
            _folder = f'{FOLDER}/{name}_{device.get("host")}/{now_time}'
            if not os.path.exists(_folder):
                os.makedirs(_folder)

            # -------------------------- 1: for rogue ap summary --------------------------
            _summary = one_command_data(cmd_dict[device["device_type"]].get("rogue_summary"), net_connect, _folder, config.get("write_file", True))
            channel = channel_5G_24G(_summary, config["rssi_min_dBm"])

            _mac_list = []
            if config.get("channels_5G"):
                _mac_list.extend([i.get("rogue_ap_mac") for i in channel.get("5G")])
            elif config.get("channels_24G"):
                _mac_list.extend([i.get("rogue_ap_mac") for i in channel.get("24G")])

            if not _mac_list:
                print(f'For WLC - {name} {device.get("host")}: No Rogue AP found')
                continue
            # print(f'拟抓取的 Rogue APs 个数： {len(_mac_list)}')

            # -------------------------- 2: for rogue ap detailed --------------------------
            _rogue_detail = rogue_detail(cmd_dict[device["device_type"]].get("rogue"), _mac_list, net_connect, _folder, config.get("write_file", True))
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
                _data[i] = one_command_data(i, net_connect, _folder, config.get("write_file", True))

            # -------------------------- 4: data relationship and output to table --------------------------
            _ap_info_all = {}
            _ap_load_dict = {}
            rogue_ap_all = []

            for i in _data.get("show ap dot11 5ghz load-info"):
                _ap_load_dict[f'{i["ap_name"]}_{i["slot"]}'] = i
            for i in _data.get("show ap dot11 5ghz summary"):
                ap_key = f'{i["ap_name"]}_{i["slot"]}'
                if ap_key in _ap_load_dict.keys():
                    i.update(_ap_load_dict[ap_key])
                    _ap_info_all[ap_key] = i
            for i in _rogue_detail:
                ap_key = f'{i["ap_name"]}_{i["slot"]}'
                if ap_key in _ap_info_all.keys():
                    i.update(_ap_info_all[ap_key])
                    # Co/Adj. channel check
                    if co_channel_5G(_ap_info_all[ap_key].get("channel"), i.get("rogue_channels")):
                        i["check_channel"] = "Co Channel"
                    elif adj_channel_5G(_ap_info_all[ap_key].get("channel"), i.get("rogue_channels")):
                        i["check_channel"] = "Adjacent Channel"
                    else:
                        i["check_channel"] = ""

                    i["client_name"] = name
                    i["WLC_host"] = device.get("host")
                    i["captured_date"] = now.strftime("%Y-%m-%d %H:%M:%S")
                    rogue_ap_all.append(i)
            # print(json.dumps(rogue_ap_all, indent=4))

            # final to csv and logging
            _header = []
            _header_missing_data = []
            for _c_name in ["rogue_mac", "rogue_ssid", "rogue_rssi", "ap_name", "check_channel", "channel_utilization",
                            "channel", "rogue_channels", "clients", "txpwr", "client_name",
                            "WLC_host", "captured_date"]:
                if _c_name in rogue_ap_all[0].keys():
                    _header.append(_c_name)
                else:
                    _header_missing_data.append(_c_name)
            if _header_missing_data:
                print(f'Missing data for this columns: {_header_missing_data}')
            # header = ["rogue_mac", "rogue_ssid", "rogue_rssi", "ap_name", "check_channel", "channel_utilization",
            #                             "channel", "rogue_channels", "clients", "txpwr", "client_name",
            #                             "captured_date"]
            # # header = ["rogue_mac", "rogue_ssid", "rogue_rssi", "ap_name", "check_channel",  "channel", "rogue_channels", "txpwr"]
            df = pd.DataFrame(rogue_ap_all)
            df.sort_values(by=['rogue_rssi'], ascending=False).to_csv(f'{FOLDER}/rogue_ap.csv', index=False, columns=_header)

            print(
                f'For WLC - {name} {device.get("host")}, rogue AP count in channels 5G/2.4G: {len(channel.get("5G"))}/{len(channel.get("24G"))}')
            print(f"请检查子目录-{FOLDER} 下，检查show命令输出文件是否生成，目录名时间戳是否正确。")


if __name__ == '__main__':
    cli.add_command(init)
    cli.add_command(run)
    cli()
