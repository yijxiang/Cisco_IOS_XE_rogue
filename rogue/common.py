
channel_5G = {
    "36": 5180,
    "40": 5200,
    "44": 5220,
    "48": 5240,
    "52": 5260,
    "56": 5280,
    "60": 5300,
    "64": 5320,
    "100": 5500,
    "104": 5520,
    "108": 5540,
    "112": 5560,
    "116": 5580,
    "120": 5600,
    "124": 5620,
    "128": 5640,
    "132": 5660,
    "136": 5680,
    "140": 5700,
    "143": 5716,
    "144": 5720,
    "149": 5745,
    "153": 5765,
    "157": 5785,
    "161": 5805,
    "165": 5825
}


def co_channel_5G(ap_channel, rogue_channel):
    # print(ap_channel)
    # print(rogue_channel)
    if ap_channel and rogue_channel:
        if ap_channel in rogue_channel:
            return True
        elif isinstance(ap_channel, list):
            for ap in ap_channel:
                if ap in rogue_channel:
                    return True
        elif "," in ap_channel:
            for ap in ap_channel.split(","):
                if ap in rogue_channel:
                    return True
        return False


def adj_channel_5G(ap_channel, rogue_channel):
    if ap_channel and rogue_channel:
        _ap = [int(i) for i in ap_channel.split(",")]
        _rogue = [int(i) for i in rogue_channel.split(",")]
        _ap_min = min(_ap)
        _ap_max = max(_ap)
        _rogue_min = min(_rogue)
        _rogue_max = max(_rogue)

        if _ap_min > _rogue_max:
            _delta = channel_5G[str(_ap_min)] - channel_5G[str(_rogue_max)]
            if _delta >= 100:
                return False
        elif _ap_max < _rogue_min:
            _delta = channel_5G[str(_rogue_min)] - channel_5G[str(_ap_max)]
            if _delta >= 100:
                return False
        return True


def show_rogue_detail_ttp_cleanup(data):
    _data = []
    for rogue_ap in data:
        if "rogue_state" in rogue_ap.keys():
            rogue_ap.pop("rogue_state")
        _reported_ap = rogue_ap.pop("reported_ap")
        for one_ap in _reported_ap:
            one_ap.pop("radio_type")
            if one_ap.get("channel"):
                _channel = one_ap.pop("channel")
                if " " in _channel:
                    one_ap["rogue_channels"] = _channel.split()[0]
                elif "MHz" in _channel:
                    one_ap["rogue_channels"] = _channel.split("(")[0]
                elif "(" in _channel:
                    one_ap["rogue_channels"] = _channel.split("(")[1].split(")")[0]
                else:
                    one_ap["rogue_channels"] = _channel
            one_ap.update(rogue_ap)
            _data.append(one_ap)
    return _data


def show_ap_dot11_x_summary_ttp_cleanup(data):
    _data_ = []
    for ap in data:
        if "Monitor" in ap.get("mode"):
            continue
        _state = ap.pop("state")
        if not ("ENABLED" == _state or "Enabled" == _state):
            continue
        # _txpwr = ap.pop("txpwr")
        _channel = ap.pop("channel")
        ap["ap_mac"] = ap.pop("mac")
        # if "*" in _txpwr:
        #     ap["TPC"] = "*"
        # else:
        #     ap["TPC"] = ""
        # ap["txpwr"] = int(_txpwr.split("(")[1].split()[0])

        # ap["DCA"] = _channel.split(")")[1]
        if "(Monitor)" in _channel:
            continue
        if "(" in _channel:
            ap["channel"] = _channel.split("(")[1].split(")")[0]
        elif "*" in _channel:
            ap["channel"] = _channel.split("*")[0]
        else:
            ap["channel"] = _channel

        # ignore some data
        ap.pop("oper_state")
        ap.pop("width")
        if "mode" in ap.keys():
            ap.pop("mode")
        if "bss" in ap.keys():
            ap.pop("bss")
        _data_.append(ap)
    return _data_


def show_ap_clean_air_ttp_cleanup(data):
    _data_ = []
    for ap in data:
        if not ap.get("avg_aq").isdigit():
            continue
        ap["avg_aq"] = int(ap.pop("avg_aq"))
        ap["min_aq"] = int(ap.pop("min_aq"))
        if "interferers" in ap.keys():
            ap.pop("interferers")
        if "spectrum_ap_type" in ap.keys():
            ap.pop("spectrum_ap_type")
        _data_.append(ap)
    return _data_


def show_ap_load_ttp_cleanup(data):
    _data_ = []
    for ap in data:
        if not ap.get("channel_utilization").isdigit():
            continue
        ap["channel_utilization"] = int(ap.pop("channel_utilization"))
        ap["clients"] = int(ap.pop("clients"))
        ap["ap_mac"] = ap.pop("mac")
        _data_.append(ap)
    return _data_


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
