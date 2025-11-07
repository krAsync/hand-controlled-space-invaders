import pygame
import random
import cv2
import json
import math
from src.MediPipeHandsModule.HandTrackingModule import hand_detector
from src.MediPipeHandsModule.GestureEvaluator import GestureEvaluator
import collections

# ============================================
# GAME 1: PAC-MAN STYLE MAZE GAME
# ============================================

class Pellet(pygame.sprite.Sprite):
    def __init__(self, x, y, is_power=False):
        super().__init__()
        self.is_power = is_power
        size = 16 if is_power else 6
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 200, 100), (size//2, size//2), size//2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.points = 50 if is_power else 10

class PacPlayer(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.size = 30
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direction = 4  # 4=right
        self.speed = 4
        self.mouth_open = 0
        self.mouth_direction = 1
        self.draw()
        
    def draw(self):
        self.image.fill((0, 0, 0, 0))
        center = self.size // 2
        # Animate mouth
        mouth_angle = 45 * (self.mouth_open / 10)
        
        # Map direction: 1=up, 2=left, 3=down, 4=right
        angle_map = {1: 270, 2: 180, 3: 90, 4: 0}
        base_angle = angle_map.get(self.direction, 0)
        
        start_angle = math.radians(base_angle + mouth_angle)
        end_angle = math.radians(base_angle + 360 - mouth_angle)
        
        points = [(center, center)]
        for angle in [start_angle + i * 0.1 for i in range(int((end_angle - start_angle) / 0.1))]:
            x = center + int(center * math.cos(angle))
            y = center + int(center * math.sin(angle))
            points.append((x, y))
        points.append((center, center))
        
        pygame.draw.polygon(self.image, (255, 255, 0), points)
        
    def update_animation(self):
        self.mouth_open += self.mouth_direction
        if self.mouth_open >= 10 or self.mouth_open <= 0:
            self.mouth_direction *= -1
        self.draw()
        
    def move(self, walls):
        old_x, old_y = self.rect.x, self.rect.y
        
        if self.direction == 4:  # Right
            self.rect.x += self.speed
        elif self.direction == 3:  # Down
            self.rect.y += self.speed
        elif self.direction == 2:  # Left
            self.rect.x -= self.speed
        elif self.direction == 1:  # Up
            self.rect.y -= self.speed
            
        # Check collision with walls
        if pygame.sprite.spritecollide(self, walls, False):
            self.rect.x, self.rect.y = old_x, old_y

class Ghost(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.size = 30
        self.color = color
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 2
        self.direction = random.randint(1, 4)
        self.change_direction_timer = 0
        self.draw()
        
    def draw(self):
        self.image.fill((0, 0, 0, 0))
        # Body
        pygame.draw.circle(self.image, self.color, (self.size//2, self.size//2), self.size//2)
        pygame.draw.rect(self.image, self.color, (0, self.size//2, self.size, self.size//2))
        # Wavy bottom
        for i in range(5):
            pygame.draw.circle(self.image, (0, 0, 0), (i * 7, self.size - 1), 4)
        # Eyes
        pygame.draw.circle(self.image, (255, 255, 255), (10, 12), 5)
        pygame.draw.circle(self.image, (255, 255, 255), (20, 12), 5)
        pygame.draw.circle(self.image, (0, 0, 255), (10, 12), 3)
        pygame.draw.circle(self.image, (0, 0, 255), (20, 12), 3)
        
    def update(self, walls):
        self.change_direction_timer += 1
        if self.change_direction_timer > 60:
            self.direction = random.randint(1, 4)
            self.change_direction_timer = 0
            
        old_x, old_y = self.rect.x, self.rect.y
        
        if self.direction == 4:  # Right
            self.rect.x += self.speed
        elif self.direction == 3:  # Down
            self.rect.y += self.speed
        elif self.direction == 2:  # Left
            self.rect.x -= self.speed
        elif self.direction == 1:  # Up
            self.rect.y -= self.speed
            
        if pygame.sprite.spritecollide(self, walls, False):
            self.rect.x, self.rect.y = old_x, old_y
            self.direction = random.randint(1, 4)

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill((0, 0, 255))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class PacManGame:
    def __init__(self, screen, cap, detector, gesture_evaluator):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.cap = cap
        self.detector = detector
        self.gesture_evaluator = gesture_evaluator
        self.recent_gestures = collections.deque(maxlen=5)
        
        self.font = pygame.font.SysFont('courier', 36, bold=True)
        self.title_font = pygame.font.SysFont('courier', 72, bold=True)
        
        self.player = None
        self.ghosts = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.pellets = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        
        self.score = 0
        self.level = 1
        self.lives = 3
        
        self.setup_maze()
        
    def setup_maze(self):
        self.all_sprites.empty()
        self.walls.empty()
        self.pellets.empty()
        self.ghosts.empty()
        
        # Create maze layout (1=wall, 0=path, 2=pellet, 3=power pellet)
        maze = [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,2,2,2,2,2,2,1,1,2,2,2,2,2,2,1],
            [1,3,1,1,2,1,2,1,1,2,1,2,1,1,3,1],
            [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
            [1,2,1,1,2,1,1,1,1,1,1,2,1,1,2,1],
            [1,2,2,2,2,2,2,1,1,2,2,2,2,2,2,1],
            [1,1,1,1,2,1,2,2,2,2,1,2,1,1,1,1],
            [1,2,2,2,2,2,2,1,1,2,2,2,2,2,2,1],
            [1,2,1,1,2,1,1,1,1,1,1,2,1,1,2,1],
            [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
            [1,3,1,1,2,1,2,1,1,2,1,2,1,1,3,1],
            [1,2,2,2,2,2,2,1,1,2,2,2,2,2,2,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        ]
        
        cell_width = 60
        cell_height = 50
        offset_x = (self.width - len(maze[0]) * cell_width) // 2
        offset_y = 100
        
        for row_idx, row in enumerate(maze):
            for col_idx, cell in enumerate(row):
                x = offset_x + col_idx * cell_width
                y = offset_y + row_idx * cell_height
                
                if cell == 1:
                    wall = Wall(x, y, cell_width, cell_height)
                    self.walls.add(wall)
                    self.all_sprites.add(wall)
                elif cell == 2:
                    pellet = Pellet(x + cell_width//2 - 3, y + cell_height//2 - 3, False)
                    self.pellets.add(pellet)
                    self.all_sprites.add(pellet)
                elif cell == 3:
                    pellet = Pellet(x + cell_width//2 - 8, y + cell_height//2 - 8, True)
                    self.pellets.add(pellet)
                    self.all_sprites.add(pellet)
        
        # Create player
        self.player = PacPlayer(offset_x + cell_width * 8, offset_y + cell_height * 9)
        self.all_sprites.add(self.player)
        
        # Create ghosts
        colors = [(255, 0, 0), (255, 184, 255), (0, 255, 255), (255, 184, 82)]
        for i, color in enumerate(colors):
            ghost = Ghost(offset_x + cell_width * (7 + i % 2), 
                         offset_y + cell_height * (6 + i // 2), color)
            self.ghosts.add(ghost)
            self.all_sprites.add(ghost)
    
    def handle_gestures(self):
        success, img = self.cap.read()
        if success:
            img = cv2.flip(img, 1)
            img = self.detector.find_hands(img)
            lm_list, bbox, _ = self.detector.get_bbox_location(img)
            handedness_list = self.detector.get_handedness()

            if lm_list and handedness_list and bbox:
                gesture = self.gesture_evaluator.evaluate(lm_list, handedness_list[0], bbox)
                self.recent_gestures.append(gesture[0])

            if len(self.recent_gestures) == self.recent_gestures.maxlen:
                most_common = collections.Counter(self.recent_gestures).most_common(1)[0][0]
                
                # 1=up, 2=left, 3=down, 4=right
                if most_common in [1, 2, 3, 4]:
                    self.player.direction = most_common
                    
        return success, img if success else None
    
    def draw_scanline(self):
        for i in range(0, self.height, 4):
            pygame.draw.line(self.screen, (10, 10, 10), (0, i), (self.width, i), 1)
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
            
            success, img = self.handle_gestures()
            
            # Update
            self.player.move(self.walls)
            self.player.update_animation()
            self.ghosts.update(self.walls)
            
            # Check pellet collection
            pellets_hit = pygame.sprite.spritecollide(self.player, self.pellets, True)
            for pellet in pellets_hit:
                self.score += pellet.points
            
            # Check ghost collision
            if pygame.sprite.spritecollide(self.player, self.ghosts, False):
                self.lives -= 1
                if self.lives <= 0:
                    return "menu"
                self.player.rect.x = self.width // 2
                self.player.rect.y = self.height // 2
            
            # Check level complete
            if len(self.pellets) == 0:
                self.level += 1
                self.setup_maze()
            
            # Draw
            self.screen.fill((0, 0, 0))
            pygame.draw.line(self.screen, (0, 255, 0), (0, 60), (self.width, 60), 2)
            
            self.all_sprites.draw(self.screen)
            
            # Draw HUD
            score_text = self.font.render(f"SCORE: {self.score:05d}", True, (255, 255, 255))
            self.screen.blit(score_text, (20, 20))
            
            lives_text = self.font.render(f"LIVES: {self.lives}", True, (255, 255, 255))
            self.screen.blit(lives_text, (self.width - 200, 20))
            
            level_text = self.font.render(f"LVL: {self.level}", True, (255, 255, 255))
            self.screen.blit(level_text, (self.width // 2 - 50, 20))
            
            # Scanlines
            self.draw_scanline()
            
            # Webcam
            if success and img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_rgb = img_rgb.swapaxes(0, 1)
                frame = pygame.surfarray.make_surface(img_rgb)
                frame = pygame.transform.scale(frame, (240, 180))
                pygame.draw.rect(self.screen, (0, 255, 0), (self.width - 262, 78, 244, 184), 2)
                self.screen.blit(frame, (self.width - 260, 80))
            
            pygame.display.flip()
            clock.tick(60)
        
        return "quit"

# ============================================
# GAME 2: BRICK BREAKER / BREAKOUT
# ============================================

class Paddle(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height):
        super().__init__()
        self.screen_width = screen_width
        self.image = pygame.Surface((120, 20))
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect()
        self.rect.x = screen_width // 2 - 60
        self.rect.y = screen_height - 50
        self.speed = 12
        
    def move_left(self):
        self.rect.x -= self.speed
        if self.rect.x < 0:
            self.rect.x = 0
            
    def move_right(self):
        self.rect.x += self.speed
        if self.rect.x > self.screen_width - self.rect.width:
            self.rect.x = self.screen_width - self.rect.width

class Ball(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 255, 255), (8, 8), 8)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed_x = random.choice([-5, 5])
        self.speed_y = -6
        self.max_speed = 10
        
    def update(self, screen_width, screen_height):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        
        # Bounce off walls
        if self.rect.left <= 0 or self.rect.right >= screen_width:
            self.speed_x *= -1
        if self.rect.top <= 60:
            self.speed_y *= -1
            
    def bounce(self):
        self.speed_y *= -1

class Brick(pygame.sprite.Sprite):
    def __init__(self, x, y, color, points):
        super().__init__()
        self.image = pygame.Surface((70, 25))
        self.image.fill(color)
        pygame.draw.rect(self.image, (255, 255, 255), self.image.get_rect(), 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.points = points

class BreakoutGame:
    def __init__(self, screen, cap, detector, gesture_evaluator):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.cap = cap
        self.detector = detector
        self.gesture_evaluator = gesture_evaluator
        self.recent_gestures = collections.deque(maxlen=5)
        
        self.font = pygame.font.SysFont('courier', 36, bold=True)
        
        self.paddle = Paddle(self.width, self.height)
        self.ball = Ball(self.width // 2, self.height // 2)
        self.bricks = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        
        self.score = 0
        self.lives = 3
        self.level = 1
        
        self.create_bricks()
        self.all_sprites.add(self.paddle, self.ball)
        
    def create_bricks(self):
        self.bricks.empty()
        colors = [
            (255, 0, 0),    # Red - 50 points
            (255, 128, 0),  # Orange - 40 points
            (255, 255, 0),  # Yellow - 30 points
            (0, 255, 0),    # Green - 20 points
            (0, 255, 255),  # Cyan - 10 points
        ]
        
        start_x = 80
        start_y = 100
        
        for row in range(5):
            for col in range(20):
                x = start_x + col * 80
                y = start_y + row * 35
                points = 50 - row * 10
                brick = Brick(x, y, colors[row], points)
                self.bricks.add(brick)
                self.all_sprites.add(brick)
    
    def handle_gestures(self):
        success, img = self.cap.read()
        if success:
            img = cv2.flip(img, 1)
            img = self.detector.find_hands(img)
            lm_list, bbox, _ = self.detector.get_bbox_location(img)
            handedness_list = self.detector.get_handedness()

            if lm_list and handedness_list and bbox:
                gesture = self.gesture_evaluator.evaluate(lm_list, handedness_list[0], bbox)
                self.recent_gestures.append(gesture[0])

            if len(self.recent_gestures) == self.recent_gestures.maxlen:
                most_common = collections.Counter(self.recent_gestures).most_common(1)[0][0]
                
                if most_common == 2:  # Left
                    self.paddle.move_left()
                elif most_common == 4:  # Right
                    self.paddle.move_right()
                    
        return success, img if success else None
    
    def draw_scanline(self):
        for i in range(0, self.height, 4):
            pygame.draw.line(self.screen, (10, 10, 10), (0, i), (self.width, i), 1)
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
            
            success, img = self.handle_gestures()
            
            # Update
            self.ball.update(self.width, self.height)
            
            # Ball-paddle collision
            if self.ball.rect.colliderect(self.paddle.rect) and self.ball.speed_y > 0:
                self.ball.bounce()
                # Adjust angle based on hit position
                hit_pos = (self.ball.rect.centerx - self.paddle.rect.left) / self.paddle.rect.width
                self.ball.speed_x = (hit_pos - 0.5) * 12
            
            # Ball-brick collision
            brick_hits = pygame.sprite.spritecollide(self.ball, self.bricks, True)
            if brick_hits:
                self.ball.bounce()
                for brick in brick_hits:
                    self.score += brick.points
            
            # Ball fell off screen
            if self.ball.rect.top > self.height:
                self.lives -= 1
                if self.lives <= 0:
                    return "menu"
                self.ball = Ball(self.width // 2, self.height // 2)
                self.all_sprites.add(self.ball)
            
            # Level complete
            if len(self.bricks) == 0:
                self.level += 1
                self.create_bricks()
                self.ball = Ball(self.width // 2, self.height // 2)
            
            # Draw
            self.screen.fill((0, 0, 0))
            pygame.draw.line(self.screen, (0, 255, 0), (0, 60), (self.width, 60), 2)
            
            self.all_sprites.draw(self.screen)
            
            # HUD
            score_text = self.font.render(f"SCORE: {self.score:05d}", True, (255, 255, 255))
            self.screen.blit(score_text, (20, 20))
            
            lives_text = self.font.render(f"LIVES: {self.lives}", True, (255, 255, 255))
            self.screen.blit(lives_text, (self.width - 200, 20))
            
            level_text = self.font.render(f"LVL: {self.level}", True, (255, 255, 255))
            self.screen.blit(level_text, (self.width // 2 - 50, 20))
            
            # Scanlines
            self.draw_scanline()
            
            # Webcam
            if success and img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_rgb = img_rgb.swapaxes(0, 1)
                frame = pygame.surfarray.make_surface(img_rgb)
                frame = pygame.transform.scale(frame, (240, 180))
                pygame.draw.rect(self.screen, (0, 255, 0), (self.width - 262, 78, 244, 184), 2)
                self.screen.blit(frame, (self.width - 260, 80))
            
            pygame.display.flip()
            clock.tick(60)
        
        return "quit"

# ============================================
# GAME 3: SPACE INVADERS
# ============================================

class SpacePlayer(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.image = pygame.Surface((50, 40), pygame.SRCALPHA)
        self.draw_player_ship()
        self.rect = self.image.get_rect()
        self.rect.x = (self.screen_width - self.rect.width) // 2
        self.rect.y = self.screen_height - self.rect.height - 20
        self.speed = 8
        self.bullet_cooldown = 400
        self.last_shot_time = 0

    def draw_player_ship(self):
        green = (0, 255, 0)
        pygame.draw.rect(self.image, green, (22, 0, 6, 8))
        pygame.draw.rect(self.image, green, (18, 8, 14, 8))
        pygame.draw.rect(self.image, green, (10, 16, 30, 8))
        pygame.draw.rect(self.image, green, (0, 24, 50, 16))

    def move_left(self):
        self.rect.x -= self.speed
        if self.rect.x < 0:
            self.rect.x = 0

    def move_right(self):
        self.rect.x += self.speed
        if self.rect.x > self.screen_width - self.rect.width:
            self.rect.x = self.screen_width - self.rect.width

    def shoot(self, all_sprites, bullets):
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > self.bullet_cooldown:
            self.last_shot_time = now
            bullet = SpaceBullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)

class SpaceAlien(pygame.sprite.Sprite):
    def __init__(self, x, y, alien_type, points):
        super().__init__()
        self.type = alien_type
        self.points = points
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_speed = 500
        
        if self.type == "red":
            self.color = (255, 50, 50)
        elif self.type == "yellow":
            self.color = (255, 255, 0)
        else:
            self.color = (0, 255, 0)
        
        self.image = pygame.Surface((44, 32), pygame.SRCALPHA)
        self.draw_alien()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def draw_alien(self):
        self.image.fill((0, 0, 0, 0))
        if self.animation_frame == 0:
            self.draw_alien_frame1()
        else:
            self.draw_alien_frame2()

    def draw_alien_frame1(self):
        pygame.draw.rect(self.image, self.color, (8, 0, 4, 4))
        pygame.draw.rect(self.image, self.color, (32, 0, 4, 4))
        pygame.draw.rect(self.image, self.color, (12, 4, 4, 4))
        pygame.draw.rect(self.image, self.color, (28, 4, 4, 4))
        pygame.draw.rect(self.image, self.color, (8, 8, 28, 12))
        pygame.draw.rect(self.image, self.color, (8, 20, 4, 8))
        pygame.draw.rect(self.image, self.color, (16, 20, 4, 4))
        pygame.draw.rect(self.image, self.color, (24, 20, 4, 4))
        pygame.draw.rect(self.image, self.color, (32, 20, 4, 8))

    def draw_alien_frame2(self):
        pygame.draw.rect(self.image, self.color, (8, 0, 4, 4))
        pygame.draw.rect(self.image, self.color, (32, 0, 4, 4))
        pygame.draw.rect(self.image, self.color, (12, 4, 4, 4))
        pygame.draw.rect(self.image, self.color, (28, 4, 4, 4))
        pygame.draw.rect(self.image, self.color, (8, 8, 28, 12))
        pygame.draw.rect(self.image, self.color, (4, 20, 4, 8))
        pygame.draw.rect(self.image, self.color, (16, 24, 4, 4))
        pygame.draw.rect(self.image, self.color, (24, 24, 4, 4))
        pygame.draw.rect(self.image, self.color, (36, 20, 4, 8))

    def update(self):
        self.animation_timer += 16
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.animation_frame = 1 - self.animation_frame
            self.draw_alien()

class SpaceBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([3, 12])
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.y = y
        self.speed = -12

    def update(self):
        self.rect.y += self.speed
        if self.rect.y < 0:
            self.kill()

class AlienBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, screen_height, color):
        super().__init__()
        self.screen_height = screen_height
        self.image = pygame.Surface([3, 12])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.y = y
        self.speed = 8

    def update(self):
        self.rect.y += self.speed
        if self.rect.y > self.screen_height:
            self.kill()

class PlatformBlock(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([8, 8])
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Platform(pygame.sprite.Group):
    def __init__(self, x, y):
        super().__init__()
        pattern = [
            [0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1],
            [1,1,1,1,1,0,0,0,0,0,0,1,1,1,1,1],
            [1,1,1,1,0,0,0,0,0,0,0,0,1,1,1,1],
        ]
        for row_idx, row in enumerate(pattern):
            for col_idx, cell in enumerate(row):
                if cell == 1:
                    block = PlatformBlock(x + col_idx * 8, y + row_idx * 8)
                    self.add(block)

class SpaceInvadersGame:
    def __init__(self, screen, cap, detector, gesture_evaluator):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.cap = cap
        self.detector = detector
        self.gesture_evaluator = gesture_evaluator
        self.recent_gestures = collections.deque(maxlen=5)
        
        self.font = pygame.font.SysFont('courier', 36, bold=True)
        self.title_font = pygame.font.SysFont('courier', 72, bold=True)
        
        self.player = SpacePlayer(self.width, self.height)
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        
        self.aliens = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.alien_bullets = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        
        self.create_platforms()
        
        self.alien_direction = 1
        self.alien_speed = 1.5
        self.alien_move_down_amount = 16
        self.score = 0
        self.level = 1
        self.lives = 3
        
        self.alien_shoot_cooldown = 800
        self.last_alien_shot_time = 0
        
        self.create_aliens()
    
    def create_platforms(self):
        num_platforms = 4
        platform_width = 16 * 8
        total_platforms_width = num_platforms * platform_width
        spacing = (self.width - total_platforms_width) / (num_platforms + 1)
        for i in range(num_platforms):
            platform_x = spacing * (i + 1) + i * platform_width
            platform = Platform(platform_x, self.height - 180)
            self.platforms.add(platform)
            self.all_sprites.add(platform)
    
    def create_aliens(self):
        start_x = (self.width - (10 * 60)) // 2
        for row in range(5):
            for col in range(11):
                if row == 0:
                    alien_type = "red"
                    points = 30
                elif row in [1, 2]:
                    alien_type = "yellow"
                    points = 20
                else:
                    alien_type = "green"
                    points = 10
                alien = SpaceAlien(start_x + col * 60, 80 + row * 50, alien_type, points)
                self.all_sprites.add(alien)
                self.aliens.add(alien)
    
    def handle_gestures(self):
        success, img = self.cap.read()
        if success:
            img = cv2.flip(img, 1)
            img = self.detector.find_hands(img)
            lm_list, bbox, _ = self.detector.get_bbox_location(img)
            handedness_list = self.detector.get_handedness()

            if lm_list and handedness_list and bbox:
                gesture = self.gesture_evaluator.evaluate(lm_list, handedness_list[0], bbox)
                self.recent_gestures.append(gesture[0])

            if len(self.recent_gestures) == self.recent_gestures.maxlen:
                most_common = collections.Counter(self.recent_gestures).most_common(1)[0][0]
                
                if most_common == 2:  # Left
                    self.player.move_left()
                elif most_common == 4:  # Right
                    self.player.move_right()
                elif most_common == 1:  # Shoot
                    self.player.shoot(self.all_sprites, self.bullets)
                    
        return success, img if success else None
    
    def draw_scanline(self):
        for i in range(0, self.height, 4):
            pygame.draw.line(self.screen, (10, 10, 10), (0, i), (self.width, i), 1)
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
            
            success, img = self.handle_gestures()
            
            # Update
            self.all_sprites.update()
            
            # Alien movement - check boundaries FIRST before moving
            move_down = False
            for alien in self.aliens:
                if alien.rect.right >= self.width - 20 and self.alien_direction > 0:
                    move_down = True
                    break
                if alien.rect.left <= 20 and self.alien_direction < 0:
                    move_down = True
                    break

            if move_down:
                self.alien_direction *= -1
                for alien in self.aliens:
                    alien.rect.y += self.alien_move_down_amount
            else:
                for alien in self.aliens:
                    alien.rect.x += self.alien_speed * self.alien_direction
            
            # Collision detection
            bullet_alien_collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)
            for bullet, aliens_hit in bullet_alien_collisions.items():
                for alien in aliens_hit:
                    self.score += alien.points
            
            pygame.sprite.groupcollide(self.alien_bullets, self.platforms, True, True)
            pygame.sprite.groupcollide(self.bullets, self.platforms, True, True)
            pygame.sprite.groupcollide(self.aliens, self.platforms, False, True)
            
            player_alien_collisions = pygame.sprite.spritecollide(self.player, self.aliens, False)
            if player_alien_collisions:
                self.lives -= 1
                if self.lives <= 0:
                    return "menu"
                self.player.rect.x = self.width // 2
            
            for alien in self.aliens:
                if alien.rect.bottom >= self.player.rect.top:
                    return "menu"
            
            if not self.aliens:
                self.level += 1
                self.alien_speed += 0.3
                self.create_aliens()
                self.screen.fill((0, 0, 0))
                level_text = self.title_font.render(f"LEVEL {self.level}", True, (0, 255, 0))
                self.screen.blit(level_text, (self.width // 2 - level_text.get_width() // 2, 
                                             self.height // 2 - level_text.get_height() // 2))
                pygame.display.update()
                pygame.time.wait(2000)
            
            # Alien shooting
            now = pygame.time.get_ticks()
            if now - self.last_alien_shot_time > self.alien_shoot_cooldown and self.aliens:
                self.last_alien_shot_time = now
                random_alien = random.choice(self.aliens.sprites())
                alien_bullet = AlienBullet(random_alien.rect.centerx, random_alien.rect.bottom,
                                          self.height, random_alien.color)
                self.all_sprites.add(alien_bullet)
                self.alien_bullets.add(alien_bullet)
            
            # Player-alien bullet collision
            player_hit = pygame.sprite.spritecollide(self.player, self.alien_bullets, True)
            if player_hit:
                self.lives -= 1
                if self.lives <= 0:
                    return "menu"
            
            # Draw
            self.screen.fill((0, 0, 0))
            pygame.draw.line(self.screen, (0, 255, 0), (0, 60), (self.width, 60), 2)
            
            self.all_sprites.draw(self.screen)
            
            # HUD
            score_text = self.font.render(f"SCORE: {self.score:05d}", True, (255, 255, 255))
            self.screen.blit(score_text, (20, 20))
            
            level_text = self.font.render(f"LEVEL: {self.level}", True, (255, 255, 255))
            self.screen.blit(level_text, (self.width // 2 - level_text.get_width() // 2, 20))
            
            lives_text = self.font.render(f"LIVES: {self.lives}", True, (255, 255, 255))
            self.screen.blit(lives_text, (self.width - 200, 20))
            
            # Scanlines
            self.draw_scanline()
            
            # Webcam
            if success and img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_rgb = img_rgb.swapaxes(0, 1)
                frame = pygame.surfarray.make_surface(img_rgb)
                frame = pygame.transform.scale(frame, (320, 240))
                cam_x = self.width - 340
                cam_y = 80
                pygame.draw.rect(self.screen, (0, 255, 0), (cam_x - 2, cam_y - 2, 324, 244), 2)
                self.screen.blit(frame, (cam_x, cam_y))
            
            pygame.display.flip()
            clock.tick(60)
        
        return "quit"

# ============================================
# MAIN MENU
# ============================================

class GameMenu:
    def __init__(self):
        pygame.init()
        
        self.info = pygame.display.Info()
        self.width = self.info.current_w
        self.height = self.info.current_h
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        pygame.display.set_caption("Retro Gesture Games")
        
        self.title_font = pygame.font.SysFont('courier', 72, bold=True)
        self.menu_font = pygame.font.SysFont('courier', 48, bold=True)
        self.font = pygame.font.SysFont('courier', 36, bold=True)
        
        self.cap = cv2.VideoCapture(0)
        self.detector = hand_detector(max_hands=1, track_con=0.8)
        self.gesture_evaluator = GestureEvaluator("models/gesture_model.pkl")
        
        self.menu_items = [
            "1. PAC-MAN MAZE",
            "2. BRICK BREAKER",
            "3. SPACE INVADERS",
            "Q. QUIT"
        ]
        self.selected = 0
    
    def draw_scanline(self):
        for i in range(0, self.height, 4):
            pygame.draw.line(self.screen, (10, 10, 10), (0, i), (self.width, i), 1)
        
    def draw_menu(self):
        self.screen.fill((0, 0, 0))
        
        # Title with retro effect
        title = "RETRO GAMES"
        title_surf = self.title_font.render(title, True, (0, 255, 0))
        title_rect = title_surf.get_rect(center=(self.width // 2, 150))
        
        # Shadow effect
        shadow_surf = self.title_font.render(title, True, (0, 100, 0))
        self.screen.blit(shadow_surf, (title_rect.x + 4, title_rect.y + 4))
        self.screen.blit(title_surf, title_rect)
        
        # Subtitle
        subtitle = "GESTURE CONTROLLED"
        sub_surf = self.font.render(subtitle, True, (255, 255, 0))
        sub_rect = sub_surf.get_rect(center=(self.width // 2, 220))
        self.screen.blit(sub_surf, sub_rect)
        
        # Menu items
        y_start = 320
        for i, item in enumerate(self.menu_items):
            color = (255, 255, 0) if i == self.selected else (255, 255, 255)
            text_surf = self.menu_font.render(item, True, color)
            text_rect = text_surf.get_rect(center=(self.width // 2, y_start + i * 80))
            
            if i == self.selected:
                pygame.draw.rect(self.screen, (0, 255, 0), 
                               (text_rect.x - 20, text_rect.y - 5, 
                                text_rect.width + 40, text_rect.height + 10), 3)
            
            self.screen.blit(text_surf, text_rect)
        
        # Instructions
        instructions = [
            "CONTROLS:",
            "GESTURE 1 = UP",
            "GESTURE 2 = LEFT", 
            "GESTURE 3 = DOWN",
            "GESTURE 4 = RIGHT"
        ]
        
        y_pos = self.height - 250
        for i, inst in enumerate(instructions):
            color = (0, 255, 0) if i == 0 else (255, 255, 255)
            inst_surf = self.font.render(inst, True, color)
            self.screen.blit(inst_surf, (50, y_pos + i * 40))
        
        # Border
        pygame.draw.rect(self.screen, (0, 255, 0), (10, 10, self.width - 20, self.height - 20), 5)
        
        # Scanlines
        self.draw_scanline()
        
        pygame.display.flip()
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    elif event.key == pygame.K_1:
                        result = PacManGame(self.screen, self.cap, self.detector, 
                                          self.gesture_evaluator).run()
                        if result == "quit":
                            running = False
                    elif event.key == pygame.K_2:
                        result = BreakoutGame(self.screen, self.cap, self.detector, 
                                            self.gesture_evaluator).run()
                        if result == "quit":
                            running = False
                    elif event.key == pygame.K_3:
                        result = SpaceInvadersGame(self.screen, self.cap, self.detector, 
                                                  self.gesture_evaluator).run()
                        if result == "quit":
                            running = False
                    elif event.key == pygame.K_UP:
                        self.selected = (self.selected - 1) % len(self.menu_items)
                    elif event.key == pygame.K_DOWN:
                        self.selected = (self.selected + 1) % len(self.menu_items)
                    elif event.key == pygame.K_RETURN:
                        if self.selected == 0:
                            result = PacManGame(self.screen, self.cap, self.detector, 
                                              self.gesture_evaluator).run()
                            if result == "quit":
                                running = False
                        elif self.selected == 1:
                            result = BreakoutGame(self.screen, self.cap, self.detector, 
                                                self.gesture_evaluator).run()
                            if result == "quit":
                                running = False
                        elif self.selected == 2:
                            result = SpaceInvadersGame(self.screen, self.cap, self.detector, 
                                                      self.gesture_evaluator).run()
                            if result == "quit":
                                running = False
                        elif self.selected == 3:
                            running = False
            
            self.draw_menu()
            clock.tick(60)
        
        self.cap.release()
        pygame.quit()

if __name__ == "__main__":
    menu = GameMenu()
    menu.run()
