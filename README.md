[![published](https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg)](https://developer.cisco.com/codeexchange/github/repo/yijxiang/Cisco_IOS_XE_rogue)

## What's Rogue AP python app

[ 中文版本 ](README_chinese.md)

The main goal of rogue.py app. is collecting all commands for rogue detection in Cisco WLC devices, and one snapshots of rogue ap report will be included as well:
- collect the rogue commands for cisco wlc includes c9800 IOS XE devices and the old WLCs runs aireos system;
- rogue ap snapshot report, export as CSV format;
- Daily operation help for wireless troubleshooting;


### How to use Rogue AP python app

Please git clone this repo and then run python application.

Recommend steps for all python applications:
- git clone https://github.com/yijxiang/Cisco_IOS_XE_rogue.git;
- cd Cisco_IOS_XE_rogue;
- create virtual python env., version 3.8+/3.9+ have been tested
  ```
  python3 -m venv venv
  source venv/bin/activate
  ```
  
- pip install -r requirements.txt
- python rogue.py init
- python rogue.py


After that, you can get the CSV file in output folder, include all raw commands output as well.



## What's the mini collector tool 

Why mini collector tool?
If the python env. is not possible for the notebook run the tools on site, you can use mini tools which collect all rogue commands output only for offline use later.
Obviously Python do NOT need be installed, what we need do is only run the executed file and get the result.


The mini collector tool collect information only：
- support both IOS XE Cisco Catalyst 9800 and the old aireos WLC devices; 
- Commands output will be saved in the folder name "output" and datetime subfolder; 
- Pyinstaller used for package all python components, so it's easy to run in notebook specially for windows PC;
- Couple of commands included in collector which help for our wireless trouble shooting;

If you need more commands included for later analyse, please make sure add the extra commands in corresponding section of config.yml file.
For example, if you run tools with IOS XE 9800, those commands should be added under "cisco_ios", otherwise, "cisco_wlc_ssh" will be the right section for your aireos WLCs.

Below is the config.yml for commands list pre-included:
```
commands:
  cisco_ios:
    2.4G:
    - show ap dot11 24ghz cleanair air-quality summary
    - show ap dot11 24ghz load-info
    - show ap dot11 24ghz summary
    5G:
    - show ap dot11 5ghz cleanair air-quality summary
    - show ap dot11 5ghz load-info
    - show ap dot11 5ghz summary
    common:
    - show version
    - show wlan summary
  cisco_wlc_ssh:
    2.4G:
    - show 802.11b cleanair air-quality summary
    - show advanced 802.11b summary
    5G:
    - show 802.11a cleanair air-quality summary
    - show advanced 802.11a summary
    common:
    - show sysinfo
    - show wlan summary
```

> Tips: channels in 5G support only.

### How to use the mini collector tool 

As packaged into one file for different OS system, include windows, MAC OS and Ubuntu, you can download different file from release of this repo.
- download file for your PC.
  - Windows system: file name is  *collector.exe*
  - MAC OS system: file name is  *collector_macos.zip*
  - Ubuntu system: file name is collector
- **collector init** used for create the config.yml file via interactive method
- **collector** used for collect information from devices.
- output folder will be used for raw data save.
- Tar/Zip the output and send to cisco CSS.


Keep it simple, for MAC OS ：
- ./collector init: create config file
- cat config.yml: make sure config file correctly
- ./collector : run tool
- Check the output folder.


for windows, steps is ：
- cmd, in windows terminal
- collector init
- check the config.yml
- collector 
- Check the output folder.


Below is one example in MAC OS：
```
(env)  ----------------MAC OS------$ ./collector init
请输入访问 WLC 无线控制器的名称 - client_name_location: demo
请输入访问 WLC 无线控制器的IP地址: localhost
请输入访问 WLC 无线控制器的用户名: 
请输入访问 WLC 无线控制器的密码: 
Repeat for confirmation: 
请输入访问 WLC 无线控制器的 SSH port [22]: 10000
请输入访问 WLC 无线控制器的 OS (ios, aireos) [ios]: 
请输入rogue AP RSSI-dBm 最低值 [-80]: 
config.yml file created successfully, next step run command: collector


(env)  ----------------MAC OS------$ cat config.yml 
channels_24G: false
channels_5G: true
commands:
  cisco_ios:
    2.4G:
    - show ap dot11 24ghz cleanair air-quality summary
    - show ap dot11 24ghz load-info
    - show ap dot11 24ghz summary
    5G:
    - show ap dot11 5ghz cleanair air-quality summary
    - show ap dot11 5ghz load-info
    - show ap dot11 5ghz summary
    common:
    - show version
    - show wlan summary
  cisco_wlc_ssh:
    2.4G:
    - show 802.11b cleanair air-quality summary
    - show advanced 802.11b summary
    5G:
    - show 802.11a cleanair air-quality summary
    - show advanced 802.11a summary
    common:
    - show sysinfo
    - show wlan summary
devices:
  demo:
    capture: true
    device_type: cisco_ios
    host: localhost
    password: admin
    port: 10000
    username: admin
rssi_min_dBm: -80


(env)  ----------------MAC OS------$ ./collector 
For WLC - demo localhost, rogue AP count in channels 5G/2.4G: 21/132
请检查子目录-output 下,检查show命令输出文件是否生成,重复运行将覆盖目录下文件.
成功运行,并已经保存文件................
(env)  ----------------MAC OS------$ tree
.
├── collector
├── config.yml
└── output
    └── demo_localhost
        ├── captured\ datetime.txt
        ├── show\ ap\ dot11\ 5ghz\ cleanair\ air-quality\ summary.txt
        ├── show\ ap\ dot11\ 5ghz\ load-info.txt
        ├── show\ ap\ dot11\ 5ghz\ summary.txt
        ├── show\ version.txt
        ├── show\ wireless\ wps\ rogue\ ap\ detailed.txt
        ├── show\ wireless\ wps\ rogue\ ap\ summary.txt
        └── show\ wlan\ summary.txt
```

##  Recommend extra information

In order to deep understanding the wireless config and status, please capture following command using your terminal:

For IOS XE c9800：

- terminal length 0
- terminal width 512
- show tech wireless

> On IOS XE C9800, you can also capture commands from GUI: Troubleshooting -> debug bundle -> add new command "show tech wireless", you can download the result after finished.

For aireos WLC：

- config paging disable
- show run-config


## Ref. links

- [ https://github.com/yijxiang/Cisco_IOS_XE_rogue ](https://github.com/yijxiang/Cisco_IOS_XE_rogue/releases)
- [ Wireless Troubleshooting Tools ](https://developer.cisco.com/docs/wireless-troubleshooting-tools/#!wireless-troubleshooting-tools/wireless-troubleshooting-tools)
- 