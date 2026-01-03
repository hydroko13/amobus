import pygame
import math
import os
from camera import Camera

class DeathAnimation:
    def __init__(self, pos):
        self.star_image = pygame.transform.scale_by(pygame.image.load(os.path.join('assets', 'img', 'sparkle.png')), 2).convert_alpha()

        self.stars = [pos]

        self.star_opacity = 255

    def draw(self, surf, cam, game):
        star_image_copy = self.star_image.copy()
        
        star_image_copy.fill((255, 255, 255, self.star_opacity), special_flags=pygame.BLEND_RGBA_MULT)

        for star in self.stars:

            pos = (star[0] - cam.pos.x + game.window_width / 2, star[1] - cam.pos.y + game.window_height / 2)

            surf.blit(star_image_copy, self.star_image.get_rect(center=pos))
            
    def update(self, dt):

        if self.star_opacity <= 0:
            self.star_opacity = 0
        else:
            self.star_opacity -= dt * 50
