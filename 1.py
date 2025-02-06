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
        self.frames = []
        self.cut_sheet(load_image("bullet_sprite.png"), 1, 1)  # Загрузка спрайтов для анимации
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.animation_speed = 0.1  # Скорость анимации
        self.animation_timer = 0

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        # Двигаем пулю в направлении, заданном векторами
        self.rect.x += self.direction[0] * BULLET_SPEED
        self.rect.y += self.direction[1] * BULLET_SPEED

        # Удаляем пулю, если она выходит за пределы экрана
        if self.rect.bottom < 0 or self.rect.left > WIDTH or self.rect.right < 0 or self.rect.top > HEIGHT:
            self.kill()

        # Обновление анимации
        self.animation_timer += self.animation_speed
        if self.animation_timer >= 1:  # Каждую секунду переключаем кадр
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]
            self.animation_timer = 0


# Класс анимации убийства врага
class EnemyKillAnimation(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = []
        self.cut_sheet(load_image("enemykill_sprite.png"), 12, 1)  # Загрузка спрайтов для анимации убийства
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 0  # Анимация не движется

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        if self.frames:  # Проверяем, что список не пуст
            self.cur_frame += 1
            if self.cur_frame >= len(self.frames):
                self.kill()  # Удаляем анимацию после завершения
            else:
                self.image = self.frames[self.cur_frame]


# Класс врага
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.hp = 1
        self.frames = []
        self.cut_sheet(load_image("Enemy_sprite.png"), 1, 1)  # Загрузка спрайтов для Enemy
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = ENEMY_SPEED

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def kills(self, hit):
        if hit:
            self.hp -= 1
        if self.hp <= 0:
            self.kill()
            kill_sound = pygame.mixer.Sound("kill_sound.mp3")
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

        # Анимация
        if self.frames:  # Проверяем, что список не пуст
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]


class Fat_enemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.hp = 3
        self.frames = []
        self.cut_sheet(load_image("Fatenemy_sprite.png"), 1, 1)  # Загрузка спрайтов для Fat_enemy
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = ENEMY_SPEED // 2

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self, player, obstacles):
        super().update(player, obstacles)  # Вызов метода обновления родительского класса
        if self.frames:  # Проверяем, что список не пуст
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]


class Fast_enemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.hp = 1
        self.frames = []
        self.cut_sheet(load_image("Fastenemy_sprite.png"), 1, 1)  # Загрузка спрайтов для Fast_enemy
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = ENEMY_SPEED * 2

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self, player, obstacles):
        super().update(player, obstacles)  # Вызов метода обновления родительского класса
        if self.frames:  # Проверяем, что список не пуст
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]


# Класс препятствия
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.frames = []
        self.cut_sheet(load_image("stone_sprite.png"), 1, 1)  # Загрузка спрайтов для анимации
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.animation_speed = 0.1  # Скорость анимации
        self.animation_timer = 0

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        # Обновление анимации
        self.animation_timer += self.animation_speed
        if self.animation_timer >= 1:  # Каждую секунду переключаем кадр
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]
            self.animation_timer = 0


# Функция для отображения меню
def show_menu(screen):
    background = load_image("MainMenu_background.jpg")  # Загрузка фона меню
    start_button = Button("Start", WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 100)
    exit_button = Button("Exit", WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 100)

    # Загрузка и воспроизведение музыки для главного меню
    pygame.mixer.music.load("mainmenu_music.wav")  # Убедитесь, что файл находится в той же папке
    pygame.mixer.music.play(-1)  # Зацикливаем музыку

    while True:
        screen.blit(background, (0, 0))  # Отрисовка фона
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
                        pygame.mixer.music.stop()  # Останавливаем музыку перед началом игры
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


def show_game_over_screen(screen):
    font = pygame.font.Font(None, 74)
    text_surface = font.render("Game Over", True, RED)
    text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))

    restart_button = Button("Restart", WIDTH // 2 - 100, HEIGHT // 2 + 10, 200, 100)
    exit_button = Button("Exit", WIDTH // 2 - 100, HEIGHT // 2 + 70, 200, 100)

    while True:
        screen.fill(BLACK)  # Заливаем экран черным цветом
        screen.blit(text_surface, text_rect)  # Отображаем текст "Game Over"
        restart_button.draw(screen)
        exit_button.draw(screen)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # ЛКМ
                    mouse_pos = pygame.mouse.get_pos()
                    if restart_button.is_hovered(mouse_pos):  # Перезапустить игру
                        return True
                    if exit_button.is_hovered(mouse_pos):  # Выйти из игры
                        pygame.quit()
                        sys.exit()


# Основная функция игры
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Simple Isaac-like Game")
    clock = pygame.time.Clock()

    show_menu(screen)  # Показать меню перед началом игры

    pygame.mixer.music.load("Game_Music.mp3")  # Убедитесь, что файл находится в той же папке
    pygame.mixer.music.play(-1)

    player = Player(load_image("player_sprite.png"), 5, 4, 80, 80)
    player_group = pygame.sprite.GroupSingle(player)
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()
    enemy_kill_animations = pygame.sprite.Group()  # Группа для анимаций убийства врагов


    # Загрузка фона игры
    background_game = load_image("background_game.png")  # Загрузка фона игры

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
                    shot_sound = pygame.mixer.Sound("shot_sound.mp3")  # Загрузка звука выстрела
                    shot_sound.play()  # Воспроизведение звука выстрела

        # Обновление
        player_group.update(obstacles)
        bullets.update()
        enemies.update(player, obstacles)
        enemy_kill_animations.update()  # Обновление анимаций убийства

        # Проверка на столкновения между пулями и врагами
        for bullet in bullets:
            hit_enemies = pygame.sprite.spritecollide(bullet, enemies, False)
            for enemy in hit_enemies:
                kill_count += enemy.kills(hit=True)  # Убийство врага + пополнение числа убийств
                bullet.kill()  # Удаляем пулю после столкновения
                # Создаем анимацию убийства врага
                enemy_kill_animation = EnemyKillAnimation(enemy.rect.centerx, enemy.rect.centery)
                enemy_kill_animations.add(enemy_kill_animation)

        # Проверка на столкновения между пулями и препятствиями
        for bullet in bullets:
            if pygame.sprite.spritecollideany(bullet, obstacles):
                bullet.kill()  # Удаляем пулю при столкновении с препятствием

        # Проверка на столкновения между игроком и врагами
        if pygame.sprite.spritecollideany(player, enemies):
            if show_game_over_screen(screen):  # Если игрок умирает, показываем экран смерти
                main()  # Перезапускаем игру
            running = False  # Завершаем игру при столкновении

        # Проверка на столкновения между игроком и врагами
        if pygame.sprite.spritecollideany(player, enemies):
            print("Игрок умер!")  # Здесь можно добавить логику для завершения игры
            running = False  # Завершаем игру при столкновении

        # Ограничение движения игрока в пределах экрана
        player.rect.x = max(0, min(WIDTH - player.rect.width, player.rect.x))
        player.rect.y = max(0, min(HEIGHT - player.rect.height, player.rect.y))

        # Отрисовка
        screen.blit(background_game, (0, 0))  # Отрисовка фона игры
        player_group.draw(screen)
        bullets.draw(screen)
        enemies.draw(screen)
        obstacles.draw(screen)
        enemy_kill_animations.draw(screen)  # Отрисовка анимаций убийства

        # Отображение счетчика убийств
        font = pygame.font.Font(None, 36)
        kill_count_surface = font.render(f'Убийства: {kill_count}', True, PURPLE)  # Изменяем цвет на фиолетовый
        screen.blit(kill_count_surface, (200, 200))  # Отображаем в верхнем левом углу

        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
