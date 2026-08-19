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

    # 2. Add IDLE_POWER_SAVING_MS alias to HalPowerManager.h if missing
    pm_path = '/root/crosspoint-reader/.pio/libdeps/simulator_x3/simulator/src/HalPowerManager.h'
    if os.path.exists(pm_path):
        with open(pm_path, 'r', encoding='utf-8') as f:
            pm_code = f.read()
        if 'IDLE_POWER_SAVING_MS' not in pm_code:
            pm_code = pm_code.replace(
                'static constexpr unsigned long IDLE_DOWNCLOCK_MS = 500;',
                'static constexpr unsigned long IDLE_DOWNCLOCK_MS = 500;\n  static constexpr unsigned long IDLE_POWER_SAVING_MS = 500;'
            )
    # 3. Add combinesGrayscaleBase to HalDisplay.h if missing
    hd_path = '/root/crosspoint-reader/.pio/libdeps/simulator_x3/simulator/src/HalDisplay.h'
    if os.path.exists(hd_path):
        with open(hd_path, 'r', encoding='utf-8') as f:
            hd_code = f.read()
        if 'combinesGrayscaleBase' not in hd_code:
            hd_code = hd_code.replace(
                'bool isInverted() const;',
                'bool isInverted() const;\n  bool combinesGrayscaleBase() const { return false; }'
            )
    # 4. Fix QRCode library C23 bool keyword issue in GCC 15
    qr_path = '/root/crosspoint-reader/.pio/libdeps/simulator_x3/QRCode/src/qrcode.h'
    if os.path.exists(qr_path):
        with open(qr_path, 'r', encoding='utf-8') as f:
            qr_code = f.read()
        target_str = """typedef unsigned char bool;
static const bool false = 0;
static const bool true = 1;"""
        if target_str in qr_code:
            qr_code = qr_code.replace(
                target_str,
                '#if !defined(__STDC_VERSION__) || __STDC_VERSION__ < 202311L\n' + target_str + '\n#endif'
            )
            with open(qr_path, 'w', encoding='utf-8') as f:
                f.write(qr_code)
            print("qrcode.h updated for C23 bool compatibility")

    # 5. Fix AnimatedGIF memcpy_P
    gif_cpp_path = '/root/crosspoint-reader/.pio/libdeps/simulator_x3/AnimatedGIF/src/AnimatedGIF.cpp'
    if os.path.exists(gif_cpp_path):
        with open(gif_cpp_path, 'r', encoding='utf-8') as f:
            gif_code = f.read()
        if '#define memcpy_P' not in gif_code:
            gif_code = gif_code.replace('#include "gif.inl"', '#ifndef memcpy_P\n#define memcpy_P memcpy\n#endif\n#include "gif.inl"')
            with open(gif_cpp_path, 'w', encoding='utf-8') as f:
                f.write(gif_code)
            print("AnimatedGIF.cpp updated with memcpy_P")

if __name__ == '__main__':
    main()
