import pygame
import os
from player import Player
import socket
import sys
from net import recv_exact
import threading
import struct

pygame.init()



class Game:
    def __init__(self):

        self.player_username = input('ENTER USERNAME: ')
        self.server_socket = socket.create_connection(('10.0.0.97', 8080))
        self.server_socket.sendall(struct.pack("!I", len(self.player_username.encode())))
        self.server_socket.sendall(self.player_username.encode())
        self.window_width = 1280
        self.window_height = 720
        self.window = pygame.display.set_mode((self.window_width, self.window_height))
        self.clock = pygame.time.Clock()
        self.done = False
        self.dt = 0
        self.notosans_font = pygame.font.Font(os.path.join('assets', 'fnt', 'notosans.ttf'))
        self.players = {}
    
    
        self.main_player = Player(self.player_username, (100, 100), self)
        self.player_pos_lock = threading.Lock()
        self.other_players_lock = threading.Lock()

        


    def draw(self):
        
        with self.other_players_lock:
            for name, player in self.players.items():
                player.draw(self.window)
                
        with self.player_pos_lock:
            self.main_player.draw(self.window)
        
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
                        

                    
                                    

                
        except (ConnectionError, OSError):
            print("Server error")
            self.done = True


    def update(self):
       
        keys = pygame.key.get_pressed()
        
        

        if keys[pygame.K_LEFT]:
            with self.player_pos_lock:
                self.main_player.pos = (self.main_player.pos[0] - self.dt * 120, self.main_player.pos[1])

        if keys[pygame.K_RIGHT]:
            with self.player_pos_lock:
                self.main_player.pos = (self.main_player.pos[0] + self.dt * 120, self.main_player.pos[1])
        
        if keys[pygame.K_UP]:
            with self.player_pos_lock:
                self.main_player.pos = (self.main_player.pos[0], self.main_player.pos[1] - self.dt * 120)

        if keys[pygame.K_DOWN]:
            with self.player_pos_lock:
                self.main_player.pos = (self.main_player.pos[0], self.main_player.pos[1] + self.dt * 120)

        self.main_player.target_pos = self.main_player.pos
        


    def run(self):
        networking_thread = threading.Thread(target=self.communicate_with_server)
        networking_thread.start()
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
            self.window.fill((0, 0, 0))
            self.dt = self.clock.tick() / 1000
            self.update()
            self.draw()
            pygame.display.flip()
        networking_thread.join()
game = Game()
game.run()