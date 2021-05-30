from screen_sharing import ServerSharing

HOST = '127.0.0.1'
PORT = 9999

server = ServerSharing(HOST, PORT)
server.start()