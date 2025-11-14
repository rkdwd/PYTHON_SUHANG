import pygame
import sys
import subprocess
import random
import time
import math
import numpy as np
from collections import deque

required = ["pygame", "numpy"]
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])



WINDOW_W, WINDOW_H = 960, 540
FPS = 60
TILE = 24
RAND_MIN, RAND_MAX = 1, 5

WHITE = (255,255,255)
BLACK = (0,0,0)

PLAYER_SIZE = 42  # 28 * 3/2 = 42
CAT_SIZE = 28

DAY_BG_COLORS = {
    1: (90, 20, 20),    # 크림슨
    2: (60, 10, 60),    # 보라
    3: (15, 30, 80),    # 남색
    4: (240, 220, 140), # 파스텔톤 노랑
    5: (255, 200, 150), # 파스텔톤 주황
    6: (255, 164, 164)  # 연붉은 핑크
}

DAY_NARRATIVES = {
    0: "",
    1: "Day1 — 집 안을 뛰어다니는 고양이! 잡아야겠다.",
    2: "Day2 — 조심히. 소리 내지 말고 몰래 문까지 가자.",
    3: "Day3 — 고양이가 밖으로 나갔어... 미로 속에서 찾아야 해.",
    4: "Day4 — 고양이가 장난이 심하다. 피해서 버텨야 해.",
    5: "Day5 — 이제 품에 안기려 한다. 조용히 재워주자.",
    6: ""
}

DAY_EMOTION = {
    1: "분노",
    2: "불안",
    3: "걱정",
    4: "이해",
    5: "감동",
}



pygame.init()
pygame.display.set_caption("고영희 키우기")
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
clock = pygame.time.Clock()
FONT = pygame.font.Font("font/bdf/DOSSaemmul-16.bdf", 20)
BIG_FONT = pygame.font.Font("font/bdf/DOSSaemmul-16.bdf", 36)

# 고양이 이미지 로드
try:
    cat_image_original = pygame.image.load("src/cat.png")
except:
    print("경고: src/cat.png 파일을 찾을 수 없습니다. 기본 픽셀아트로 대체합니다.")
    cat_image_original = None

try:
    cat_sleeping_image = pygame.image.load("src/cat_sleeping.png")
except:
    print("경고: src/cat_sleeping.png 파일을 찾을 수 없습니다. 기본 이미지로 대체합니다.")
    cat_sleeping_image = None

# 플레이어 이미지 로드 (흰색 버전)
try:
    player_front_white = pygame.image.load("src/player_front_white.png")
except:
    print("경고: src/player_front_white.png 파일을 찾을 수 없습니다.")
    player_front_white = None

try:
    player_left_white = pygame.image.load("src/player_left_white.png")
except:
    print("경고: src/player_left_white.png 파일을 찾을 수 없습니다.")
    player_left_white = None

try:
    player_right_white = pygame.image.load("src/player_right_white.png")
except:
    print("경고: src/player_right_white.png 파일을 찾을 수 없습니다.")
    player_right_white = None

# 플레이어 이미지 로드 (검은색 버전)
try:
    player_front_black = pygame.image.load("src/player_front_black.png")
except:
    print("경고: src/player_front_black.png 파일을 찾을 수 없습니다.")
    player_front_black = None

try:
    player_left_black = pygame.image.load("src/player_left_black.png")
except:
    print("경고: src/player_left_black.png 파일을 찾을 수 없습니다.")
    player_left_black = None

try:
    player_right_black = pygame.image.load("src/player_right_black.png")
except:
    print("경고: src/player_right_black.png 파일을 찾을 수 없습니다.")
    player_right_black = None

try:
    player_failed = pygame.image.load("src/player_failed.png")
except:
    print("경고: src/player_failed.png 파일을 찾을 수 없습니다.")
    player_failed = None

class GameState:
    def __init__(self):
        self.day = 0
        self.emotions = []
        self.running = True
        self.in_mission = False
        self.mission_result = None
        self.show_title = True
        self.show_narration = False
        self.show_end = False
gs = GameState()

class Entity:
    def __init__(self, x, y, size, color):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.speed = 140

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.size, self.size)

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect())



def draw_cat(surf, x, y, size, color, flip=False, sleeping=False):
    if sleeping and cat_sleeping_image:
        image_to_use = cat_sleeping_image
    elif cat_image_original:
        image_to_use = cat_image_original
    else:
        image_to_use = None
    
    if image_to_use:
        scaled_cat = pygame.transform.scale(image_to_use, (size, size))
        if flip:
            scaled_cat = pygame.transform.flip(scaled_cat, True, False)
        surf.blit(scaled_cat, (x, y))
    else:
        body = pygame.Rect(x, y, size, size)
        pygame.draw.rect(surf, color, body)
        eye_w = size//6
        pygame.draw.rect(surf, WHITE, (x+size//4, y+size//4, eye_w, eye_w))
        pygame.draw.rect(surf, WHITE, (x+size*3//5, y+size//4, eye_w, eye_w))
        pygame.draw.rect(surf, (30,30,30), (x+size//4+1, y+size//4+1, eye_w-2, eye_w-2))
        pygame.draw.rect(surf, (30,30,30), (x+size*3//5+1, y+size//4+1, eye_w-2, eye_w-2))

def draw_player(surf, x, y, size, color, direction='front', use_white=True):
    """플레이어를 이미지로 그립니다.
    direction: 'front', 'left', 'right'
    use_white: True면 흰색 버전, False면 검은색 버전
    """
    image = None
    
    if use_white:
        if direction == 'front':
            image = player_front_white
        elif direction == 'left':
            image = player_left_white
        elif direction == 'right':
            image = player_right_white
    else:
        if direction == 'front':
            image = player_front_black
        elif direction == 'left':
            image = player_left_black
        elif direction == 'right':
            image = player_right_black
    
    if image:
        scaled_player = pygame.transform.scale(image, (size, size))
        surf.blit(scaled_player, (int(x), int(y)))
    else:
        # 이미지가 없으면 기본 사각형으로 표시
        pygame.draw.rect(surf, color, (int(x), int(y), size, size))
        pygame.draw.rect(surf, (255,255,255), (int(x)+size//4, int(y)+size//3, size//2, size//6))

def draw_pixel_player(surf, x, y, size, color):
    pygame.draw.rect(surf, color, (x,y,size,size))
    pygame.draw.rect(surf, (255,255,255), (x+size//4, y+size//3, size//2, size//6))

def draw_text_center(surf, text, y, font=BIG_FONT, color=WHITE):
    r = font.render(text, True, color)
    rect = r.get_rect(center=(WINDOW_W//2, y))
    surf.blit(r, rect)

def draw_text(surf, text, x, y, font=FONT, color=WHITE):
    surf.blit(font.render(text, True, color), (x,y))

def draw_timer_bar(elapsed, total):
    w = int((1 - elapsed/total) * (WINDOW_W - 40))
    pygame.draw.rect(screen, (40,40,40), (20, 20, WINDOW_W-40, 16))
    pygame.draw.rect(screen, (80,200,120), (20, 20, w, 16))

def title_screen():
    screen.fill((20,20,20))
    draw_text_center(screen, "고영희 키우기", 80)
    draw_cat(screen, WINDOW_W//2 - 32, 160, 64, (200,160,200))
    draw_text_center(screen, "게임 시작 (스페이스 또는 마우스 클릭)", 360, font=FONT)

def narration_screen():
    """나레이션 화면을 보여줍니다. 스페이스키 또는 마우스 클릭으로 다음 화면으로 넘어갑니다."""
    waiting = True
    
    while waiting:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if ev.key == pygame.K_SPACE or ev.key == pygame.K_RETURN:
                    waiting = False
            if ev.type == pygame.MOUSEBUTTONDOWN:
                waiting = False
        
        screen.fill((20, 20, 20))
        
        # 나레이션 텍스트 (사용자가 채울 부분)
        draw_text_center(screen, "********************", 150, font=FONT)
        draw_text_center(screen, "********************", 190, font=FONT)
        draw_text_center(screen, "********************", 230, font=FONT)
        draw_text_center(screen, "********************", 270, font=FONT)
        draw_text_center(screen, "********************", 310, font=FONT)
        draw_text_center(screen, "계속하려면 스페이스 또는 마우스 클릭", WINDOW_H - 60, font=FONT)
        
        pygame.display.flip()
        clock.tick(FPS)

def ending_screen():
    screen.fill(DAY_BG_COLORS[6])
    draw_text_center(screen, DAY_NARRATIVES[6], 60)
    draw_cat(screen, WINDOW_W//2 - 32, 110, 64, (200,160,200))
    draw_text_center(screen, "회복한 감정들:", 220, font=FONT)
    y = 260
    for i, e in enumerate(gs.emotions):
        draw_text_center(screen, f"{i+1}. {e}", y+30*i, font=FONT)
    draw_text_center(screen, "게임 종료 (ESC)", WINDOW_H - 60, font=FONT)

def run_mission(day, mission_func):
    gs.in_mission = True
    gs.mission_result = None
    start_time = time.time()
    narrated = False

    while True:
        dt = clock.tick(FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

        screen.fill(DAY_BG_COLORS.get(day, (40,40,40)))
        draw_text_center(screen, f"Day {day}", 40, font=BIG_FONT, color=BLACK if day == 4 else WHITE)
        draw_text_center(screen, DAY_NARRATIVES[day], 90, font=FONT, color=BLACK if day == 4 else WHITE)
        draw_text_center(screen, "미션 시작...", 140, font=FONT, color=BLACK if day == 4 else WHITE)
        draw_text(screen, "조작: 방향키/WASD / 마우스(특정 미션)", 20, WINDOW_H-40, color=BLACK if day == 4 else WHITE)
        pygame.display.flip()
        if time.time() - start_time > 2:
            narrated = True
        if narrated:
            break

    result = mission_func()
    gs.in_mission = False
    gs.mission_result = 'success' if result else 'fail'

    if result:
        gs.emotions.append(DAY_EMOTION[day])

    end_show_start = time.time()
    while time.time() - end_show_start < 2:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        if result:
            screen.fill((20,20,20))
            draw_text_center(screen, "미션 성공!", WINDOW_H//2 - 40)
            draw_text_center(screen, f"회복한 감정: {DAY_EMOTION[day]}", WINDOW_H//2 + 10)
        else:
            screen.fill((40,10,10))
            draw_text_center(screen, "실패했습니다. 다시 시도하세요.", WINDOW_H//2)
        pygame.display.flip()
        clock.tick(FPS)
    return result



# ---------- Day1: 술래잡기 ----------
def mission_day1():
    player = Entity(WINDOW_W//2 - PLAYER_SIZE//2, WINDOW_H - PLAYER_SIZE - 40, PLAYER_SIZE, (180,180,255))
    cat = Entity(random.randint(40, WINDOW_W-40-CAT_SIZE), random.randint(100, WINDOW_H-160), CAT_SIZE, (200,160,200))
    cat.speed = 160
    total_time = 30.0
    start = time.time()

    change_interval = random.randint(RAND_MIN, RAND_MAX) / 10.0 + 0.3
    last_change = time.time()
    cat_dir = [random.choice([-1,0,1]), random.choice([-1,0,1])]
    cat_facing_left = False
    player_direction = 'front'  # 플레이어 방향 추적

    while True:
        dt = clock.tick(FPS) / 1000.0
        elapsed = time.time() - start
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

        screen.fill(DAY_BG_COLORS[1])

        keys = pygame.key.get_pressed()
        move_x = move_y = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x = -1
            player_direction = 'left'
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x = 1
            player_direction = 'right'
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_y = 1
        
        # 아무 키도 안 눌렀으면 front
        if not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            if move_y == 0:  # 위아래만 움직이는 경우가 아니면
                player_direction = 'front'
        
        if move_x != 0 or move_y != 0:
            norm = math.hypot(move_x, move_y)
            player.x += (move_x / norm) * player.speed * dt
            player.y += (move_y / norm) * player.speed * dt

        player.x = max(10, min(WINDOW_W - player.size - 10, player.x))
        player.y = max(80, min(WINDOW_H - player.size - 10, player.y))

        # 고양이 랜덤 이동
        if time.time() - last_change > change_interval:
            cat_dir = [random.choice([-1,0,1]), random.choice([-1,0,1])]
            change_interval = random.randint(RAND_MIN, RAND_MAX) / 10.0 + 0.3
            last_change = time.time()
        
        if cat_dir[0] != 0 or cat_dir[1] != 0:
            normc = math.hypot(cat_dir[0], cat_dir[1])
            cat.x += (cat_dir[0] / normc) * cat.speed * dt
            cat.y += (cat_dir[1] / normc) * cat.speed * dt
            
            if cat_dir[0] < 0:
                cat_facing_left = True
            elif cat_dir[0] > 0:
                cat_facing_left = False

        if cat.x < 10: cat.x = 10; cat_dir[0] *= -1
        if cat.x > WINDOW_W-cat.size-10: cat.x = WINDOW_W-cat.size-10; cat_dir[0] *= -1
        if cat.y < 80: cat.y = 80; cat_dir[1] *= -1
        if cat.y > WINDOW_H-cat.size-10: cat.y = WINDOW_H-cat.size-10; cat_dir[1] *= -1

        if player.rect().colliderect(cat.rect()):
            # 고양이를 잡았을 때: 고양이가 자는 모습으로 변경하고 1초 대기
            screen.fill(DAY_BG_COLORS[1])
            draw_timer_bar(elapsed, total_time)
            draw_player(screen, int(player.x), int(player.y), player.size, player.color, player_direction, use_white=True)
            draw_cat(screen, int(cat.x), int(cat.y), cat.size, cat.color, flip=cat_facing_left, sleeping=True)
            draw_text(screen, f"남은시간: {max(0, int(total_time - elapsed))}초", 20, 45)
            pygame.display.flip()
            time.sleep(1)
            return True

        draw_timer_bar(elapsed, total_time)
        draw_player(screen, int(player.x), int(player.y), player.size, player.color, player_direction, use_white=True)
        draw_cat(screen, int(cat.x), int(cat.y), cat.size, cat.color, flip=cat_facing_left)
        draw_text(screen, f"남은시간: {max(0, int(total_time - elapsed))}초", 20, 45)
        pygame.display.flip()

        if elapsed >= total_time:
            return False

# ---------- Day2: 방탈출 ----------
def mission_day2():
    player = Entity(40, WINDOW_H - PLAYER_SIZE - 40, PLAYER_SIZE, (180,180,255))
    cat = Entity(WINDOW_W//2 - CAT_SIZE//2, WINDOW_H//2 - CAT_SIZE//2, CAT_SIZE, (200,160,200))
    total_time = 30.0
    start = time.time()
    sound_score = 0
    player.speed = 140
    door_rect = pygame.Rect(WINDOW_W - 80, 80, 60, 80)
    player_direction = 'front'

    while True:
        dt = clock.tick(FPS) / 1000.0
        elapsed = time.time() - start
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

        keys = pygame.key.get_pressed()
        move_x = move_y = 0
        moving = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x = -1; moving = True
            player_direction = 'left'
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x = 1; moving = True
            player_direction = 'right'
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_y = -1; moving = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_y = 1; moving = True
        
        # 아무 키도 안 눌렀으면 front
        if not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            if move_y == 0:
                player_direction = 'front'

        if move_x != 0 or move_y != 0:
            norm = math.hypot(move_x, move_y)
            player.x += (move_x / norm) * player.speed * dt
            player.y += (move_y / norm) * player.speed * dt

        if moving:
            delta = random.randint(RAND_MIN, RAND_MAX)
            sound_score += delta
        else:
            sound_score -= 1
        sound_score = max(0, sound_score)

        # 소리 점수가 100 이상이면 실패
        if sound_score >= 100:
            # 고양이가 일어난 모습으로 변경하고 1초 대기
            screen.fill(DAY_BG_COLORS[2])
            pygame.draw.rect(screen, (80,50,20), door_rect)
            draw_text(screen, "Door", door_rect.x+6, door_rect.y+door_rect.height+4)
            draw_cat(screen, int(cat.x), int(cat.y), cat.size, cat.color, sleeping=False)
            draw_player(screen, int(player.x), int(player.y), player.size, player.color, player_direction, use_white=True)
            draw_timer_bar(elapsed, total_time)
            draw_text(screen, f"소리 점수: {sound_score}", 20, 45)
            draw_text(screen, f"남은시간: {max(0, int(total_time - elapsed))}초", 20, 65)
            draw_text(screen, "움직이면 소리 점수 ↑, 멈추면 ↓ (100 이상이면 고양이 깸)", 20, WINDOW_H-40)
            pygame.display.flip()
            time.sleep(1)
            return False

        if player.rect().colliderect(door_rect):
            if sound_score < 100:
                return True
            else:
                return False

        screen.fill(DAY_BG_COLORS[2])
        pygame.draw.rect(screen, (80,50,20), door_rect)
        draw_text(screen, "Door", door_rect.x+6, door_rect.y+door_rect.height+4)
        draw_cat(screen, int(cat.x), int(cat.y), cat.size, cat.color, sleeping=True)
        draw_player(screen, int(player.x), int(player.y), player.size, player.color, player_direction, use_white=True)

        draw_timer_bar(elapsed, total_time)
        draw_text(screen, f"소리 점수: {sound_score}", 20, 45)
        draw_text(screen, f"남은시간: {max(0, int(total_time - elapsed))}초", 20, 65)
        draw_text(screen, "움직이면 소리 점수 ↑, 멈추면 ↓ (100 이상이면 고양이 깸)", 20, WINDOW_H-40)
        pygame.display.flip()

        if elapsed >= total_time:
            return False

# ---------- Day3: 미로찾기 ----------
def generate_maze(cols, rows):
    maze = np.ones((rows, cols), dtype=int)
    stack = []
    start = (1,1)
    maze[start[1], start[0]] = 0
    stack.append(start)
    while stack:
        x,y = stack[-1]
        neighbors = []
        for dx,dy in [(2,0),(-2,0),(0,2),(0,-2)]:
            nx, ny = x+dx, y+dy
            if 0 < nx < cols and 0 < ny < rows and maze[ny, nx] == 1:
                neighbors.append((nx,ny))
        if neighbors:
            nx,ny = random.choice(neighbors)
            bx, by = (x+nx)//2, (y+ny)//2
            maze[by, bx] = 0
            maze[ny, nx] = 0
            stack.append((nx,ny))
        else:
            stack.pop()
    return maze

def mission_day3():
    cols = (WINDOW_W // TILE) | 1
    rows = ((WINDOW_H - 120) // TILE) | 1
    maze = generate_maze(cols, rows)
    start = (1,1)

    def farthest_cell():
        visited = set()
        q = deque()
        q.append((start,0))
        visited.add(start)
        far = start
        far_d = 0
        while q:
            (x,y),d = q.popleft()
            if d > far_d:
                far_d = d; far = (x,y)
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < cols and 0 <= ny < rows and maze[ny,nx]==0 and (nx,ny) not in visited:
                    visited.add((nx,ny))
                    q.append(((nx,ny), d+1))
        return far

    goal = farthest_cell()

    grid_w = cols * TILE
    grid_h = rows * TILE
    offset_x = (WINDOW_W - grid_w)//2
    offset_y = (WINDOW_H - grid_h)//2

    player_cell = list(start)
    total_time = 30.0
    start_time = time.time()
    player_color = (180,180,255)
    player_direction = 'front'

    while True:
        dt = clock.tick(FPS) / 1000.0
        elapsed = time.time() - start_time
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            nx = player_cell[0]-1; ny = player_cell[1]
            if nx>=0 and maze[ny,nx]==0:
                player_cell[0] = nx
                player_direction = 'left'
                time.sleep(0.08)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            nx = player_cell[0]+1; ny = player_cell[1]
            if nx<cols and maze[ny,nx]==0:
                player_cell[0] = nx
                player_direction = 'right'
                time.sleep(0.08)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            nx = player_cell[0]; ny = player_cell[1]-1
            if ny>=0 and maze[ny,nx]==0:
                player_cell[1] = ny
                time.sleep(0.08)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            nx = player_cell[0]; ny = player_cell[1]+1
            if ny<rows and maze[ny,nx]==0:
                player_cell[1] = ny
                time.sleep(0.08)

        if tuple(player_cell) == goal:
            screen.fill(DAY_BG_COLORS[3])
            for y in range(rows):
                for x in range(cols):
                    rect = pygame.Rect(offset_x + x*TILE, offset_y + y*TILE, TILE, TILE)
                    if maze[y,x] == 1:
                        pygame.draw.rect(screen, (20,20,20), rect)
                    else:
                        pygame.draw.rect(screen, (220,220,240), rect)
            
            gx, gy = goal
            draw_cat(screen, offset_x + gx*TILE + (TILE - CAT_SIZE)//2, offset_y + gy*TILE + (TILE - CAT_SIZE)//2, CAT_SIZE, (200,160,200), sleeping=False)
            
            px, py = player_cell
            draw_player(screen, offset_x + px*TILE + (TILE - PLAYER_SIZE)//2, offset_y + py*TILE + (TILE - PLAYER_SIZE)//2, PLAYER_SIZE, player_color, player_direction, use_white=False)
            
            draw_timer_bar(elapsed, total_time)
            draw_text(screen, f"남은시간: {max(0, int(total_time - elapsed))}초", 20, 45)
            pygame.display.flip()
            time.sleep(1)
            return True

        screen.fill(DAY_BG_COLORS[3])
        for y in range(rows):
            for x in range(cols):
                rect = pygame.Rect(offset_x + x*TILE, offset_y + y*TILE, TILE, TILE)
                if maze[y,x] == 1:
                    pygame.draw.rect(screen, (20,20,20), rect)
                else:
                    pygame.draw.rect(screen, (220,220,240), rect)
        
        gx, gy = goal
        draw_cat(screen, offset_x + gx*TILE + (TILE - CAT_SIZE)//2, offset_y + gy*TILE + (TILE - CAT_SIZE)//2, CAT_SIZE, (200,160,200))
        
        px, py = player_cell
        draw_player(screen, offset_x + px*TILE + (TILE - PLAYER_SIZE)//2, offset_y + py*TILE + (TILE - PLAYER_SIZE)//2, PLAYER_SIZE, player_color, player_direction, use_white=False)

        draw_timer_bar(elapsed, total_time)
        draw_text(screen, f"남은시간: {max(0, int(total_time - elapsed))}초", 20, 45)
        pygame.display.flip()

        if elapsed >= total_time:
            return False

# ---------- Day4: 피하기 ----------
def mission_day4():
    player = Entity(random.randint(40, WINDOW_W-40-PLAYER_SIZE), random.randint(120, WINDOW_H-120-PLAYER_SIZE), PLAYER_SIZE, (180,180,255))
    cat = Entity(random.randint(40, WINDOW_W-40-CAT_SIZE), random.randint(120, WINDOW_H-120-CAT_SIZE), CAT_SIZE, (200,160,200))
    cat.speed = 200
    total_time = 20.0
    start = time.time()
    obstacles = []
    spawn_timer = 0
    spawn_interval = max(0.3, random.randint(RAND_MIN, RAND_MAX) / 20.0)
    cat_facing_left = False
    prev_cat_x = cat.x
    player_direction = 'front'

    while True:
        dt = clock.tick(FPS) / 1000.0
        elapsed = time.time() - start
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

        keys = pygame.key.get_pressed()
        move_x = move_y = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x = -1
            player_direction = 'left'
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x = 1
            player_direction = 'right'
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_y = 1
        
        # 아무 키도 안 눌렀으면 front
        if not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            if move_y == 0:
                player_direction = 'front'
        
        if move_x != 0 or move_y != 0:
            norm = math.hypot(move_x, move_y)
            player.x += (move_x / norm) * player.speed * dt
            player.y += (move_y / norm) * player.speed * dt
        player.x = max(10, min(WINDOW_W-player.size-10, player.x))
        player.y = max(80, min(WINDOW_H-player.size-10, player.y))

        if random.random() < 0.01 + 0.002 * random.randint(RAND_MIN, RAND_MAX):
            dx = player.x - cat.x
            dy = player.y - cat.y
            dist = max(1, math.hypot(dx,dy))
            cat.x += (dx / dist) * cat.speed * dt * 2.2
            cat.y += (dy / dist) * cat.speed * dt * 2.2
        else:
            cat.x += math.sin(time.time()*1.2) * 30 * dt
            cat.y += math.cos(time.time()*0.9) * 30 * dt

        if cat.x < prev_cat_x:
            cat_facing_left = True
        elif cat.x > prev_cat_x:
            cat_facing_left = False
        prev_cat_x = cat.x

        spawn_timer += dt
        if spawn_timer >= spawn_interval:
            spawn_timer = 0
            spawn_interval = max(0.2, random.randint(RAND_MIN, RAND_MAX) / 20.0)
            side = random.choice(['top','left','right'])
            if side == 'top':
                sx = random.randint(20, WINDOW_W-20)
                sy = 80
            elif side == 'left':
                sx = 20
                sy = random.randint(80, WINDOW_H-60)
            else:
                sx = WINDOW_W - 40
                sy = random.randint(80, WINDOW_H-60)
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
            if player.rect().colliderect(pygame.Rect(ob['x'], ob['y'], ob['w'], ob['h'])):
                return False
            if cat.rect().colliderect(pygame.Rect(ob['x'], ob['y'], ob['w'], ob['h'])):
                obstacles.remove(ob)
                break

        if player.rect().colliderect(cat.rect()):
            return False

        screen.fill(DAY_BG_COLORS[4])
        draw_player(screen, int(player.x), int(player.y), player.size, player.color, player_direction, use_white=False)
        draw_cat(screen, int(cat.x), int(cat.y), cat.size, cat.color, flip=cat_facing_left)
        for ob in obstacles:
            pygame.draw.rect(screen, (120,50,50), (int(ob['x']), int(ob['y']), ob['w'], ob['h']))

        draw_timer_bar(elapsed, total_time)
        draw_text(screen, f"남은시간: {max(0, int(total_time - elapsed))}초", 20, 45, color=BLACK)
        pygame.display.flip()

        if elapsed >= total_time:
            return True

# ---------- Day5: 재우기 ----------
def mission_day5():
    cat_x = WINDOW_W//2 - CAT_SIZE//2
    cat_y = WINDOW_H//2 - CAT_SIZE//2
    total_time = 10.0
    start = time.time()
    obstacles = []
    spawn_timer = 0
    spawn_interval = max(0.4, random.randint(RAND_MIN, RAND_MAX)/20.0)

    while True:
        dt = clock.tick(FPS) / 1000.0
        elapsed = time.time() - start

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

        spawn_timer += dt
        if spawn_timer >= spawn_interval:
            spawn_timer = 0
            spawn_interval = max(0.25, random.randint(RAND_MIN, RAND_MAX)/20.0)

            side = random.choice(['top','left','right','bottom'])
            if side == 'top':
                sx = random.randint(20, WINDOW_W-20); sy = 80
            elif side == 'bottom':
                sx = random.randint(20, WINDOW_W-20); sy = WINDOW_H-20
            elif side == 'left':
                sx = 20; sy = random.randint(80, WINDOW_H-60)
            else:
                sx = WINDOW_W-20; sy = random.randint(80, WINDOW_H-60)

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
        for ob in obstacles[:]:
            if math.hypot(ob['x'] - mx, ob['y'] - my) <= ob['r'] + 4:
                obstacles.remove(ob)

        cx = cat_x + CAT_SIZE/2
        cy = cat_y + CAT_SIZE/2
        for ob in obstacles:
            if math.hypot(ob['x'] - cx, ob['y'] - cy) <= ob['r'] + CAT_SIZE/2 - 4:
                return False

        screen.fill(DAY_BG_COLORS[5])
        draw_cat(screen, cat_x, cat_y, CAT_SIZE, (200,160,200), sleeping=True)

        for ob in obstacles:
            color = (150,150,150) if ob['type']=='dust' else (220,180,40) if ob['type']=='fly' else (120,200,240)
            pygame.draw.circle(screen, color, (int(ob['x']), int(ob['y'])), ob['r'])

        draw_timer_bar(elapsed, total_time)
        draw_text(screen, f"남은시간: {max(0, int(total_time - elapsed))}초", 20, 45)
        draw_text(screen, "마우스로 닿아서 장애물을 제거하세요!", 20, 65)
        pygame.display.flip()

        if elapsed >= total_time:
            return True



# ---------- 메인 ----------
def main_loop():
    while gs.running:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                gs.running = False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE or ev.key == pygame.K_RETURN:
                    if gs.show_title:
                        gs.show_title = False
                        gs.show_narration = True
                if ev.key == pygame.K_ESCAPE:
                    gs.running = False
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if gs.show_title:
                    gs.show_title = False
                    gs.show_narration = True

        if gs.show_title:
            title_screen()
            pygame.display.flip()
            continue

        if gs.show_narration:
            narration_screen()
            gs.show_narration = False
            gs.day = 1
            continue

        if 1 <= gs.day <= 5:
            screen.fill(DAY_BG_COLORS.get(gs.day, (30,30,30)))
            draw_text_center(screen, f"Day {gs.day}", 40)
            draw_text(screen, f"미션: {DAY_NARRATIVES[gs.day]}", 20, 80)
            pygame.display.flip()
            
            if gs.day == 1:
                ok = run_mission(1, mission_day1)
            elif gs.day == 2:
                ok = run_mission(2, mission_day2)
            elif gs.day == 3:
                ok = run_mission(3, mission_day3)
            elif gs.day == 4:
                ok = run_mission(4, mission_day4)
            elif gs.day == 5:
                ok = run_mission(5, mission_day5)
            else:
                ok = False

            if ok:
                gs.day += 1

            if gs.day > 5:
                gs.show_end = True
        elif gs.show_end:
            ending_screen()
            pygame.display.flip()
            for ev in pygame.event.get():
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    pygame.quit(); sys.exit()
        else:
            title_screen()
            pygame.display.flip()

if __name__ == "__main__":
    try:
        main_loop()
    except Exception as e:
        print("오류 발생:", e)
    finally:
        pygame.quit()