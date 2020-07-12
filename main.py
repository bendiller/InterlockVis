import json
import logging
import sys
import traceback

from opc_scanner import OPCScanner


def prove_connectivity(inp_cfg, use_alt_host=False):
    """Use some known paths to validate that retrieval of values is functioning properly"""
    if use_alt_host:
        opc = OPCScanner(opc_host=inp_cfg["OPC_HOST_ALT"])
    else:
        opc = OPCScanner(opc_host=inp_cfg["OPC_HOST"])
    try:
        opc.connect()

        result_1 = opc.get_datapoint(inp_cfg["TEST_PATH_1"])
        print(result_1)
        print(repr(result_1))

        result_2 = opc.get_datapoint(inp_cfg["TEST_PATH_2"])
        print(result_2)
        print(repr(result_2))

    except Exception as e:
        print("Exception encountered: " + str(e))
        traceback.print_exc()

    finally:
        opc.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    with open('cfg.json', 'r') as fp:
        cfg = json.load(fp)

    if not cfg:
        print("Could not load configuration from 'cfg.json'. Exiting.")
        sys.exit()

    prove_connectivity(cfg, use_alt_host=False)
