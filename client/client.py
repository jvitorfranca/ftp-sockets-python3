import socket
import struct
import sys
import tqdm
import os


class ClientFTP:
    def __init__(self, ip, port, buffer=1024):

        self.__ip = ip
        self.__port = port
        self.__buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        '''
            Connect with the server.
        '''

        try:
            self.socket.connect((self.__ip, self.__port))
            print("Connection sucessful \n")
        except:
            print("Connection unsucessful. Make sure the server is online. \n")

    def list_files(self):
        '''
            List the files avaliable on the file server.
        '''
        try:
            self.socket.send("LIST".encode())

        except:
            print(
                "Couldn't make server request. Make sure a connection has bene established. \n")

        files = self.socket.recv(1024)

        files = files.decode().split(' ')

        for f in files[:-1]:

            print("\t {0}".format(f))

        print("")

    def download(self, filename):
        '''
            Download file from a remote server
        '''

        try:
            self.socket.send("DOWN".encode())

        except:
            print(
                "Couldn't make server request. Make sure a connection has bene established. \n")

        self.socket.send(filename.encode())

        with open(filename, 'wb') as f:

            print('Starting download \n')

            bytes_recieved = 0

            size = struct.unpack("i", self.socket.recv(4))[0]

            while True:

                data = self.socket.recv(self.__buffer)

                f.write(data)

                bytes_recieved += self.__buffer

                if bytes_recieved >= size:

                    break

        print('Download Successful\n')

    def upload(self, filename):
        '''
            Send at first the size of the file's name and then
            send it in batches.
        '''

        try:
            self.socket.send("UP".encode())

        except:
            print(
                "Couldn't make server request. Make sure a connection has bene established. \n")

        self.socket.send(struct.pack("i", len(filename.encode())))

        self.socket.send(filename.encode())

        filesize = os.path.getsize(filename)

        progress = tqdm.tqdm(range(
            filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)

        with open(filename, "rb") as f:

            self.socket.send(struct.pack("i", filesize))

            for _ in progress:

                bytes_read = f.read(self.__buffer)

                if not bytes_read:

                    break

                self.socket.sendall(bytes_read)

                progress.update(len(bytes_read))

    def chdir(self, pathname):

        '''
            Change the current working directory .
        '''

        try:
            self.socket.send("CD".encode())

        except:
            print(
                "Couldn't make server request. Make sure a connection has bene established. \n")
    
        self.socket.send(struct.pack("i", len(pathname.encode())))

        self.socket.send(pathname.encode())


    def quit(self):
        '''
            Send quit requisition and wait for confirmation
        '''

        self.socket.send("QUIT".encode())
        self.socket.recv(self.__buffer)
        self.socket.close()

        print("Server connection ended \n")


if __name__ == "__main__":

    client = ClientFTP('127.0.0.1', 2350)

    print("\nFTP Client \n")

    while True:

        command = input('Insert a command: ')

        if command.upper() == "CONN":

            print("\nSending server request... \n")

            client.connect()

        elif command.upper() == "LS":

            print('\nRequesting files... \n')

            client.list_files()

        elif command.upper() == "DOWN":

            filename = input('\nInsert filename: ')

            print("")

            client.download(filename)

        elif command.upper() == "UP":

            filename = input('\nInsert filename: ')

            print("")

            client.upload(filename)
        
        elif command.upper() == "CD":

            filename = input('\nInsert pathname: ')

            print("")

            client.chdir(filename)

        elif command.upper() == "QUIT":

            print('\nExiting... \n')

            client.quit()

            break

        else:

            client.socket.send(command.encode())
