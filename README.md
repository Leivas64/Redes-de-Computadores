# Chat Multiusuário (Modelo Client/Server)

Uma aplicação de bate-papo em tempo real desenvolvida como projeto prático para a disciplina de Redes de Computadores. O objetivo principal do projeto é aplicar conceitos fundamentais de comunicação em rede, sockets TCP/IP e programação concorrente utilizando Threads.

## Sobre o Projeto

Este projeto implementa uma sala de bate-papo interativa no modelo Cliente/Servidor. A aplicação permite a troca de mensagens em tempo real entre clientes conectados a um servidor central, combinando envio de texto, suporte a comandos personalizados e notificações automáticas de sistema.

A arquitetura foi desenhada para demonstrar a manipulação de conexões persistentes, sincronização de tarefas através de memória compartilhada e separação clara de responsabilidades entre Threads de leitura, envio e processamento.

## Principais Funcionalidades

- Conexão TCP Confiável: Estabelecimento de canal de comunicação bidirecional e estável.
- Mensagem de Boas-Vindas: Envio imediato da confirmação de conexão com carimbo de data/hora assim que o cliente se conecta.
- Identificação Flexível: Atribuição automática de nome padrão (IP:Porta) com suporte a alteração de apelido em tempo de execução via comandos.
- Comunicação Concorrente: Uso de Threads dedicadas no cliente e no servidor para permitir envio e recepção simultâneos sem travamento da interface.
- Relógio Periódico do Servidor: Notificação automática com o horário do sistema enviada a todos os clientes a cada minuto.
- Eco de Confirmação: Confirmação visual para o próprio usuário das mensagens enviadas ao canal.

-----------------------------

## Tecnologias Utilizadas

- Linguagem: Python 3
- Módulos Nativos:
  - socket — Comunicação de rede em baixo nível via TCP/IP
  - threading — Programação concorrente e controle de tarefas em segundo plano
  - datetime / time — Manipulação e controle de carimbos de data/hora
  - entre outros...

## Como Executar o Projeto

Como o projeto utiliza apenas bibliotecas padrão do Python, não é necessária a instalação de dependências externas.

### Pré-requisitos
- Python 3.8 ou superior instalado no sistema.

### Passo a Passo

1. Clonar o Repositório:
   ```bash
   git clone https://github.com/Leivas64/Redes-de-Computadores.git
   cd Redes-de-Computadores
   ```

2. Iniciar o servidor (argumento opcional: número máximo de clientes, padrão 5):
   ```bash
   python servidor.py 3 -p 5000
   ```

3. Iniciar um ou mais clientes, cada um em um terminal:
   ```bash
   python cliente.py -s 127.0.0.1 -p 5000
   ```

### Comandos do cliente
- Texto sem `:` no início: mensagem pública para todos os usuários.
- `:nome <NOME>`: altera o nome do usuário.
- `:quem`: lista os usuários na sala.
- `:quit`: desconecta e encerra o cliente.

## Chat com Um Usuário (Fase 1)

- Cliente: recebe `<HORARIO>: CONECTADO!!` ao conectar; a thread 1 lê o teclado e envia ao servidor (`:nome <NOME>`, `:quit` ou mensagem) e a thread 2 imprime tudo que chega do servidor.
- Servidor: a thread 1 lê o socket e guarda os comandos em memória compartilhada; a thread 2 varre essa memória e executa a ação (definir nome, enviar a mensagem a todos ou desconectar); nome padrão `IP:porta`; eco `Voce digitou: MENSAGEM` para quem enviou e `NOME (horario): MENSAGEM` para os demais; data e hora enviadas a cada minuto.

## Multi-Cliente (Fase 2)

- Cliente: comando `:quit` solicita a desconexão e encerra a execução.
- Servidor: uma thread de trabalho por conexão, com a thread principal voltando ao `accept()`; clientes independentes, com dados em memória compartilhada protegida por lock; limite de clientes por linha de comando (`python servidor.py 3`); com o servidor lotado o cliente recebe `SERVIDOR LOTADO!` no lugar de `CONECTADO!!` e a conexão é fechada; no `:quit` a conexão TCP é fechada, os dados do cliente são removidos e a vaga é liberada.

## Tratamento de Exceções (Fase 3)

- Cliente: timeout na conexão, mensagem clara quando o servidor está fora do ar, detecção de queda do servidor durante a sessão e encerramento limpo, sem traceback.
- Servidor: queda abrupta de cliente libera a vaga e avisa os demais; linhas gigantes sem quebra desconectam apenas quem as enviou; falha ao abrir a porta gera mensagem em vez de erro; Ctrl+C encerra avisando os clientes.
