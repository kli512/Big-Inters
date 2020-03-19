from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QMainWindow
import logging
import sys

from app import Application

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s')

    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext
    window = Application()
    window.show()
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)
