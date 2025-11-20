import pygame
import sys
import subprocess
import random
import time
import math
import numpy as np
from collections import deque



# --------------- 패키지 설치 ---------------
for pkg in ["pygame", "numpy"]:
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])



# --------------- 게임 세팅 ---------------
pygame.init()

WINDOW_W, WINDOW_H = 960, 540
FPS = 60
TILE = 24 # 미로 타일 크기
RAND_MIN, RAND_MAX = 1, 5

WHITE = (255,255,255)
BLACK = (0,0,0)
TIMER_TIME = (40,40,40)
TIMER_BG = (80,200,120)
DOOR = (80,50,20)
MAZE_ROAD = (220,220,240)
MAZE_WALL = (50,50,50)
CAT_FOOD = (120,50,50)
DUST = (150,150,150)
FLY = (220,180,40)
WIND = (120,200,240)

PLAYER_SIZE = 28
CAT_SIZE = 28

BG_COLORS = {
    0: (20, 20, 20),
    1: (90, 20, 20),
    2: (60, 10, 60),
    3: (15, 30, 80),
    4: (240, 220, 140),
    5: (255, 200, 150),
    6: (255, 164, 164)
}
NARRATIVES = {
    1: "고영희가 날뛴다! 저걸 좀 잡아야겠어.",
    2: "고영희가 잔다..! 조용히, 건드리지 말고 몰래 방을 나가자.",
    3: "고영희가 밖으로 나갔어... 찾으러 가봐야겠어.",
    4: "고영희가 장난을 치기 시작했다. 피해서 버텨야 해.",
    5: "고영희가 이제 품에 안긴다. 조용히 재워주자.",
    6: "주인공은 감정을 모두 회복했다! 이제 고영희와 행복하게 지낼 수 있다!"
}
EMOTIONS = {
    1: "분노",
    2: "불안",
    3: "걱정",
    4: "이해",
    5: "감동",
}
FONT = pygame.font.Font("font/bdf/DOSSaemmul-16.bdf", 20)

pygame.display.set_caption("고영희 키우기")
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
clock = pygame.time.Clock()
dt = clock.tick(FPS) / 1000.0
cat_image = pygame.image.load("src/cat.png")
cat_sleeping_image = pygame.image.load("src/cat_sleeping.png")
player_front_white = pygame.image.load("src/player_front_white.png")
player_left_white = pygame.image.load("src/player_left_white.png")
player_right_white = pygame.image.load("src/player_right_white.png")
player_front_black = pygame.image.load("src/player_front_black.png")
player_left_black = pygame.image.load("src/player_left_black.png")
player_right_black = pygame.image.load("src/player_right_black.png")

class GameState:
    def __init__(self):
        self.day = 0
        self.emotions = []
        self.total_time = 30.0
        self.show_title = True
        self.show_narration = False
        self.show_end = False
gs = GameState()

class Entity:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size
        self.speed = 140

    def rect(self): # 충돌 감지용 사각형
        return pygame.Rect(int(self.x), int(self.y), self.size, self.size)



# --------------- 그리기 함수 ---------------
def draw_cat(surf, x, y, size, flip=False, sleeping=False):
    if sleeping: image_to_use = cat_sleeping_image
    else: image_to_use = cat_image
    scaled_cat = pygame.transform.scale(image_to_use, (size, size))
    if flip: scaled_cat = pygame.transform.flip(scaled_cat, True, False)
    surf.blit(scaled_cat, (x, y))

def draw_player(surf, x, y, size, direction='front', use_white=True):
    image = None
    if use_white:
        if direction == 'front': image = player_front_white
        elif direction == 'left': image = player_left_white
        elif direction == 'right': image = player_right_white
    else:
        if direction == 'front': image = player_front_black
        elif direction == 'left': image = player_left_black
        elif direction == 'right': image = player_right_black
    scaled_player = pygame.transform.scale(image, (size, size))
    surf.blit(scaled_player, (int(x), int(y)))

def draw_text_center(surf, text, y, color=WHITE):
    r = FONT.render(text, True, color)
    rect = r.get_rect(center=(WINDOW_W//2, y))
    surf.blit(r, rect)

def draw_text(surf, text, x, y, color=WHITE):
    surf.blit(FONT.render(text, True, color), (x,y))

def draw_timer_bar(elapsed, total):
    pygame.draw.rect(screen, TIMER_TIME, (20, 20, WINDOW_W-40, 16))
    pygame.draw.rect(screen, TIMER_BG, (20, 20, int((1 - elapsed/total) * (WINDOW_W - 40)), 16))



# --------------- 미션 함수 ---------------
def game_quit():
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT or ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            pygame.quit(); sys.exit()

        if gs.show_title:
            if ev.type == pygame.MOUSEBUTTONDOWN or ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                gs.show_title = False; gs.show_narration = True
        elif gs.show_narration:
            if ev.type == pygame.MOUSEBUTTONDOWN or ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                gs.show_narration = False

def mission_day1():
    player = Entity(WINDOW_W//2 - PLAYER_SIZE//2, WINDOW_H - PLAYER_SIZE - 40, PLAYER_SIZE)
    cat = Entity(random.randint(40, WINDOW_W-40-CAT_SIZE), random.randint(100, WINDOW_H-160), CAT_SIZE)
    cat.speed = 280
    gs.total_time = 20.0
    start = time.time()
    change_interval = random.randint(RAND_MIN, RAND_MAX) / 10.0 + 0.3
    last_change = time.time()
    cat_dir = [random.choice([-1,0,1]), random.choice([-1,0,1])]
    cat_facing_left = False
    player_direction = 'front'

    while True:
        game_quit()

        dt = clock.tick(FPS) / 1000.0
        elapsed = time.time() - start
        screen.fill(BG_COLORS[1])

        keys = pygame.key.get_pressed()
        move_x = move_y = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move_x = -1; player_direction = 'left'
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_x = 1; player_direction = 'right'
        if keys[pygame.K_UP] or keys[pygame.K_w]: move_y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: move_y = 1
        if not (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not(keys[pygame.K_RIGHT] or keys[pygame.K_d]) and move_y == 0: player_direction = 'front'
        if move_x != 0 or move_y != 0:
            normp = math.hypot(move_x, move_y)
            player.x += (move_x / normp) * player.speed * dt
            player.y += (move_y / normp) * player.speed * dt
        player.x = max(10, min(WINDOW_W - player.size - 10, player.x))
        player.y = max(80, min(WINDOW_H - player.size - 10, player.y))

        if time.time() - last_change > change_interval:
            cat_dir = [random.choice([-1,0,1]), random.choice([-1,0,1])]
            change_interval = random.randint(RAND_MIN, RAND_MAX) / 10.0 + 0.3
            last_change = time.time()
        if cat_dir[0] != 0 or cat_dir[1] != 0:
            normc = math.hypot(cat_dir[0], cat_dir[1])
            cat.x += (cat_dir[0] / normc) * cat.speed * dt
            cat.y += (cat_dir[1] / normc) * cat.speed * dt
            if cat_dir[0] == -1: cat_facing_left = True
            elif cat_dir[0] == 1: cat_facing_left = False
        if cat.x < 10: cat.x = 10; cat_dir[0] *= -1
        if cat.x > WINDOW_W-cat.size-10: cat.x = WINDOW_W-cat.size-10; cat_dir[0] *= -1
        if cat.y < 80: cat.y = 80; cat_dir[1] *= -1
        if cat.y > WINDOW_H-cat.size-10: cat.y = WINDOW_H-cat.size-10; cat_dir[1] *= -1

        if player.rect().colliderect(cat.rect()):
            screen.fill(BG_COLORS[1])
            draw_timer_bar(elapsed, gs.total_time)
            draw_player(screen, int(player.x), int(player.y), player.size, player_direction, use_white=True)
            draw_cat(screen, int(cat.x), int(cat.y), cat.size, flip=cat_facing_left, sleeping=True)
            draw_text(screen, f"남은시간: {max(0, int(gs.total_time - elapsed))}초", 20, 45)
            draw_text(screen, "움직이는 고양이를 잡아보자!", 20, WINDOW_H-40)
            pygame.display.flip()
            time.sleep(1)
            return True
        draw_timer_bar(elapsed, gs.total_time)
        draw_player(screen, int(player.x), int(player.y), player.size, player_direction, use_white=True)
        draw_cat(screen, int(cat.x), int(cat.y), cat.size, flip=cat_facing_left)
        draw_text(screen, f"남은시간: {max(0, int(gs.total_time - elapsed))}초", 20, 45)
        draw_text(screen, "움직이는 고양이를 잡아보자!", 20, WINDOW_H-40)
        pygame.display.flip()
        
        if elapsed >= gs.total_time: return False

def mission_day2():
    player = Entity(40, WINDOW_H - PLAYER_SIZE - 40, PLAYER_SIZE)
    cat = Entity(WINDOW_W//2 - CAT_SIZE//2, WINDOW_H//2 - CAT_SIZE//2, CAT_SIZE)
    gs.total_time = 30.0
    start = time.time()
    sound_score = 0
    door = pygame.Rect(WINDOW_W - 80, 80, 60, 80)
    player_direction = 'front'

    while True:
        game_quit()

        dt = clock.tick(FPS) / 1000.0
        elapsed = time.time() - start

        keys = pygame.key.get_pressed()
        move_x = move_y = 0
        moving = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move_x = -1; moving = True; player_direction = 'left'
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_x = 1; moving = True; player_direction = 'right'
        if keys[pygame.K_UP] or keys[pygame.K_w]: move_y = -1; moving = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: move_y = 1; moving = True
        if not (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not(keys[pygame.K_RIGHT] or keys[pygame.K_d]) and move_y == 0: player_direction = 'front'
        if move_x != 0 or move_y != 0:
            norm = math.hypot(move_x, move_y)
            player.x += (move_x / norm) * player.speed * dt
            player.y += (move_y / norm) * player.speed * dt

        if moving: sound_score += random.randint(RAND_MIN, RAND_MAX)
        else: sound_score -= 1
        sound_score = max(0, sound_score)

        if sound_score >= 100:
            screen.fill(BG_COLORS[2])
            pygame.draw.rect(screen, DOOR, door)
            draw_text(screen, "Door", door.x+6, door.y+door.height+4)
            draw_cat(screen, int(cat.x), int(cat.y), cat.size, sleeping=False)
            draw_player(screen, int(player.x), int(player.y), player.size, player_direction, use_white=True)
            draw_timer_bar(elapsed, gs.total_time)
            draw_text(screen, f"남은시간: {max(0, int(gs.total_time - elapsed))}초", 20, 65)
            draw_text(screen, f"소리 점수: {sound_score}", 20, 45)
            draw_text(screen, "움직이면 소리 점수 증가, 멈추면 감소 (100 이상이면 고양이가 깨요 ㅠㅠ)", 20, WINDOW_H-40)
            pygame.display.flip()
            time.sleep(1)
            return False
        if player.rect().colliderect(cat.rect()):
            screen.fill(BG_COLORS[2])
            pygame.draw.rect(screen, DOOR, door)
            draw_text(screen, "Door", door.x+6, door.y+door.height+4)
            draw_cat(screen, int(cat.x), int(cat.y), cat.size)
            draw_player(screen, int(player.x), int(player.y), player.size, player_direction, use_white=True)
            draw_timer_bar(elapsed, gs.total_time)
            draw_text(screen, f"남은시간: {max(0, int(gs.total_time - elapsed))}초", 20, 65)
            draw_text(screen, f"소리 점수: {sound_score}", 20, 45)
            draw_text(screen, "움직이면 소리 점수 증가, 멈추면 감소 (100 이상이면 고양이가 깨요 ㅠㅠ)", 20, WINDOW_H-40)
            pygame.display.flip()
            time.sleep(1)
            return False
        if player.rect().colliderect(door):
            if sound_score < 100: return True
            else: return False
        screen.fill(BG_COLORS[2])
        pygame.draw.rect(screen, DOOR, door)
        draw_text(screen, "Door", door.x+6, door.y+door.height+4)
        draw_cat(screen, int(cat.x), int(cat.y), cat.size, sleeping=True)
        draw_player(screen, int(player.x), int(player.y), player.size, player_direction, use_white=True)
        draw_timer_bar(elapsed, gs.total_time)
        draw_text(screen, f"남은시간: {max(0, int(gs.total_time - elapsed))}초", 20, 65)
        draw_text(screen, f"소리 점수: {sound_score}", 20, 45)
        draw_text(screen, "움직이면 소리 점수 증가, 멈추면 감소 (100 이상이면 고양이가 깨요 ㅠㅠ)", 20, WINDOW_H-40)
        pygame.display.flip()

        if elapsed >= gs.total_time:return False

def generate_maze(cols, rows):
    maze = np.ones((rows, cols), dtype=int) # 0(통로), 1(벽)
    stack = []
    start = (1,1)
    maze[start[1], start[0]] = 0 # 시작점
    stack.append(start)
    while stack:
        x,y = stack[-1]
        neighbors = []

        # 2칸 떨어진 위치 탐색 (벽 사이에 통로 만들기)
        for dx,dy in [(2,0),(-2,0),(0,2),(0,-2)]:
            nx, ny = x+dx, y+dy
            if 0 < nx < cols and 0 < ny < rows and maze[ny, nx] == 1: neighbors.append((nx,ny))
        if neighbors:
            nx,ny = random.choice(neighbors)
            bx, by = (x+nx)//2, (y+ny)//2 # 중간 벽 제거
            maze[by, bx] = 0
            maze[ny, nx] = 0
            stack.append((nx,ny))
        else: stack.pop() # 막다른 곳이면 백트래킹
    return maze

def mission_day3():
    cols = (WINDOW_W // TILE) | 1
    rows = ((WINDOW_H - 120) // TILE) | 1
    maze = generate_maze(cols, rows)
    start = (1,1)

    def farthest_cell():
        visited = set()
        q = deque()
        q.append((start,0)) # (위치, 거리)
        visited.add(start)
        far = start
        far_d = 0
        while q:
            (x,y),d = q.popleft()
            if d > far_d:
                far_d = d
                far = (x,y) # 가장 먼 지점 업데이트

            # 4방향 탐색
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < cols and 0 <= ny < rows and maze[ny,nx]==0 and (nx,ny) not in visited:
                    visited.add((nx,ny))
                    q.append(((nx,ny), d+1))
        return far

    goal_x, goal_y = farthest_cell()
    player_x, player_y = start
    grid_w = cols * TILE
    grid_h = rows * TILE
    offset_x = (WINDOW_W - grid_w)//2
    offset_y = (WINDOW_H - grid_h)//2

    gs.total_time = 30.0
    start_time = time.time()
    player_direction = 'front'

    while True:
        game_quit()

        elapsed = time.time() - start_time

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            nx = player_x-1
            if nx>=0 and maze[player_y,nx]==0: player_x = nx; player_direction = 'left'; time.sleep(0.08)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            nx = player_x+1
            if nx<cols and maze[player_y,nx]==0: player_x = nx; player_direction = 'right'; time.sleep(0.08)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            ny = player_y-1
            if ny>=0 and maze[ny,player_x]==0: player_y = ny; time.sleep(0.08)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            ny = player_y+1
            if ny<rows and maze[ny,player_x]==0: player_y = ny; time.sleep(0.08)

        if (player_x, player_y) == (goal_x, goal_y+1) or (player_x, player_y) == (goal_x, goal_y-1) or (player_x, player_y) == (goal_x+1, goal_y) or (player_x, player_y) == (goal_x-1, goal_y):
            screen.fill(BG_COLORS[3])
            for y in range(rows):
                for x in range(cols):
                    rect = pygame.Rect(offset_x + x*TILE, offset_y + y*TILE, TILE, TILE)
                    if maze[y,x] == 1: pygame.draw.rect(screen, MAZE_WALL, rect)
                    else: pygame.draw.rect(screen, MAZE_ROAD, rect)
            draw_cat(screen, offset_x + goal_x*TILE + (TILE - CAT_SIZE)//2, offset_y + goal_y*TILE + (TILE - CAT_SIZE)//2, CAT_SIZE, sleeping=False)
            draw_player(screen, offset_x + player_x*TILE + (TILE - PLAYER_SIZE)//2, offset_y + player_y*TILE + (TILE - PLAYER_SIZE)//2, PLAYER_SIZE, player_direction, use_white=False)
            draw_timer_bar(elapsed, gs.total_time)
            draw_text(screen, f"남은시간: {max(0, int(gs.total_time - elapsed))}초", 20, 45)
            draw_text(screen, "고영희가 있는 곳까지 빨리 가야해...", 20, WINDOW_H-40)
            pygame.display.flip()
            time.sleep(1)
            return True
        screen.fill(BG_COLORS[3])
        for y in range(rows):
            for x in range(cols):
                rect = pygame.Rect(offset_x + x*TILE, offset_y + y*TILE, TILE, TILE)
                if maze[y,x] == 1: pygame.draw.rect(screen, MAZE_WALL, rect)
                else: pygame.draw.rect(screen, MAZE_ROAD, rect)
        draw_cat(screen, offset_x + goal_x*TILE + (TILE - CAT_SIZE)//2, offset_y + goal_y*TILE + (TILE - CAT_SIZE)//2, CAT_SIZE, sleeping=True)
        draw_player(screen, offset_x + player_x*TILE + (TILE - PLAYER_SIZE)//2, offset_y + player_y*TILE + (TILE - PLAYER_SIZE)//2, PLAYER_SIZE, player_direction, use_white=False)
        draw_timer_bar(elapsed, gs.total_time)
        draw_text(screen, f"남은시간: {max(0, int(gs.total_time - elapsed))}초", 20, 45)
        draw_text(screen, "고영희가 있는 곳까지 빨리 가야해...", 20, WINDOW_H-40)
        pygame.display.flip()

        if elapsed >= gs.total_time: return False

def mission_day4():
    player = Entity(random.randint(40, WINDOW_W-40-PLAYER_SIZE), random.randint(120, WINDOW_H-120-PLAYER_SIZE), PLAYER_SIZE)
    cat = Entity(random.randint(40, WINDOW_W-40-CAT_SIZE), random.randint(120, WINDOW_H-120-CAT_SIZE), CAT_SIZE)
    cat.speed = 200
    gs.total_time = 10.0
    start = time.time()
    obstacles = []
    spawn_timer = 0
    spawn_interval = max(0.3, random.randint(RAND_MIN, RAND_MAX) / 20.0)
    change_interval = random.randint(RAND_MIN, RAND_MAX) / 10.0 + 0.3
    last_change = time.time()
    cat_dir = [random.choice([-1,0,1]), random.choice([-1,0,1])]
    cat_facing_left = False
    player_direction = 'front'

    while True:
        game_quit()

        dt = clock.tick(FPS) / 1000.0
        elapsed = time.time() - start
        
        keys = pygame.key.get_pressed()
        move_x = move_y = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move_x = -1; player_direction = 'left'
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_x = 1; player_direction = 'right'
        if keys[pygame.K_UP] or keys[pygame.K_w]: move_y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: move_y = 1
        if not (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not(keys[pygame.K_RIGHT] or keys[pygame.K_d]) and move_y == 0: player_direction = 'front'
        if move_x != 0 or move_y != 0:
            norm = math.hypot(move_x, move_y)
            player.x += (move_x / norm) * player.speed * dt
            player.y += (move_y / norm) * player.speed * dt
        player.x = max(10, min(WINDOW_W-player.size-10, player.x))
        player.y = max(80, min(WINDOW_H-player.size-10, player.y))

        if time.time() - last_change > change_interval:
            cat_dir = [random.choice([-1,0,1]), random.choice([-1,0,1])]
            change_interval = random.randint(RAND_MIN, RAND_MAX) / 10.0 + 0.3
            last_change = time.time()
        if cat_dir[0] != 0 or cat_dir[1] != 0:
            normc = math.hypot(cat_dir[0], cat_dir[1])
            cat.x += (cat_dir[0] / normc) * cat.speed * dt
            cat.y += (cat_dir[1] / normc) * cat.speed * dt
            if cat_dir[0] < 0: cat_facing_left = True
            elif cat_dir[0] > 0: cat_facing_left = False
        if cat.x < 10: cat.x = 10; cat_dir[0] *= -1
        if cat.x > WINDOW_W-cat.size-10: cat.x = WINDOW_W-cat.size-10; cat_dir[0] *= -1
        if cat.y < 80: cat.y = 80; cat_dir[1] *= -1
        if cat.y > WINDOW_H-cat.size-10: cat.y = WINDOW_H-cat.size-10; cat_dir[1] *= -1

        spawn_timer += dt
        if spawn_timer >= spawn_interval:
            spawn_timer = 0
            spawn_interval = max(0.2, random.randint(RAND_MIN, RAND_MAX) / 20.0)
            side = random.choice(['top','left','right'])
            if side == 'top': sx = random.randint(20, WINDOW_W-20); sy = 80
            elif side == 'left': sx = 20; sy = random.randint(80, WINDOW_H-60)
            else: sx = WINDOW_W - 40; sy = random.randint(80, WINDOW_H-60)
            dx = (player.x - sx) + random.uniform(-60,60)
            dy = (player.y - sy) + random.uniform(-60,60)
            dist = math.hypot(dx,dy)
            speed = random.randint(100, 220)
            vx, vy = dx/dist*speed, dy/dist*speed
            obstacles.append({'x':sx, 'y':sy, 'w':14, 'h':14, 'vx':vx, 'vy':vy})
        for ob in obstacles:
            ob['x'] += ob['vx'] * dt
            ob['y'] += ob['vy'] * dt

        for ob in obstacles:
            if player.rect().colliderect(pygame.Rect(ob['x'], ob['y'], ob['w'], ob['h'])): return False
            if cat.rect().colliderect(pygame.Rect(ob['x'], ob['y'], ob['w'], ob['h'])): obstacles.remove(ob)
        if player.rect().colliderect(cat.rect()): return False
        screen.fill(BG_COLORS[4])
        draw_player(screen, int(player.x), int(player.y), player.size, player_direction, use_white=False)
        draw_cat(screen, int(cat.x), int(cat.y), cat.size, flip=cat_facing_left)
        for ob in obstacles: pygame.draw.rect(screen, CAT_FOOD, (int(ob['x']), int(ob['y']), ob['w'], ob['h']))
        draw_timer_bar(elapsed, gs.total_time)
        draw_text(screen, f"남은시간: {max(0, int(gs.total_time - elapsed))}초", 20, 45, color=BLACK)
        draw_text(screen, "고영희와 고영희가 뿌리는 사료를 피해서 도망쳐야겠어..!", 20, WINDOW_H-40, color=BLACK)
        pygame.display.flip()

        if elapsed >= gs.total_time: return True

def mission_day5():
    cat_x, cat_y = WINDOW_W//2 - CAT_SIZE//2, WINDOW_H//2 - CAT_SIZE//2
    gs.total_time = 10.0
    start = time.time()
    obstacles = []
    spawn_timer = 0
    spawn_interval = max(0.4, random.randint(RAND_MIN, RAND_MAX)/20.0)

    while True:
        game_quit()

        dt = clock.tick(FPS) / 1000.0
        elapsed = time.time() - start
        spawn_timer += dt
        if spawn_timer >= spawn_interval:
            spawn_timer = 0
            spawn_interval = max(0.25, random.randint(RAND_MIN, RAND_MAX)/20.0)
            side = random.choice(['top','left','right','bottom'])
            if side == 'top': sx = random.randint(20, WINDOW_W-20); sy = 80
            elif side == 'bottom': sx = random.randint(20, WINDOW_W-20); sy = WINDOW_H-20
            elif side == 'left': sx = 20; sy = random.randint(80, WINDOW_H-60)
            else: sx = WINDOW_W-20; sy = random.randint(80, WINDOW_H-60)
            typ = random.choice(['dust','fly','wind'])
            r = 10 if typ in ('dust','fly') else 16
            dx = (cat_x - sx) + random.uniform(-40,40)
            dy = (cat_y - sy) + random.uniform(-40,40)
            dist = max(1, math.hypot(dx,dy))
            speed = random.randint(60, 180)
            vx, vy = dx/dist*speed, dy/dist*speed
            obstacles.append({'x':sx, 'y':sy, 'r':r, 'vx':vx, 'vy':vy, 'type':typ})
        for ob in obstacles:
            ob['x'] += ob['vx'] * dt
            ob['y'] += ob['vy'] * dt

        mx, my = pygame.mouse.get_pos()
        obstacles = [ob for ob in obstacles if math.hypot(ob['x'] - mx, ob['y'] - my) > ob['r'] + 4]

        cx, cy = cat_x + CAT_SIZE/2, cat_y + CAT_SIZE/2
        for ob in obstacles:
            if math.hypot(ob['x'] - cx, ob['y'] - cy) <= ob['r'] + CAT_SIZE/2 - 4:
                screen.fill(BG_COLORS[5])
                draw_cat(screen, cat_x, cat_y, CAT_SIZE)
                for ob in obstacles:
                    color = DUST if ob['type']=='dust' else FLY if ob['type']=='fly' else WIND
                    pygame.draw.circle(screen, color, (int(ob['x']), int(ob['y'])), ob['r'])
                draw_timer_bar(elapsed, gs.total_time)
                draw_text(screen, f"남은시간: {max(0, int(gs.total_time - elapsed))}초", 20, 45, BLACK)
                draw_text(screen, "마우스가 닿게 하여 장애물들을 제거하세요!", 20, WINDOW_H-40, color=BLACK)
                pygame.display.flip()
                time.sleep(1)
                return False
        screen.fill(BG_COLORS[5])
        draw_cat(screen, cat_x, cat_y, CAT_SIZE, sleeping=True)
        for ob in obstacles:
            color = DUST if ob['type']=='dust' else FLY if ob['type']=='fly' else WIND
            pygame.draw.circle(screen, color, (int(ob['x']), int(ob['y'])), ob['r'])
        draw_timer_bar(elapsed, gs.total_time)
        draw_text(screen, f"남은시간: {max(0, int(gs.total_time - elapsed))}초", 20, 45, BLACK)
        draw_text(screen, "마우스가 닿게 하여 장애물들을 제거하세요!", 20, WINDOW_H-40, color=BLACK)
        pygame.display.flip()

        if elapsed >= gs.total_time: return True

def run_mission(day, mission_func):
    start_time = time.time()

    while True:
        game_quit()
        
        screen.fill(BG_COLORS[day])
        draw_text_center(screen, f"Day {day}", 40, color=BLACK if day == 4 or day == 5 else WHITE)
        draw_text_center(screen, NARRATIVES[day], 90, color=BLACK if day == 4 or day == 5 else WHITE)
        draw_text_center(screen, "미션 시작...", 140, color=BLACK if day == 4 or day == 5 else WHITE)
        draw_text(screen, "조작: 방향키/WASD 또는 마우스(특정 미션)", 20, WINDOW_H-40, color=BLACK if day == 4 or day == 5 else WHITE)
        pygame.display.flip()
        if time.time() - start_time > 2: break

    result = mission_func()

    if result: gs.emotions.append(EMOTIONS[day])
    end_show_start = time.time()
    while time.time() - end_show_start < 2:
        game_quit()

        if result:
            screen.fill(BG_COLORS[0])
            draw_text_center(screen, "미션 성공!", WINDOW_H//2 - 40)
            draw_text_center(screen, f"회복한 감정: {EMOTIONS[day]}", WINDOW_H//2 + 10)
        else:
            screen.fill(BG_COLORS[0])
            draw_text_center(screen, "실패했습니다. 다시 시도하세요.", WINDOW_H//2)
        pygame.display.flip()
        clock.tick(FPS)
    return result



# --------------- 화면 함수 ---------------
def title_screen():
    while gs.show_title:
        game_quit()

        screen.fill(BG_COLORS[0])
        draw_text_center(screen, "고영희 키우기", 80)
        draw_cat(screen, WINDOW_W//2 - 32, 160, 64)
        draw_text_center(screen, "게임 시작 (스페이스 또는 마우스 클릭)", 360)
        pygame.display.flip()
        clock.tick(FPS)

def narration_screen():
    while gs.show_narration:
        game_quit()

        screen.fill(BG_COLORS[0])
        draw_text_center(screen, "인생이 재미없다고 느끼면서 살아가는 주인공", 120)
        draw_text_center(screen, "고양이 한마리를 키우게 되는데...", 150)
        draw_text_center(screen, "그 이름은 고영희..!", 180)
        draw_text_center(screen, "5일동안 고영희가 일으키는 이벤트들에 대한 미션을 해결하고,", 240)
        draw_text_center(screen, "감정을 회복해보자!", 270)
        draw_text_center(screen, "계속하려면 스페이스 또는 마우스 클릭,", WINDOW_H - 150)
        draw_text_center(screen, "게임을 종료하려면 ECS키를 눌러주세요.", WINDOW_H - 120)
        pygame.display.flip()
        clock.tick(FPS)

def ending_screen():
    while gs.show_end:
        game_quit()

        screen.fill(BG_COLORS[6])
        draw_text_center(screen, NARRATIVES[6], 60, BLACK)
        draw_cat(screen, WINDOW_W//2 - 32, 110, 64)
        draw_text_center(screen, "회복한 감정들:", 220, BLACK)
        y = 260
        for i, e in enumerate(gs.emotions):
            draw_text_center(screen, f"{i+1}. {e}", y+30*i, BLACK)
        draw_text_center(screen, "게임 종료 (ESC)", WINDOW_H - 60, BLACK)
        pygame.display.flip()



# --------------- 메인 함수 ---------------
def main_loop():
    while True:
        game_quit()

        clock.tick(FPS)
            
        if gs.show_title: title_screen()
        elif gs.show_narration: narration_screen(); gs.day = 1
        elif 1 <= gs.day <= 5:
            if gs.day == 1: ok = run_mission(1, mission_day1)
            elif gs.day == 2: ok = run_mission(2, mission_day2)
            elif gs.day == 3: ok = run_mission(3, mission_day3)
            elif gs.day == 4: ok = run_mission(4, mission_day4)
            elif gs.day == 5: ok = run_mission(5, mission_day5)
            if ok:
                gs.day += 1
                if gs.day > 5: gs.show_end = True
        elif gs.show_end: ending_screen()



# --------------- 실행 ---------------
main_loop()