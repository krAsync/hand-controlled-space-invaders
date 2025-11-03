import pygame
import random
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
        self.gesture_evaluator = GestureEvaluator("models/gesture_model_knn.pkl")

        self.snake = Snake(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.SNAKE_BLOCK)
        self.food = Food(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.SNAKE_BLOCK)
        self.clock = pygame.time.Clock()

    def message(self, msg, color):
        mesg = self.FONT.render(msg, True, color)
        self.SCREEN.blit(mesg, [self.SCREEN_WIDTH / 6, self.SCREEN_HEIGHT / 3])

    def run(self):
        game_over = False
        game_close = False

        while not game_over:
            while game_close:
                self.SCREEN.fill(self.BLACK)
                self.message("You Lost! Press Q-Quit or C-Play Again", self.RED)
                pygame.display.update()

                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q:
                            game_over = True
                            game_close = False
                        if event.key == pygame.K_c:
                            self.snake = Snake(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.SNAKE_BLOCK)
                            self.food = Food(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.SNAKE_BLOCK)
                            game_close = False

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
                    print(f"Detected gesture: {gesture}")
                    x, y, w, h = bbox
                    cv2.putText(img, str(gesture[0]), (x + w + 10, y + 20), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                if gesture[0] == 1: # Up
                    if self.snake.y1_change != self.SNAKE_BLOCK:
                        self.snake.y1_change = -self.SNAKE_BLOCK
                        self.snake.x1_change = 0
                elif gesture[0] == 2: # Left
                    if self.snake.x1_change != self.SNAKE_BLOCK:
                        self.snake.x1_change = -self.SNAKE_BLOCK
                        self.snake.y1_change = 0
                elif gesture[0] == 3: # Down
                    if self.snake.y1_change != -self.SNAKE_BLOCK:
                        self.snake.y1_change = self.SNAKE_BLOCK
                        self.snake.x1_change = 0
                elif gesture[0] == 4: # Right
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

        self.cap.release()
        pygame.quit()
        quit()

if __name__ == "__main__":
    game = Game()
    game.run()
