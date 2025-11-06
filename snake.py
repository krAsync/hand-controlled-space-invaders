import collections
import pygame
import math
import random
import pygame

import json

LEADERBOARD_FILE = 'leaderboard.json'

def load_leaderboard():
    try:
        with open(LEADERBOARD_FILE, 'r') as file:
            leaderboard = json.load(file)
            if leaderboard is None:
                return []
            return leaderboard
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error loading leaderboard: {e}")
        return []

def save_leaderboard(leaderboard):
    with open(LEADERBOARD_FILE, 'w') as file:
        json.dump(leaderboard, file, indent=4)


import cv2
import numpy as np
from src.MediPipeHandsModule.HandTrackingModule import hand_detector
from src.MediPipeHandsModule.GestureEvaluator import GestureEvaluator

class Snake:
    def __init__(self, screen_width, screen_height, snake_block):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.snake_block = snake_block
        self.x1 = self.screen_width / 2
        self.y1 = self.screen_height / 2
        self.x1_change = 0
        self.y1_change = 0
        self.snake_list = []
        self.length_of_snake = 1

    def move(self):
        self.x1 += self.x1_change
        self.y1 += self.y1_change

    def grow(self):
        self.length_of_snake += 1

    def draw(self, screen, color):
        snake_head = [self.x1, self.y1]
        self.snake_list.append(snake_head)
        if len(self.snake_list) > self.length_of_snake:
            del self.snake_list[0]

        for x in self.snake_list:
            pygame.draw.rect(screen, color, [x[0], x[1], self.snake_block, self.snake_block])

    def has_collided_with_wall(self):
        return self.x1 >= self.screen_width or self.x1 < 0 or self.y1 >= self.screen_height or self.y1 < 0

    def has_collided_with_self(self):
        snake_head = [self.x1, self.y1]
        for x in self.snake_list[:-1]:
            if x == snake_head:
                return True
        return False

    def out_of_bounds(self):
        return self.x1 < 0 or self.x1 >= self.screen_width or self.y1 < 0 or self.y1 >= self.screen_height

class Food:
    def __init__(self, screen_width, screen_height, snake_block):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.snake_block = snake_block
        self.food_x = round(random.randrange(0, self.screen_width - self.snake_block) / 10.0) * 10.0
        self.food_y = round(random.randrange(0, self.screen_height - self.snake_block) / 10.0) * 10.0

    def draw(self, screen, color):
        pygame.draw.rect(screen, color, [self.food_x, self.food_y, self.snake_block, self.snake_block])

    def respawn(self):
        self.food_x = round(random.randrange(0, self.screen_width - self.snake_block) / 10.0) * 10.0
        self.food_y = round(random.randrange(0, self.screen_height - self.snake_block) / 10.0) * 10.0

class Game:
    def __init__(self):
        pygame.init()

        self.infoObject = pygame.display.Info()
        self.SCREEN_WIDTH = self.infoObject.current_w
        self.SCREEN_HEIGHT = self.infoObject.current_h
        self.SCREEN = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Snake Game")

        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.BLACK = (0, 0, 0)

        self.SNAKE_BLOCK = 10
        self.SNAKE_SPEED = 15

        self.FONT = pygame.font.SysFont(None, 50)

        self.cap = cv2.VideoCapture(0)
        self.detector = hand_detector(max_hands=1)
        self.gesture_evaluator = GestureEvaluator("models/gesture_model.pkl")

        self.snake = Snake(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.SNAKE_BLOCK)
        self.food = Food(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.SNAKE_BLOCK)
        self.clock = pygame.time.Clock()
        self.recent_gestures = collections.deque(maxlen=5)

    def message(self, msg, color):
        mesg = self.FONT.render(msg, True, color)
        self.SCREEN.blit(mesg, [self.SCREEN_WIDTH / 6, self.SCREEN_HEIGHT / 3])

    def draw_leaderboard(self, leaderboard, current_score):
        self.SCREEN.fill(self.BLACK)
        leaderboard_title = self.FONT.render("Leaderboard", True, self.WHITE)
        self.SCREEN.blit(leaderboard_title, (self.SCREEN_WIDTH / 2 - leaderboard_title.get_width() / 2, 50))

        score_text = self.FONT.render(f"Your Score: {current_score}", True, self.WHITE)
        self.SCREEN.blit(score_text, (self.SCREEN_WIDTH / 2 - score_text.get_width() / 2, 120))

        y_offset = 200
        for i, entry in enumerate(leaderboard):
            entry_text = self.FONT.render(f"{i+1}. {entry['name']} - {entry['score']}", True, self.WHITE)
            self.SCREEN.blit(entry_text, (self.SCREEN_WIDTH / 2 - entry_text.get_width() / 2, y_offset))
            y_offset += 40
        pygame.display.update()

        waiting_for_input = True
        while waiting_for_input:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.KEYDOWN:
                    waiting_for_input = False

    def game_loop(self):
        game_over = False
        game_close = False

        while not game_over:
            if game_close:
                return self.snake.length_of_snake - 1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        if self.snake.x1_change != self.SNAKE_BLOCK:
                            self.snake.x1_change = -self.SNAKE_BLOCK
                            self.snake.y1_change = 0
                    elif event.key == pygame.K_RIGHT:
                        if self.snake.x1_change != -self.SNAKE_BLOCK:
                            self.snake.x1_change = self.SNAKE_BLOCK
                            self.snake.y1_change = 0
                    elif event.key == pygame.K_UP:
                        if self.snake.y1_change != self.SNAKE_BLOCK:
                            self.snake.y1_change = -self.SNAKE_BLOCK
                            self.snake.x1_change = 0
                    elif event.key == pygame.K_DOWN:
                        if self.snake.y1_change != -self.SNAKE_BLOCK:
                            self.snake.y1_change = self.SNAKE_BLOCK
                            self.snake.x1_change = 0

            success, img = self.cap.read()
            img = cv2.flip(img, 1)
            img = self.detector.find_hands(img)
            lm_list, bbox, mid = self.detector.get_bbox_location(img)
            handedness_list = self.detector.get_handedness()

            if lm_list and handedness_list:
                if bbox:
                    gesture = self.gesture_evaluator.evaluate(lm_list, handedness_list[0], bbox)
                    self.recent_gestures.append(gesture[0])
                    x, y, w, h = bbox
                    cv2.putText(img, str(gesture[0]), (x + w + 10, y + 20), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

                if len(self.recent_gestures) == self.recent_gestures.maxlen:
                    most_common_gesture = collections.Counter(self.recent_gestures).most_common(1)[0][0]

                    if most_common_gesture == 1: # Up
                        if self.snake.y1_change != self.SNAKE_BLOCK:
                            self.snake.y1_change = -self.SNAKE_BLOCK
                            self.snake.x1_change = 0
                    elif most_common_gesture == 2: # Left
                        if self.snake.x1_change != self.SNAKE_BLOCK:
                            self.snake.x1_change = -self.SNAKE_BLOCK
                            self.snake.y1_change = 0
                    elif most_common_gesture == 3: # Down
                        if self.snake.y1_change != -self.SNAKE_BLOCK:
                            self.snake.y1_change = self.SNAKE_BLOCK
                            self.snake.x1_change = 0
                    elif most_common_gesture == 4: # Right
                        if self.snake.x1_change != -self.SNAKE_BLOCK:
                            self.snake.x1_change = self.SNAKE_BLOCK
                            self.snake.y1_change = 0

            if self.snake.has_collided_with_wall() or self.snake.has_collided_with_self():
                game_close = True

            if self.snake.out_of_bounds():
                game_close = True


            self.snake.move()
            self.SCREEN.fill(self.BLACK)

            if success:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = img.swapaxes(0, 1)
                frame = pygame.surfarray.make_surface(img)
                frame = pygame.transform.scale(frame, (400, 300))
                self.SCREEN.blit(frame, (self.SCREEN_WIDTH - 400, 0))

            self.food.draw(self.SCREEN, self.RED)
            self.snake.draw(self.SCREEN, self.GREEN)
            pygame.display.update()

            if self.snake.x1 == self.food.food_x and self.snake.y1 == self.food.food_y:
                self.food.respawn()
                self.snake.grow()

            self.clock.tick(self.SNAKE_SPEED)

    def run(self):
        while True:
            current_score = self.game_loop()
            
            leaderboard = load_leaderboard()

            if len(leaderboard) < 5 or current_score > leaderboard[-1]['score']:
                root = tk.Tk()
                root.withdraw()
                initials = simpledialog.askstring("Leaderboard", "Congratulations! You made it to the leaderboard!\nEnter your initials (max 3 characters):", parent=root)
                root.destroy()

                if initials and len(initials) <= 3:
                    leaderboard.append({'name': initials.upper(), 'score': current_score})
                    leaderboard.sort(key=lambda x: x['score'], reverse=True)
                    leaderboard = leaderboard[:5]
                    save_leaderboard(leaderboard)

            self.draw_leaderboard(leaderboard, current_score)

            self.SCREEN.fill(self.BLACK)
            self.message("Press 'P' to Play Again or 'Q' to Quit", self.WHITE)
            pygame.display.update()

            waiting_for_input = True
            while waiting_for_input:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.cap.release()
                        pygame.quit()
                        quit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q:
                            self.cap.release()
                            pygame.quit()
                            quit()

                        if event.key == pygame.K_p:
                            waiting_for_input = False

            self.snake = Snake(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.SNAKE_BLOCK)
            self.food = Food(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.SNAKE_BLOCK)

if __name__ == "__main__":
    game = Game()
    game.run()