import json
import logging
import unittest
import sys
import time
import traceback

from opc_scanner import OPCScanner


class CommsIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.INFO)
        with open('..\\cfg.json', 'r') as fp:
            cfg = json.load(fp)

        if not cfg:
            logging.error("Could not load configuration from 'cfg.json'. Exiting.")
            sys.exit()

        cls.opc = OPCScanner(cfg)

        try:
            cls.opc.connect()

        except Exception as e:
            logging.exception("Exception encountered: " + str(e))
            traceback.print_exc()

    @classmethod
    def tearDownClass(cls):
        cls.opc.close()

    def test_good_comms_integrity(self):
        for i in range(2*self.opc.MAX_HB_DELTA):
            self.opc.update_integrity_markers()
            time.sleep(1)

        result, status_text = self.opc.get_comms_integrity()

        self.assertTrue(result)
        self.assertEqual(status_text, 'Good')
