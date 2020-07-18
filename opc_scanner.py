from collections import deque
import datetime
import logging

import OpenOPC


class DataPoint:
    conn_status = {
        -3: 'External reference not resolved',
        -2: 'Parameter not configured',
        -1: 'Module not configured',
        0: 'Good',
        1: 'Not communicating',
    }

    def __init__(self, name, canonical_datatype, value, quality, timestamp, conn_status_int, required_attempts):
        self.name = name
        self.canonical_datatype = canonical_datatype
        self.value = value
        self.quality = quality
        self.timestamp = datetime.datetime.strptime(timestamp[:-6], "%Y-%m-%d %H:%M:%S")
        self.conn_status_int = conn_status_int
        self.required_attempts = required_attempts

    @property
    def conn_status_str(self):
        return DataPoint.conn_status[self.conn_status_int]

    def __str__(self):
        """Short-hand access to name:value pair"""
        return f"{self.name}: {self.value}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r}, {self.canonical_datatype!r}, {self.value!r}, " \
               f"{self.quality!r}, {self.timestamp!r}, {self.conn_status_int!r}, {self.required_attempts!r})"


class OPCScanner:
    MAX_RETRIES = 500
    MAX_HB_DELTA = 5  # Seconds beyond which an unchanged heartbeat value indicates stale communications

    def __init__(self, conn_cfg, use_alt_host=False):
        if use_alt_host:
            self.opc_host = conn_cfg["OPC_HOST_ALT"]
        else:
            self.opc_host = conn_cfg["OPC_HOST"]
        self.client = OpenOPC.client(client_name="PyOPC")
        self.landmark_path = conn_cfg["LANDMARK_PATH"]  # Path to known/expected value, for health checks
        self.expected_landmark_val = conn_cfg["EXPECTED_LANDMARK_VAL"]  # Value to compare landmark observation against
        self.heartbeat_path = conn_cfg["HEARTBEAT_PATH"] # Path to constantly changing value, for health checks
        self.landmark = None
        self.heartbeats = deque(maxlen=2)

    def connect(self):
        try:
            self.client.connect(opc_server='OPC.DeltaV.1', opc_host=self.opc_host)
            logging.info("Achieved successful connection to DeltaV OPC server")
            logging.info(self.client.info())

        except OpenOPC.OPCError as e:
            logging.error("Could not connect: " + str(e))
            raise e

    def close(self):
        try:
            self.client.close()
            logging.info("Closed connection to DeltaV OPC server")
        except NameError:
            pass  # No need to attempt to close if opc object never created.

    def get_datapoint(self, path):
        """Retrieve a single value for an OPC path."""
        retries = self.MAX_RETRIES
        exc_for_return = None
        while retries > 0:
            try:
                properties = self.client.properties(path)
                good = False
                for prop in properties:
                    # SCAN PROPERTIES, LOOKING FOR ITEM QUALITY == GOOD
                    if str(prop[1]) == 'Item Quality':
                        if str(prop[2]) == 'Good':
                            good = True
                        else:
                            retries -= 1  # Should not occur, but had to include.
                if good:
                    return DataPoint(
                        name=properties[0][2],
                        canonical_datatype=properties[1][2],
                        value=properties[2][2],
                        quality=properties[3][2],
                        timestamp=properties[4][2],
                        conn_status_int=properties[9][2],
                        required_attempts=self.MAX_RETRIES + 1 - retries
                    )
                else:  # 'Item Quality' EITHER NEVER FOUND, OR FOUND TO BE BAD
                    retries -= 1
                    exc_for_return = "Item quality not good on final pass"

            except Exception as exc:
                logging.debug(exc)
                retries -= 1
                exc_for_return = exc

        if "OLE error 0xc0040007" in str(exc_for_return):
            exc_for_return = "DoesNotExist"
        return exc_for_return  # DEPLETED ALL RETRIES - UNSUCCESSFUL SCAN

    def update_integrity_markers(self):
        """
        Record results of scanning a path with a known/expected value, and a path known/expected to change constantly.
        Intended to be run cyclically by outer program loop to provide up-to-date assessment of communications health.
        """
        self.landmark = self.get_datapoint(self.landmark_path)
        current_heartbeat = self.get_datapoint(self.heartbeat_path)
        if len(self.heartbeats) < 2 or current_heartbeat.value != self.heartbeats[-1].value:  # Only record on change
            self.heartbeats.append(current_heartbeat)

    def get_comms_integrity(self):
        # TODO - need to thoroughly evaluate the ways heartbeat stuff can fail
        landmark_result = self.landmark.value == self.expected_landmark_val
        heartbeat_delta = (self.heartbeats[-1].timestamp - self.heartbeats[0].timestamp).seconds
        heartbeat_result = heartbeat_delta <= self.MAX_HB_DELTA

        result, status_text = True, ''
        if landmark_result and heartbeat_result:
            status_text += 'Good'

        if not landmark_result:
            result = False
            status_text += f"| Bad landmark - expected {self.expected_landmark_val}, got {self.landmark}"

        if not heartbeat_result:
            result = False
            status_text += f"| Bad heartbeat - delta: {heartbeat_delta} seconds"

        return result, status_text
