import os
from datetime import datetime

import yaml
from netmiko import ConnectHandler
from ttp import ttp
import re
import click

CMD_ROGUE_SUMMARY = "show wireless wps rogue ap summary"
CMD_LIST = ["show ap dot11 5ghz summary", "show ap dot11 24ghz load-info", "show ap dot11 5ghz load-info",
            "show wireless wps rogue ap summary"]
CMD_ROGUE_DETAIL = "show wireless wps rogue ap detailed"
config = {}

# raw data folder
FOLDER = "output"
if not os.path.exists(FOLDER):
    os.makedirs(FOLDER)


def show_wireless_wps_rogue_ap_summary(data):
    ttp_template = """{{rogue_ap_mac}} {{ignore}} {{ignore}} {{ignore}} {{ignore}} {{last_heard_date}} {{last_heard_time}} {{ap_mac}} {{rssi| to_int}} {{channel | to_int}}
    """
    parser = ttp(data=data, template=ttp_template)
    parser.parse()
    return parser.result()[0][0]


def show_wireless_wps_rogue_ap_summary_regex(data):
    _data = []
    mac = '[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}'
    rogue_str = re.compile(r'''({m})\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(-\d+)+\s+(\d+)\s+'''.format(m=mac))
    found = re.findall(rogue_str, data)
    for i in found:
        rogue_ap_mac, rssi, channel = i
        _one_data = {
            "rogue_ap_mac": rogue_ap_mac,
            "rssi": int(rssi),
            "channel": int(channel)
        }
        _data.append(_one_data)
    return _data


def channel_5G_24G(data):
    channel = {
        "5G": [],
        "24G": []
    }
    for one in data:
        if one.get("rssi") >= config.get("rssi_min_dBm"):
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
@click.option("--client", prompt="请输入访问 WLC 无线控制器的名称 - client_name_location：", help="Client_name_location of WLC.")
@click.option("--host", prompt="请输入访问 WLC 无线控制器的IP地址：", help="host or IP of WLC.")
@click.option("--username", prompt="请输入访问 WLC 无线控制器的用户名：", help="username of WLC.")
@click.option("--password", prompt="请输入访问 WLC 无线控制器的密码：", help="password of WLC.")
@click.option("--port", default=22, prompt="请输入访问 WLC 无线控制器的 SSH port：", help="SSH port of WLC.")
@click.option('--channel', type=click.Choice(['5G', '2.4G', 'all']), prompt="请输入分析的频段：")
@click.option("--rssi", default=-80, prompt="请输入rogue AP RSSI-dBm 最低值：", help="Min RSSI of Rogue AP.")
def init(client, host, username, password, port, channel, rssi):
    """ 步骤一：交互式生成 config.yml 文件，第一次使用请先运行命令: rogue init"""
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

    _wlc[client] = {
        "host": host,
        "username": username,
        "password": password,
        "port": port,
        "capture": True
    }
    _config = {
            "channels_5G": channels_5G,
            "channels_24G": channels_24G,
            "rssi_min_dBm": rssi,
            "devices": _wlc
        }
    # print(_config)
    with open(f'config.yml', "w") as file:
        yaml.dump(_config, file)
    return


@click.command()
def run():
    """ 步骤二：从无线控制器 - WLC 中抓取 Rogue AP 信息，命令格式可以是：rogue 或者 rogue run"""
    if not os.path.isfile('config.yml'):
        print("Please run it first: rogue init")

    now = datetime.now()
    now_time = now.strftime("%Y%m%d-%H%M%S")

    global config
    with open('config.yml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    if not config.get("channels_5G") and not config.get("channels_5G"):
        print("至少需要一个频段：5G、2.4G。在 config.yml 中设置 channels_5G、channels_24G，其中一个是 yes")
        return
    if not isinstance(config.get("rssi_min_dBm"), int):
        print("rssi_min_dBm 需要设置为数值，比如：-80 ")
        return

    # add device type for consumed by netmiko
    # C9800 type: cisco_ios
    _wlcs = {}
    for name, device in config["devices"].items():
        if device.get("capture"):
            device.update({"device_type": "cisco_ios"})
            device.pop("capture")
            # devices_list.append(device)
            _wlcs[name] = device

    if not _wlcs:
        print("没有 WLC 需要信息抓取，检查devices至少一个 WLC 里面：capture: yes")
        return

    # Show command that we execute
    for name, device in _wlcs.items():
        with ConnectHandler(**device) as net_connect:
            _folder = f'{FOLDER}/{name}_{device.get("host")}'
            if not os.path.exists(_folder):
                os.makedirs(_folder)
            output = net_connect.send_command(CMD_ROGUE_SUMMARY)
            if config.get("write_file", True):
                with open(f'{_folder}/{CMD_ROGUE_SUMMARY}_{now_time}.txt', "w") as file:
                    file.write(output)
            else:
                print("Rogue ap summary file no need, write cancel")
                # print(output)

            channel = channel_5G_24G(show_wireless_wps_rogue_ap_summary_regex(output))

            _mac_list = []
            if config.get("channels_5G"):
                rogue_ap_mac = [i.get("rogue_ap_mac") for i in channel.get("5G")]
                _mac_list.extend(rogue_ap_mac)
            elif config.get("channels_24G"):
                rogue_ap_mac = [i.get("rogue_ap_mac") for i in channel.get("24G")]
                _mac_list.extend(rogue_ap_mac)

            if not _mac_list:
                print(f'For WLC - {name} {device.get("host")}: No Rogue AP found')
                continue

            # print(f'拟抓取的 Rogue APs 个数： {len(_mac_list)}')
            _detail_str = ""
            for i in _mac_list:
                _detail_str += f'-------- {CMD_ROGUE_DETAIL} {i} --------\n'
                _detail_str += net_connect.send_command(f'{CMD_ROGUE_DETAIL} {i}')
                _detail_str += "\n"

            if config.get("write_file", True):
                with open(f'{_folder}/{CMD_ROGUE_DETAIL}_{now_time}.txt', "w") as file:
                    file.write(_detail_str)
            else:
                print("rogue ap detail file no need, write cancel")
                # print(_detail_str)

            print(
                f'For WLC - {name} {device.get("host")}, rogue AP count in channels 5G/2.4G: {len(channel.get("5G"))}/{len(channel.get("24G"))}')
            print(f"请检查子目录-{FOLDER} 下，检查show命令输出文件是否生成，文件名中时间戳是否正确。")


cli.add_command(init)
cli.add_command(run)

if __name__ == '__main__':
    cli()
