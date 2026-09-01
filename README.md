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
   git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
   cd seu-repositorio
