import json
import logging
import sys
import threading
import time

import PySimpleGUI as sg

import jsonizer
from opc_scanner import OPCScanner
from frontend.styling import MAIN_WIDTH, style_args
from frontend.gui_logger import gui_log_formatter, GuiHandler


def scan_opc(thread_name, run_freq, window, conn_cfg, logger):
    opc = OPCScanner(conn_cfg)
    try:
        opc.connect()
    except Exception as e:
        logger.exception("Exception encountered: " + str(e))
        return  # Exit thread, this one cannot be useful

    for i in range(5):
        time.sleep(run_freq/1000)
        result = opc.get_datapoint(conn_cfg["TEST_PATH_1"])
        window.write_event_value(thread_name, str(result))

    opc.close()


class Gui:
    def __init__(self, conn_cfg_path, interlock_cfg_path):
        error_status = ''
        try:
            with open(conn_cfg_path, 'r') as fp:
                self.conn_cfg = json.load(fp)
        except Exception as e:
            error_status += f"\nError loading connection configuration:\n{e}\n"

        try:
            self.interlock = jsonizer.read_file(interlock_cfg_path)
        except Exception as e:
            error_status += f"\nError loading interlock configuration:\n{e}\n"

        if error_status != '':
            # Program cannot continue without valid configuration. Create a pop-up explaining, and exit after.
            sg.popup_error(f"Failed to load configuration - program must exit. Details:\n{error_status}")
            sys.exit()

        self.logger = None  # Can only be set after Window object exists
        self.layout = self.build_layout()

    def configure_logger(self, window):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        gui_handler = GuiHandler(logging.INFO, window.write_event_value)
        gui_handler.setFormatter(gui_log_formatter)
        self.logger.addHandler(gui_handler)

    def build_layout(self):
        ilock_rows = list()
        ilock_rows.append([sg.Text(text=self.interlock.name, key='ilock_name', **style_args(self.interlock, 'name')), ])
        for comp in self.interlock.components:
            ilock_rows.append([sg.Text(text=comp.name, key=comp.name, **style_args(comp, 'name')), ])
            ilock_rows.append([sg.Text(text=comp.desc, key=comp.desc, **style_args(comp, 'desc')), ])

        return [
            *ilock_rows,
            [sg.Multiline(size=(MAIN_WIDTH*2, 26), key='-ML-', autoscroll=True)],
            [sg.Button('Exit')],
        ]

    def run(self):
        window = sg.Window('Interlock Visualizer', self.layout, finalize=True)
        self.configure_logger(window)
        threading.Thread(
            target=scan_opc,
            args=('MainWorker', 2000, window, self.conn_cfg, self.logger),
            daemon=True
        ).start()

        sg.cprint_set_output_destination(window, '-ML-')

        while True:
            event, values = window.read()
            if event == '-LOG-':
                sg.cprint(values[event])
            elif event in (sg.WIN_CLOSED, 'Exit'):
                break
            else:
                sg.cprint(event, values[event])  # This is where the GUI is updated with return info from thread

        window.close()
