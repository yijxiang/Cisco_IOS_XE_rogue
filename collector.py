import os
from datetime import datetime
import click
import yaml
from netmiko import ConnectHandler
import re

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


data_f_map = {
    "show rogue ap summary": wlc_summary_data,
    "show wireless wps rogue ap summary": ios_summary_data
}


def channel_5G_24G(data, rssi_min_dBm):
    channel = {
        "5G": [],
        "24G": []
    }
    for one in data:
        if one.get("rssi") >= rssi_min_dBm:
            if one.get("channel") > 20:
                channel["5G"].append(one)
            else:
                channel["24G"].append(one)
    return channel


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if not ctx.invoked_subcommand:
        ctx.invoke(run)


@click.command()
@click.option("--client", prompt="请输入访问 WLC 无线控制器的名称 - client_name_location", help="Client_name_location of WLC.")
@click.option("--host", prompt="请输入访问 WLC 无线控制器的IP地址 - IP or host of WLC", help="host or IP of WLC.")
@click.option("--username", prompt="请输入访问 WLC 无线控制器的用户名 - username", help="username of WLC.")
@click.password_option(prompt="请输入访问 WLC 无线控制器的密码 - password", help="password of WLC.", confirmation_prompt=False)
@click.option("--port", default=22, prompt="请输入访问 WLC 无线控制器的 SSH port", help="SSH port of WLC.")
# @click.option('--channel', default="5G", type=click.Choice(['5G', '2.4G', 'all']), prompt="请输入无线信道频段")
@click.option('--device_type', default="ios", type=click.Choice(['ios', 'aireos']), prompt="请输入访问 WLC 无线控制器的 OS", help="运行OS选择方法：C9800=ios、35/55/85 WLC=aireos")
@click.option("--rssi", default=-80, prompt="请输入 - input rogue AP minimum RSSI in -dBm", help="Min RSSI of Rogue AP.")
def init(client, host, username, password, port, rssi, device_type="ios", channel="5G"):
    """ 步骤一：交互式生成 config.yml 文件，第一次使用请先运行命令: collector init，运行该命令，将删除同目录中的 config.yml文件。对于熟练使用者，可以直接修改config.yml实现多个控制器的信息获取"""
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
    with open(f'config.yml', "w") as file:
        yaml.dump(_config, file)
        print("config.yml file created successfully, next step run command: collector")
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
    return


def one_command_data(_cmd, _netmiko, _folder, _file_write, _need_result=False):
    output = _netmiko.send_command(_cmd)
    if _file_write:
        with open(f'{_folder}/{_cmd}.txt', "w") as file:
            file.write(output)

    if _need_result:
        return data_f_map[_cmd](output)
    else:
        return


@click.command()
def run():
    """ 步骤二：从无线控制器 - WLC 中抓取 Rogue AP 信息，命令格式可以是：collector 或者 collector run"""
    config = {}
    if not os.path.isfile('config.yml'):
        print("config.yml 文件不存在，please run it first: collector init")
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
    # now_time = now.strftime("%Y%m%d-%H%M%S")
    # now_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # Show command that we execute
    for name, device in _wlcs.items():
        with ConnectHandler(**device) as net_connect:
            _folder = f'{FOLDER}/{name}_{device.get("host")}/{now.strftime("%Y%m%d-%H%M%S")}'
            if not os.path.exists(_folder):
                os.makedirs(_folder)

            # -------------------------- 1: for rogue ap summary --------------------------
            _summary = one_command_data(cmd_dict[device["device_type"]].get("rogue_summary"), net_connect, _folder, config.get("write_file", True), True)
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
            rogue_detail(cmd_dict[device["device_type"]].get("rogue"), _mac_list, net_connect, _folder, config.get("write_file", True))
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
                one_command_data(i, net_connect, _folder, config.get("write_file", True))

        # with open(f'{_folder}/captured datetime.txt', "w") as file:
        #     file.write(f'{now.strftime("%Y%m%d_%H%M%S")}')

        print(
            f'For WLC - {name} {device.get("host")}, rogue AP count in channels 5G/2.4G: {len(channel.get("5G"))}/{len(channel.get("24G"))}')
        print(f"请检查子目录-{FOLDER} 下，检查show命令输出文件是否生成，重复运行将覆盖目录下文件。")
        print("成功运行，并已经保存文件................")


if __name__ == '__main__':
    # raw data folder
    FOLDER = "output"
    if not os.path.exists(FOLDER):
        os.makedirs(FOLDER)

    cli.add_command(init)
    cli.add_command(run)
    cli()
