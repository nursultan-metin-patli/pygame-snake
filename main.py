import sys
import pygame
import random

# ------------------ CONSTANTS ------------------
WIDTH, HEIGHT = 800, 600
GRID = 25

GAME_MENU = 0
GAME_PLAYING = 1
GAME_OVER = 2

DIFFICULTIES = {
    "Easy":   {"start_delay": 220, "speedup": 5,  "min_delay": 120},
    "Medium": {"start_delay": 180, "speedup": 10, "min_delay": 80},
    "Hard":   {"start_delay": 140, "speedup": 15, "min_delay": 50},
}

# ------------------ INIT ------------------
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake")
clock = pygame.time.Clock()

# ------------------ FONTS ------------------
font_big = pygame.font.SysFont("arialblack", 72)
font_mid = pygame.font.SysFont("arial", 40)
font_small = pygame.font.SysFont("arial", 24)

# ------------------ ASSETS ------------------
background = pygame.Surface((WIDTH, HEIGHT))
background.fill((180, 220, 180))

pause_img = pygame.image.load("Pictures/pause.png").convert_alpha()
pause_img = pygame.transform.scale(pause_img, (300, 300))  # adjust size
pause_rect = pause_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))

snake_head_img = pygame.transform.scale(
    pygame.image.load("Pictures/snake_head.png").convert_alpha(), (GRID, GRID)
)
snake_head_hungry_img = pygame.transform.scale(
    pygame.image.load("Pictures/snake_head_hungry1.png").convert_alpha(), (GRID, GRID)
)
snake_body_img = pygame.transform.scale(
    pygame.image.load("Pictures/snake_body_main.png").convert_alpha(), (GRID, GRID)
)
snake_tail_img = pygame.transform.scale(
    pygame.image.load("Pictures/snake_tail.png").convert_alpha(), (GRID, GRID)
)
apple_img = pygame.transform.scale(
    pygame.image.load("Pictures/snake_bite.png").convert_alpha(), (GRID, GRID)
)

game_surface = pygame.Surface((WIDTH, HEIGHT))

pygame.mixer.music.load("Sounds/background.mp3")
pygame.mixer.music.set_volume(0.2)
pygame.mixer.music.play(-1)

eat_sound = pygame.mixer.Sound("Sounds/eat.wav")
hiss_sound = pygame.mixer.Sound("Sounds/hiss.wav")

# ------------------ HELPERS ------------------
def load_high_scores(filename="highest_score.txt"):
    scores = {"Easy": 0, "Medium": 0, "Hard": 0}

    try:
        with open(filename, "r") as f:
            for line in f:
                name, value = line.strip().split("=")
                scores[name] = int(value)
    except FileNotFoundError:
        pass

    return scores


def save_high_scores(scores, filename="highest_score.txt"):
    with open(filename, "w") as f:
        for diff, score in scores.items():
            f.write(f"{diff}={score}\n")

def update_high_score(difficulty, score):
    scores = load_high_scores()
    if score > scores[difficulty]:
        scores[difficulty] = score
        save_high_scores(scores)
    return scores

def random_apple(snake):
    while True:
        x = random.randrange(0, WIDTH, GRID)
        y = random.randrange(0, HEIGHT, GRID)
        rect = pygame.Rect(x, y, GRID, GRID)
        if not any(rect.colliderect(s) for s in snake):
            return rect

def get_angle(dx, dy):
    if dx > 0: return 90
    if dx < 0: return 270
    if dy > 0: return 0
    if dy < 0: return 180
    return 0

def head_angle_from_direction(direction):
    if direction[0]: return 0     # UP
    if direction[1]: return 180   # DOWN
    if direction[2]: return -90   # RIGHT
    if direction[3]: return 90    # LEFT
    return 0


# ------------------ GAME STATE ------------------
game_state = GAME_MENU
difficulty_names = list(DIFFICULTIES.keys())
difficulty_index = 0
difficulty = None

snake = []
direction = [0, 1, 0, 0]  # up, down, right, left
apple = None
move_delay = 200
last_move = 0
score = 0

shake_timer = 0
shake_duration = 150
shake_strength = 4

muted = False
was_hungry = False
paused = False

# ------------------ RESET ------------------
def start_game():
    global snake, direction, apple, move_delay, score, last_move, game_state
    center = (WIDTH // 2, HEIGHT // 2)
    head = pygame.Rect(center[0], center[1], GRID, GRID)
    body = pygame.Rect(head.x, head.y - GRID, GRID, GRID)
    tail = pygame.Rect(body.x, body.y - GRID, GRID, GRID)
    snake = [head, body, tail]

    direction[:] = [0, 1, 0, 0]
    apple = random_apple(snake)

    settings = DIFFICULTIES[difficulty]
    move_delay = settings["start_delay"]
    score = 0
    last_move = pygame.time.get_ticks()
    game_state = GAME_PLAYING

# ------------------ MAIN LOOP ------------------
while True:
    now = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            paused = not paused
            vol = 0 if paused else 0.2
            pygame.mixer.music.set_volume(vol)
            eat_sound.set_volume(0 if paused else 0.8)
            hiss_sound.set_volume(0 if paused else 0.3)

        if event.type == pygame.KEYDOWN and not paused:
            if event.key == pygame.K_m:
                muted = not muted
                vol = 0 if muted else 0.2
                pygame.mixer.music.set_volume(vol)
                eat_sound.set_volume(0 if muted else 0.8)
                hiss_sound.set_volume(0 if muted else 0.3)

            # -------- MENU --------
            if game_state == GAME_MENU:
                if event.key == pygame.K_UP:
                    difficulty_index = (difficulty_index - 1) % len(difficulty_names)
                elif event.key == pygame.K_DOWN:
                    difficulty_index = (difficulty_index + 1) % len(difficulty_names)
                elif event.key == pygame.K_RETURN:
                    difficulty = difficulty_names[difficulty_index]
                    start_game()

            # -------- PLAYING --------
            elif game_state == GAME_PLAYING:
                if event.key == pygame.K_LEFT and not direction[2]:
                    direction[:] = [0,0,0,1]
                elif event.key == pygame.K_RIGHT and not direction[3]:
                    direction[:] = [0,0,1,0]
                elif event.key == pygame.K_UP and not direction[1]:
                    direction[:] = [1,0,0,0]
                elif event.key == pygame.K_DOWN and not direction[0]:
                    direction[:] = [0,1,0,0]

            # -------- GAME OVER --------
            elif game_state == GAME_OVER:
                if event.key == pygame.K_r:
                    game_state = GAME_MENU
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    # ------------------ UPDATE ------------------
    if game_state == GAME_PLAYING and now - last_move >= move_delay and not paused:
        for i in range(len(snake)-1, 0, -1):
            snake[i].topleft = snake[i-1].topleft

        if direction[0]: snake[0].y -= GRID
        if direction[1]: snake[0].y += GRID
        if direction[2]: snake[0].x += GRID
        if direction[3]: snake[0].x -= GRID

        head = snake[0]

        if (
            head.left < 0 or head.right > WIDTH or
            head.top < 0 or head.bottom > HEIGHT or
            any(head.colliderect(s) for s in snake[1:])
        ):
            game_state = GAME_OVER

        if head.colliderect(apple):
            eat_sound.play()
            shake_timer = now
            snake.append(pygame.Rect(snake[-1].topleft, (GRID, GRID)))
            apple = random_apple(snake)
            settings = DIFFICULTIES[difficulty]
            move_delay = max(move_delay - settings["speedup"], settings["min_delay"])
            score += 1

        last_move = now

    # ------------------ DRAW ------------------

    offset_x = offset_y = 0
    if shake_timer and now - shake_timer < shake_duration:
        offset_x = random.randint(-shake_strength, shake_strength)
        offset_y = random.randint(-shake_strength, shake_strength)
    else:
        shake_timer = 0

    game_surface.blit(background, (0, 0))

    if game_state in (GAME_PLAYING, GAME_OVER):
        pause_txt = font_small.render(f"{"[P] Pause" if not paused else "[P] resume"}", True, (0, 0, 0))
        game_surface.blit(pause_txt, (670, 40))


    if game_state == GAME_MENU:
        title = font_big.render("SNAKE", True, (0,0,0))
        game_surface.blit(title, title.get_rect(center=(400,150)))
        for i, name in enumerate(difficulty_names):
            col = (200,0,0) if i == difficulty_index else (0,0,0)
            txt = font_mid.render(name, True, col)
            game_surface.blit(txt, txt.get_rect(center=(400,300+i*50)))
        hint = font_small.render("↑ ↓ Enter", True, (0,0,0))
        game_surface.blit(hint, hint.get_rect(center=(400,500)))

    elif game_state in (GAME_PLAYING, GAME_OVER):

        for i in range(1, len(snake)-1):
            dx = snake[i-1].x - snake[i].x
            dy = snake[i-1].y - snake[i].y
            game_surface.blit(pygame.transform.rotate(snake_body_img, get_angle(dx,dy)), snake[i])

        if len(snake) > 1:
            dx = snake[-2].x - snake[-1].x
            dy = snake[-2].y - snake[-1].y
            game_surface.blit(pygame.transform.rotate(snake_tail_img, get_angle(dx,dy)), snake[-1])

        dx = abs(snake[0].x - apple.x)//GRID
        dy = abs(snake[0].y - apple.y)//GRID
        hungry = dx <= 4 and dy <= 4

        if hungry and not was_hungry:
            hiss_sound.play()
        was_hungry = hungry

        base_head = snake_head_hungry_img if hungry else snake_head_img
        angle = head_angle_from_direction(direction)
        rotated_head = pygame.transform.rotate(base_head, angle)
        game_surface.blit(rotated_head, snake[0])

        score_txt = font_small.render(f"Score: {score}", True, (0,0,0))
        game_surface.blit(score_txt, (10,10))

        mute_txt = font_small.render(f"{"[M] Mute" if not muted else "[M] Unmute"}", True, (0, 0, 0))
        game_surface.blit(mute_txt, (670, 10))

        pause_txt = font_small.render(f"{"[P] Pause" if not paused else "[P] resume"}", True, (0, 0, 0))
        game_surface.blit(pause_txt, (670, 40))
        game_surface.blit(apple_img, apple)

        if game_state == GAME_OVER:
            over = font_big.render("GAME OVER", True, (200,0,0))
            game_surface.blit(over, over.get_rect(center=(400,260)))
            hint = font_small.render("R = Menu | ESC = Quit", True, (0,0,0))
            game_surface.blit(hint, hint.get_rect(center=(400,330)))
            high_scores = update_high_score(difficulty, score)
            current_high = high_scores[difficulty]
            txt = font_small.render(
                f"High Score ({difficulty}): {current_high}", True, (0, 0, 0)
            )
            game_surface.blit(txt, txt.get_rect(center=(WIDTH // 2, 380)))

    if paused and game_state == GAME_PLAYING:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))  # semi-transparent black
        game_surface.blit(overlay, (0, 0))

        game_surface.blit(pause_img, pause_rect)

    screen.blit(game_surface, (offset_x, offset_y))

    pygame.display.flip()
    clock.tick(60)
