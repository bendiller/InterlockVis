import logging
from frontend.gui import Gui


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gui = Gui('cfg.json', 'HS_525069.json')
    gui.run()
