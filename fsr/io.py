import sys
import glob
import serial
import atexit

connections = []

def closeAll():
    for c in connections:
        if c.is_open:
            c.close()

atexit.register(closeAll())

def getConnection(port):
    try:
        s = serial.Serial(port, 9600, timeout=1)
        connections.append(s)

        s.setDTR(1)
        s.write("9\r\n")
        side = s.readline()
        if len(side) == 1:
            return s

        s.close()
        return False
    except (OSError, serial.SerialException):
        pass

    return False

def detectPads():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    detected = []

    for port in ports:
        s = getConnection(port)
        if s != False:
            detected.append(port)
            s.close()

        try:
            s = serial.Serial(port, 9600)
            s.setDTR(1)
            s.write("9\r\n")
            side = s.readline()
            if len(side) == 1:
                detected.append(port)

            s.close()
        except (OSError, serial.SerialException):
            pass

    return detected

def getPresures(port):
    s = getConnection(port)
    if s == False:
        return None

    try:
        s.write("7\r\n")
        presures = s.read(78).split(',')
        s.close()

        return {
            'left': int(presures[1]),
            'up': int(presures[3]),
            'right': int(presures[5]),
            'down': int(presures[7]),
        }
    except (OSError, serial.SerialException):
        return None

def sendPresures(port, presures):
    s = getConnection(port)
    if s == False:
        return False

    try:
        s.write(presures['left'])
        s.read(78)
        s.write(presures['up'])
        s.read(78)
        s.write(presures['right'])
        s.read(78)
        s.write(presures['down'])
        s.read(78)
        s.close()

        return True
    except (OSError, serial.SerialException):
        return False