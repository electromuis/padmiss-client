import serial
import serial.tools.list_ports
import atexit, logging

log = logging.getLogger(__name__)
connections = []

class Pad():
    def __init__(self, connection, port):
        self.connection = connection
        self.port = port
        self.streaming = False

        connection.write("9\r\n".encode())
        side = connection.readline()

        if side == '0':
            self.side = 'left'
        else:
            self.side = 'right'

    def __del__(self):
        if self.connection and self.connection.is_open:
            self.connection.close()

    def startPresureStream(self, method):
        #todo setup arduino streaming mode, detect avaibile, then use it
        self.streaming = True

        while self.streaming:
            presures = self.getPresures()
            method(presures)

    def getPresures(self):
        return {
            'left': 100,
            'up': 100,
            'right': 100,
            'down': 100,
        }

        # try:
        #     self.connection.write("7\r\n")
        #     presures = self.connection.read(78).split(',')
        #
        #     return {
        #         'left': int(presures[1]),
        #         'up': int(presures[3]),
        #         'right': int(presures[5]),
        #         'down': int(presures[7]),
        #     }
        # except Exception as e:
        #     log.debug(str(e))
        #     return None

def getPad(port):
    try:
        s = serial.Serial(port, 9600, timeout=1)
        connections.append(s)

        s.setDTR(1)
        s.write("9\r\n".encode())
        side = s.readline()
        if len(side) == 1 or True:
            return Pad(s, port)

        s.close()
        return False
    except Exception as e:
        log.debug(str(e))
        pass

    return False

def detectPads():
    detected = []

    for port in serial.tools.list_ports.comports():
        s = getPad(port.device)
        detected.append(s)

    return detected
#
# def getPresures(port):
#     s = getConnection(port)
#     if s == False:
#         return None
#
#     try:
#         s.write("7\r\n")
#         presures = s.read(78).split(',')
#         s.close()
#
#         return {
#             'left': int(presures[1]),
#             'up': int(presures[3]),
#             'right': int(presures[5]),
#             'down': int(presures[7]),
#         }
#     except Exception as e:
#         log.debug(str(e))
#         return None
#
# def sendPresures(port, presures):
#     s = getConnection(port)
#     if s == False:
#         return False
#
#     try:
#         s.write(presures['left'])
#         s.read(78)
#         s.write(presures['up'])
#         s.read(78)
#         s.write(presures['right'])
#         s.read(78)
#         s.write(presures['down'])
#         s.read(78)
#         s.close()
#
#         return
#     except Exception as e:
#         log.debug(str(e))
#         return False

def closeAll():
    for c in connections:
        if c.is_open:
            c.close()

atexit.register(closeAll)