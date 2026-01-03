import socket
import threading
import struct
from net import recv_exact
import uuid

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind(('10.0.0.97', 8080))

players = {

}

message_data = []

lock1 = threading.Lock()
msg_lock = threading.Lock()

def handle_player(client: socket.socket, addr):
    global players

    username = None

    try:

        len_bytes = recv_exact(client, 4)


        username_len, = struct.unpack("!I", len_bytes)
 

        username = recv_exact(client, username_len).decode()



        print(f'{username} joined from address {addr}')

        with lock1:
            
            players[username] = (0, 0)

    
        while True:
            player_pos_bytes = recv_exact(client, 8)

            player_pos_x, player_pos_y = struct.unpack('!ii', player_pos_bytes)
            
            



            with lock1:
                
                players[username] = (player_pos_x, player_pos_y)

            with lock1:
                players_copy = dict(players)

            positions_expected = len(players_copy)-1

            client.sendall(struct.pack('!I', positions_expected))

            for name, pos in players_copy.items():

                if name != username:

                    x = int(pos[0])
                    y = int(pos[1])

                    encoded_name = name.encode()

                    data_buffer = struct.pack("!iiI", x, y, len(encoded_name))

                    client.sendall(data_buffer + encoded_name)

            new_messages_amount_buf = recv_exact(client, 4)
            new_messages_amount, = struct.unpack('!I', new_messages_amount_buf)
            new_messages = []
            for i in range(new_messages_amount):
                msg_len, timestamp = struct.unpack("!IQ", recv_exact(client, 12))
                msg = recv_exact(client, msg_len).decode()



                new_messages.append((msg, timestamp))

            with msg_lock:
                for msg in new_messages:
                    full_msg = (msg[1], username, msg[0])
                    if full_msg not in message_data:
                        message_data.append(full_msg)

                message_data_copy = list(message_data)

            client.sendall(struct.pack('!I', len(message_data_copy)))

            for full_msg in message_data_copy:
                timestamp, name, msg = full_msg
                name_encoded = name.encode()
                msg_encoded = msg.encode()

                client.sendall(struct.pack('!QII', timestamp, len(name_encoded), len(msg_encoded)))

                client.sendall(name_encoded)
                client.sendall(msg_encoded)





    except (ConnectionError, OSError):
        with lock1:
            if username in players and username is not None:
                del players[username]

        print(f'{username} left')


        
    

server.listen()

print("Listening...")

while True:
    client, addr = server.accept()
    thread = threading.Thread(target=handle_player, args=(client, addr))
    thread.start()

