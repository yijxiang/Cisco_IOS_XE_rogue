## Cisco_IOS_XE_rogue

该工具仅仅是收集 Cisco Catalyst 9800 无线控制器，其运行 IOS XE 系列软件的 rogue AP list，帮助我们进行 *troubleshooting*

该工具收集的命令输出，将保存在子目录 output 下，并在文件名字中包含抓取的日期和时间信息。


### 软件使用方法

自右侧栏 releases 下载最新的软件，目前可以支持 MAC OS、windows 2种格式。
- 下载软件至本地；
- 在同一个目录中，参考 config_template.yml 文件说明，生成自己的 config.yml 文件；
- 运行 rogue 可执行文件即可；
- 如果运行顺利，软件将自动创建子目录 output ，仔细检查该目录下文件是否完整；
- 压缩目录 output ，并发送给思科。


###  其他有帮助的信息收集

发送抓取文件同时，请登录至 C9800 CLI下，获取下述命令输出，注意提前设置 terminal length 0：

- show tech wireless
- 
