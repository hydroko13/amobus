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
    
    
        self.main_player = Player(self.player_username, (100, 100), self)
        self.player_pos_lock = threading.Lock()
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

        
        cam_offset = (self.cam.pos.x + self.window_width / 2, self.cam.pos.y + self.window_height / 2)



        
        self.window.blit(self.world_tilemap_surface, (int(-cam_offset[0]), int(-cam_offset[1])))
        
        with self.other_players_lock:
            for name, player in self.players.items():
                player.draw(self.window, self.cam, False)
                
        with self.player_pos_lock:
            self.main_player.draw(self.window, self.cam, True)

        if self.debug_hud:
            if self.dt != 0:
                fps = 1 / self.dt

                rendered_fps_text = self.notosans_font.render(f'FPS: {fps}', False, (255, 255, 255))

                self.window.blit(rendered_fps_text, (50, 50))

        if self.chat_open:
            type_a_message_label = self.notosans_font.render('Type a message and press enter...', False, (255, 255, 255), (20, 20, 20))
            self.window.blit(type_a_message_label, (50, self.window_height-100))

            msg = self.notosans_font_bigger.render(self.chat_message, False, (255, 255, 255), (20, 20, 20))
            self.window.blit(msg, (50, self.window_height-60))

            for i, msg in enumerate(sorted(self.message_data, key=lambda x: x[0], reverse=True)):
                _, name, text = msg
                chat_msg = self.notosans_font.render(f'<{name}> {text}', False, (255, 255, 255), (20, 20, 20))
                self.window.blit(chat_msg, (50, self.window_height-200-i*30))
                



        
    def communicate_with_server(self):
        try:
            while not self.done:

                with self.player_pos_lock:
                    x = round(self.main_player.pos[0])
                    y = round(self.main_player.pos[1])

                self.server_socket.sendall(struct.pack("!ii", x, y))

                

                positions_expected, = struct.unpack("!I", recv_exact(self.server_socket, 4))

                player_data = {}


                for i in range(positions_expected):

                    buf = recv_exact(self.server_socket, 12)
                
                    player_pos_x, player_pos_y, username_len = struct.unpack("!iiI", buf)

                    username = recv_exact(self.server_socket, username_len).decode()



                    player_data[username] = (player_pos_x, player_pos_y)

               

                for name, pos in player_data.items():        
                    with self.other_players_lock:
                        if name in self.players: 
                            self.players[name].target_pos = pos
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



                                    

                
        except (ConnectionError, OSError):
            print("Server error")
            self.done = True


    def update(self):
       

        with self.player_pos_lock:
            player_pos = self.main_player.pos
        
        self.cam.pos.x = player_pos[0]
        self.cam.pos.y = player_pos[1]

        keys = pygame.key.get_pressed()
        
        
        if not self.chat_open:

            if keys[pygame.K_LEFT]:
                with self.player_pos_lock:
                    self.main_player.pos = (self.main_player.pos[0] - self.dt * 250, self.main_player.pos[1])

            if keys[pygame.K_RIGHT]:
                with self.player_pos_lock:
                    self.main_player.pos = (self.main_player.pos[0] + self.dt * 250, self.main_player.pos[1])
            
            if keys[pygame.K_UP]:
                with self.player_pos_lock:
                    self.main_player.pos = (self.main_player.pos[0], self.main_player.pos[1] - self.dt * 250)

            if keys[pygame.K_DOWN]:
                with self.player_pos_lock:
                    self.main_player.pos = (self.main_player.pos[0], self.main_player.pos[1] + self.dt * 250)

        self.main_player.target_pos = self.main_player.pos
        


    def run(self):
        networking_thread = threading.Thread(target=self.communicate_with_server)
        networking_thread.start()
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F3:
                        self.debug_hud = not self.debug_hud
                    if event.key == pygame.K_ESCAPE:
                        if self.chat_open:
                            self.chat_open = False
                            self.chat_message = ''
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        if self.chat_open:
                            timestamp = time.time_ns()
                            with self.message_data_lock:
                                self.message_data.append((timestamp, self.player_username, self.chat_message))
                            with self.sent_messages_lock:
                                self.messages_sent.append((timestamp, self.chat_message))
                            self.chat_message = ''
                    if event.key == pygame.K_BACKSPACE:
                        if self.chat_open:
                            self.chat_message = self.chat_message[:-1]
                    if self.chat_open:
                        if event.key in typeable_letters:
                            letter = typeable_letters[event.key]
                            self.chat_message += letter
                    if event.key == pygame.K_t:
                        self.chat_open = True




            self.window.fill((0, 0, 0))
            self.dt = self.clock.tick(60) / 1000
            self.update()
            self.draw()
            pygame.display.flip()
        networking_thread.join()

game = Game()
game.run()