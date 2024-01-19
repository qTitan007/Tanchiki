import os
from random import randint

import pygame


# загружаем изображения
def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Не удаётся загрузить:', name)
        raise SystemExit(message)
    image = image.convert_alpha()
    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    return image


pygame.init()
size = WIDTH, HEIGHT = 1155, 770
FPS = 60
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Танчики")
clock = pygame.time.Clock()
DIRECTS = [[0, -1], [1, 0], [0, 1], [-1, 0]]  # направления танка / куда будет лететь пуля
TILE = 35
image_block = [load_image('break_wall.png'), load_image('wall.png'), load_image('indestructible_wall.png')]
image_tanks = [[load_image('p1_small_tank.png'), load_image('p1_medium_tank.png'), load_image('p1_heavy_tank.png')],
               [load_image('p2_small_tank.png'), load_image('p2_medium_tank.png'), load_image('p2_heavy_tank.png')]]
image_bangs = [load_image('bang1.png'), load_image('bang2.png'), load_image('bang3.png')]
image_screensaver = load_image('screensaver.png')
sound_engine = pygame.mixer.Sound('sound/engine.mp3')
sound_shoot = pygame.mixer.Sound('sound/shoot.mp3')
sound_tank_explosion = pygame.mixer.Sound('sound/tank_explosive.mp3')


# немного интерфейса
class UI:
    def __init__(self):
        self.font = pygame.font.Font(None, 30)

    def update(self):
        pass

    def draw(self):
        pygame.draw.line(screen, 'white', (WIDTH - TILE, 0), (WIDTH - TILE, HEIGHT), 2)
        screen.blit(self.font.render('P1:', 1, 'gray'), (WIDTH - TILE + 1, 1))
        screen.blit(self.font.render('P2:', 1, 'gray'), (WIDTH - TILE + 1, TILE * 2))
        for obj in objects:
            if obj.type == 'tank':
                if obj.color == 'green':
                    screen.blit(self.font.render(str(tank_kills[0]), 1, 'gray'), (WIDTH - TILE + 1, TILE / 2))
                elif obj.color == 'red':
                    screen.blit(self.font.render(str(tank_kills[1]), 1, 'gray'), (WIDTH - TILE + 1, TILE * 2.5))


# здесь создается танк
class Tank:
    def __init__(self, color, px, py, direct):
        objects.append(self)
        self.type = 'tank'
        self.rect = pygame.Rect(px, py, 30, 30)
        self.direct = direct  # направление
        self.color = color  # цвет
        self.shotTimer = 60  # задержка в 60 FPS
        self.cooldown = 0
        self.bulletSpeed = 7  # скорость пули

        # назначаем кнопки управления и картинку танка
        if color == 'green':
            self.view = tank_view[0]
            self.img_tank = image_tanks[0][self.view]
            self.KeyLEFT = pygame.K_a
            self.KeyRIGHT = pygame.K_d
            self.KeyUP = pygame.K_w
            self.KeyDOWN = pygame.K_s
            self.KeySHOOT = pygame.K_SPACE

        elif color == 'red':
            self.view = tank_view[1]
            self.img_tank = image_tanks[1][self.view]
            self.KeyLEFT = pygame.K_LEFT
            self.KeyRIGHT = pygame.K_RIGHT
            self.KeyUP = pygame.K_UP
            self.KeyDOWN = pygame.K_DOWN
            self.KeySHOOT = pygame.K_KP_0

        # расписываем характеристики танков каждого уровня
        if self.view == 0:
            self.moveSpeed = 4
            self.hp = 40
            self.bulletDamage = 20
            self.bullet_r = 2

        elif self.view == 1:
            self.moveSpeed = 3
            self.hp = 60
            self.bulletDamage = 40
            self.bullet_r = 4

        elif self.view == 2:
            self.moveSpeed = 2
            self.hp = 80
            self.bulletDamage = 60
            self.bullet_r = 6

        self.image = pygame.transform.rotate(self.img_tank, -self.direct * 90)  # меняем направление картинки
        self.rect = self.image.get_rect(center=self.rect.center)  # и определяем её центр

    def update(self):
        self.image = pygame.transform.rotate(self.img_tank, -self.direct * 90)
        self.rect = self.image.get_rect(center=self.rect.center)

        oldx, oldy = self.rect.topleft
        # меняем координаты и направление картинки, в зависимости от нажатой кнопки
        if keys[self.KeyLEFT]:
            if self.rect.x - self.moveSpeed >= 0:
                self.rect.x -= self.moveSpeed
            self.direct = 3
        elif keys[self.KeyRIGHT]:
            self.rect.x += self.moveSpeed
            self.direct = 1
        elif keys[self.KeyUP]:
            if self.rect.y - self.moveSpeed >= 0:
                self.rect.y -= self.moveSpeed
            self.direct = 0
        elif keys[self.KeyDOWN]:
            self.rect.y += self.moveSpeed
            self.direct = 2

        # если изменённые координаты пересекаются со стеной или другим танком
        for obj in objects:
            if obj != self and (obj.type[len(obj.type) - 4:] == 'wall' or obj.type == 'tank') \
                    and self.rect.colliderect(obj.rect):
                self.rect.topleft = oldx, oldy  # то возвращаем координаты

        if keys[self.KeySHOOT] and self.cooldown == 0:
            sound_shoot.set_volume((self.bullet_r + 1) * 0.1)  # звук выстрела
            sound_shoot.play()
            dx = DIRECTS[self.direct][0] * self.bulletSpeed  # скорость пули * направление
            dy = DIRECTS[self.direct][1] * self.bulletSpeed
            Bullet(self, self.rect.centerx, self.rect.centery, dx, dy, self.bulletDamage)  # создаем пулю
            self.cooldown = self.shotTimer
        if self.cooldown > 0:  # перезарядка
            self.cooldown -= 1

    def draw(self):
        screen.blit(self.image, self.rect)  # рисуем картинку танка

    def damage(self, value):
        self.hp -= value
        if self.hp <= 0:  # если не осталось hp
            sound_tank_explosion.set_volume((self.bullet_r + 1) * 0.1)  # звук уничтожения танка
            sound_tank_explosion.play()
            if self.color == 'green':  # если уничтожен зелёный танк
                # то красному:
                tank_kills[1] += 1  # +фраг
                # +лвл
                if tank_view[1] == 2:
                    tank_view[1] = 0
                else:
                    tank_view[1] += 1
            elif self.color == 'red':  # тоже самое , но на оборот
                tank_kills[0] += 1
                if tank_view[0] == 2:
                    tank_view[0] = 0
                else:
                    tank_view[0] += 1

            # респавн танков
            for obj in objects:
                if obj.type == 'tank':
                    objects.remove(obj)
            remove_list = []
            for obj in objects:
                if obj.type == 'tank':
                    remove_list.append(obj)
            for obj in remove_list:
                objects.remove(obj)
            field.spawn_tank()  # спавн танков


# здесь создается пуля
class Bullet:
    def __init__(self, parent, px, py, dx, dy, damage):
        bullets.append(self)
        self.parent = parent
        self.px, self.py = px, py
        self.dx, self.dy = dx, dy
        self.damage = damage

        # размер пули
        for obj in objects:
            if obj == self.parent:
                self.bullet_r = obj.bullet_r

    def update(self):
        # обновляем позицию пули
        self.px += self.dx
        self.py += self.dy

        if self.px < 0 or self.px > WIDTH or self.py < 0 or self.py > HEIGHT:  # если улетела за карту
            bullets.remove(self)  # то удаляем
        else:  # иначе
            for obj in objects:
                # ищем в кого попала и наносим ему урон (кроме неразрушимой стены)
                if obj != self.parent and obj.type != 'bang' and obj.rect.collidepoint(self.px, self.py):
                    obj.damage(self.damage)
                    bullets.remove(self)
                    if obj.type != 'indestructible_wall':
                        Bang(self.px, self.py, self.bullet_r)  # анимация попадания
                    break

    def draw(self):
        pygame.draw.circle(screen, 'white', (self.px, self.py), self.bullet_r)  # рисуем пулю


# анимация попадания
class Bang:
    def __init__(self, px, py, bullet_r):
        objects.append(self)
        self.type = 'bang'
        self.px, self.py = px, py
        self.frame = 0
        self.bullet_r = bullet_r

    def update(self):
        # меняем картинку или удаляем объект
        self.frame += 0.3
        if self.frame >= 3:
            objects.remove(self)

    def draw(self):
        # определяем картинку и её место
        img = pygame.transform.scale(image_bangs[int(self.frame)], (self.bullet_r * 6, self.bullet_r * 6))
        rect = img.get_rect(center=(self.px, self.py))
        screen.blit(img, rect)  # рисуем


# создаем стену
class Block:
    def __init__(self, type, px, py, size, hp):
        objects.append(self)
        self.type = type
        self.rect = pygame.Rect(px, py, size, size)
        self.hp = hp

    def update(self):
        pass

    def draw(self):
        # у стен есть 3 вида
        if self.type == 'break_wall':  # легко разрушается
            screen.blit(image_block[0], self.rect)
        elif self.type == 'wall':  # долго разрушается
            screen.blit(image_block[1], self.rect)
        elif self.type == 'indestructible_wall':  # не должна разрушаться
            screen.blit(image_block[2], self.rect)

    def damage(self, value):
        if self.type != 'indestructible_wall':
            self.hp -= value
            if self.hp <= 0:
                objects.remove(self)


# создаем уровень
class Create_level:
    def __init__(self, name):
        self.n = str(name)
        self.level = ()

    def load_level(self):  # загрузка из файла
        filename = 'map/' + self.n
        with open(filename, 'r') as mapFile:
            level_map = [line.strip() for line in mapFile]
        max_width = max(map(len, level_map))
        self.level = list(map(lambda x: list(x.ljust(max_width, '.')), level_map))

    def generate_level(self):  # генерация
        for y in range(len(self.level)):
            for x in range(len(self.level[y])):
                if self.level[y][x] == '-':
                    Block('break_wall', TILE * x, TILE * y, TILE, 20)
                elif self.level[y][x] == '=':
                    Block('wall', TILE * x, TILE * y, TILE, 150)
                elif self.level[y][x] == '|':
                    Block('indestructible_wall', TILE * x, TILE * y, TILE, 1)

    def spawn_tank(self):  # случайный спавн танков
        color = 'green'
        direct = randint(0, 3)
        for _ in range(2):
            while True:
                x = randint(0, WIDTH // TILE - 1) * TILE
                y = randint(0, HEIGHT // TILE - 1) * TILE
                rect = pygame.Rect(x, y, TILE, TILE)
                fined = False
                for obj in objects:
                    if rect.colliderect(obj.rect):
                        fined = True
                if not fined:
                    Tank(color, x, y, direct)
                    direct = randint(0, 3)
                    color = 'red'
                    break


tank_kills = [0, 0]  # фраги
tank_view = [0, 0]  # уровень танка
ui = UI()
objects = []  # сюда записываются блоки, танки, анимацию взрыва
bullets = []  # а вот сюда - выстреливаемые пули

winner = '0'  # пока нет победителя
running = True  # запуск окна
start = True  # стартового экрана
play = False  # игры
while running:
    y_image_screensaver = -188
    pygame.mixer.music.load('sound/them.mp3')  # музыка стартового экрана
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play()
    while start:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                start = False
                play = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:  # если нажата кнопка '1'
                    bullets = []
                    objects = []
                    field = Create_level('1.map')  # генерируем 1-ую карту
                    field.load_level()
                    field.generate_level()
                    field.spawn_tank()
                    sound_engine.set_volume(0.03)
                    sound_engine.play(-1)
                    play = True
                    start = False
                elif event.key == pygame.K_2:  # если нажата кнопка '2'
                    bullets = []
                    objects = []
                    field = Create_level('2.map')  # генерируем 2-ую карту
                    field.load_level()
                    field.generate_level()
                    field.spawn_tank()
                    sound_engine.set_volume(0.03)
                    sound_engine.play(-1)
                    play = True
                    start = False

        # чтобы не был пустой, черный экран:
        if y_image_screensaver < HEIGHT // 6:
            screen.fill('black')
            y_image_screensaver += 5
            screen.blit(image_screensaver, (355, y_image_screensaver, 200, 70))
        else:
            font = pygame.font.Font(None, 50)
            screen.blit(font.render('SELECT LEVEL (keyboard 1-2)', 1, '#B53120'), (WIDTH / 3.5, HEIGHT / 2))
        pygame.display.update()
        clock.tick(FPS)

    while play:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                play = False
                start = False
            elif event.type == pygame.KEYDOWN and int(winner) > 0:  # если определён победитель
                if event.key == pygame.K_KP_ENTER:  # и нажат 'NUM Enter'
                    tank_kills = [0, 0]  # сбрасываем фраги
                    tank_view = [0, 0]  # и уровень
                    winner = '0'  # и победителя...
                    play = False  # завершаем игру
                    start = True  # переходим на стартовый экран

        if int(winner[0]) > 0:  # если определён победитель
            sound_engine.stop()  # выключаем фоновый звук
            screen.fill('black')
            font = pygame.font.Font(None, 100)
            # показываем победителя
            screen.blit(font.render(f'PLAYER {winner} WIN', 1, 'white'), (WIDTH // 3.5, HEIGHT // 3))
            font = pygame.font.Font(None, 50)
            # и подсказку
            screen.blit(font.render('restart: "Enter"', 1, 'white'), (WIDTH // 5, HEIGHT // 2))

        else:
            keys = pygame.key.get_pressed()  # считываем нажатую кнопку
            for obj in objects:
                obj.update()  # обновляем объекты
            for bullet in bullets:
                bullet.update()  # обновляем положение пуль
            ui.update()  # обновляем интерфейс

            # и рисуем
            screen.fill('black')
            for obj in objects:
                obj.draw()
            for bullet in bullets:
                bullet.draw()

            # определяем победителя
            if tank_kills[0] >= 10:
                winner = '1'
            elif tank_kills[1] >= 10:
                winner = '2'
            ui.draw()  # и снова рисуем
        pygame.display.update()
        clock.tick(FPS)
pygame.quit()
