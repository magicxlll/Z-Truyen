import os

def main():
    path = '/root/crosspoint-reader/.pio/libdeps/simulator_x3/simulator/src/WiFi.h'
    if not os.path.exists(path):
        print("File not found:", path)
        return

    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()

    code = code.replace('wifi_mode_t currentMode = WIFI_OFF;', 'wifi_mode_t currentMode = WIFI_STA;')
    code = code.replace('wl_status_t currentStatus = WL_DISCONNECTED;', 'wl_status_t currentStatus = WL_CONNECTED;')
    code = code.replace('String currentSsid;', 'String currentSsid = "Simulator WiFi (fake)";')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)

    print("WiFi.h updated successfully with auto-connected state")

if __name__ == '__main__':
    main()
