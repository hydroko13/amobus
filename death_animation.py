import pygame
import math
import os
from camera import Camera

class DeathAnimation:
    def __init__(self, pos):
        self.star_image = pygame.transform.scale_by(pygame.image.load(os.path.join('assets', 'img', 'sparkle.png')), 2).convert_alpha()

        self.stars = []
        self.center = pos
        for i in range(12):
            angle = math.radians((360 / 12) * i)
            self.stars.append((pos[0] + math.cos(angle) * 10, pos[1] + math.sin(angle) * 10))
 
        self.star_opacity = 255
        self.angle_offset = 0
        self.spread = 0

    def draw(self, surf, cam, game):
        star_image_copy = self.star_image.copy()
        
        star_image_copy.fill((255, 255, 255, self.star_opacity), special_flags=pygame.BLEND_RGBA_MULT)

        for star in self.stars:

            pos = (star[0] - cam.pos.x + game.window_width / 2, star[1] - cam.pos.y + game.window_height / 2)

            surf.blit(star_image_copy, self.star_image.get_rect(center=pos))
            
    def update(self, dt):

        for i in range(12):
            angle = math.radians((360 / 12) * i + self.angle_offset)
            self.stars[i] = (self.center[0] + math.cos(angle) * (10 + self.spread), self.center[1] + math.sin(angle) * (10 + self.spread))

        if self.star_opacity <= 0:
            self.star_opacity = 0
        else:
            self.star_opacity -= dt * 190
            self.angle_offset += dt * 100
            self.spread += dt * 120

