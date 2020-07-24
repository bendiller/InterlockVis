import json
import logging
import sys
import threading
import time

import PySimpleGUI as sg

import jsonizer
from opc_scanner import OPCScanner
from frontend.indication_row import IndicationRow
from frontend.styling import MAIN_WIDTH, style_args
from frontend.gui_logger import gui_log_formatter, GuiHandler


def scan_opc(run_freq, window, conn_cfg, logger, interlock):
    opc = OPCScanner(conn_cfg)
    try:
        opc.connect()
    except Exception as e:
        logger.exception("Exception encountered: " + str(e))
        return  # Exit thread, this one cannot be useful

    while True:
        time.sleep(run_freq/1000)
        for comp in interlock.components:
            for indication in comp.indications:
                dp = opc.get_datapoint(indication.path)
                window.write_event_value('-DP-', {'indication': indication, 'dp': dp})


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

        self.indication_rows = {}
        self.layout = self.build_layout()
        self.window = sg.Window('Interlock Visualizer', self.layout, finalize=True)
        self.logger = self.configure_logger()

    def configure_logger(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        gui_handler = GuiHandler(logging.INFO, self.window.write_event_value)
        gui_handler.setFormatter(gui_log_formatter)
        logger.addHandler(gui_handler)
        return logger

    def build_layout(self):
        ilock_rows = list()
        ilock_rows.append([sg.Text(text=self.interlock.name, key='ilock_name', **style_args(self.interlock, 'name')), ])
        for comp in self.interlock.components:
            ilock_rows.append([
                sg.Text(text=comp.name, key=comp.name, **style_args(comp, 'name')),
                sg.Text(text=f"({comp.desc})", key=comp.desc, **style_args(comp, 'desc'))
            ])
            for indication in comp.indications:
                ind_row = IndicationRow(indication)
                self.indication_rows[indication] = ind_row  # For easy access later during update cycle
                ilock_rows.append(ind_row)

        return [
            *ilock_rows,
            [sg.Multiline(size=(MAIN_WIDTH*2, 26), key='-ML-', autoscroll=True)],
            [sg.Button('Exit')],
        ]

    def run(self):
        threading.Thread(
            target=scan_opc,
            args=(250, self.window, self.conn_cfg, self.logger, self.interlock),
            daemon=True
        ).start()
        sg.cprint_set_output_destination(self.window, '-ML-')

        while True:
            event, values = self.window.read()
            if event in (sg.WIN_CLOSED, 'Exit'):
                break
            elif event == '-LOG-':
                sg.cprint(values[event])
            elif event == '-DP-':  # DataPoint collected - update relevant GUI elements
                try:
                    self.indication_rows[values[event]['indication']].update(values[event]['dp'], self.logger)
                except IndexError as e:
                    self.logger.exception(e)
            else:
                self.logger.warning(f"Unknown event type: {event} - {values[event]}")

        self.window.close()
