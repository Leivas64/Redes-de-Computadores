import socket
import threading
import time

from datetime import datetime
from queue import Queue

fila = Queue()
nome = ""

def thread_recebe(conexao):
    
    while True:
        try:
            dados = conexao.recv(1024)
            if not dados: 
                break
            msg = dados.decode('utf-8').strip()
            if msg:
                fila.put(msg)
        except:
            break

def thread_processa(conexao):
    
    global nome
    t_relogio = time.time

    while True:
        if time.time() - t_relogio >=60:
            conexao.sendall(f"[HORA]: {datetime.now().strftime('%H:%M:%S')}\n".encode('utf-8'))
            t_relogio = time.time()

            if not fila.empty():
                msg = fila.get()
                if msg.startswith(':nome '):
                    nome = msg.split(' ',1)[1]
                elif msg == ':quit':
                    break
                else:
                    hora = datetime.now().strftime('%H:%M:%S')
                    conexao.sendall(f"Voce digitou: {msg}\n{nome} ({hora}): {msg}\n".encode('utf-8'))
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 50000))
s.listen()

conn, addr = s.accept()
nome = (f"{addr[0]}:{addr[1]}")
conn.sendall(f"<{datetime.now().strftime('%H:%M:%S')}>: CONECTADO!\n".encode('utf-8'))

threading.Thread(target=thread_recebe, args=(conn,),daemon=True).start()
threading.Thread(target=thread_processa, args=(conn,)).start()