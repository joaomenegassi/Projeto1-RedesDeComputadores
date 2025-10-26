
import socket
import os
import threading
import math
from protocol import *
import time

HOST = '127.0.0.1'
PORT = 65432

def threaded_client_handler(main_sock, initial_data, client_address):
    thread_name = threading.current_thread().name
    print(f"[{thread_name}] Nova thread iniciada para o cliente {client_address}.")
    try:
        request_msg = initial_data.decode('utf-8')
        if not request_msg.startswith("GET /"):
            print(f"[{thread_name}] Requisição inválida de {client_address}.")
            send_error(main_sock, client_address, "Requisição inválida.")
            return

        filename = request_msg.replace("GET /", "")
        file_path = os.path.join('test_files', filename)

        if not os.path.exists(file_path):
            print(f"[{thread_name}] Arquivo '{filename}' não encontrado para {client_address}.")
            send_error(main_sock, client_address, "Arquivo não encontrado.")
            return

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as thread_socket:
            thread_socket.bind((HOST, 0))
            thread_port = thread_socket.getsockname()[1]
            print(f"[{thread_name}] Atendendo {client_address} na porta dedicada {thread_port} para o arquivo '{filename}'.")
            send_file(thread_socket, file_path, client_address)

    except Exception as e:
        print(f"[{thread_name}] Erro inesperado: {e}")
    print(f"[{thread_name}] Comunicação com {client_address} finalizada.")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as main_socket:
        main_socket.bind((HOST, PORT))
        print(f"[*] Servidor 'Recepcionista' escutando em {HOST}:{PORT}")
        while True:
            try:
                data, addr = main_socket.recvfrom(BUFFER_SIZE)
                print(f"[*] Nova requisição de {addr}. Delegando para uma nova thread.")
                client_thread = threading.Thread(target=threaded_client_handler, args=(main_socket, data, addr))
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                print(f"[!] Erro no servidor principal: {e}")

def send_file(sock, file_path, addr):
    thread_name = threading.current_thread().name
    
    with open(file_path, 'rb') as f:
        file_data = f.read()

    total_segments = math.ceil(len(file_data) / PAYLOAD_SIZE)
    print(f"[{thread_name}] Arquivo dividido em {total_segments} segmentos para {addr}.")
    
    segments = {}
    for i in range(total_segments):
        start = i * PAYLOAD_SIZE
        end = start + PAYLOAD_SIZE
        segment_data = file_data[start:end]
        checksum = calculate_checksum(segment_data)
        header = create_header(MSG_TYPE_DATA, i, checksum)
        segments[i] = header + segment_data

    segments_to_send = set(range(total_segments))
    
    for retry in range(10):
        if not segments_to_send:
            print(f"[{thread_name}] Todos os segmentos para {addr} foram confirmados.")
            break

        for seq_num in sorted(list(segments_to_send)):
            sock.sendto(segments[seq_num], addr)
            time.sleep(0.001)

        print(f"[{thread_name}] Aguardando ACKs/NAKs do cliente {addr}...")

        sock.settimeout(2.0)
        try:
            while True:
                ack_packet, sender_addr = sock.recvfrom(BUFFER_SIZE)
                if sender_addr != addr: continue

                msg_type, seq_num, ack_checksum = parse_header(ack_packet[:HEADER_SIZE])
                
                if msg_type == MSG_TYPE_ACK and seq_num in segments_to_send:
                    print(f"  [{thread_name}] <- ACK recebido para o segmento {seq_num}. {len(segments_to_send)-1} restantes.")
                    segments_to_send.remove(seq_num)
                elif msg_type == MSG_TYPE_NAK:
                    missing = parse_nak_packet(ack_packet[HEADER_SIZE:])
                    segments_to_send.update(missing)
                    break
                
                if not segments_to_send: break
        except socket.timeout:
            print(f"[{thread_name}] Timeout esperando ACKs/NAKs de {addr}. Tentativa {retry + 1}.")
    
    sock.sendto(create_header(MSG_TYPE_FINISH, total_segments), addr)
    print(f"[{thread_name}] Mensagem de finalização enviada para {addr}.")

def send_error(sock, addr, error_msg):
    message = create_header(MSG_TYPE_ERROR, 0) + error_msg.encode('utf-8')
    sock.sendto(message, addr)

if __name__ == '__main__':
    if not os.path.exists('test_files'):
        os.makedirs('test_files')
    start_server()