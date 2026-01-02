import pygame

class Player:
    def __init__(self, username, pos, game):
        self.username = username
        self.pos = pos
        self.target_pos = pos
        self.username_surf = game.notosans_font.render(self.username, False, (255, 255, 255))



    def draw(self, surf):

        self.pos = (self.pos[0] + (self.target_pos[0] - self.pos[0]) / 12, self.pos[1] + (self.target_pos[1] - self.pos[1])  / 12)

        pygame.draw.circle(surf, (255, 0, 0), self.pos, 20)
        surf.blit(self.username_surf, self.username_surf.get_rect(center=(self.pos[0], self.pos[1]-20)))
       