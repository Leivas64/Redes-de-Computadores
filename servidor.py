import argparse
import socket
import sys
import threading
import time
from datetime import datetime

HOST = "0.0.0.0"
PORT = 5000
DEFAULT_C = 5
INTERVALO_RELOGIO = 60
INTERVALO_VARREDURA = 0.2
TAMANHO_MAX_LINHA = 4096
TIMEOUT_ACCEPT = 1

lock = threading.Lock()
encerrando = threading.Event()
comandos = []  
clientes = {}
trabalhadores = []
MAX_CLIENTES = DEFAULT_C


def hora():
    return datetime.now().strftime("%H:%M:%S")


def data_hora():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def nome_de(conn, padrao="?"):
    """Devolve o nome atual do cliente, lendo a memoria compartilhada."""
    with lock:
        info = clientes.get(conn)
    return info["nome"] if info else padrao

def ocupacao():
    with lock:
        return len(clientes)

def enviar(conn, texto):
    """Envia uma linha de texto para um cliente."""
    with lock:
        info = clientes.get(conn)
    trava = info["envio"] if info else None
    try:
        if trava:
            with trava:
                conn.sendall((texto + "\n").encode("utf-8"))
        else:
            conn.sendall((texto + "\n").encode("utf-8"))
    except OSError:
        pass


def broadcast(texto, exceto=None):
    """Envia uma linha para todos os clientes conectados."""
    with lock:
        destinos = [c for c, i in clientes.items() if c is not exceto and i["pronto"]]
    for c in destinos:
        enviar(c, texto)

# Working Thread: 

def thread_trabalho(conn, addr):
    nome_padrao = f"{addr[0]}:{addr[1]}"
    try:
        conn.settimeout(None)
        conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    except OSError:
        pass

    with lock:
        lotado = len(clientes) >= MAX_CLIENTES
        if not lotado:
            clientes[conn] = {"nome": nome_padrao, "addr": addr,
                              "envio": threading.Lock(), "pronto": False}
        usadas = len(clientes)

    if lotado:
        print(f"[x] conexao de {nome_padrao} RECUSADA "
              f"(limite de {MAX_CLIENTES} atingido)")
        enviar(conn, f"{hora()}: SERVIDOR LOTADO! "
               f"Tente novamente mais tarde")
        time.sleep(0.5)
        try:
            conn.close()
        except OSError:
            pass
        return

    print(f"[+] {nome_padrao} conectado ({usadas}/{MAX_CLIENTES})")
    enviar(conn, f"{hora()}: CONECTADO!!")
    with lock:
        clientes[conn]["pronto"] = True
    broadcast(f"{hora()}: {nome_padrao} entrou na sala.", exceto=conn)

    t1 = threading.Thread(target=thread_1_recebe, args=(conn, addr), daemon=True)
    t2 = threading.Thread(target=thread_2_processa, args=(conn, addr), daemon=True)
    t1.start()
    t2.start()

    t2.join()
    t1.join(timeout=1)
    print(f"[i] vaga liberada({ocupacao()}/{MAX_CLIENTES})")

def thread_1_recebe(conn, addr):
    buffer = ""
    try:
        while True:
            dados = conn.recv(1024)
            if not dados:                      # cliente fechou a conexao
                break
            buffer += dados.decode("utf-8", errors="ignore")
            if len(buffer) > TAMANHO_MAX_LINHA and "\n" not in buffer:
                print(f"[!] {nome_de(conn, f'{addr[0]}:{addr[1]}')} enviou linha muito longa")
                enviar(conn, f"{hora()}: linha muito longa, desconectando")
                break
            while "\n" in buffer:              # separa mensagem por mensagem
                linha, buffer = buffer.split("\n", 1)
                linha = linha.strip()
                if not linha:
                    continue
                print(f"[T1] {nome_de(conn, f'{addr[0]}:{addr[1]}')} -> {linha}")
                with lock:
                    comandos.append((conn, linha))
    except OSError as erro:
        if not encerrando.is_set():
            print(f"[!] conexao com {nome_de(conn, f'{addr[0]}:{addr[1]}')} perdida ({erro.__class__.__name__})")
    finally:
        # sinaliza para a thread 2 que este cliente saiu
        with lock:
            if conn in clientes:
                comandos.append((conn, ":quit"))


def thread_2_processa(conn, addr):
    ultimo_relogio = time.time()
    ativo = True

    try:
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
    finally:
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

        elif cmd in ("quit", "sair"):
            enviar(conn, f"{hora()}: DESCONECTADO!!")
            return False

        elif cmd == "quem":
            with lock:
                nomes = [info["nome"] for info in clientes.values()]
            enviar(conn, f"{hora()}: na sala ({len(nomes)}/{MAX_CLIENTES}): " + ", ".join(nomes))

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
        pendentes = [item for item in comandos if item[0] is conn]
        for item in pendentes:
            comandos.remove(item)
    try:
        conn.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        conn.close()
    except OSError:
        pass

    if encerrando.is_set():
        return

    nome = info["nome"] if info else f"{addr[0]}:{addr[1]}"
    print(f"[-] {nome} desconectou")
    broadcast(f"{hora()}: {nome} saiu da sala")


def main(): 
    global MAX_CLIENTES

    parser = argparse.ArgumentParser(
        description="Servidor do chat multiusuário")
    parser.add_argument("max_clientes", nargs="?", type=int, default=DEFAULT_C,
                         help="numero maximo de clientes simultaneos " f"(padrao: {DEFAULT_C})")
    parser.add_argument("-p", "--porta", type=int, default=PORT, help=f"porta de escuta (padrao: {PORT})")
    args = parser.parse_args()

    if args.max_clientes < 1:
        parser.error("max_clientes deve ser no minimo 1")
    MAX_CLIENTES = args.max_clientes

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    else:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        servidor.bind((HOST, args.porta))
        servidor.listen(5)
    except OSError as erro:
        print(f"Nao foi possivel abrir a porta {args.porta} -> {erro}")
        servidor.close()
        return 1

    servidor.settimeout(TIMEOUT_ACCEPT)
    print(f"Servidor ouvindo em {HOST}:{args.porta} | limite: {MAX_CLIENTES} clientes simultaneos")

    try:
        while True:
            try:
                conn, addr = servidor.accept()
            except socket.timeout:
                continue
            except OSError as erro:
                print(f"[!] falha ao aceitar conexao ({erro.__class__.__name__})")
                continue

            t = threading.Thread(target=thread_trabalho, args=(conn, addr), daemon=True)

            t.start()
            with lock:
                trabalhadores.append(t)
                trabalhadores[:] = [x for x in trabalhadores if x.is_alive()]
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
    finally:
        encerrando.set()
        servidor.close()
        with lock:
            abertas = list(clientes.keys())
        for c in abertas:
            enviar(c, f"{hora()}: SERVIDOR ENCERRADO")
            try:
                c.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                c.close()
            except OSError:
                pass
        with lock:
            pendentes = list(trabalhadores)
        for t in pendentes:
            t.join(timeout=1)
    return 0

if __name__ == "__main__":
    sys.exit(main())