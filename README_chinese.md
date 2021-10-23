
## Rogue AP python app

rogue.py 主要实现从 Cisco WLC-无线控制器中，抓取rogue ap 信息同时自动生成 CSV 格式文件，帮助我们收集当前时间的 rogue ap快照信息，提高rogue ap 故障排查：
- 收集rogue ap 相关命令输出；
- rogue ap 快照格式 csv 输出；


### Rogue AP python app 使用方法

请先 clone 本仓库源代码，init 之后，再开始重复使用。

推荐的使用步骤为：
- git clone https://github.com/yijxiang/Cisco_IOS_XE_rogue.git；
- 进入自动创建的目录：cd Cisco_IOS_XE_rogue；
- 创建 virtual python 环境(3.8， 3.9等版本)：
  ```
  python3 -m venv venv
  source venv/bin/activate
  ```
  
- pip install -r requirements.txt
- python rogue.py init
- python rogue.py

该 app 将在目录 output 中生成 *.CSV* 文件供我们无线故障排查参考。


## 简化版 - Mini collector tool 

该 mini collector tool 主要简化现场环境PC设置而来，该 mini tool 具备明显的优势：已打包，不需要创建python环境

该 mini collector tool 工具仅仅收集无线控制器的命令输出，以便离线工具使用，帮助我们进行无线干扰的 *trouble shooting*：
- 工具支持 运行 IOS XE Cisco Catalyst 9800、 和 Aireos 的无线控制器产品； 
- 该工具收集的命令输出，将保存在子目录 output 下，并在输出目录名称中包含抓取的日期、和时间信息； 
- 该工具已经集成了python virtual environment ，所以运行时不需要额外安装python环境；
- 该工具已经预设了少量抓取的命令，通过修改config.yml文件，可以按需增加其他的命令收集；

注意和你计划采集的设备类型有关系，如果你将从 Catalyst 9800里采集数据，则选择在"cisco_ios"下面增加命令；如果设备是35/55/8500系列 *Aireos*，则选"cisco_wlc_ssh":

下文是 config.yml 文件中的关于命令收集的片段：
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

> 注意：目前工具仅仅针对 **5G** 频段进行收集和分析，对 *2.4G* 还不支持。

### Mini collector tool 工具使用方法

可以从 github 右侧栏 releases 下载最新的软件，目前可以支持 MAC OS、windows、ubuntu 3种格式。
- 下载软件至本地，windows系统请下载 *collector.exe*，MAC OS 则下载 *collector_macos.zip*，运行程序需要*稍等片刻*，主要是由于工具软件打包成一个文件，运行时需要解压缩到临时目录造成的延迟；
- 在工具目录下，config.yml 配置文件通过命令 **collector init** 交互式生成，config.yml 配置文件说明请参考 config_template.yml 中的说明；
    在 config.yml 文件中，还可以自定义需要抓取的命令清单，可以在 commands 下方自行增加。
- 配置文件创建之后，就可以运行 collector 可执行文件，windows terminal下 *collector*， MAC OS terminal下 *./collector*；
- 如果运行顺利，工具将保存命令输出文件至子目录 output ，请仔细检查该目录下文件是否正确；
- 压缩打包子目录 **output** ，并发送给思科工程师。


在MAC OS上，请参考该工具软件使用方法，简单步骤有：
- ./collector init
- cat config.yml
- ./collector 
- 检查output 子目录下自动保存的文件。


如果使用Windows，可以在cmd、powershell下方，使用该工具，如果在CMD下：
- cmd 回车，使用windows自带的cli；
- cd 到文件目录中；
- collector.exe init    (说明：生成config.yml)
- collector.exe         (说明：命令采集)


如果使用powershell，则为：
- powershell 回车，使用windows自带的cli；
- cd 到文件目录中；
- ./collector.exe init   (说明：生成config.yml)
- ./collector.exe        (说明：命令采集)


下方为在mac os上，完整的工具软件运行参考步骤：
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
请检查子目录-output 下，检查show命令输出文件是否生成，重复运行将覆盖目录下文件。
成功运行，并已经保存文件................
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

##  其他帮助信息的收集

发送抓取文件同时，最好登录至 WLC CLI下，获取下述命令输出一起打包发出（文件较大，
不建议使用上述工具抓取）：

针对 IOS XE c9800 无线控制器：

- terminal length 0
- terminal width 512
- show tech wireless

> c9800上，推荐在 GUI 中获取：Troubleshooting -> debug bundle -> 增加命令"show tech wireless"，抓取结束之后下载。

针对 aireos WLC 无线控制器：

- config paging disable
- show run-config


## 参考 links

- [ https://github.com/yijxiang/Cisco_IOS_XE_rogue： Rogue AP 信息收集](https://github.com/yijxiang/Cisco_IOS_XE_rogue/releases)
- [ Wireless Troubleshooting Tools ](https://developer.cisco.com/docs/wireless-troubleshooting-tools/#!wireless-troubleshooting-tools/wireless-troubleshooting-tools)
- 