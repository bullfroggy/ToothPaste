import bluetooth
import os
import sys
import socket
import subprocess
import ntpath
import threading
from threading import *
import time
from subprocess import Popen, PIPE
bt = True
accepter = True
lock = threading.Lock()
server_sock = ""
client_sock = ""
port = 17

class Thread(threading.Thread):
    def __init__(self, t, *args):
        threading.Thread.__init__(self, target=t, args=args)
        self.start()

class Device():
    friendly = ""
    addr = ""
    index = 0
    def __init__(self, friendly, addr, index):
        self.friendly = friendly
        self.addr = addr
        self.index = index

def make_device(friendly, addr, index):
    device = Device(friendly, addr, index)
    return device

def checkBT():
    print("Bluetooth adapter check")
    command = 'netsh interface set interface name="Bluetooth Network Connection" admin=enabled'
    out, err = subprocess.Popen(command, stdout=PIPE, stderr=PIPE).communicate()
    out = out.decode('utf-8')
    err = err.decode('utf-8')
    if "The system cannot find the file specified." in out:
        print("Bluetooth adapter does not exist or is switched off")
        return False
    elif "Run as administrator" in out:
        print("Please run the program as an administrator to utilize Bluetooth functionality")
    else:
        print("Bluetooth adapter enabled")
        return True

def start(device_list):
    global bt	
    print("Transfer files over Bluetooth or Wi-Fi?")
    print("\t1. Bluetooth")
    print("\t2. Wi-Fi")
    print("\t3. Exit")
    response = input()
    if("1" in response or "bluetooth" in response.lower()):
        if checkBT():
            bt = True
            nextBT(device_list)
        else:
            start(device_list)
    elif("2" in response or "wi" in response.lower()):
        bt = False
        nextWF(device_list)
    elif("3" in response or "exit" in response.lower()):
        os._exit(1)
    else:
        print("Not a valid response")
        start(device_list)

def nextBT(device_list):
    print("What would you like to do?:")
    print("\t1. Scan for Bluetooth Devices")
    print("\t2. Connect to Bluetooth Device")
    print("\t3. Listen for Bluetooth Connection")
    print("\t4. Return to Main Menu")
    response = input()	
    if("1" in response or "scan" in response.lower()):
        scanBT(device_list)
    elif("2" in response or "connect" in response.lower()):
        connect(device_list)
    elif("3" in response or "listen" in response.lower()):
        a = Thread(accept, device_list)
        b = Thread(back, a)
    elif("4" in response or "return" in response.lower()):
        start(device_list)
    else:	
        print("Not a valid response.")
        start(device_list)

def back(a):
    global server_sock
    q = input("Press q to quit\n")
    if q == 'q':
        #try:
        a._delete()
        os._exit(1)
        #except:
                #print(sys.exc_info())
    else:
        back(a)


def nextWF(device_list):
    print("What would you like to do?:")
    print("\t1. Scan for Wi-Fi Devices")
    print("\t2. Connect to Wi-Fi Device")
    print("\t3. Listen for Wi-Fi Connection")
    print("\t4. Return to Main Menu")
    response = input()
    if("1" in response or "scan" in response.lower()):
        scanWF(device_list)
    elif("2" in response or "connect" in response.lower()):
        connect(device_list)
    elif("3" in response or "listen" in response.lower()):
        a = Thread(accept, device_list)
        b = Thread(back, a)
    elif("4" in response or "return" in response.lower()):
        start(device_list)
    else:	
        print("Not a valid response.")
        start(device_list)

def scanBT(device_list):
    device_list[0] = []
    i = 0
    for bdaddr in bluetooth.discover_devices():
        friendly = bluetooth.lookup_name(bdaddr, 10)
        device_list[0].append(make_device(friendly, bdaddr, i))
        print(friendly + " : " + bdaddr)
        i = i + 1
    scannedBTMenu(device_list)

def scanWF(device_list):
    wifi_address = []
    device_list[1] = []
    out, err = subprocess.Popen("powershell.exe arp -a", stdout=PIPE, stderr=PIPE).communicate()
    out = out.decode('utf-8')
    print(out)
    out = out.split('\n')
    for x in out:
        if "dynamic" in x:
            x = x.split()[0]
            wifi_address.append(x)
    i = 0
    for x in wifi_address:
        command = "powershell.exe -ExecutionPolicy ByPass -File getFriendly.ps1 " + x
        out, err = subprocess.Popen(command, stdout=PIPE, stderr=PIPE).communicate()
        out = out.decode('utf-8').rstrip()
        device_list[1].append(make_device(x, out, i))
        print(x + " : " + out)
        i = i + 1
    scannedWFMenu(device_list)

def scannedBTMenu(device_list):
    print("What would you like to do?:")
    print("\t1. Connect to Bluetooth Device")
    print("\t2. Return to Bluetooth Menu")
    response = input()
    if("1" in response or ("connect" in response.lower() or "bluetooth" in response.lower())):
        connect(device_list)
    elif("2" in response or ("main" in response.lower() and "menu" in response.lower())):
        nextBT(device_list)
    else:
        print("Not a valid response.")
        scannedBTMenu(device_list)

def scannedWFMenu(device_list):
    print("What would you like to do?:")
    print("\t1. Connect to Wi-Fi Device")
    print("\t2. Return to Wi-Fi Menu")
    response = input()
    if("1" in response or ("connect" in response.lower() or "wi" in response.lower())):
        connect(device_list)
    elif("2" in response or ("main" in response.lower() and "menu" in response.lower())):
        nextWF(device_list)
    else:
        print("Not a valid response.")
        scannedWFMenu(device_list)

def checkDevice(friendly, device_list):
    print("Verifying device name")
    for bdaddr in bluetooth.discover_devices():
        if friendly == bluetooth.lookup_name(bdaddr, 10):
            print("Device exists!")
            return bdaddr
        elif friendly == bdaddr:
            print("Device exists!")
            return bdaddr
    print("Device does not exist")
    if len(device_list[0]) == 0:
        nextBT(device_list)
    else:
        connect(device_list)
    os._exit(1)

def getBTDeviceaddr(inpt, device_list):
    for device in device_list[0]:
        if inpt == device.friendly:
            addr = device.addr
            print("Device exists!")
            return addr
        elif inpt == str(device.index + 1):
            addr = device.addr
            print("Device exists!")
            return addr
        elif inpt == device.addr:
            addr = device.addr
            print("Device exists!")
            return addr
        elif inpt == str(len(device_list[0]) + 1):
            friendly = input("Enter the name or address of the device you would like to connect to: ")
            addr = checkDevice(friendly, device_list)
            return addr
        elif inpt == str(len(device_list[0]) + 2):
            nextBT(device_list)
    print("Not a valid response")
    connect(device_list)
    os._exit(1)

def getWFDeviceaddr(inpt, device_list):
    for device in device_list[1]:
        if inpt == device.friendly:
            addr = device.addr
            return addr
        elif inpt == str(device.index + 1):
            addr = device.addr
            return addr
        elif inpt == device.addr:
            addr = device.addr
            return addr
        elif inpt == str(len(device_list[1]) + 1):
            addr = input("Enter the name or address of the device you would like to connect to: ")
            return addr
        elif inpt == str(len(device_list[1]) + 2):
            nextWF(device_list)
    print("Not a valid response")
    connect(device_list)
    os._exit(1)

def connect(device_list):
    addr = ""
    global accepter
    global bt
    accepter = False
    if bt:
        num = 0
    else:
        num = 1
    if len(device_list[num]) == 0:
        if bt:
            addr = input("Enter the address of the device you would like to connect to: ")
        else:
            addr = input("Enter the name or address of the device you would like to connect to: ")
    else:
        print("Which device would you like to connect to?: ")
        i = 0
        for device in device_list[num]:
            print("\t" + str(device_list[num][i].index + 1) + ". " +  device_list[num][i].friendly + " : " +  device_list[num][i].addr)
            i = i + 1
        print("\t" + str(i + 1) + ". Unlisted Device")
        print("\t" + str(i + 2) + ". Cancel and return to Wi-Fi Menu")
        addr = input()
    if bt:
        addr = getBTDeviceaddr(addr, device_list)
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    else:
        addr = getWFDeviceaddr(addr, device_list)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 17
    print("Connecting to: " + addr)
    try:
        sock.connect((addr, port))
    except:
        print("Could not connect to device")
        if len(device_list[1]) == 0:
            if bt:
                nextBT(device_list)
            else:
                nextWF(device_list)
        else:
            connect(device_list)
    print("Connection successful!")
    connected(sock, addr, device_list, port)

def send(sock, addr, device_list, port):
    global bt
    print(str(port))
    if sock == "":
        if bt:
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #try:
        sock.connect((addr, port))
        #except:
        #	print("The other user has been disconnected")
        #	sock.close()
        #	start(device_list)
    source = input("Please enter the name and destination of the file you wish to send: ")
    try:
        name = ntpath.basename(source) + "\n"
        size = str(os.path.getsize(source)) + "\n"
        f = open(source, "rb")
    except:
        print("File does not appear to exist")
        send(sock, addr, device_list, port)
    l = f.read()
    print("Sending " + ntpath.basename(source))
    print(str(os.path.getsize(source)) + " bytes")
    name = bytes(name, 'utf-8')
    size = bytes(size, 'utf-8')
    sock.send(name)
    sock.send(size)
    sock.send(l)
    f.close()
    print("File transfer complete!")
    send(sock, addr, device_list, port)

def accept(device_list):
    global bt
    global server_sock
    print("Listening for connections")
    global accepter
    accepter = True
    port = 17
    if bt:
        server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        server_sock.bind(("",port))
    else:
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(("",port))
    server_sock.listen(1)
    client_sock,address = server_sock.accept()
    if bt:
        print("Accepted connection from " + address[0])
    else:
        print("Accepted connection from " + address[0])
    connected(client_sock, address[0], device_list, port)

def connected(sock, addr, device_list, port):
    a = Thread(receive, sock, addr, device_list, port)
    s = Thread(send, sock, addr, device_list, port)

def receive(sock, addr, device_list, port):
    print("Waiting to receive file")
    dat = True
    nameArray = []
    sizeArray = []
    while(dat):
        data = sock.recv(1)
        data = data.decode("utf-8")
        if(data == '\n'):
            dat = False
        else:
            nameArray.append(data)
    nameArray = str(''.join(nameArray))
    print("Receiving " + nameArray)
    dat = True
    f = open(nameArray, 'wb')
    while(dat):
        data = sock.recv(1)
        data = data.decode("utf-8")
        if(data == '\n'):
            dat = False
        else:
            sizeArray.append(data)
    sizeArray = str(''.join(sizeArray))
    print(sizeArray + " bytes")
    dat = True
    total = 0
    while(dat):
        data = sock.recv(512000)
        f.write(data)
        val = len(data)
        total = total + val
        print(str(total) + "/" + str(int(sizeArray)))
        sys.stdout.flush()
        percent = (os.stat(nameArray).st_size/int(sizeArray))*100
        sys.stdout.write("\r" + str(int(percent)) + "% complete " + str(total) + "/" + str(sizeArray) + " bytes")
        if total == int(sizeArray):
            dat = False
    f.close()
    sys.stdout.flush()
    percent = (os.stat(nameArray).st_size/int(sizeArray))*100
    sys.stdout.write("\r" + str(int(percent)) + "% complete " + str(total) + "/" + str(sizeArray) + " bytes\n")
    print("File transfer complete!")
    receive(sock, addr, device_list, port)

def directConnectBT(sock):
    start(device_list)

def directConnectWF(sock):
    start(device_list)

device_list = []
device_listBT = []
device_listWF = []
device_list.append(device_listBT)
device_list.append(device_listWF)
start(device_list)