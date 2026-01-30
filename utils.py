import os
from IPython.core.magic import (Magics, magics_class, cell_magic)
from IPython import get_ipython
import psutil
import pandas as pd
import re
from pathlib import Path

@magics_class
class TrafficMagic(Magics):

    @cell_magic
    def nettraffic(self, line, cell):
        net_io_start = psutil.net_io_counters()

        exec(cell, globals())  # esegue il contenuto della cella

        net_io_end = psutil.net_io_counters()
        sent_diff = (net_io_end.bytes_sent - net_io_start.bytes_sent) / (1024 ** 2)
        recv_diff = (net_io_end.bytes_recv - net_io_start.bytes_recv) / (1024 ** 2)

        print(f"{sent_diff:.2f} MB inviati; {recv_diff:.2f} MB ricevuti.")

def register_traffic_magic():
    ip = get_ipython()
    ip.register_magics(TrafficMagic)


class Movimenti:
    def __init__(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        os.system('mkdir -p ~/code/conto/data')
        self.data_dir = Path("~/code/conto/data").expanduser()
        self.data = self.load_excel_movimenti()

    def load_excel_movimenti(self):
        name_pattern = r'MovimentiCC_\d{4}-\d{2}-\d{2}\.xlsx'
        files = []
        for file in self.data_dir.iterdir():
            if re.match(name_pattern, file.name):
                files.append(str(file.resolve()))
        files.sort()
        if not files:
            print("No matching Excel files found.")
            return None
        df = pd.read_excel(files[0], header=None)
        return df
