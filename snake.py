import pygame
import random
import cv2
import numpy as np
from src.MediPipeHandsModule.HandTrackingModule import hand_detector

# Initialize Pygame
pygame.init()

# Camera setup
cap = cv2.VideoCapture(0)
detector = hand_detector()
CAM_WIDTH = 400  # Camera window width
CAM_HEIGHT = 300  # Camera window height

# Screen dimensions
infoObject = pygame.display.Info()
SCREEN_WIDTH = infoObject.current_w
SCREEN_HEIGHT = infoObject.current_h
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Snake Game")

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# Snake properties
SNAKE_BLOCK = 10
SNAKE_SPEED = 15

# Font for game over message
FONT = pygame.font.SysFont(None, 50)

def message(msg, color):
    mesg = FONT.render(msg, True, color)
    SCREEN.blit(mesg, [SCREEN_WIDTH / 6, SCREEN_HEIGHT / 3])

def gameLoop():
    game_over = False
    game_close = False

    x1 = SCREEN_WIDTH / 2
    y1 = SCREEN_HEIGHT / 2

    x1_change = 0
    y1_change = 0

    snake_list = []
    length_of_snake = 1

    food_x = round(random.randrange(0, SCREEN_WIDTH - SNAKE_BLOCK) / 10.0) * 10.0
    food_y = round(random.randrange(0, SCREEN_HEIGHT - SNAKE_BLOCK) / 10.0) * 10.0

    clock = pygame.time.Clock()

    while not game_over:
        success, img = cap.read()
        img = detector.find_hands(img)
        lm_list, bbox, mid = detector.get_bbox_location(img)
        while game_close:
            SCREEN.fill(BLACK)
            message("You Lost! Press Q-Quit or C-Play Again", RED)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        gameLoop()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x1_change = -SNAKE_BLOCK
                    y1_change = 0
                elif event.key == pygame.K_RIGHT:
                    x1_change = SNAKE_BLOCK
                    y1_change = 0
                elif event.key == pygame.K_UP:
                    y1_change = -SNAKE_BLOCK
                    x1_change = 0
                elif event.key == pygame.K_DOWN:
                    y1_change = SNAKE_BLOCK
                    x1_change = 0

        if x1 >= SCREEN_WIDTH or x1 < 0 or y1 >= SCREEN_HEIGHT or y1 < 0:
            game_close = True

        x1 += x1_change
        y1 += y1_change
        SCREEN.fill(BLACK)

        # Display camera feed
        if success:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = np.rot90(img)
            frame = pygame.surfarray.make_surface(img)
            frame = pygame.transform.scale(frame, (CAM_WIDTH, CAM_HEIGHT))
            SCREEN.blit(frame, (SCREEN_WIDTH - CAM_WIDTH, 0))

        pygame.draw.rect(SCREEN, RED, [food_x, food_y, SNAKE_BLOCK, SNAKE_BLOCK])

        snake_head = []
        snake_head.append(x1)
        snake_head.append(y1)
        snake_list.append(snake_head)
        if len(snake_list) > length_of_snake:
            del snake_list[0]

        for x in snake_list[:-1]:
            if x == snake_head:
                game_close = True

        for x in snake_list:
            pygame.draw.rect(SCREEN, GREEN, [x[0], x[1], SNAKE_BLOCK, SNAKE_BLOCK])

        pygame.display.update()

        if x1 == food_x and y1 == food_y:
            while True:
                food_x = round(random.randrange(0, SCREEN_WIDTH - SNAKE_BLOCK) / 10.0) * 10.0
                food_y = round(random.randrange(0, SCREEN_HEIGHT - SNAKE_BLOCK) / 10.0) * 10.0
                if not (food_x >= SCREEN_WIDTH - CAM_WIDTH and food_y <= CAM_HEIGHT):
                    break
            length_of_snake += 1

        clock.tick(SNAKE_SPEED)

    cap.release()
    pygame.quit()
    quit()

gameLoop()