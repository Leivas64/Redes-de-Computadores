import socket
import threading
import time
from datetime import datetime

HOST = "0.0.0.0"
PORT = 5000
INTERVALO_RELOGIO = 60
INTERVALO_VARREDURA = 0.2  
lock = threading.Lock()
comandos = []  
clientes = {}


def hora():
    return datetime.now().strftime("%H:%M:%S")


def data_hora():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def nome_de(conn, padrao="?"):
    """Devolve o nome atual do cliente, lendo a memoria compartilhada."""
    with lock:
        info = clientes.get(conn)
    return info["nome"] if info else padrao


def enviar(conn, texto):
    """Envia uma linha de texto para um cliente."""
    try:
        conn.sendall((texto + "\n").encode("utf-8"))
    except OSError:
        pass


def broadcast(texto, exceto=None):
    """Envia uma linha para todos os clientes conectados."""
    with lock:
        destinos = [c for c in clientes if c is not exceto]
    for c in destinos:
        enviar(c, texto)


def thread_1_recebe(conn, addr):
    buffer = ""
    try:
        while True:
            dados = conn.recv(1024)
            if not dados:                      # cliente fechou a conexao
                break
            buffer += dados.decode("utf-8", errors="ignore")
            while "\n" in buffer:              # separa mensagem por mensagem
                linha, buffer = buffer.split("\n", 1)
                linha = linha.strip()
                if not linha:
                    continue
                print(f"[T1] {nome_de(conn, f'{addr[0]}:{addr[1]}')} -> {linha}")
                with lock:
                    comandos.append((conn, linha))
    except OSError:
        pass
    finally:
        # sinaliza para a thread 2 que este cliente saiu
        with lock:
            comandos.append((conn, ":quit"))


def thread_2_processa(conn, addr):
    ultimo_relogio = time.time()
    ativo = True

    while ativo:
        # 1) retira da memoria compartilhada os comandos deste cliente
        with lock:
            meus = [item for item in comandos if item[0] is conn]
            for item in meus:
                comandos.remove(item)

        # 2) executa as acoes solicitadas
        for _, texto in meus:
            ativo = executa(conn, texto)
            if not ativo:
                break

        # 3) envia data/hora periodicamente
        if ativo and time.time() - ultimo_relogio >= INTERVALO_RELOGIO:
            enviar(conn, f"[SERVIDOR] {data_hora()}")
            ultimo_relogio = time.time()

        time.sleep(INTERVALO_VARREDURA)

    desconecta(conn, addr)


def executa(conn, texto):
    """Executa um comando/mensagem. Retorna False quando o cliente deve sair."""
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
                enviar(conn, f"{hora()}: seu nome agora e {arg}")
                broadcast(f"{hora()}: {antigo} agora se chama {arg}", exceto=conn)
            else:
                enviar(conn, f"{hora()}: uso correto -> :nome <NOME>")

        elif cmd == "quit":
            enviar(conn, f"{hora()}: DESCONECTADO!!")
            return False

        else:
            enviar(conn, f'{hora()}: comando desconhecido "{cmd}"')
    else:
        # mensagem publica: eco para quem enviou, formatada para os demais
        enviar(conn, f"Voce digitou: {texto}")
        broadcast(f'{info["nome"]} ({hora()}): {texto}', exceto=conn)

    return True


def desconecta(conn, addr):
    with lock:
        info = clientes.pop(conn, None)
    try:
        conn.close()
    except OSError:
        pass
    nome = info["nome"] if info else str(addr)
    print(f"[-] {nome} desconectou")
    broadcast(f"{hora()}: {nome} saiu da sala")


def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen(5)
    print(f"Servidor ouvindo em {HOST}:{PORT}")

    try:
        while True:
            conn, addr = servidor.accept()
            nome_padrao = f"{addr[0]}:{addr[1]}"   # nome default = IP:porta
            with lock:
                clientes[conn] = {"nome": nome_padrao, "addr": addr}
            print(f"[+] conexao de {nome_padrao}")

            enviar(conn, f"{hora()}: CONECTADO!!")   # MSG1

            threading.Thread(target=thread_1_recebe,
                             args=(conn, addr), daemon=True).start()
            threading.Thread(target=thread_2_processa,
                             args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
    finally:
        servidor.close()


if __name__ == "__main__":
    main()