import socket
import time
import threading
from datetime import datetime

#Variáveis Globais
HOST = "0.0.0.0"
PORT = 5000
INT_RELOG = 60
DELAY = 0.2

lock = threading.Lock()
comandos = []
clientes = {}

def hora():
    """Retorna a hora atual formatada como string."""
    return datetime.now().strftime("%H:%M:%S")

def data_hora():
    """Retorna a data e hora atual formatada como string."""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")
def nome_de(conn, padrao="?"):
    """Retorna o nome do cliente associado à conexão."""
    with lock:
        info = clientes.get(conn)
    return info["nome"] if info else padrao
def enviar(conn, texto):
    """Envia uma mensagem para o cliente."""
    try:
        conn.sendall((texto+ "\n").encode("utf-8"))
    except OSError:
        pass

def broadcast(texto, exceto=None):
    """Envia uma mensagem para todos os clientes conectados, exceto o especificado."""
    with lock:
        destinos = [c for c in clientes if c is not exceto]
    for c in destinos:
        enviar(c, texto)

#Thread 1 (Le socket e salva na memória)

def thread_1_recebe(conn,addr):
    buffer = ""
    try:
        while True:
            dados = conn.recv(1024)
            if not dados:
                break
            buffer += dados.decode("utf-8", errors="ignore")
            while "\n" in buffer:
                linha, buffer = buffer.split("\n", 1)
                linha = linha.strip()
                if not linha:
                    continue
                print(f"[T1]{nome_de(conn, f'{addr[0]}:{addr[1]}')}->{linha}")
                with lock:
                    comandos.append((conn, linha))
    except OSError:
        pass
    finally:
        with lock:
            comandos.append((conn, ":quit"))

#Thread 2 (varredura de mamória e relogio)

def thread_2_proccess(conn, addr):
    ultimo_relogio = time.time()
    ativo = True

    while ativo:
        with lock:
            meus = [item for item in comandos if item[0] is conn]
            for item in meus:
                comandos.remove(item)

            for _, texto in meus:
                ativo = executa(conn, texto)
                if not ativo:
                    break

            if ativo and time.time() - ultimo_relogio >= INT_RELOG:
                enviar(conn, f"[SERVIDOR] {data_hora()}")
                ultimo_relogio = time.time()

            time.sleep(DELAY)

        desconecta(conn, addr)

def exectuta(conn, texto):
    with lock:
        info = clientes.get(conn)
    if info is None:
        return False

    if texto.startswith(":"):
        partes = texto[1:].split(" ", 1)
        cmd = partes[0].lower()
        arg = partes[1].strip() if len(partes) > 1 else ""

    if cmd == "nome":
        if arg:
            with lock:
                antigo = clientes[conn]["nome"]
                clientes[conn]["nome"] = arg
            print(f"[T2] {antigo} agora se chama {arg}")
            enviar(conn,f"{hora()}:seu nome agora eh {arg}")
            broadcast(f"{hora()}:{antigo} agora se chama {arg}", exceto=conn)
        else:
            enviar(conn, f"{hora()}:Uso correto -> :nome <NOME>")

    elif cmd == "quit":
        enviar(conn, f"{hora()}:DESCONECTADO!!")
        return False

    else:
        enviar(conn, f"{hora()}:Comando desconhecido -> "{cmd}""")

   else:
    enviar(conn, f"Voce digitou: {texto}")
    broadcast(f'{info["nome"]}({hora()}): {texto}', exceto=conn)

return True

def desconecta(conn, addr):
 #terminar...

def main():
#terminar...