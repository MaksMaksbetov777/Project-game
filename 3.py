import os
import sys
import pygame
import math
import random

# Инициализация Pygame
pygame.init()

# Константы
WIDTH, HEIGHT = 1920, 1080  # Увеличиваем размеры карты
FPS = 75
PLAYER_SPEED = 5
BULLET_SPEED = 35
ENEMY_SPEED = 2
SPAWN_RATE = 600  # Время в миллисекундах между спавном врагов

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)  # Цвет пуль
RED = (255, 0, 0)  # Цвет врагов
BLUE = (0, 0, 255)  # Цвет препятствий
GREEN = (0, 255, 0)  # Цвет кнопок
PURPLE = (128, 0, 128)  # Фиолетовый цвет для счетчика убийств


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


# Класс кнопки
class Button:
    def __init__(self, text, x, y, width, height):
        self.font = pygame.font.Font(None, 74)
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = GREEN
        self.hover_color = (0, 200, 0)

    def draw(self, screen):
        # Отрисовка кнопки
        pygame.draw.rect(screen, self.color, self.rect)
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


# Класс игрока
class Player(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y):
        super().__init__()
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)
        self.health = 3
        self.direction = (0, -1)  # Изначально направлен вверх

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self, obstacles):
        keys = pygame.key.get_pressed()
        original_position = self.rect.topleft

        if keys[pygame.K_a]:
            self.rect.x -= PLAYER_SPEED
            self.direction = (-1, 0)
        if keys[pygame.K_d]:
            self.rect.x += PLAYER_SPEED
            self.direction = (1, 0)

        if pygame.sprite.spritecollideany(self, obstacles):
            self.rect.x = original_position[0]

        if keys[pygame.K_w]:
            self.rect.y -= PLAYER_SPEED
            self.direction = (0, -1)
        if keys[pygame.K_s]:
            self.rect.y += PLAYER_SPEED
            self.direction = (0, 1)

        if pygame.sprite.spritecollideany(self, obstacles):
            self.rect.y = original_position[1]

        self.direction = (0, 0)

        # Ограничение движения игрока в пределах экрана
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(HEIGHT - self.rect.height, self.rect.y))

        # Отрисовка спрайта
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]


# Класс пули
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(YELLOW)  # Изменяем цвет пули на желтый
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction

    def update(self):
        # Двигаем пулю в направлении, заданном векторами
        self.rect.x += self.direction[0] * BULLET_SPEED
        self.rect.y += self.direction[1] * BULLET_SPEED

        # Удаляем пулю, если она выходит за пределы экрана
        if self.rect.bottom < 0 or self.rect.left > WIDTH or self.rect.right < 0 or self.rect.top > HEIGHT:
            self.kill()


# Класс врага
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.hp = 1
        self.image = pygame.Surface((40, 40))
        self.image.fill(RED)  # Изменяем цвет врага на красный
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = ENEMY_SPEED

    def kills(self, hit):
        if hit:
            self.hp -= 1
        if self.hp <= 0:
            self.kill()
            kill_sound = pygame.mixer.Sound("kill_sound.wav")
            kill_sound.play()  # Воспроизводим звук убийства
            return 1
        return 0

    def update(self, player, obstacles):
        original_position = self.rect.topleft

        if player.rect.x < self.rect.x:
            self.rect.x -= self.speed
            if pygame.sprite.spritecollideany(self, obstacles):
                self.rect.x = original_position[0]
        elif player.rect.x > self.rect.x:
            self.rect.x += self.speed
            if pygame.sprite.spritecollideany(self, obstacles):
                self.rect.x = original_position[0]

        if player.rect.y < self.rect.y:
            self.rect.y -= self.speed
            if pygame.sprite.spritecollideany(self, obstacles):
                self.rect.y = original_position[1]
        elif player.rect.y > self.rect.y:
            self.rect.y += self.speed
            if pygame.sprite.spritecollideany(self, obstacles):
                self.rect.y = original_position[1]


class Fat_enemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.hp = 3
        self.image = pygame.Surface((60, 60))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = ENEMY_SPEED // 2

class Fast_enemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.hp = 1
        self.image = pygame.Surface((30, 30))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = ENEMY_SPEED * 2

# Класс препятствия
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(BLUE)  # Цвет препятствия
        self.rect = self.image.get_rect(topleft=(x, y))


# Функция для отображения меню
def show_menu(screen):
    start_button = Button("Start", WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 100)
    exit_button = Button("Exit", WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 100)

    while True:
        screen.fill(BLACK)
        start_button.draw(screen)
        exit_button.draw(screen)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # ЛКМ
                    mouse_pos = pygame.mouse.get_pos()
                    if start_button.is_hovered(mouse_pos):  # Начать игру
                        return
                    if exit_button.is_hovered(mouse_pos):  # Выйти из игры
                        pygame.quit()
                        exit()


# Функция для спавна врагов
def spawn_enemy(enemies, type_en=Enemy):
    side = random.choice(['top', 'bottom', 'left', 'right'])
    if side == 'top':
        x = random.randint(0, WIDTH)
        y = 0
    elif side == 'bottom':
        x = random.randint(0, WIDTH)
        y = HEIGHT
    elif side == 'left':
        x = 0
        y = random.randint(0, HEIGHT)
    else:  # side == 'right'
        x = WIDTH
        y = random.randint(0, HEIGHT)
    enemy = type_en(x, y)
    enemies.add(enemy)


# Основная функция игры
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Simple Isaac-like Game")
    clock = pygame.time.Clock()

    # Загрузка и воспроизведение музыки
    pygame.mixer.music.load("doom_music.wav")  # Убедитесь, что файл находится в той же папке
    pygame.mixer.music.play(-1)  # Зацикливаем музыку

    # Загрузка звукового эффекта для убийства врага

    show_menu(screen)  # Показать меню перед началом игры

    player = Player(load_image("123.png"), 5, 4, 80, 80)
    player_group = pygame.sprite.GroupSingle(player)
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()

    # Переменная для хранения количества убитых врагов
    kill_count = 0

    # Создание препятствий
    for _ in range(8):  # Создаем 8 препятствий
        width, height = random.randint(50, 100), random.randint(50, 100)
        x = random.randint(0, WIDTH - width)
        y = random.randint(0, HEIGHT - height)
        obstacle = Obstacle(x, y, width, height)
        obstacles.add(obstacle)

    # Таймер для спавна врагов
    spawn_timer = pygame.USEREVENT + 1
    pygame.time.set_timer(spawn_timer, SPAWN_RATE)

    spawn_timer_fat = pygame.USEREVENT + 2
    pygame.time.set_timer(spawn_timer_fat, SPAWN_RATE * 3)

    spawn_timer_fast = pygame.USEREVENT + 3
    pygame.time.set_timer(spawn_timer_fast, SPAWN_RATE * 4)
    Fast_enemy
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == 27:
                    running = False
            if event.type == pygame.QUIT:
                running = False
            # спавн врагов
            if event.type == spawn_timer:
                spawn_enemy(enemies)
            if event.type == spawn_timer_fat:
                spawn_enemy(enemies, Fat_enemy)
            if event.type == spawn_timer_fast:
                spawn_enemy(enemies, Fast_enemy)


            if event.type == pygame.MOUSEBUTTONDOWN:  # Проверяем нажатие кнопки мыши
                if event.button == 1:  # ЛКМ
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    # Вычисляем направление стрельбы
                    direction_x = mouse_x - player.rect.centerx
                    direction_y = mouse_y - player.rect.centery
                    length = math.hypot(direction_x, direction_y)
                    if length != 0:  # Избегаем деления на ноль
                        direction_x /= length
                        direction_y /= length
                    bullet = Bullet(player.rect.centerx, player.rect.centery, (direction_x, direction_y))
                    bullets.add(bullet)

        # Обновление
        player_group.update(obstacles)
        bullets.update()
        enemies.update(player, obstacles)

        # Проверка на столкновения между пулями и врагами
        for bullet in bullets:
            hit_enemies = pygame.sprite.spritecollide(bullet, enemies, False)
            for enemy in hit_enemies:
                kill_count += enemy.kills(hit=True)  # убийство врага + пополнение числа убийств
                bullet.kill()  # Удаляем пулю после столкновения

        # Проверка на столкновения между пулями и препятствиями
        for bullet in bullets:
            if pygame.sprite.spritecollideany(bullet, obstacles):
                bullet.kill()  # Удаляем пулю при столкновении с препятствием

        # Проверка на столкновения между игроком и врагами
        if pygame.sprite.spritecollideany(player, enemies):
            print("Игрок умер!")  # Здесь можно добавить логику для завершения игры
            running = False  # Завершаем игру при столкновении

        # Ограничение движения игрока в пределах экрана
        player.rect.x = max(0, min(WIDTH - player.rect.width, player.rect.x))
        player.rect.y = max(0, min(HEIGHT - player.rect.height, player.rect.y))

        # Отрисовка
        screen.fill(BLACK)
        player_group.draw(screen)
        bullets.draw(screen)
        enemies.draw(screen)
        obstacles.draw(screen)

        # Отображение счетчика убийств
        font = pygame.font.Font(None, 36)
        kill_count_surface = font.render(f'Убийства: {kill_count}', True, PURPLE)  # Изменяем цвет на фиолетовый
        screen.blit(kill_count_surface, (200, 200))  # Отображаем в верхнем левом углу

        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
