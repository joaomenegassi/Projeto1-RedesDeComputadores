# Transferência de Arquivos Confiável sobre UDP

Implementação de um protocolo de transferência de arquivos cliente-servidor sobre UDP, focado em adicionar mecanismos de confiabilidade como detecção de erros e retransmissão de pacotes.

## Funcionalidades Principais

* **Servidor Multithreaded:** Usa um modelo de "recepcionista" que delega cada cliente a uma thread dedicada.
* **Detecção de Erros:** Garante a integridade dos dados com um checksum CRC32 em cada pacote.
* **Controle de Perda:** Implementa retransmissão seletiva usando um mecanismo de **ACK** (confirmação por pacote) e **NAK** (solicitação de pacotes perdidos).
* **Simulação de Perda:** O cliente pode ser instruído a descartar pacotes intencionalmente para testes.

## Como Executar

Requisitos
-----------
- Python 3.x


## 1. Preparação do Ambiente

Todos os arquivos que você deseja transferir devem estar localizados dentro de um diretório chamado "test_files".


## 2. Execução do Servidor e Cliente

Você precisará de dois terminais abertos simultaneamente: um para o servidor e outro para o cliente.

Passo 1: Iniciar o Servidor

Abra um terminal e execute o seguinte comando. O servidor ficará aguardando por conexões.

    python server.py

A saída esperada é: [*] Servidor 'Recepcionista' escutando em 127.0.0.1:65432

Passo 2: Executar o Cliente

Abra um novo terminal (mantenha o terminal do servidor em execução) e utilize um dos formatos abaixo. 

Para solicitar um arquivo que está na pasta "test_files" do servidor.

Formato:

    python client.py <IP_servidor> <porta> <nome_do_arquivo>

Exemplo:

    python client.py 127.0.0.1 65432 arquivo.txt


Testando com Simulação de Perda de Pacotes

Formato:

    python client.py <IP_servidor> <porta> <nome_do_arquivo> <pacotes_a_descartar>

Exemplo (descartando os pacotes 10, 25 e 50):

    python client.py 127.0.0.1 65432 arquivo_grande.txt 10,25,50


## 3. Verificação

Após a transferência ser concluída com sucesso, um novo arquivo chamado "received_[nome_do_arquivo_original]" será criado no diretório principal do projeto.

