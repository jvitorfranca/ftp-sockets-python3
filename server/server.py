import socket
import os
import sys
import tqdm
import struct


class ServerFTP:
    def __init__(self, ip, port, buffer=1024):

        self.__ip = ip
        self.__port = port
        self.__buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.conn = None
        self.addr = None

    def bind(self):
        '''
            Wait a client's connection.

            Return a connection and address.
        '''
        self.socket.bind((self.__ip, self.__port))
        self.socket.listen(1)
        self.conn, self.addr = self.socket.accept()

    def receive(self):
        ''' Receive data from the socket.

            The return value is a string representing the data received.
        '''

        return self.conn.recv(self.__buffer)

    def list_files(self):
        '''
            1. Get list of files in directory
            2. Send over the number of files, so the client knows what to expect
            3. Send over the file names and sizes whilst totaling the directory size
        '''

        send = ""

        path = os.getcwd()

        dirs = os.listdir(path)

        for f in dirs:
            send = send + f + ' '

        self.conn.send(send.encode())

        print("Successfully sent file listing \n")

    def download(self):
        '''
            Send file in batches with the buffer size
        '''

        filename = self.conn.recv(1024)

        filesize = os.path.getsize(filename)

        progress = tqdm.tqdm(range(
            filesize), f"Sending {filename.decode()}", unit="B", unit_scale=True, unit_divisor=1024)

        self.conn.send(struct.pack("i", filesize))

        with open(filename, "rb") as f:

            for _ in progress:

                bytes_read = f.read(self.__buffer)

                if not bytes_read:

                    break

                self.conn.sendall(bytes_read)

                progress.update(len(bytes_read))

    def upload(self):
        '''
            Receive a file from client and save it in chunks
        '''

        str_size = struct.unpack("i", self.conn.recv(4))[0]

        filename = self.conn.recv(str_size)

        print(filename)

        filename = filename.decode()

        with open(filename, 'wb') as f:

            print('Starting upload \n')

            bytes_recieved = 0

            size = struct.unpack("i", self.conn.recv(4))[0]

            while True:

                data = self.conn.recv(self.__buffer)

                f.write(data)

                bytes_recieved += self.__buffer

                if bytes_recieved >= size:

                    break

        print('Upload Successful\n')

    def quit(self):
        ''' Send quit confirmation and restart server.
        '''
        self.conn.send("1".encode())
        self.conn.close()
        self.socket.close()

        os.execl(sys.executable, sys.executable, *sys.argv)


if __name__ == "__main__":

    server = ServerFTP('127.0.0.1', 2350)

    print('FTP Server \n')

    print('Binding... \n')

    server.bind()

    while True:

        print("Waiting instructions \n")

        data = server.receive()

        data = data.decode()

        print("Received instruction: {0}\n".format(data))

        if data == "LIST":

            server.list_files()

        elif data == "DOWN":

            server.download()

        elif data == "UP":

            server.upload()

        elif data == "QUIT":

            server.quit()

            break

        data = None
