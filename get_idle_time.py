from cross_platform import IS_MAC, get_cmd_output


def get_idle_time_mac_os():
    out = get_cmd_output("ioreg -c IOHIDSystem | awk '/HIDIdleTime/ {print $NF/1000000000; exit}'", temp_file='/tmp/idle_time', shell=True)
    try:
        return float(out.replace(',', '.'))
    except:
        return '?'


if IS_MAC:
    get_idle_time = get_idle_time_mac_os
else:
    from idle_time import IdleMonitor
    idle_monitor = IdleMonitor.get_monitor()
    get_idle_time = idle_monitor.get_idle_time
