#!/usr/bin/python

import time
import os
import sys
import logging
import helpers
from powerpi import Powerpi


# Logging
logging.basicConfig(level=logging.INFO)


# GPIO
GPIO4_AVAILABLE = True
try:
    import RPi.GPIO as GPIO
except:
    GPIO4_AVAILABLE = False
    logging.error(
        "Error importing GPIO library, UPS will work without interrupt")


# Timeout
TIMEOUT = 100  # timeout to shutdown in seconds
counter = 0


# Power pi

#### Pass in options to this section to suit your battery and input specs ####
# Refer to http://www.ti.com/lit/ds/symlink/bq25895.pdf for register maps

# ILIM_INDEX is used to set the input current limit, i.e the maximum current the
# UPS will draw from the power input. It does not affect the output current from
# the UPS. If more current is required at the output than the input is cpabale of,
# the UPS will augment that current from the battery.

# BAT_CAPACITY, CURRENT_DRAW and VBAT_MAX are used to estimated the state of charge
# of the battery since there is not current sensor on this UPS. These values along
# with the battery voltage is used to derive the state of charge of the battery.

# To make the charge percent of the battery shown more accurate, take a note of
# the battery voltage when charging is complete (red LED turns off after plugging in)
# and edit the VBAT_MAX to that value.

# NB: Changing these values does not affect or change the behavior of the UPS.

ppi = Powerpi({
    # Input current limit, list index from BYTE_ILIM_LIST in powerpi.py
    'ILIM_INDEX': helpers.env_var('ILIM_INDEX') or 1,  # 1 = 3.25A

    # Charging current limit, list index from BYTE_ILIM_LIST in powerpi.py
    'ICHG_INDEX': helpers.env_var('ICHG_INDEX') or 1,  # 1 = 1.0A

    # Charge voltage, list index from BYTE_ILIM_LIST in powerpi.py
    'VREG_INDEX': helpers.env_var('VREG_INDEX') or 4,  # 4 = 4.208V

    # Battery capacity in mAh
    'BAT_CAPACITY': helpers.env_var('BAT_CAPACITY') or 2900,  # 2900mAh

    # Approx current draw in mAh
    'CURRENT_DRAW': helpers.env_var('CURRENT_DRAW') or 2000,  # 2000mAh

    # This should be the battery when charged to a 100%
    'VBAT_MAX': helpers.env_var('VBAT_MAX') or 4.208,  # 4.208v

    # Determines the battery voltage at which the UPS will shutoff.
    'VBAT_LOW': helpers.env_var('VBAT_LOW') or 3.200,  # 3.200v
})


def read_status(clear_fault=False):
    global disconnectflag, ENABLE_UDP, counter, TIMEOUT
    err, status = ppi.read_status(clear_fault)

    if err:
        time.sleep(1)
        return

    if status["PowerInputStatus"] == "Not Connected" and disconnectflag == False:
        disconnectflag = True
        message = "echo Power Disconnected, system will shutdown in %d minutes! | wall" % (
            status['TimeRemaining'])
        os.system(message)

    if status["PowerInputStatus"] == "Connected" and disconnectflag == True:
        disconnectflag = False
        message = "echo Power Restored, battery at %d percent | wall" % (
            status['BatteryPercentage'])
        os.system(message)
        counter = 0

    logging.debug(status)

    if(status['BatteryVoltage'] < ppi.VBAT_LOW):
        ppi.bat_disconnect()
        os.system('sudo shutdown now')

    if disconnectflag:
        if counter > TIMEOUT:
            ppi.bat_disconnect()
            os.system('sudo shutdown now')
        counter = counter + 2


def interrupt_handler(channel):
    read_status(True)


def main():
    if ppi.initialize():
        sys.exit(1)

    if GPIO4_AVAILABLE:
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                4, GPIO.FALLING, callback=interrupt_handler, bouncetime=200)
        except Exception as ex:
            logging.error(
                "Error attaching interrupt to GPIO4, UPS will work without interrupt.")

    while (True):
        read_status()


if __name__ == "__main__":
    main()
