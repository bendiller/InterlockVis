import json
import logging
import sys
import traceback

import jsonizer
from opc_scanner import OPCScanner


def prove_connectivity(inp_cfg, use_alt_host=False, test_path=None):
    """Use some known paths to validate that retrieval of values is functioning properly"""
    if use_alt_host:
        opc = OPCScanner(opc_host=inp_cfg["OPC_HOST_ALT"])
    else:
        opc = OPCScanner(opc_host=inp_cfg["OPC_HOST"])
    try:
        opc.connect()

        if test_path:  # For quick testing off OPC paths to add to interlock configurations
            result = opc.get_datapoint(test_path)
            logging.info(result)
            logging.info(repr(result))

        else:  # Default run mode just to prove connectivity
            result_1 = opc.get_datapoint(inp_cfg["TEST_PATH_1"])
            logging.info(result_1)
            logging.info(repr(result_1))

            result_2 = opc.get_datapoint(inp_cfg["TEST_PATH_2"])
            logging.info(result_2)
            logging.info(repr(result_2))

    except Exception as e:
        logging.exception("Exception encountered: " + str(e))
        traceback.print_exc()

    finally:
        opc.close()


def store_sample_data(conn_cfg, tag_cfg_fname, out_fname):
    """
    Read OPC data and build DataPoint objects for tags in tag_cfg_file; store results as Python repr in out_file.
    This is only used to collect "dummy" data to allow for easier development offline from production system.
    """
    interlock = jsonizer.read_file(tag_cfg_fname)
    datapoints = list()
    opc = OPCScanner(opc_host=conn_cfg['OPC_HOST'])
    try:
        opc.connect()

        for component in interlock.components:
            for indication in component.indications:
                datapoints.append(opc.get_datapoint(indication.path))

    except Exception as e:
        logging.exception("Exception encountered: " + str(e))
        traceback.print_exc()

    finally:
        opc.close()

    logging.info(datapoints)
    with open(out_fname, 'w') as f:
        f.write(repr(datapoints))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with open('cfg.json', 'r') as fp:
        cfg = json.load(fp)

    if not cfg:
        logging.error("Could not load configuration from 'cfg.json'. Exiting.")
        sys.exit()

    # prove_connectivity(cfg, use_alt_host=False)
    store_sample_data(cfg, 'HS_525069.json', 'samples.py')
