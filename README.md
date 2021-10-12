## Cisco_IOS_XE_rogue

该工具软件支持收集IOS XE 系列软件的 Cisco Catalyst 9800、 以及运行 aireos 的无线控制器产品，抓取 rogue AP 清单，帮助我们进行无线干扰的 *troubleshooting*

该工具收集的命令输出，将保存在子目录 output 下，并在输出目录名称中包含抓取的日期、时间信息。

该工具抓取的命令有，通过修改config.yml文件，也可以按需增加其他的命令收集。

注意和你计划采集的设备类型有关系，如果你计划从Catalyst 9800里面采集数据，则选择在"cisco_ios"下面增加命令；如果是35/55/8500系列*AIREOS*的设备，则选"cisco_wlc_ssh":

```
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
  cisco_wlc_ssh:
    2.4G:
    - show 802.11b cleanair air-quality summary
    - show advanced 802.11b summary
    5G:
    - show 802.11a cleanair air-quality summary
    - show advanced 802.11a summary
    common:
    - show sysinfo
```

目前工具仅仅针对 **5G** 频段进行收集和分析，对 *2.4G* 暂不支持。

### 工具软件使用方法

自 github 右侧栏 releases 下载最新的软件，目前可以支持 MAC OS、windows 2种格式。
- 下载软件至本地，windows系统请下载 *rogue.exe*，MAC OS 则下载 *rogue.zip*，运行程序可能*稍等片刻*，主要是由于工具软件打包成一个文件，运行时需要解压缩到临时目录造成的延迟；
- 在同一个目录中，参考 config_template.yml 文件说明，生成自己的 config.yml 文件，该文件也可以通过命令 rogue init 交互式生成；
    在 config.yml 文件中，还可以自定义需要抓取的命令清单，可以在 commands 下方自行增加。
- 运行 rogue 可执行文件即可，windows terminal下 *rogue*， MAC OS terminal下 *./rogue*；
- 如果运行顺利，软件将在本地自动创建子目录 output ，仔细检查该目录下文件是否完整；
- 压缩打包子目录 **output** ，并发送给思科工程师。


下面为MAC OS上，如何使用该工具软件，供大家参考，简单步骤有几步：
- ./rogue init
- cat config.yml
- ./rogue 
- 检查output 子目录下自动保存的文件，以及该文件的时间戳


```
########################## MAC OS$ ./rogue init
请输入访问 WLC 无线控制器的名称 - client_name_location：: test
请输入访问 WLC 无线控制器的IP地址：: localhost
请输入访问 WLC 无线控制器的用户名：: admin
请输入访问 WLC 无线控制器的密码：: admin
请输入访问 WLC 无线控制器的 SSH port： [22]: 10000
请输入分析的频段： (5G, 2.4G, all): 5G
请输入rogue AP RSSI-dBm 最低值： [-80]: 
########################## MAC OS$ 
########################## MAC OS$ 
########################## MAC OS$ ls -l
total 21584
-rw-r--r--  1 staff  staff       167 Oct  6 11:35 config.yml
drwxr-xr-x  2 staff  staff        64 Oct  6 11:34 output
-rwxr-xr-x@ 1 staff  staff  11043232 Oct  6 11:31 rogue
########################## MAC OS$ cat config.yml 
channels_24G: false
channels_5G: true
devices:
  test:
    capture: true
    host: localhost
    password: admin
    port: 10000
    username: admin
rssi_min_dBm: -80
########################## MAC OS$ ./rogue 
For WLC - test localhost, rogue AP count in channels 5G/2.4G: 22/347
请检查子目录-output 下，检查show命令输出文件是否生成，文件名中时间戳是否正确。
########################## MAC OS$ tree
.
├── config.yml
├── output
│   └── test_localhost
│       ├── show\ wireless\ wps\ rogue\ ap\ detailed_20211006-113605.txt
│       └── show\ wireless\ wps\ rogue\ ap\ summary_20211006-113605.txt
└── rogue
```

###  其他有帮助的信息收集

发送抓取文件同时，请登录至 WLC CLI下，获取下述命令输出：

针对 IOS XE c9800 无线控制器：

- terminal length 0
- terminal width 512
- show tech wireless


针对 AireOS WLC 无线控制器：
- config paging disable
- show run-config


### links

- [ https://github.com/yijxiang/Cisco_IOS_XE_rogue： Rogue AP 信息收集](https://github.com/yijxiang/Cisco_IOS_XE_rogue/releases)