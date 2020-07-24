import json
import logging
import sys
import threading
import time

import PySimpleGUI as sg

from interlock import Indication
import jsonizer
from opc_scanner import OPCScanner
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
                window.write_event_value('-DP-', (indication, dp))


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
                ilock_rows.append(self.build_indication_row(indication))

        return [
            *ilock_rows,
            [sg.Multiline(size=(MAIN_WIDTH*2, 26), key='-ML-', autoscroll=True)],
            [sg.Button('Exit')],
        ]

    def build_indication_row(self, indication):
        """
        Core element of this project - this displays condensed info about interlock indication (will need to become a
        more full-featured object at some point, probably a custom PySimpleGUI Element).

        For now I just want to demonstrate live-updating GUI elements from OPC-scanning thread.
        """
        # May be better leave contents of these blank until first OPCScanner run, OR to run a full scan before layout
        name = sg.Text(text=indication.path, key=f"{indication.path}_name")
        pre_val_status = sg.Text(text="?????", key=f"{indication.path}_pre_val_status")
        post_val_status = sg.Text(text="?????", key=f"{indication.path}_post_val_status")
        return [name, pre_val_status, post_val_status]

    def update_elements(self, ilock_item, dp):
        """Determine type of element(s) to update; locate elements by key and give new contents, etc."""
        elems = {  # Clunky way to associate GUI elements with expected values for comparison with DP; fine for now
            'pre_val_status': {
                'obj': self.window.FindElement(f"{ilock_item.path}_pre_val_status", silent_on_error=True),
                'comp_attr': 'expected_val_pre'  # Name of attribute member of ilock_item to compare
            },
            'post_val_status': {
                'obj': self.window.FindElement(f"{ilock_item.path}_post_val_status", silent_on_error=True),
                'comp_attr': 'expected_val_post'
            }
        }

        for k in elems:
            if elems[k]['obj'] is None:
                self.logger.error(f"Could not find window element: {ilock_item.path}_{k}")
                for i in self.window.AllKeysDict:
                    self.logger.info(i)
            else:
                # Determine whether values match pre- and post-trip expectations, update elements:
                self.logger.debug(f"Updating window element: {ilock_item.path}_{k}")
                if dp.value == ilock_item.__dict__[elems[k]['comp_attr']]:
                    elems[k]['obj'].Update("True")
                else:
                    elems[k]['obj'].update("False")

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
                    self.update_elements(values[event][0], values[event][1])
                except IndexError as e:
                    self.logger.exception(e)
            else:
                self.logger.warning(f"Unknown event type: {event} - {values[event]}")

        self.window.close()
