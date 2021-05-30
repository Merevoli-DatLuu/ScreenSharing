import socket
import cv2
import threading
import pickle
import struct
import pyautogui
import numpy as np

class ServerSharing:
    """ 
    This is class for server side.

    Author
    ------
    Lưu Thành Đạt
        https://github.com/Merevoli-DatLuu/SGUInfo

    Methods
    -------
    __init__(): None
        
    start(): None
        starts the server (streaming)
    listen_client(): None
        listens the new connections
    get_frame(): None
        get screentshot frame
    handle_client(): None
        handle a client connection
    """

    def __init__(self, host, port, screen_size = (1000, 600)):
        """
        Create a new instance

        :param: host -> str
            host address of server
        :paramm: port -> int
            port of server
        :param: screen_size -> tuple
            size of sharing screen
        :return: None
        """
        self.host = host
        self.port = port
        self.used_slot = 0
        self.is_running = False
        self.conf = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        self.lock = threading.Lock()
        self.screen_size = screen_size
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.server_socket.bind((self.host, self.port))

    def start(self):
        """
        starts the server (streaming)

        :return: None
        """
        if self.is_running:
            print("Server is running")
        else:
            print("Staring...")
            print("Server's info")
            print(f"==> Host: {self.host}")
            print(f"==> Port: {self.port}")

            self.is_running = True
            client_thread = threading.Thread(target = self.listen_client)
            client_thread.start()

    def listen_client(self):
        """
        listens the new connections

        :return: None
        """
        self.server_socket.listen()
        while self.is_running:
            self.lock.acquire()
            conn, addr = self.server_socket.accept()
            print(f'({addr}) is connecting')
            self.used_slot += 1
            self.lock.release()

            thread = threading.Thread(target = self.handle_client, args = (conn, addr))
            thread.start()

    def get_frame(self):
        """
        get screentshot frame

        :return: None
        """
        screen = pyautogui.screenshot()
        frame = np.array(screen)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, self.screen_size, interpolation = cv2.INTER_AREA)
        return frame

    def handle_client(self, conn, addr):
        """
        handle a client connection

        :param: conn -> socket
            connection of client
        :param: addr -> tuple
            client's address
        :return: None
        """
        self.lock.acquire()

        client_running = True

        while client_running:
            frame = self.get_frame()
            _, frame = cv2.imencode('.jpg', frame, self.conf)
            data = pickle.dumps(frame, 0)
            size = len(data)

            try:
                conn.sendall(struct.pack('>L', size) + data)
            except ConnectionAbortedError:
                client_running = False
            except ConnectionRefusedError:
                client_running = False
            except ConnectionResetError:
                client_running = False
            except BrokenPipeError:
                client_running = False

        cv2.destroyAllWindows()
        conn.close()
        print(f'({addr}) is disconnected')
        self.used_slot -= 1
        self.lock.release()

class ClientSharing:
    """ 
    This is class for client side.

    Author
    ------
    Lưu Thành Đạt
        https://github.com/Merevoli-DatLuu/SGUInfo

    Methods
    -------
    __init__(): None
        
    start(): None
        starts the client (show streaming)
    show_streaming(): None
        render the frame that sent from server
    """


    def __init__(self, host, port):
        """
        Create a new instance

        :param: host -> str
            host address of server
        :paramm: port -> int
            port of server
        :return: None
        """
        self.host = host
        self.port = port
        self.is_running = False
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        """
        starts the client (show streaming)

        :return: None
        """
        if self.is_running:
            print("Client is running")
        else:
            print("Starting...")
            self.is_running = True
            client_thread = threading.Thread(target = self.show_streaming)
            client_thread.start()

    def show_streaming(self):
        """
        render the frame that sent from server

        :return: None
        """
        self.client_socket.connect((self.host, self.port))

        payload_size = struct.calcsize('>L')
        data = b''
        while self.is_running:

            while len(data) < payload_size:
                data_recv = self.client_socket.recv(4096)
                data += data_recv

            packed_data_size = data[:payload_size]
            data = data[payload_size:]

            data_size = struct.unpack(">L", packed_data_size)[0]

            while len(data) < data_size:
                data += self.client_socket.recv(4096)

            frame_data = data[:data_size]
            data = data[data_size:]

            frame = pickle.loads(frame_data, fix_imports=True, encoding='bytes')
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            cv2.imshow(str(self.host) + ":" + str(self.port), frame)

            if cv2.waitKey(1) == ord('q'):
                self.is_running = False

            if not self.is_running:
                break