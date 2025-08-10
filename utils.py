from IPython.core.magic import (Magics, magics_class, cell_magic)
from IPython import get_ipython
import psutil

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