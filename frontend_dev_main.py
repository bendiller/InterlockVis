from frontend.gui import Gui


if __name__ == "__main__":
    gui = Gui('cfg.json', 'dev_ilock.json')
    gui.run()
