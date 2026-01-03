import socket
import threading
import struct
from net import recv_exact
import uuid
from collections import deque
from jab import Jab
import math
from pygame.time import Clock
import time



server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

server.bind(('10.0.0.97', 8080))

players = {

}

message_data = set()

lock1 = threading.Lock()
msg_lock = threading.Lock()
jab_echo_queue = deque()
jab_echo_queue_lock = threading.Lock()
jabs = []
jabs_lock = threading.Lock()
dt = 0
direction_facing_dict_inverted = {
    0: 'left',
    1: 'right',
    2: 'up',
    3: 'down'
    
}
hurt_players = set()
hurt_player_timers = []
hurt_players_lock = threading.Lock()


def handle_player(client: socket.socket, addr):
    global players, jabs, hurt_players, hurt_player_timers, jab_echo_queue, message_data

    username = None

    try:

        len_bytes = recv_exact(client, 4)


        username_len, = struct.unpack("!I", len_bytes)
 

        username = recv_exact(client, username_len).decode()



        print(f'{username} joined from address {addr}')

        with lock1:
            
            players[username] = (0, 0)

    
        while True:
            
            with hurt_players_lock:
                hurt_players_copy = set(hurt_players)


            if username in hurt_players_copy:

                client.sendall(b'H')

            else:

                client.sendall(b'N')
            

            player_pos_bytes = recv_exact(client, 8)

            player_pos_x, player_pos_y = struct.unpack('!ii', player_pos_bytes)
            
            

            if username not in hurt_players_copy:
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

                    if name in hurt_players_copy:
                        b = b'H'
                    else:
                        b = b'N'

                    data_buffer = struct.pack("!iiIc", x, y, len(encoded_name), b)

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
                    message_data.add(full_msg)

                message_data_copy = list(message_data)

            client.sendall(struct.pack('!I', len(message_data_copy)))

            for full_msg in message_data_copy:
                timestamp, name, msg = full_msg
                name_encoded = name.encode()
                msg_encoded = msg.encode()

                client.sendall(struct.pack('!QII', timestamp, len(name_encoded), len(msg_encoded)))

                client.sendall(name_encoded)
                client.sendall(msg_encoded)
            
            buf = recv_exact(client, 1)

            if buf == b'J':
                jab_buf = recv_exact(client, 12)
                jab_x, jab_y, jab_direction = struct.unpack("!iii", jab_buf)

                with jabs_lock:
                    
                    jabs.append(Jab((jab_x, jab_y), direction_facing_dict_inverted[jab_direction], username))

                with lock1:
                    players_copy = dict(players)


                with jab_echo_queue_lock:

                    for name, _ in players_copy.items():
                        if name != username:
                            jab_echo_queue.append((name, jab_x, jab_y, jab_direction))
               
            jab_data = None
            with jab_echo_queue_lock:
                if len(jab_echo_queue) > 0:
                    if jab_echo_queue[-1][0] == username:
                        jab_data = jab_echo_queue.pop()

            
            if jab_data is not None:
                client.sendall(b"J")
                buf = struct.pack("!iii", jab_data[1], jab_data[2], jab_data[3])
                client.sendall(buf)

            else:
                client.sendall(b"N")


    except (ConnectionError, OSError):
        with lock1:
            if username in players and username is not None:
                del players[username]

        print(f'{username} left')


def update_server():
    global players, jabs, hurt_players, hurt_player_timers, jab_echo_queue, message_data, dt
    
    clock = Clock()

    while True:
        dt = clock.tick(60) / 1000

        with lock1:
            player_data_copy = dict(players)

        with jabs_lock:
            hurt_players_temp = set()
            for jab in jabs:
                jab.update_serverside(dt)
                tip = jab.get_tip_pos()
                
                for name, pos in player_data_copy.items():
                    distance = math.dist(pos, tip)
                    if distance < 18 and name != jab.player_name:

                        hurt_players_temp.add(name)

            
                            

            jabs = [jab for jab in jabs if not jab.finished]

        with hurt_players_lock:
            for name in hurt_players_temp:
                hurt_players.add(name)
                hurt_player_timers.append((0, name))
   
        for i, timer in enumerate(hurt_player_timers):
            hurt_player_timers[i] = (timer[0] + dt, timer[1])

        players_timer_finished = [t[1] for t in hurt_player_timers if not t[0] < 0.4]

        with hurt_players_lock:
            hurt_players = {p for p in hurt_players if p not in players_timer_finished}
        
        hurt_player_timers = [t for t in hurt_player_timers if t[0] < 0.4]
            
    

server.listen()

print("Listening...")

thread = threading.Thread(target=update_server)
thread.start()



while True:
    client, addr = server.accept()
    thread = threading.Thread(target=handle_player, args=(client, addr))
    thread.start()


