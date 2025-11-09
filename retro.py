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
    def __init__(self, x, y, cell_width=60, cell_height=50):
        super().__init__()
        self.size = 30
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

        # Snap to grid center
        self.target_x = x
        self.target_y = y
        self.rect.x = x
        self.rect.y = y

        self.direction = 4  # 4=right
        self.next_direction = 4  # Queued direction
        self.speed = 180  # pixels per second (slower for better control)
        self.mouth_open = 0
        self.mouth_direction = 1
        self.is_moving = False
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

    def can_move_to(self, target_x, target_y, walls):
        """Check if Pac-Man can move to the target position without colliding"""
        old_x, old_y = self.rect.x, self.rect.y
        self.rect.x = target_x
        self.rect.y = target_y
        collision = pygame.sprite.spritecollide(self, walls, False)
        self.rect.x, self.rect.y = old_x, old_y
        return not collision

    def move(self, walls, dt):
        # Check if we're close enough to target (grid-aligned)
        threshold = 2
        at_target = (abs(self.rect.x - self.target_x) < threshold and
                    abs(self.rect.y - self.target_y) < threshold)

        if at_target:
            # Snap exactly to target
            self.rect.x = self.target_x
            self.rect.y = self.target_y
            self.is_moving = False

            # Try to change direction if queued
            if self.next_direction != self.direction:
                new_target_x, new_target_y = self.get_next_target(self.next_direction)
                if self.can_move_to(new_target_x, new_target_y, walls):
                    self.direction = self.next_direction
                    self.target_x = new_target_x
                    self.target_y = new_target_y
                    self.is_moving = True

            # If not changing direction or can't change, continue in current direction
            if not self.is_moving:
                new_target_x, new_target_y = self.get_next_target(self.direction)
                if self.can_move_to(new_target_x, new_target_y, walls):
                    self.target_x = new_target_x
                    self.target_y = new_target_y
                    self.is_moving = True

        # Move towards target
        if self.is_moving or not at_target:
            dx = self.target_x - self.rect.x
            dy = self.target_y - self.rect.y
            distance = math.sqrt(dx*dx + dy*dy)

            if distance > 0:
                movement = min(self.speed * dt, distance)
                self.rect.x += (dx / distance) * movement
                self.rect.y += (dy / distance) * movement

    def get_next_target(self, direction):
        """Get the next grid-aligned target position based on direction"""
        if direction == 4:  # Right
            return self.rect.x + self.cell_width, self.rect.y
        elif direction == 3:  # Down
            return self.rect.x, self.rect.y + self.cell_height
        elif direction == 2:  # Left
            return self.rect.x - self.cell_width, self.rect.y
        elif direction == 1:  # Up
            return self.rect.x, self.rect.y - self.cell_height
        return self.rect.x, self.rect.y

class Ghost(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.size = 30
        self.color = color
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 120  # pixels per second (was 2 pixels per frame at 60fps)
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
        
    def update(self, walls, dt):
        self.change_direction_timer += dt
        if self.change_direction_timer > 1.0:  # 1 second
            self.direction = random.randint(1, 4)
            self.change_direction_timer = 0

        old_x, old_y = self.rect.x, self.rect.y

        movement = self.speed * dt

        if self.direction == 4:  # Right
            self.rect.x += movement
        elif self.direction == 3:  # Down
            self.rect.y += movement
        elif self.direction == 2:  # Left
            self.rect.x -= movement
        elif self.direction == 1:  # Up
            self.rect.y -= movement

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

        self.cell_width = 60
        self.cell_height = 50

        self.player = None
        self.ghosts = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.pellets = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()

        self.score = 0
        self.level = 1
        self.lives = 3
        self.spawn_x = 0
        self.spawn_y = 0

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

        offset_x = (self.width - len(maze[0]) * self.cell_width) // 2
        offset_y = 100

        for row_idx, row in enumerate(maze):
            for col_idx, cell in enumerate(row):
                x = offset_x + col_idx * self.cell_width
                y = offset_y + row_idx * self.cell_height

                if cell == 1:
                    wall = Wall(x, y, self.cell_width, self.cell_height)
                    self.walls.add(wall)
                    self.all_sprites.add(wall)
                elif cell == 2:
                    pellet = Pellet(x + self.cell_width//2 - 3, y + self.cell_height//2 - 3, False)
                    self.pellets.add(pellet)
                    self.all_sprites.add(pellet)
                elif cell == 3:
                    pellet = Pellet(x + self.cell_width//2 - 8, y + self.cell_height//2 - 8, True)
                    self.pellets.add(pellet)
                    self.all_sprites.add(pellet)

        # Create player at grid-aligned position (centered in cell)
        self.spawn_x = offset_x + self.cell_width * 8 + (self.cell_width - 30) // 2
        self.spawn_y = offset_y + self.cell_height * 9 + (self.cell_height - 30) // 2
        self.player = PacPlayer(self.spawn_x, self.spawn_y, self.cell_width, self.cell_height)
        self.all_sprites.add(self.player)

        # Create ghosts in valid positions (not in walls)
        colors = [(255, 0, 0), (255, 184, 255), (0, 255, 255), (255, 184, 82)]
        ghost_positions = [(6, 6), (9, 6), (6, 7), (9, 7)]  # All valid path cells
        for i, color in enumerate(colors):
            col, row = ghost_positions[i]
            ghost = Ghost(offset_x + self.cell_width * col,
                         offset_y + self.cell_height * row, color)
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
                # Queue the direction change instead of changing immediately
                if most_common in [1, 2, 3, 4]:
                    self.player.next_direction = most_common

        return success, img if success else None
    
    def draw_scanline(self):
        for i in range(0, self.height, 4):
            pygame.draw.line(self.screen, (10, 10, 10), (0, i), (self.width, i), 1)
    
    def run(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            dt = clock.tick(60) / 1000.0  # Delta time in seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"

            success, img = self.handle_gestures()

            # Update
            self.player.move(self.walls, dt)
            self.player.update_animation()
            for ghost in self.ghosts:
                ghost.update(self.walls, dt)

            # Check pellet collection
            pellets_hit = pygame.sprite.spritecollide(self.player, self.pellets, True)
            for pellet in pellets_hit:
                self.score += pellet.points

            # Check ghost collision
            if pygame.sprite.spritecollide(self.player, self.ghosts, False):
                self.lives -= 1
                if self.lives <= 0:
                    return "menu"
                # Respawn at original spawn position with grid alignment
                self.player.rect.x = self.spawn_x
                self.player.rect.y = self.spawn_y
                self.player.target_x = self.spawn_x
                self.player.target_y = self.spawn_y
                self.player.is_moving = False

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

            # Webcam - bigger and centered on right side
            if success and img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_rgb = img_rgb.swapaxes(0, 1)
                frame = pygame.surfarray.make_surface(img_rgb)
                cam_width, cam_height = 400, 300
                frame = pygame.transform.scale(frame, (cam_width, cam_height))
                cam_x = self.width - cam_width - 20
                cam_y = (self.height - cam_height) // 2
                pygame.draw.rect(self.screen, (0, 255, 0), (cam_x - 2, cam_y - 2, cam_width + 4, cam_height + 4), 2)
                self.screen.blit(frame, (cam_x, cam_y))

            pygame.display.flip()

        return "quit"

# ============================================
# GAME 2: BRICK BREAKER / BREAKOUT
# ============================================

class Paddle(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.width = 120
        self.height = 20
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect()
        self.rect.x = screen_width // 2 - self.width // 2
        self.rect.y = screen_height - 50
        self.speed = 720  # pixels per second (was 12 pixels per frame at 60fps)

    def enlarge(self):
        old_center = self.rect.centerx
        self.width = min(250, self.width + 50)  # Max width of 250
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect()
        self.rect.centerx = old_center
        self.rect.y = self.screen_height - 50

    def move_left(self, dt):
        self.rect.x -= self.speed * dt
        if self.rect.x < 0:
            self.rect.x = 0

    def move_right(self, dt):
        self.rect.x += self.speed * dt
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
        self.speed_x = random.choice([-300, 300])  # pixels per second (was -5/5 at 60fps)
        self.speed_y = -360  # pixels per second (was -6 at 60fps)
        self.max_speed = 600  # pixels per second (was 10 at 60fps)

    def make_faster(self):
        # Increase speed by 2
        if abs(self.speed_x) < self.max_speed:
            self.speed_x *= 1.5
        if abs(self.speed_y) < self.max_speed:
            self.speed_y *= 1.5

    def update(self, screen_width, screen_height, dt):
        self.rect.x += self.speed_x * dt
        self.rect.y += self.speed_y * dt

        # Bounce off walls and clamp position
        if self.rect.left <= 0:
            self.speed_x = abs(self.speed_x)
            self.rect.left = 0
        elif self.rect.right >= screen_width:
            self.speed_x = -abs(self.speed_x)
            self.rect.right = screen_width

        if self.rect.top <= 60:
            self.speed_y = abs(self.speed_y)
            self.rect.top = 60

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

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, power_type):
        super().__init__()
        self.power_type = power_type  # 'multi_ball', 'double_balls', 'bigger_paddle', 'faster_ball'
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)

        # Different colors for different power-ups
        if power_type == 'multi_ball':
            color = (255, 100, 255)  # Magenta - spawn 2 balls
            symbol = "MB"
        elif power_type == 'double_balls':
            color = (100, 255, 255)  # Cyan - double all balls
            symbol = "x2"
        elif power_type == 'bigger_paddle':
            color = (255, 255, 100)  # Yellow - bigger paddle
            symbol = "BP"
        else:  # faster_ball
            color = (255, 100, 100)  # Red - faster ball
            symbol = "FB"

        # Draw power-up
        pygame.draw.circle(self.image, color, (15, 15), 15)
        pygame.draw.circle(self.image, (0, 0, 0), (15, 15), 15, 2)

        # Draw symbol
        font = pygame.font.SysFont('courier', 14, bold=True)
        text = font.render(symbol, True, (0, 0, 0))
        text_rect = text.get_rect(center=(15, 15))
        self.image.blit(text, text_rect)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed_y = 180  # pixels per second (was 3 at 60fps)

    def update(self, screen_height, dt):
        self.rect.y += self.speed_y * dt
        if self.rect.top > screen_height:
            self.kill()

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
        self.balls = pygame.sprite.Group()
        self.bricks = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()

        # Create initial ball
        initial_ball = Ball(self.width // 2, self.height // 2)
        self.balls.add(initial_ball)
        self.all_sprites.add(initial_ball)

        self.score = 0
        self.lives = 1  # Changed to 1 life
        self.level = 1

        self.create_bricks()
        self.all_sprites.add(self.paddle)
        
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
    
    def handle_gestures(self, dt):
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
                    self.paddle.move_left(dt)
                elif most_common == 4:  # Right
                    self.paddle.move_right(dt)

        return success, img if success else None
    
    def draw_scanline(self):
        for i in range(0, self.height, 4):
            pygame.draw.line(self.screen, (10, 10, 10), (0, i), (self.width, i), 1)
    
    def run(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            dt = clock.tick(60) / 1000.0  # Delta time in seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"

            success, img = self.handle_gestures(dt)

            # Update balls
            for ball in self.balls:
                ball.update(self.width, self.height, dt)

                # Ball-paddle collision
                if ball.rect.colliderect(self.paddle.rect) and ball.speed_y > 0:
                    ball.bounce()
                    # Adjust angle based on hit position
                    hit_pos = (ball.rect.centerx - self.paddle.rect.left) / self.paddle.rect.width
                    ball.speed_x = (hit_pos - 0.5) * 720  # pixels per second (was 12 at 60fps)

                # Ball-brick collision
                brick_hits = pygame.sprite.spritecollide(ball, self.bricks, True)
                if brick_hits:
                    ball.bounce()
                    for brick in brick_hits:
                        self.score += brick.points
                        # 30% chance to spawn a power-up
                        if random.random() < 0.3:
                            power_type = random.choice(['multi_ball', 'double_balls', 'bigger_paddle', 'faster_ball'])
                            powerup = PowerUp(brick.rect.centerx, brick.rect.centery, power_type)
                            self.powerups.add(powerup)
                            self.all_sprites.add(powerup)

                # Ball fell off screen
                if ball.rect.top > self.height:
                    ball.kill()
                    self.all_sprites.remove(ball)

            # Update power-ups
            for powerup in self.powerups:
                powerup.update(self.height, dt)

            # Power-up collision with paddle
            powerup_hits = pygame.sprite.spritecollide(self.paddle, self.powerups, True)
            for powerup in powerup_hits:
                if powerup.power_type == 'multi_ball':
                    # Spawn 2 new balls from paddle position
                    for i in range(2):
                        new_ball = Ball(self.paddle.rect.centerx, self.paddle.rect.top - 20)
                        new_ball.speed_x = random.choice([-300, 300])  # pixels per second
                        new_ball.speed_y = -360  # pixels per second
                        self.balls.add(new_ball)
                        self.all_sprites.add(new_ball)
                elif powerup.power_type == 'double_balls':
                    # Double all balls on screen
                    current_balls = list(self.balls)
                    for ball in current_balls:
                        new_ball = Ball(ball.rect.x, ball.rect.y)
                        new_ball.speed_x = -ball.speed_x  # Opposite direction
                        new_ball.speed_y = ball.speed_y
                        self.balls.add(new_ball)
                        self.all_sprites.add(new_ball)
                elif powerup.power_type == 'bigger_paddle':
                    # Make paddle larger
                    self.paddle.enlarge()
                elif powerup.power_type == 'faster_ball':
                    # Make all balls faster
                    for ball in self.balls:
                        ball.make_faster()

            # Check if no balls on screen - game over
            if len(self.balls) == 0:
                return "menu"

            # Level complete
            if len(self.bricks) == 0:
                self.level += 1
                self.create_bricks()
                # Reset balls
                self.balls.empty()
                new_ball = Ball(self.width // 2, self.height // 2)
                self.balls.add(new_ball)
                self.all_sprites.add(new_ball)

            # Draw
            self.screen.fill((0, 0, 0))
            pygame.draw.line(self.screen, (0, 255, 0), (0, 60), (self.width, 60), 2)

            self.all_sprites.draw(self.screen)

            # HUD
            score_text = self.font.render(f"SCORE: {self.score:05d}", True, (255, 255, 255))
            self.screen.blit(score_text, (20, 20))

            balls_text = self.font.render(f"BALLS: {len(self.balls)}", True, (255, 255, 255))
            self.screen.blit(balls_text, (self.width - 200, 20))

            level_text = self.font.render(f"LVL: {self.level}", True, (255, 255, 255))
            self.screen.blit(level_text, (self.width // 2 - 50, 20))

            # Scanlines
            self.draw_scanline()

            # Webcam - bigger and centered on right side
            if success and img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_rgb = img_rgb.swapaxes(0, 1)
                frame = pygame.surfarray.make_surface(img_rgb)
                cam_width, cam_height = 400, 300
                frame = pygame.transform.scale(frame, (cam_width, cam_height))
                cam_x = self.width - cam_width - 20
                cam_y = (self.height - cam_height) // 2
                pygame.draw.rect(self.screen, (0, 255, 0), (cam_x - 2, cam_y - 2, cam_width + 4, cam_height + 4), 2)
                self.screen.blit(frame, (cam_x, cam_y))

            pygame.display.flip()

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
        self.speed = 480  # pixels per second (was 8 at 60fps)
        self.bullet_cooldown = 0.4  # seconds (was 400ms)
        self.last_shot_time = 0

    def draw_player_ship(self):
        green = (0, 255, 0)
        pygame.draw.rect(self.image, green, (22, 0, 6, 8))
        pygame.draw.rect(self.image, green, (18, 8, 14, 8))
        pygame.draw.rect(self.image, green, (10, 16, 30, 8))
        pygame.draw.rect(self.image, green, (0, 24, 50, 16))

    def move_left(self, dt):
        self.rect.x -= self.speed * dt
        if self.rect.x < 0:
            self.rect.x = 0

    def move_right(self, dt):
        self.rect.x += self.speed * dt
        if self.rect.x > self.screen_width - self.rect.width:
            self.rect.x = self.screen_width - self.rect.width

    def shoot(self, all_sprites, bullets, current_time):
        if current_time - self.last_shot_time > self.bullet_cooldown:
            self.last_shot_time = current_time
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
        self.animation_speed = 0.5  # seconds (was 500ms)
        
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

    def update(self, dt):
        self.animation_timer += dt
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
        self.speed = -720  # pixels per second (was -12 at 60fps)

    def update(self, dt):
        self.rect.y += self.speed * dt
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
        self.speed = 480  # pixels per second (was 8 at 60fps)

    def update(self, dt):
        self.rect.y += self.speed * dt
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
        self.alien_speed = 90  # pixels per second (was 1.5 at 60fps)
        self.alien_move_down_amount = 16
        self.score = 0
        self.level = 1
        self.lives = 3

        self.alien_shoot_cooldown = 0.8  # seconds (was 800ms)
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
    
    def handle_gestures(self, dt, current_time):
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
                    self.player.move_left(dt)
                elif most_common == 4:  # Right
                    self.player.move_right(dt)
                elif most_common == 1:  # Shoot
                    self.player.shoot(self.all_sprites, self.bullets, current_time)

        return success, img if success else None
    
    def draw_scanline(self):
        for i in range(0, self.height, 4):
            pygame.draw.line(self.screen, (10, 10, 10), (0, i), (self.width, i), 1)
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        current_time = 0

        while running:
            dt = clock.tick(60) / 1000.0  # Delta time in seconds
            current_time += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"

            success, img = self.handle_gestures(dt, current_time)

            # Update sprites with delta time
            for sprite in self.all_sprites:
                if hasattr(sprite, 'update'):
                    # Check if update needs dt parameter
                    if isinstance(sprite, (SpaceAlien, SpaceBullet, AlienBullet)):
                        sprite.update(dt)

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
                    alien.rect.x += self.alien_speed * self.alien_direction * dt
            
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
                self.alien_speed += 18  # pixels per second (was 0.3 at 60fps)
                self.create_aliens()
                self.screen.fill((0, 0, 0))
                level_text = self.title_font.render(f"LEVEL {self.level}", True, (0, 255, 0))
                self.screen.blit(level_text, (self.width // 2 - level_text.get_width() // 2,
                                             self.height // 2 - level_text.get_height() // 2))
                pygame.display.update()
                pygame.time.wait(2000)

            # Alien shooting
            if current_time - self.last_alien_shot_time > self.alien_shoot_cooldown and self.aliens:
                self.last_alien_shot_time = current_time
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
            
            # Webcam - bigger and centered on right side
            if success and img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_rgb = img_rgb.swapaxes(0, 1)
                frame = pygame.surfarray.make_surface(img_rgb)
                cam_width, cam_height = 400, 300
                frame = pygame.transform.scale(frame, (cam_width, cam_height))
                cam_x = self.width - cam_width - 20
                cam_y = (self.height - cam_height) // 2
                pygame.draw.rect(self.screen, (0, 255, 0), (cam_x - 2, cam_y - 2, cam_width + 4, cam_height + 4), 2)
                self.screen.blit(frame, (cam_x, cam_y))

            pygame.display.flip()

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
