import socket
import threading

# 服务器地址和端口
SERVER_ADDRESS = ('127.0.0.1', 8888)
# 用于控制服务器是否继续运行
server_running = True

def handle_client(client_socket):
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            message = data.decode('utf-8')
            # 处理其他消息
            client_socket.sendall("Message received".encode('utf-8'))
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()
        print("Client connection closed")

def start_server():
    global server_running
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(5)
    print(f"Server listening on {SERVER_ADDRESS}")

    try:
        while server_running:
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")
            client_handler = threading.Thread(target=handle_client, args=(client_socket,))
            client_handler.start()
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()
        print("Server closed")

if __name__ == "__main__":
    start_server()
