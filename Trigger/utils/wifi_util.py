def get_wifi_state(driver):
    return 'enabled' in driver.shell('dumpsys wifi | grep ^Wi-Fi').output.strip()

def restart_wifi(driver):
    driver.shell('cmd wifi remove-all-suggestions')
    driver.shell('cmd wifi set-wifi-enabled disabled')
    # driver.shell('cmd wifi add-suggestion TP-LINK_5G_ZSK wpa2 zsk405629')
    driver.shell('cmd wifi add-suggestion TP-LINK_5G wpa2 123456')
    driver.shell('cmd wifi set-wifi-enabled enabled')