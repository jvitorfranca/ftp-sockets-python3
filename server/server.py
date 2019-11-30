import socket
import os
import sys
import tqdm
import struct
import time



class ServerFTP():
    def __init__(self, ip, port, buffer=1024):

        self.__ip = ip
        self.__port = port
        self.__buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.conn = None
        self.addr = None

        self.data_address = None
        self.datasock = None

        self.mode = 'I'
    
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

    def pwd(self):
        '''
            1. Get list of files in directory
            2. Send over the number of files, so the client knows what to expect
            3. Send over the file names and sizes whilst totaling the directory size
        '''
        path = os.getcwd()
        
        self.conn.send(('257 \"%s\" is current directory.\r\n' % path).encode() )
        
        print("Successfully sent file listing \n")

    def list_files(self):
        '''
            1. Get list of files in directory
            2. Send over the number of files, so the client knows what to expect
            3. Send over the file names and sizes whilst totaling the directory size
        '''

        self.conn.send('150 Here comes the directory listing.\r\n'.encode())
        self.datasock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.datasock.connect(self.data_address)

        l = os.listdir('.')
        
        for t in l:
            k=self.to_list_item(t)
            self.datasock.send(k.encode())
            
        self.datasock.close()
        self.datasock = None
        self.conn.send('226 Directory send OK.\r\n'.encode())

    def to_list_item(self,fn):
        st=os.stat(fn)
        fullmode='rwxrwxrwx'
        mode=''
        for i in range(9):
            mode+=((st.st_mode>>(8-i))&1) and fullmode[i] or '-'
        d=(os.path.isdir(fn)) and 'd' or '-'
        ftime=time.strftime(' %b %d %H:%M ', time.gmtime(st.st_mtime))
        return d+mode+' 1 user group '+str(st.st_size)+ftime+os.path.basename(fn)+'\r\n'

    def port(self, data):
        
        cmd_addr = data.split(" ")
        cmd_ip_port = cmd_addr[1].split(",")

        ip = ".".join(str(x) for x in cmd_ip_port[0:4])
        port = cmd_ip_port[-2:]
        port =  int(port[0])*256 + int(port[1])
        
        server.data_address = (ip, port)

        send = '200  Port command successfull.\r\n'
        server.conn.send(send.encode())    

    def download(self,data):
        '''
            Send file in batches with the buffer size
        '''
        filename = data.split(" ")[1]
        
        print('Download file... ',filename)

        try:
            filesize = os.path.getsize(filename)
        except: 
            self.conn.send(("550 can't access file '{}'.\r\n").format(filename).encode())
            return

        progress = tqdm.tqdm(range(
            filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)

        self.conn.send('150 Opening data connection.\r\n'.encode())
        
        self.datasock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.datasock.connect(self.data_address)

        readmode = 'rb' if  self.mode == 'I' else 'r'

        # self.conn.send(struct.pack("i", filesize))
        try: 
            with open(filename, readmode) as f:

                for _ in progress:

                    bytes_read = f.read(self.__buffer)

                    if not bytes_read:
                        break
                    # self.conn.sendall(bytes_read)
                    self.datasock.send(bytes_read)
                    progress.update(len(bytes_read))

            self.conn.send('226 Transfer complete.\r\n'.encode())        
        except:
            self.conn.send("550 can't access file: Permission denied.\r\n".encode())
        
        self.datasock.close()
        

    def upload(self, data):
        '''
            Receive a file from client and save it in chunks
        '''

        # str_size = struct.unpack("i", self.conn.recv(4))[0]

        # filename = self.conn.recv(str_size)
        filename = data.split(" ")[1]
        
        print('Upload file... ',filename)

        self.conn.send('150 Opening data connection.\r\n'.encode())

        self.datasock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.datasock.connect(self.data_address)

        readmode = 'wb' if  self.mode == 'I' else 'w'

        try:
            with open(filename, readmode) as f:
                
                while True:
                    bytes_recieved = self.datasock.recv(self.__buffer)
                    
                    if not bytes_recieved: break

                    f.write(bytes_recieved)

            self.conn.send('226 Transfer complete.\r\n'.encode())        
        except:
            self.conn.send("550 can't access file .\r\n".encode())
        
        self.datasock.close()
    
        print('Upload Successful\n')

    def chdir(self, data):
        '''
            Change the current working directory .
        '''
        pathname = data.split(" ")[1]

        try: 
            os.chdir(pathname) 
            print("The current directory is", os.getcwd()) 
            self.conn.send(('250 \"%s\" is current directory.\r\n' % os.getcwd()).encode() )

        # Caching the exception     
        except: 
            print("Something wrong with specified directory. Exception- ", sys.exc_info())
            self.conn.send(('550 \"{}\" Requested action not taken. File unavailable.\r\n'.format(os.getcwd()+"/"+str(pathname))).encode() )

    def welcome_message(self):
        send = '220 connection started.\r\n'
        self.conn.send(send.encode())
    
    def _type(self,data):
        self.mode = data.split(" ")[1]
        send = '200 funcioned.\r\n'
        self.conn.send(send.encode())

    def pasv(self):
        send = '227 passive mode activated.\r\n'
        self.conn.send(send.encode())

    def abor(self):
        send = '225 abor command.\r\n'
        self.conn.send(send.encode())    
    
    def user(self, data):
        u = data.split(" ")[1]
        self.conn.send(('331 OK - {}.\r\n'.format(u)).encode())

    def _pass(self, data):
        # p = data.split(" ")[1] #password 
        self.conn.send('230 OK.\r\n'.encode())

    def quit(self):
        ''' Send quit confirmation and restart server.
        '''
        self.conn.send('221 Goodbye.\r\n'.encode())
        self.conn.close()
        self.socket.close()

        os.execl(sys.executable, sys.executable, *sys.argv)


if __name__ == "__main__":
    # FTP SERVER SETUP
    
    IP = '127.0.0.1'
    PORT = 2330

    server = ServerFTP(IP, PORT)
    
    print('FTP Server - {}:{} \n'.format( IP, PORT))
    print('This FTP server only works in passive mode\n')
    print('Binding... \n')
    
    server.bind()
   
    server.welcome_message()
        
    while True:
      
        
        print("Waiting instructions \n")

        data = server.receive()
        
        if not data: break

        data = data.decode()
       
        print("Received instruction: {0}\n".format(data))

        data_arr = data.split('\r\n')[:-1]

        for i in range(0,len(data_arr)):
            
            data = data_arr[i]

            if  data == "PWD" :
                server.pwd()
            elif data == "LIST" : 
                server.list_files()
            elif "PORT" in data:
                server.port(data)
            elif "CWD" in data:
                server.chdir(data) 
            elif "USER" in data:
                server.user(data)
            elif "PASS" in data:
                server._pass(data) 
            elif  "TYPE" in data:
                server._type(data)
            elif  "RETR" in data:
                server.download(data)
            elif "STOR" in data:  
                server.upload(data)
            elif  "ABOR" in data:
                server.abor()        
            elif data == 'PASV':
                server.pasv()
           

            elif data == "QUIT":

                server.quit()
                break
            else: 
                send = '220 starting connection funcioned tunino.\r\n'
                server.conn.send(send.encode())

            data = None
