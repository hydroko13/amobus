import pygame
from camera import Camera

class Player:
    def __init__(self, username, pos, game):
        self.username = username
        self.pos = pos
        self.target_pos = pos
        self.username_surf = game.notosans_font.render(self.username, False, (255, 255, 255))
        self.window_size = (game.window_width, game.window_height)
        self.hurt = False
        self.dead = False


    def draw(self, surf: pygame.Surface, cam: Camera, is_main_player):

        self.pos = (self.pos[0] + (self.target_pos[0] - self.pos[0]) / 3, self.pos[1] + (self.target_pos[1] - self.pos[1]) / 3)
        
        
        if not self.dead:

            offset_position = (self.pos[0] - cam.pos.x + self.window_size[0] / 2, self.pos[1] - cam.pos.y + self.window_size[1] / 2)



            if self.hurt:
                if is_main_player:
                    pygame.draw.circle(surf, (255, 0, 0), offset_position, 20)
                else:
                    pygame.draw.circle(surf, (255, 150, 150), offset_position, 20)
            else:
                if is_main_player:
                    pygame.draw.circle(surf, (0, 255, 0), offset_position, 20)
                else:
                    pygame.draw.circle(surf, (150, 255, 150), offset_position, 20)

            pygame.draw.circle(surf, (12, 12, 12), offset_position, 20, 2)
                    
            surf.blit(self.username_surf, self.username_surf.get_rect(center=(offset_position[0], offset_position[1]-20)))



            
       