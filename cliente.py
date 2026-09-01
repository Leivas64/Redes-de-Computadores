import socket
import threading

HOST = "127.0.0.1"
PORT = 5000

parar = threading.Event()   # usado para as duas threads combinarem o fim

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
            break

        if texto.lower() == ":quit":
            parar.set()
            break

    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    
def thread_2_recebe(sock):
    buffer = ""
    while not parar.is_set():
        try:
            dados = sock.recv(1024)
        except OSError:
            break
        if not dados:
            break

        buffer += dados.decode("utf-8", errors="ignore")
        while "\n" in buffer:
            linha, buffer = buffer.split("\n", 1)
            if linha.strip():
                print(linha)

    parar.set()
    print("\n[conexao encerrada - pressione Enter para sair]")

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    print(f"Conectado a {HOST}:{PORT}")
    print("Digite uma mensagem, ou :nome <NOME> / :quit\n")

    t1 = threading.Thread(target=thread_1_envia, args=(sock,))
    t2 = threading.Thread(target=thread_2_recebe, args=(sock,))
    t1.start()
    t2.start()

    t1.join()
    t2.join(timeout = 1)
    sock.close()


if __name__ == "__main__":
    main()
