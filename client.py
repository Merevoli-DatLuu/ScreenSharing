from screen_sharing import ClientSharing

HOST = '127.0.0.1'
PORT = 9999

host = input("Server's host: ")
port = input("Server's port: ")

if host == "":
    host = HOST
if port == "":
    port = PORT
else:
    port = int(port)

client = ClientSharing(host, port)
client.start()

