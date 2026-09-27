import argparse
import os
import socket
import sys
import threading

HOST_PADRAO = "127.0.0.1"
PORTA_PADRAO = 5000
TIMEOUT_QUIT = 3
TIMEOUT_CONEXAO = 5

parar = threading.Event()
saindo = threading.Event()

def thread_1_envia(sock):
    while not parar.is_set():
        try:
            texto = input()
        except (EOFError, KeyboardInterrupt):
            texto = ":quit"

        if parar.is_set():
            break

        texto = texto.strip()
        if not texto:
            continue

        try:
            sock.sendall((texto + "\n").encode("utf-8"))
        except OSError:
            # FALTA IMPLEMENTAR (Maria 1): avisar o usuario que a conexao com o servidor foi perdida
            parar.set()
            break

        if texto.lower() in (":quit", ":sair"):
            saindo.set()
            print("Solicitando desconexao ao servidor...")
            if not parar.wait(TIMEOUT_QUIT):
                print("Servidor nao respondeu a tempo; encerrando assim mesmo.")
                parar.set()
            break

def thread_2_recebe(sock):
    buffer = ""
    while not parar.is_set():
        try:
            dados = sock.recv(1024)
        except OSError:
            # FALTA IMPLEMENTAR (Maria 2): avisar o usuario quando a conexao cair durante o recebimento
            break
        if not dados:                   
            break

        buffer += dados.decode("utf-8", errors="ignore")
        while "\n" in buffer:
            linha, buffer = buffer.split("\n", 1)
            if linha.strip():
                print(linha)

    if not parar.is_set() and not saindo.is_set():
        print("[conexao encerrada pelo servidor]")
    parar.set()


def main():
    parser = argparse.ArgumentParser(description="Cliente do chat multiusuario")
    parser.add_argument("-s", "--servidor", default=HOST_PADRAO,
                        help=f"IP do servidor (padrao: {HOST_PADRAO})")
    parser.add_argument("-p", "--porta", type=int, default=PORTA_PADRAO,
                        help=f"porta do servidor (padrao: {PORTA_PADRAO})")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # FALTA IMPLEMENTAR (Maria 3): timeout na conexao e keepalive no socket
    try:
        sock.connect((args.servidor, args.porta))
    except OSError as erro:
        print(f"Nao foi possivel conectar em {args.servidor}:{args.porta} -> {erro}")
        return 1

    print(f"Conectado a {args.servidor}:{args.porta}")
    print("Digite uma mensagem, ou :nome <NOME> / :quem / :quit\n")

    threading.Thread(target=thread_1_envia, args=(sock,), daemon=True).start()
    threading.Thread(target=thread_2_recebe, args=(sock,), daemon=True).start()

    # FALTA IMPLEMENTAR (Maria 4): fazer o Ctrl+C funcionar durante a espera
    try:
        parar.wait()
    except KeyboardInterrupt:
        parar.set()

    try:
        sock.close()
    except OSError:
        pass

    print("Aplicacao encerrada.")
    return 0


if __name__ == "__main__":
    codigo = main()
    sys.stdout.flush()
    os._exit(codigo)