import pygame
import os
from player import Player
import socket
import sys
from net import recv_exact
import threading
import struct
from camera import Camera
import time
from jab import Jab
from death_animation import DeathAnimation

pygame.init()

typeable_letters = {
    pygame.K_a : 'a', 
    pygame.K_b : 'b', 
    pygame.K_c : 'c', 
    pygame.K_d : 'd', 
    pygame.K_e : 'e', 
    pygame.K_f : 'f', 
    pygame.K_g : 'g', 
    pygame.K_h : 'h', 
    pygame.K_i : 'i', 
    pygame.K_j : 'j', 
    pygame.K_k : 'k', 
    pygame.K_l : 'l', 
    pygame.K_m : 'm', 
    pygame.K_n : 'n', 
    pygame.K_o : 'o', 
    pygame.K_p : 'p', 
    pygame.K_q : 'q', 
    pygame.K_r : 'r', 
    pygame.K_s : 's', 
    pygame.K_t : 't', 
    pygame.K_u : 'u', 
    pygame.K_v : 'v', 
    pygame.K_w : 'w', 
    pygame.K_x : 'x', 
    pygame.K_y : 'y', 
    pygame.K_z : 'z', 
    pygame.K_SPACE : ' ', 
    pygame.K_0 : '0', 
    pygame.K_1 : '1', 
    pygame.K_2 : '2', 
    pygame.K_3 : '3', 
    pygame.K_4 : '4', 
    pygame.K_5 : '5', 
    pygame.K_6 : '6', 
    pygame.K_7 : '7', 
    pygame.K_8 : '8',
    pygame.K_9 : '9',
    pygame.K_KP0 : '0', 
    pygame.K_KP1 : '1', 
    pygame.K_KP2 : '2', 
    pygame.K_KP3 : '3', 
    pygame.K_KP4 : '4', 
    pygame.K_KP5 : '5', 
    pygame.K_KP6 : '6', 
    pygame.K_KP7 : '7', 
    pygame.K_KP8 : '8',
    pygame.K_KP9 : '9',
    pygame.K_COMMA : ',',
    pygame.K_PERIOD : '.',
}

num_keys = {
    pygame.K_0 : '0', 
    pygame.K_1 : '1', 
    pygame.K_2 : '2', 
    pygame.K_3 : '3', 
    pygame.K_4 : '4', 
    pygame.K_5 : '5', 
    pygame.K_6 : '6', 
    pygame.K_7 : '7', 
    pygame.K_8 : '8',
    pygame.K_9 : '9',
    pygame.K_KP0 : '0', 
    pygame.K_KP1 : '1', 
    pygame.K_KP2 : '2', 
    pygame.K_KP3 : '3', 
    pygame.K_KP4 : '4', 
    pygame.K_KP5 : '5', 
    pygame.K_KP6 : '6', 
    pygame.K_KP7 : '7', 
    pygame.K_KP8 : '8',
    pygame.K_KP9 : '9'
}

class Game:
    def __init__(self):

        self.player_username = input('ENTER USERNAME: ')
        self.server_socket = socket.create_connection(('10.0.0.97', 8080))
        self.server_socket.sendall(struct.pack("!I", len(self.player_username.encode())))
        self.server_socket.sendall(self.player_username.encode())
        self.window_width = 1280
        self.window_height = 720
        self.window = pygame.display.set_mode((self.window_width, self.window_height), pygame.DOUBLEBUF, vsync=1)
        self.clock = pygame.time.Clock()
        self.done = False
        self.dt = 0
        self.notosans_font = pygame.font.Font(os.path.join('assets', 'fnt', 'notosans.ttf'))
        self.notosans_font_bigger = pygame.font.Font(os.path.join('assets', 'fnt', 'notosans.ttf'), 24)
        self.players = {}
        self.death_animations = []
        self.death_animations_lock = threading.Lock()
    
    
        self.main_player = Player(self.player_username, (100, 100), self)
        self.main_player_lock = threading.Lock()
        self.other_players_lock = threading.Lock()
        self.sent_messages_lock = threading.Lock()
        self.message_data_lock = threading.Lock()

        self.cam = Camera(self.main_player.pos)

        self.world_data = [[0 for x in range(100)] for y in range(100)]
        self.window_rect = pygame.Rect(0, 0, self.window_width, self.window_height)
        self.world_tilemap_surface = pygame.Surface((5000, 5000), pygame.SRCALPHA)

        self.update_world_surface()

        self.debug_hud = False
        self.chat_open = False
        self.chat_message = ''

        self.messages_sent = []

        self.message_data = []
        
        self.inventory_data = [[-1 for x in range(9)] for y in range(4)]
        self.selected_hotbar_slot = 1

        self.direction_facing = 'left'


        self.jab_dagger_img = pygame.image.load(os.path.join('assets', 'img', 'dagger_jab.png'))

        self.jabs = []
        self.main_player_jab = None

        self.hurt = False
        self.hurt_lock = threading.Lock()

        self.health = 30
        self.health_lock = threading.Lock()


        
        self.echo_jab = False # whether or not to tell the server of a dagger jab

        self.jab_lock = threading.Lock()
        self.jabs_lock = threading.Lock()
        
        self.direction_facing_dict = {
            'left': 0,
            'right': 1,
            'up' : 2,
            'down': 3
            
        }

        self.direction_facing_dict_inverted = {
            0: 'left',
            1: 'right',
            2: 'up',
            3: 'down'
            
        }

        self.jab_data = None

        self.respawning = False
        self.respawning_lock = threading.Lock()
        self.chat_open_lock = threading.Lock()

        


    def update_world_surface(self):
        

        for y, row in enumerate(self.world_data):
            for x, tile in enumerate(row):

                tile_rect = pygame.Rect(x*50, y*50, 50, 50)
                

                    
                pygame.draw.rect(self.world_tilemap_surface, (71, 158, 74), tile_rect)
        for y, row in enumerate(self.world_data):
            for x, tile in enumerate(row):
                
                tile_rect = pygame.Rect(x*50, y*50, 50, 50)

                pygame.draw.rect(self.world_tilemap_surface, (8, 10, 8), tile_rect, 2)

    def draw(self):

        with self.chat_open_lock:
            chat_open = self.chat_open

        
        cam_offset = (self.cam.pos.x + self.window_width / 2, self.cam.pos.y + self.window_height / 2)



        
        self.window.blit(self.world_tilemap_surface, (int(-cam_offset[0]), int(-cam_offset[1])))

        with self.jabs_lock:
            for jab in self.jabs:
                jab.draw(self)
        
        with self.other_players_lock:
            for name, player in self.players.items():
                player.draw(self.window, self.cam, False)
                
        with self.main_player_lock:
            main_player_pos = self.main_player.pos

        
        

        if self.main_player_jab:
            self.main_player_jab.draw(self)
        

        with self.main_player_lock:
            # maybe some room for optimization here?

            self.main_player.draw(self.window, self.cam, True)

        with self.death_animations_lock:
            for death_animation in self.death_animations:
                death_animation.draw(self.window, self.cam, self)

        if self.debug_hud:
            if self.dt != 0:
                fps = 1 / self.dt

                rendered_fps_text = self.notosans_font.render(f'FPS: {fps}', False, (255, 255, 255))

                self.window.blit(rendered_fps_text, (50, 50))

        if chat_open:
            type_a_message_label = self.notosans_font.render('Type a message and press enter...', False, (255, 255, 255), (20, 20, 20))
            self.window.blit(type_a_message_label, (50, self.window_height-100))

            msg = self.notosans_font_bigger.render(self.chat_message, False, (255, 255, 255), (20, 20, 20))
            self.window.blit(msg, (50, self.window_height-60))

            for i, msg in enumerate(sorted(self.message_data, key=lambda x: x[0], reverse=True)):
                _, name, text = msg
                chat_msg = self.notosans_font.render(f'<{name}> {text}', False, (255, 255, 255), (20, 20, 20))
                self.window.blit(chat_msg, (50, self.window_height-200-i*30))
                
        if not chat_open:

            for x in range(9):
                if x+1 == self.selected_hotbar_slot:
                    pygame.draw.rect(self.window, (180, 100, 100), pygame.Rect(x*52+650, self.window_height-100, 50, 50))
                else:
                    pygame.draw.rect(self.window, (180, 180, 180), pygame.Rect(x*52+650, self.window_height-100, 50, 50))

            for x in range(9):
                if x+1 == self.selected_hotbar_slot:
                    pygame.draw.rect(self.window, (150, 50, 50), pygame.Rect(x*52+650, self.window_height-100, 50, 50), 2)
                else:
                    pygame.draw.rect(self.window, (150, 150, 150), pygame.Rect(x*52+650, self.window_height-100, 50, 50), 2)

            for x in range(9):
                text_surf = self.notosans_font.render(f'{x+1}', False, (230, 230, 230))
                self.window.blit(text_surf, text_surf.get_rect(center=(x*52+675, self.window_height-100)))

        with self.health_lock:
            health_copy = self.health

        pygame.draw.rect(self.window, (46, 46, 46), pygame.Rect(self.window_width-350, 80, 200, 30))
        pygame.draw.rect(self.window, (250, 61, 40), pygame.Rect(self.window_width-350, 80, (health_copy/30)*200, 30))


        
        
    def communicate_with_server(self):
        try:
            while not self.done:

                with self.main_player_lock:
                    x = round(self.main_player.pos[0])
                    y = round(self.main_player.pos[1])

                b = recv_exact(self.server_socket, 1)

                if b == b'H':
                    with self.hurt_lock:
                        self.hurt = True
                else:
                    with self.hurt_lock:
                        self.hurt = False


                self.server_socket.sendall(struct.pack("!ii", x, y))

                received_health, = struct.unpack('!i', recv_exact(self.server_socket, 4))

                with self.health_lock:
                    self.health = received_health
                

                positions_expected, = struct.unpack("!I", recv_exact(self.server_socket, 4))

                player_data = {}


                for i in range(positions_expected):

                    buf = recv_exact(self.server_socket, 17)
                
                    player_pos_x, player_pos_y, health, username_len, hurt_byte = struct.unpack("!iiiIc", buf)

                    username = recv_exact(self.server_socket, username_len).decode()



                    player_data[username] = (player_pos_x, player_pos_y, True if hurt_byte == b'H' else False)


               

                for name, data in player_data.items():        
                    pos = (data[0], data[1])
                    hurt = data[2]
                    with self.other_players_lock:
                        if name in self.players: 
                            self.players[name].target_pos = pos
                            self.players[name].hurt = hurt
                        if name not in self.players: 
                            self.players[name] = Player(name, pos, self)
                            

                with self.other_players_lock:
                    players_copy = dict(self.players)

                for name, player in players_copy.items():
                    if name not in player_data:
                        with self.other_players_lock:
                            del self.players[name]

                with self.sent_messages_lock:
                    messages_sent_copy = list(self.messages_sent)

                self.server_socket.sendall(struct.pack("!I", len(messages_sent_copy)))

                for timestamp, msg in messages_sent_copy:
                    encoded_msg = msg.encode()
                    
                    self.server_socket.sendall(struct.pack("!IQ", len(encoded_msg), timestamp))

                    self.server_socket.sendall(encoded_msg)
                
                with self.sent_messages_lock:
                    self.messages_sent = []

                messages_expected, = struct.unpack("!I", recv_exact(self.server_socket, 4))

                new_message_data = []

                for i in range(messages_expected):
                    timestamp, name_len, msg_len = struct.unpack("!QII", recv_exact(self.server_socket, 16))

                    name_bytes = recv_exact(self.server_socket, name_len)
                    msg_bytes = recv_exact(self.server_socket, msg_len)

                    new_message_data.append((timestamp, name_bytes.decode(), msg_bytes.decode()))

                with self.message_data_lock:
                    self.message_data = new_message_data

                with self.jab_lock:
                    echo_jab_copy = self.echo_jab
                    if self.echo_jab:
                        self.echo_jab = False
                    jab_data_copy = self.jab_data

                if echo_jab_copy:
                    self.server_socket.sendall(b'J')
                    self.server_socket.sendall(jab_data_copy)
                else:
                    self.server_socket.sendall(b'N')

                b = recv_exact(self.server_socket, 1)

                if b == b'J':
                    jab_x, jab_y, jab_direction = struct.unpack("!iii", recv_exact(self.server_socket, 12))


                    with self.jabs_lock:
                        self.jabs.append(Jab((jab_x, jab_y), self.direction_facing_dict_inverted[jab_direction], ''))

                death_b = recv_exact(self.server_socket, 1)
                if death_b == b'D':
                    dead_player_name_length, death_x, death_y = struct.unpack("!Iii", recv_exact(self.server_socket, 12))
                    dead_player_name = recv_exact(self.server_socket, dead_player_name_length).decode()
                    with self.death_animations_lock:
                        self.death_animations.append(DeathAnimation((death_x, death_y)))
                    if dead_player_name == self.player_username:
                        with self.main_player_lock:
                            self.main_player.dead = True
                        self.death()

                    else:
                        with self.other_players_lock:
                            for name, player in self.players.items():
                                if name == dead_player_name:

                                    self.players[name].dead = True
                                    break
                
                respawn_b = recv_exact(self.server_socket, 1) # b in respawn_b means byte, same in death_b, etc
                if respawn_b == b'R':
                    player_name_length, = struct.unpack("!I", recv_exact(self.server_socket, 4))
                    respawn_player_name = recv_exact(self.server_socket, player_name_length).decode()

                    if respawn_player_name == self.player_username:
                        with self.main_player_lock:
                            self.main_player.dead = False
                        self.respawn()

                    else:
                        with self.other_players_lock:
                            for name, player in self.players.items():
                                if name == respawn_player_name:

                                    self.players[name].dead = False
                                    break

                
        except (ConnectionError, OSError):
            print("Server error")
            self.done = True

    def death(self):

        with self.respawning_lock:
            self.respawning = True
        with self.chat_open_lock:
            self.chat_open = False


    def respawn(self):
        with self.main_player_lock:
            self.main_player.pos = (100, 100)
        with self.respawning_lock:
            self.respawning = False
        with self.chat_open_lock:
            self.chat_open = False


    def update(self):
       
        with self.respawning_lock:
            is_respawning = self.respawning

        with self.main_player_lock:
            player_pos = self.main_player.pos
        
        with self.chat_open_lock:
            chat_open = self.chat_open
        
        self.cam.pos.x = player_pos[0]
        self.cam.pos.y = player_pos[1]

        keys = pygame.key.get_pressed()

        
        

        with self.hurt_lock:
            hurt_copy = self.hurt
        with self.main_player_lock:
            self.main_player.hurt = hurt_copy

        if not is_respawning:
            
            if not chat_open and self.main_player_jab is None and not hurt_copy:

                if keys[pygame.K_a]:
                    self.direction_facing = 'left'
                    with self.main_player_lock:
                        self.main_player.pos = (self.main_player.pos[0] - self.dt * 250, self.main_player.pos[1])

                if keys[pygame.K_d]:
                    self.direction_facing = 'right'
                    with self.main_player_lock:
                        self.main_player.pos = (self.main_player.pos[0] + self.dt * 250, self.main_player.pos[1])
                
                if keys[pygame.K_w]:
                    self.direction_facing = 'up'
                    with self.main_player_lock:
                        self.main_player.pos = (self.main_player.pos[0], self.main_player.pos[1] - self.dt * 250)

                if keys[pygame.K_s]:
                    self.direction_facing = 'down'
                    with self.main_player_lock:
                        self.main_player.pos = (self.main_player.pos[0], self.main_player.pos[1] + self.dt * 250)

            if not chat_open:
                if keys[pygame.K_a]:
                    self.direction_facing = 'left'

                if keys[pygame.K_d]:
                    self.direction_facing = 'right'

                if keys[pygame.K_w]:
                    self.direction_facing = 'up'

                if keys[pygame.K_s]:
                    self.direction_facing = 'down'

        self.main_player.target_pos = self.main_player.pos

        if self.main_player_jab:
            self.main_player_jab.update(self)
            if self.main_player_jab.finished:
                self.main_player_jab = None

        with self.jabs_lock:
            for jab in self.jabs:
                jab.update(self)
            self.jabs = [jab for jab in self.jabs if not jab.finished]

        with self.death_animations_lock:
            for death_animation in self.death_animations:
                death_animation.update(self.dt)
            self.death_animations = [anim for anim in self.death_animations if anim.star_opacity > 0]
        

    def jab(self):
        if self.main_player_jab is None:

            with self.main_player_lock:
                main_player_pos = self.main_player.pos



            with self.jab_lock:
                self.echo_jab = True
                
                self.jab_data = struct.pack("!iii", int(main_player_pos[0]), int(main_player_pos[1]), int(self.direction_facing_dict[self.direction_facing]))


            
            self.main_player_jab = Jab(main_player_pos, self.direction_facing, '')

    def run(self):
        networking_thread = threading.Thread(target=self.communicate_with_server)
        networking_thread.start()
        while not self.done:
            with self.respawning_lock:
                is_respawning = self.respawning
            with self.chat_open_lock:
                chat_open = self.chat_open
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F3:
                        self.debug_hud = not self.debug_hud
                    if event.key == pygame.K_ESCAPE:
                        if chat_open and not is_respawning:
                            with self.chat_open_lock:
                                self.chat_open = False
                            chat_message = ''
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        if self.chat_open and not is_respawning:
                            timestamp = time.time_ns()
                            with self.message_data_lock:
                                self.message_data.append((timestamp, self.player_username, self.chat_message))
                            with self.sent_messages_lock:
                                self.messages_sent.append((timestamp, self.chat_message))
                            self.chat_message = ''
                    if event.key == pygame.K_BACKSPACE:
                        if chat_open and not is_respawning:
                            self.chat_message = self.chat_message[:-1]
                    if self.chat_open:
                        if event.key in typeable_letters and not is_respawning:
                            letter = typeable_letters[event.key]
                            self.chat_message += letter
                    if event.key == pygame.K_t and not is_respawning:
                        with self.chat_open_lock:
                            self.chat_open = True
                    if event.key == pygame.K_o and not is_respawning:
                        if not self.chat_open and not self.hurt:
                            self.jab()

                    if event.key in num_keys and not chat_open and not is_respawning:
                        n = num_keys[event.key]

                        if n == '1':
                            self.selected_hotbar_slot = 1    

                        elif n == '2':
                            self.selected_hotbar_slot = 2

                        elif n == '3':
                            self.selected_hotbar_slot = 3

                        elif n == '4':
                            self.selected_hotbar_slot = 4

                        elif n == '5':
                            self.selected_hotbar_slot = 5

                        elif n == '6':
                            self.selected_hotbar_slot = 6

                        elif n == '7':
                            self.selected_hotbar_slot = 7

                        elif n == '8':
                            self.selected_hotbar_slot = 8
                            
                        elif n == '9':
                            self.selected_hotbar_slot = 9
                            



            self.window.fill((0, 0, 0))
            self.dt = self.clock.tick(60) / 1000
            self.update()
            self.draw()
            pygame.display.flip()
        networking_thread.join()

game = Game()
game.run()