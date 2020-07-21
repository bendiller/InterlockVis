import json
import logging
import unittest
import sys
import time
import traceback

from opc_scanner import OPCScanner


class CommsIntegrityTests(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        with open('..\\cfg.json', 'r') as fp:
            cfg = json.load(fp)

        if not cfg:
            logging.error("Could not load configuration from 'cfg.json'. Exiting.")
            sys.exit()

        self.opc = OPCScanner(cfg)

        try:
            self.opc.connect()

        except Exception as e:
            logging.exception("Exception encountered: " + str(e))
            traceback.print_exc()

        self.sleep_val = self.opc.HEARTBEAT_UPDATE_RATE / 2  # Prevent aliasing

    def tearDown(self):
        self.opc.close()

    def test_good_comms_integrity(self):
        for i in range(3):
            self.opc.update_integrity_markers()
            time.sleep(self.sleep_val)

        result, status_text = self.opc.get_comms_integrity()

        self.assertTrue(result)
        self.assertEqual(status_text, 'Good')

    def test_bad_landmark(self):
        self.opc.landmark_path += 'nonsense_str'  # Temporarily set landmark_path to a bad path
        self.opc.update_integrity_markers()

        result, status_text = self.opc.get_comms_integrity()
        self.assertFalse(result)
        self.assertIn('Bad landmark', status_text)

    def test_unchanging_heartbeat(self):
        self.opc.heartbeat_path = self.opc.landmark_path  # Temporarily set to path with a known static value
        for i in range(3):
            self.opc.update_integrity_markers()
            time.sleep(self.sleep_val)

        result, status_text = self.opc.get_comms_integrity()

        self.assertFalse(result)
        self.assertIn('Bad heartbeat', status_text)

    def test_aliasing_possible(self):
        for i in range(3):
            self.opc.update_integrity_markers()
            time.sleep(2 * self.sleep_val)

        self.assertTrue(self.opc.aliasing_possible)

    def test_aliasing_not_possible(self):
        for i in range(3):
            self.opc.update_integrity_markers()
            time.sleep(self.sleep_val)

        self.assertFalse(self.opc.aliasing_possible)
