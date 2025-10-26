import socket
import sys
import os
import struct
import zlib
import time
from protocol import *

MAX_RETRIES = 5
TIMEOUT = 5

def start_client(server_ip, server_port, filename, segments_to_drop=set()):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(TIMEOUT)
        
        server_address = (server_ip, server_port)
        
        request_msg = f"GET /{filename}".encode('utf-8')
        print(f"[*] Solicitando o arquivo '{filename}' do servidor principal em {server_address}")
        
        try:
            s.sendto(request_msg, server_address)
            receive_file(s, filename, server_address, segments_to_drop)
        except socket.timeout:
            print("[!] Tempo de espera esgotado na requisição inicial. Verifique se o servidor está online.")
        except Exception as e:
            print(f"[!] Erro ao enviar requisição: {e}")

def receive_file(sock, filename, initial_server_address, segments_to_drop):
    received_segments = {}
    expected_segments = -1
    
    worker_server_address = None

    for retry in range(MAX_RETRIES):
        if expected_segments != -1 and len(received_segments) == expected_segments:
            print("[*] Todos os segmentos foram recebidos com sucesso.")
            break

        if retry > 0 and expected_segments != -1 and worker_server_address:
            missing = [i for i in range(expected_segments) if i not in received_segments]
            if missing:
                print(f"[!] Solicitando retransmissão de {len(missing)} segmentos: {missing}")
                nak_packet = create_nak_packet(missing)
                sock.sendto(nak_packet, worker_server_address)

        try:
            while True:
                packet, addr = sock.recvfrom(BUFFER_SIZE)
                
                if worker_server_address is None:
                    worker_server_address = addr
                    print(f"[*] Comunicação estabelecida com o atendente do servidor em {worker_server_address}")
                elif addr != worker_server_address:
                    print(f"[!] Pacote ignorado de fonte inesperada {addr}.")
                    continue

                msg_type, seq_num, checksum_recv = parse_header(packet[:HEADER_SIZE])
                payload = packet[HEADER_SIZE:]

                if msg_type == MSG_TYPE_DATA:
                    if seq_num in segments_to_drop:
                        print(f"[!] SIMULANDO PERDA: Pacote {seq_num} descartado.")
                        segments_to_drop.remove(seq_num)
                        continue

                    if calculate_checksum(payload) != checksum_recv:
                        print(f"[!] Checksum incorreto no pacote {seq_num}. Descartando.")
                        continue

                    if seq_num not in received_segments:
                        received_segments[seq_num] = payload
                    
                    ack_packet = create_ack_packet(seq_num)
                    
                    print(f" Enviando ACK {seq_num}")

                    sock.sendto(ack_packet, worker_server_address)

                elif msg_type == MSG_TYPE_FINISH:
                    expected_segments = seq_num
                    print(f"[*] Pacote de finalização recebido. Total de segmentos esperado: {expected_segments}")
                    sock.sendto(create_ack_packet(seq_num), worker_server_address)

                elif msg_type == MSG_TYPE_ERROR:
                    print(f"[!] Erro do servidor: {payload.decode('utf-8')}")
                    return

                if expected_segments != -1 and len(received_segments) == expected_segments:
                    break
        
        except socket.timeout:
            print(f"[*] Timeout. Tentativa {retry + 1}/{MAX_RETRIES}.")
            if worker_server_address is None:
                print("[!] O servidor principal não respondeu.")
                sock.sendto(f"GET /{filename}".encode('utf-8'), initial_server_address)
            continue
    
    if expected_segments != -1 and len(received_segments) == expected_segments:
        print("[*] Remontando o arquivo...")
        sorted_data = b''.join([received_segments[i] for i in sorted(received_segments.keys())])
        output_filename = "received_" + filename
        with open(output_filename, 'wb') as f:
            f.write(sorted_data)
        print(f"[+] Arquivo '{output_filename}' salvo com sucesso.")
    else:
        print("[!] Falha na transferência do arquivo após múltiplas tentativas.")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Uso: python client.py <IP_servidor> <porta> <nome_do_arquivo> [segmentos_a_descartar]")
        print("Exemplo: python client.py 127.0.0.1 65432 grande.txt 5,10,15")
    else:
        server_ip = sys.argv[1]
        server_port = int(sys.argv[2])
        filename = sys.argv[3]
        segments_to_drop = set()
        if len(sys.argv) > 4:
            segments_to_drop = set(map(int, sys.argv[4].split(',')))
        start_client(server_ip, server_port, filename, segments_to_drop)