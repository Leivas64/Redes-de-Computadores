import socket
import threading

def recebe(s):
    while True:
        try:
            dados = s.recv(1024)
            if not dados:
                print("\n[Servidor desconectado]")
                break
            print(dados.decode('utf-8'), end='')
        except Exception:
            print("\n[Conexão com o servidor perdida]")
            break

c = socket.socket()
c.connect(('127.0.0.1', 50000))

print(c.recv(1024).decode('utf-8'), end='')

threading.Thread(target=recebe, args=(c,), daemon=True).start()

while True:
    msg = input()
    c.sendall(msg.encode('utf-8'))
    if msg == ':quit': break

c.close()