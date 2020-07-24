"""Collect all logic for creating and updating the GUI elements based on new scans"""
from interlock import Indication
from opc_scanner import DataPoint
import PySimpleGUI as sg


class IndicationRow(list):
    def __init__(self, indication: Indication):
        self.indication = indication
        self.name = sg.Text(text=indication.path, key=f"{indication.path}_name")
        self.pre_val_status = sg.Text(text="*******", key=f"{indication.path}_pre_val_status")
        self.post_val_status = sg.Text(text="*******", key=f"{indication.path}_post_val_status")
        super().__init__([self.name, self.pre_val_status, self.post_val_status])

    def update(self, dp: DataPoint, logger):
        if self.name.get() != dp.name:
            logger.error(
                f"IndicationRow.update() tried to update incorrect element!\n"
                f"Element name: {self.name.get()}\n"
                f"DataPoint name: {dp.name}"
            )
        self.pre_val_status.update(f"{self.indication.expected_val_pre == dp.value}")
        self.post_val_status.update(f"{self.indication.expected_val_post == dp.value}")
