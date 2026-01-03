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
death_broadcast_queue = deque()
death_broadcast_queue_lock = threading.Lock()
respawn_broadcast_queue = deque()
respawn_broadcast_queue_lock = threading.Lock()
dt = 0
direction_facing_dict_inverted = {
    0: 'left',
    1: 'right',
    2: 'up',
    3: 'down'
    
}
hurt_players = set()
dead_players = set()
dead_players_lock = threading.Lock()
hurt_player_timers = []
hurt_players_lock = threading.Lock()
hurt_player_timers_lock = threading.Lock()
respawn_timers = []
respawn_timers_lock = threading.Lock()


def handle_player(client: socket.socket, addr):
    global players, jabs, hurt_players, hurt_player_timers, jab_echo_queue, message_data

    username = None

    try:

        len_bytes = recv_exact(client, 4)


        username_len, = struct.unpack("!I", len_bytes)
 

        username = recv_exact(client, username_len).decode()



        print(f'{username} joined from address {addr}')

        with lock1:
            
            players[username] = (0, 0, 30) # x, y, health

    
        while True:
            
            with hurt_players_lock:
                hurt_players_copy = set(hurt_players)


            if username in hurt_players_copy:

                client.sendall(b'H')

            else:

                client.sendall(b'N')
            

            player_pos_bytes = recv_exact(client, 8)

            player_pos_x, player_pos_y = struct.unpack('!ii', player_pos_bytes)

            with lock1:
                players_copy = dict(players)

            client.sendall(struct.pack("!i", players_copy[username][2]))
            
            

            if username not in hurt_players_copy:
                with lock1:
                    players[username] = (player_pos_x, player_pos_y, players[username][2])

            with lock1:
                players_copy = dict(players)

            positions_expected = len(players_copy)-1

            client.sendall(struct.pack('!I', positions_expected))

            for name, player in players_copy.items():

                if name != username:

                    x = int(player[0])
                    y = int(player[1])
                    
                    # player[2] is health

                    encoded_name = name.encode()

                    if name in hurt_players_copy:
                        b = b'H'
                    else:
                        b = b'N'

                    data_buffer = struct.pack("!iiiIc", x, y, player[2], len(encoded_name), b)

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
                    for i, jab in enumerate(jab_echo_queue):
                        if jab[0] == username:
                            jab_data = jab
                            jab_echo_queue.remove(jab)
                            break

            
            if jab_data is not None:
                client.sendall(b"J")
                buf = struct.pack("!iii", jab_data[1], jab_data[2], jab_data[3])
                client.sendall(buf)

            else:
                client.sendall(b"N")
        
            death_data = None
            with death_broadcast_queue_lock:
                
                if len(death_broadcast_queue) > 0:
                    for i, death_broadcast in enumerate(death_broadcast_queue):
                        if death_broadcast[0] == username:
                            death_data = death_broadcast
                            death_broadcast_queue.remove(death_broadcast)
                            
                            break
                    


            

            if death_data is not None:

                client.sendall(b'D')

                dead_player_name, death_x, death_y = death_data[1]

                dead_player_name_encoded = dead_player_name.encode()

                client.sendall(struct.pack("!Iii", len(dead_player_name_encoded), death_x, death_y)) # send byte length of dead player name, death x, and death y

                client.sendall(dead_player_name_encoded)

            else:
                client.sendall(b'N')


            respawn_player = None
            with respawn_broadcast_queue_lock:
                
                if len(respawn_broadcast_queue) > 0:
                    for i, respawn_broadcast in enumerate(respawn_broadcast_queue):
                        if respawn_broadcast[0] == username:
                            respawn_player = respawn_broadcast[1]
                            respawn_broadcast_queue.remove(respawn_broadcast)
                            
                            break
                            
            if respawn_player is not None:
                client.sendall(b'R')

                player_name_encoded = respawn_player.encode()

                client.sendall(struct.pack("!I", len(player_name_encoded))) # send byte length of dead player name, death x, and death y

                client.sendall(player_name_encoded)

            else:
                client.sendall(b'N')

    except (ConnectionError, OSError):
        with lock1:
            if username in players and username is not None:
                del players[username]

        print(f'{username} left')


def update_server():
    global players, jabs, hurt_players, hurt_player_timers, jab_echo_queue, message_data, dt, respawn_timers
    
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
                
                for name, player in player_data_copy.items():
                    distance = math.dist((player[0], player[1]), tip)
                    if distance < 25 and name != jab.player_name:
                        if not jab.hit_player:
                        
                            jab.hit_player = True
                            
                            hurt_players_temp.add(name)

            
                            

            jabs = [jab for jab in jabs if not jab.finished]

        with lock1:
            for name in hurt_players_temp:
                
                players[name] = (players[name][0], players[name][1], players[name][2]-2)

        with hurt_players_lock:
            new_timers = []
            for name in hurt_players_temp:
                hurt_players.add(name)
                new_timers.append((0, name))
            
        
        with hurt_player_timers_lock:
            for timer in new_timers:
                hurt_player_timers.append((timer[0], timer[1]))
   
        with hurt_player_timers_lock:
            for i, timer in enumerate(hurt_player_timers):
                hurt_player_timers[i] = (timer[0] + dt, timer[1])

        with hurt_player_timers_lock:
            hurt_player_timers_copy = list(hurt_player_timers)

        players_timer_finished = [t[1] for t in hurt_player_timers_copy if t[0] >= 0.2]

        with hurt_players_lock:
            hurt_players = {p for p in hurt_players if p not in players_timer_finished}

        
        with hurt_player_timers_lock:
            hurt_player_timers = [t for t in hurt_player_timers if t[0] < 0.2]
            
        with lock1:
            players_copy = dict(players)

        new_dead_players = []

        with dead_players_lock:
            dead_players_copy = set(dead_players)

        for name, player in players_copy.items():
            if player[2] <= 0: # check if health <= 0
                if name not in dead_players_copy:
                    new_dead_players.append((name, player[0], player[1]))
                    

        if len(new_dead_players) > 0:
            
            with death_broadcast_queue_lock:
                
                for new_dead_player in new_dead_players:
                    for name, _ in players_copy.items():
                        death_broadcast_queue.append((name, new_dead_player))
                    
                        
            with dead_players_lock:
                for new_dead_player in new_dead_players:
                    dead_players.add(new_dead_player[0])
            
            with respawn_timers_lock:
                for new_dead_player in new_dead_players:
                    respawn_timers.append((new_dead_player[0], 0))

        with respawn_timers_lock:
            for i, timer in enumerate(respawn_timers):
                respawn_timers[i] = (timer[0], timer[1] + dt)


        players_to_respawn = []

        with respawn_timers_lock:
            respawn_timers_copy = list(respawn_timers)

        for i, timer in enumerate(respawn_timers_copy):
            if timer[1] >= 1:
                players_to_respawn.append(timer[0])

        with respawn_timers_lock:
            respawn_timers = [timer for timer in respawn_timers if timer[1] < 1]

        with lock1:
            players_copy = dict(players)

        with respawn_broadcast_queue_lock:
            for player_to_respawn in players_to_respawn:
                for name, player in players_copy.items():                
                    respawn_broadcast_queue.append((name, player_to_respawn))
        
        with lock1:
            for player_to_respawn in players_to_respawn:
                players[player_to_respawn] = (players[player_to_respawn][0], players[player_to_respawn][1], 30)

        with dead_players_lock:
            for player_to_respawn in players_to_respawn:
                dead_players.remove(player_to_respawn)

        with respawn_timers_lock:
            print(respawn_timers)
        


server.listen()

print("Listening...")

thread = threading.Thread(target=update_server)
thread.start()



while True:
    client, addr = server.accept()
    thread = threading.Thread(target=handle_player, args=(client, addr))
    thread.start()


