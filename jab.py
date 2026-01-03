import pygame

class Jab:
    def __init__(self, pos, direction, player_name):
        self.show_jab_dagger = True
        self.jab_tick = 0
        self.jab_rebound = False
        self.jab_wait = False
        self.jab_offset = 0
        self.pos = pos
        self.direction = direction
        self.player_name = player_name
        self.finished = False
        self.hit_player = False

    def update(self, game):
        if self.jab_rebound:
            self.jab_offset -= game.dt * 400
            if self.jab_offset <= 0:
                self.show_jab_dagger = False
                self.jab_tick = 0
                self.jab_rebound = False
                self.jab_offset = 0
                self.finished = True
            
        else:
            if self.jab_wait:
                self.jab_tick += game.dt
                if self.jab_tick > 0.12:
                    self.jab_wait = False
                    self.jab_rebound = True
                    self.jab_offset = 50
            else:
                self.jab_offset += game.dt * 600
                if self.jab_offset >= 50:
                    self.jab_wait = True
                    self.jab_tick = 0
                    self.jab_offset = 50

    def get_tip_pos(self):
        if self.direction == 'left':
            dagger_forward_vec = (-1, 0)
        if self.direction == 'right':
            dagger_forward_vec = (1, 0)
        if self.direction == 'down':
            dagger_forward_vec = (0, 1)
        if self.direction == 'up':
            dagger_forward_vec = (0, -1)

        pos = ((self.pos[0])+dagger_forward_vec[0]*(self.jab_offset+14), (self.pos[1])+dagger_forward_vec[1]*(self.jab_offset+14))
        return pos

    def update_serverside(self, dt):
        if self.jab_rebound:
            self.jab_offset -= dt * 400
            if self.jab_offset <= 0:
                self.show_jab_dagger = False
                self.jab_tick = 0
                self.jab_rebound = False
                self.jab_offset = 0
                self.finished = True
            
        else:
            if self.jab_wait:
                self.jab_tick += dt
                if self.jab_tick > 0.12:
                    self.jab_wait = False
                    self.jab_rebound = True
                    self.jab_offset = 50
            else:
                self.jab_offset += dt * 600
                if self.jab_offset >= 50:
                    self.jab_wait = True
                    self.jab_tick = 0
                    self.jab_offset = 50

    def draw(self, game):


        
        scaled_dagger_img = pygame.transform.scale_by(game.jab_dagger_img, 5)

        

        if self.direction == 'left':
            rotated_dagger_img = pygame.transform.rotate(scaled_dagger_img, 90)
            dagger_forward_vec = (-1, 0)
        if self.direction == 'right':
            rotated_dagger_img = pygame.transform.rotate(scaled_dagger_img, -90)
            dagger_forward_vec = (1, 0)
        if self.direction == 'down':
            rotated_dagger_img = pygame.transform.rotate(scaled_dagger_img, 180)
            dagger_forward_vec = (0, 1)
        if self.direction == 'up':
            rotated_dagger_img = scaled_dagger_img.copy()
            dagger_forward_vec = (0, -1)


        if self.show_jab_dagger:

            
            game.window.blit(rotated_dagger_img, scaled_dagger_img.get_rect(center=((self.pos[0] - game.cam.pos.x + game.window_width / 2)+dagger_forward_vec[0]*self.jab_offset, (self.pos[1] - game.cam.pos.y + game.window_height / 2)+dagger_forward_vec[1]*self.jab_offset)))
            
            
                        
                    