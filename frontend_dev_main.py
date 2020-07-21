import json
import logging
import sys
import threading
import time
import traceback

import PySimpleGUI as sg

from opc_scanner import OPCScanner


def worker(thread_name, run_freq, window, conn_cfg):
    opc = OPCScanner(conn_cfg)
    try:
        opc.connect()
    except Exception as e:
        logging.exception("Exception encountered: " + str(e))
        traceback.print_exc()
        return  # Exit thread, this one cannot be useful

    for i in range(5):
        time.sleep(run_freq/1000)
        result = opc.get_datapoint(conn_cfg["TEST_PATH_1"])
        window.write_event_value(thread_name, str(result))

    opc.close()  # TODO Will need to figure out how to trigger this on program close / GUI loop exit


def run_gui(conn_cfg):
    layout = [
        [sg.Multiline(size=(40, 26), key='-ML-', autoscroll=True)],
        [sg.Button('Exit')],
    ]

    window = sg.Window('Interlock Visualizer', layout, finalize=True)
    threading.Thread(target=worker, args=('MainWorker', 2000, window, conn_cfg), daemon=True).start()

    sg.cprint_set_output_destination(window, '-ML-')

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        sg.cprint(event, values[event])  # This is where the GUI is updated with return info from thread

    window.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    with open('cfg.json', 'r') as fp:
        cfg = json.load(fp)

    if not cfg:
        logging.error("Could not load configuration from 'cfg.json'. Exiting.")  # TODO - handle in GUI later
        sys.exit()

    run_gui(cfg)
