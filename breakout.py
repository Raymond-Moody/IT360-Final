import glfw
import math
import random
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from PIL import Image

BALL_SPEED_MULT = 1.2
#Screen size information
screen_dimx = 500
screen_dimy = 650
screen_leftx = 0
screen_rightx = 20
screen_topy = 26
screen_bottomy = 0
char_width = 1 / 16
char_height = 1 / 6.4

cheating = False

char_dict = {
    'S' : (3,4),
    'C' : (12,0),
    'O' : (3,0),
    'R' : (3,3),
    'E' : (14,0),
    'L' : (4,0),
    'I' : (4,3),
    'V' : (5,0),
    '0' : (7,5),
    '1' : (7,0),
    '2' : (7,1),
    '3' : (7,2),
    '4' : (7,3),
    '5' : (7,4),
    '6' : (8,0),
    '7' : (8,1),
    '8' : (8,2),
    '9' : (8,3),
    ':' : (2,0),
    'G' : (6,5),
    'A' : (10,0),
    'M' :  (0,3),
    'P' :  (2,2),
    'r' :  (13,1),
    'e' :  (9,2.8),
    's' :  (12,1),
    'T' :  (4,5),
    't' :  (8,4),
    'a' :  (10,1),
    'o' :  (9,1),
}

image = Image.open("vcr.png")
#texture_data = image.tobytes("raw", "I", 0, -1)
texture_data = image.tobytes()
img_width, img_height = image.size

#Class / Function Definitions 
def distance(x1, y1, x2, y2):
    dx = x2-x1
    dy = y2-y1
    return sqrt(dx*dx + dy+dy)

def translate_to_world_coords(screenx, screeny):
    x = (screenx / screen_dimx) * screen_rightx
    y = screen_topy - (screeny / screen_dimy) * screen_topy
    return (x, y)

class TextBlock:
    WIDTH = 1
    HEIGHT = 1.25

    def __init__(self, x, y, char):
        self.x = x
        self.y = y
        self.char_x, self.char_y = char_dict[char]
        self.char_x = self.char_x * char_width
        self.char_y = self.char_y * char_height

    def setChar(self, char):
        self.char_x, self.char_y = char_dict[char] 
        self.char_x = self.char_x * char_width
        self.char_y = self.char_y * char_height

    def draw(self):
        glEnable(GL_TEXTURE_2D)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(self.char_x, self.char_y + char_height); glVertex2f(self.x, self.y)
        glTexCoord2f(self.char_x + char_width, self.char_y + char_height); glVertex2f(self.x + self.WIDTH, self.y)
        glTexCoord2f(self.char_x + char_width, self.char_y); glVertex2f(self.x + self.WIDTH, self.y + self.HEIGHT)
        glTexCoord2f(self.char_x, self.char_y); glVertex2f(self.x, self.y + self.HEIGHT)
        glEnd()
        glDisable(GL_TEXTURE_2D)

class Block:
    SCALE = 1.75
    WIDTH = 1.0 * SCALE
    HEIGHT = 0.3 * SCALE

    def __init__(self, x, y, color, value):
        self.x = x
        self.y = y
        self.color = color
        self.value = value
        self.active = True

    def draw(self):
        glColor3f(*self.color)
        glBegin(GL_QUADS)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.WIDTH, self.y)
        glVertex2f(self.x + self.WIDTH, self.y + self.HEIGHT)
        glVertex2f(self.x, self.y + self.HEIGHT)
        glEnd()

    def resolveCollision(self, ball):
        if self.active:
            # Check if ball is hitting the side of a block
            left = self.x
            right = self.x + self.WIDTH
            bottom = self.y
            top = self.y + self.HEIGHT
            center_x = self.x + self.WIDTH / 2
            center_y = self.y + self.HEIGHT / 2
            ball_left = ball.x - ball.radius
            ball_right = ball.x + ball.radius
            ball_bottom = ball.y - ball.radius
            ball_top = ball.y + ball.radius
            
            #Ball is colliding
            if abs(ball.x - center_x) < ball.radius + self.WIDTH / 2 and \
                    abs(ball.y - center_y) < ball.radius + self.HEIGHT / 2:

                #Check if ball is hitting the top or bottom of the block
                if (ball_top >= bottom and ball_top - ball.vy < bottom) or (ball_bottom <= top and ball_bottom - ball.vy > top):
                    if not ball.bounced:
                        ball.vy = -1 * ball.vy
                        ball.bounced = True

                #ball must have hit the side
                else:
                    if not ball.bounced:
                        ball.vx = -1 * ball.vx
                        ball.bounced = True

                self.active = False
                return True
                
        return False

class YellowBlock(Block):
    def __init__(self, x, y):
        super().__init__(x, y, (1.0,1.0,0.0), 1)

class GreenBlock(Block):
    def __init__(self, x, y):
        super().__init__(x, y, (0.0,1.0,0.0), 3)

class OrangeBlock(Block):
    def __init__(self, x, y):
        super().__init__(x, y, (1.0,0.647,0.0), 5)

    def resolveCollision(self, ball):
        if super().resolveCollision(ball):
            if 'orange' in ball.speed_sources:
                ball.speed_sources.remove('orange')
                ball.speed = ball.speed * BALL_SPEED_MULT
            return True
        else:
            return False


class RedBlock(Block):
    def __init__(self, x, y):
        super().__init__(x, y, (1.0,0.0,0.0), 7)

    def resolveCollision(self, ball):
        if super().resolveCollision(ball):
            if 'red' in ball.speed_sources:
                ball.speed_sources.remove('red')
                ball.speed = ball.speed * BALL_SPEED_MULT
            return True
        else:
            return False

class Paddle(Block):
    WIDTH = 2.5
    #WIDTH = 1.875
    HEIGHT = 0.1875

    def __init__(self):
        super().__init__((screen_rightx - Paddle.WIDTH) / 2, 2, (1.0,1.0,1.0), 0)

    def resolveCollision(self, ball):
        if ball.x + ball.radius > self.x and ball.x - ball.radius < self.x + self.WIDTH and ball.y + ball.radius >= self.y and ball.y - ball.radius <= self.y + self.HEIGHT:
            ball.paddle_bounces = ball.paddle_bounces + 1
            if ball.paddle_bounces in ball.speed_sources:
                ball.speed_sources.remove(ball.paddle_bounces)
                ball.speed = ball.speed * BALL_SPEED_MULT

            dx = ball.x - (self.x + self.WIDTH / 2)
            max_dx = self.WIDTH / 2
            if dx > 0:
                if dx < max_dx / 4:
                    vx = 0.05
                elif dx > max_dx / 4 and dx < max_dx / 2:
                    vx = 0.25 
                elif dx > max_dx / 2 and dx < max_dx:
                    vx = 0.5
                else:
                    vx = 1.5
            else:
                if dx > -1 * max_dx / 4:
                    vx = -0.05
                elif dx < -1 * max_dx / 4 and dx > -1 * max_dx / 2:
                    vx = -0.25 
                elif dx < -1 * max_dx / 2 and dx > -1 * max_dx:
                    vx = -0.5
                else:
                    vx = -1.5

            vy = 1
            v_mag = math.sqrt(vx * vx + vy * vy)
            ball.vx = vx / v_mag * ball.speed
            ball.vy = vy / v_mag * ball.speed
            return True
        return False

    def move(self, direction):
        #direction: 1 = right, -1 = left
        speed = 0.5
        self.x = self.x + (speed * direction)
        if self.x < screen_leftx:
            self.x = screen_leftx
        if self.x > screen_rightx - self.WIDTH:
            self.x = screen_rightx - self.WIDTH 

    def setX(self, x):
        if x < screen_leftx:
            x = screen_leftx
        elif x > screen_rightx - Paddle.WIDTH:
            x = screen_rightx - Paddle.WIDTH
        self.x = x

class Ball:
    radius = 0.40

    def __init__(self):
        self.x = screen_rightx / 2
        self.y = 7
        self.vx = 0
        self.vy = 0
        self.speed = 0.2
        self.speed_sources = [4, 8, 12, 'orange', 'red']
        self.paddle_bounces = 0
        self.served = False
        self.bounced = False

    def serve(self):
        if not self.served:
            self.vy = -0.1
            self.served = True

    def draw(self):
        steps = 100
        step_size = 2 * math.pi / steps

        glPushMatrix()
        glColor3f(0.75,0.75,0.75)
        glLoadIdentity()
        glTranslate(2 * self.x / screen_rightx - 1, 2 * self.y / screen_topy - 1, 0)
        glBegin(GL_POLYGON)
        for i in range(steps):
            px = self.radius / screen_rightx * math.cos(i * step_size)
            py = self.radius / screen_topy * math.sin(i * step_size)
            glVertex2f(px, py)
        glEnd()
        glPopMatrix()

    def update(self):
        #print(self.vx, self.vy)
        self.x = self.x + self.vx
        self.y = self.y + self.vy

class Game:
    BLOCKS_PER_ROW = 10

    def __init__(self):
        self.paused = False
        self.over = False
        self.lives = 3
        self.score = 0
        self.screen = 1
        self.paddle = Paddle()
        self.balls = [Ball() for i in range(self.screen)]
        self.blocks = [self.paddle] 
        self.score_label = [
            TextBlock(0,25,'S'),
            TextBlock(1,25,'C'),
            TextBlock(2,25,'O'),
            TextBlock(3,25,'R'),
            TextBlock(4,25,'E'),
            TextBlock(5,25,':'),
            TextBlock(6,25,'0'),
            TextBlock(7,25,'0'),
            TextBlock(8,25,'0'),
            TextBlock(9,25,'0'),
        ]
        self.lives_label = [
            TextBlock(11,25,'L'),
            TextBlock(12,25,'I'),
            TextBlock(13,25,'V'),
            TextBlock(14,25,'E'),
            TextBlock(15,25,'S'),
            TextBlock(16,25,':'),
            TextBlock(17,25,'0'),
            TextBlock(18,25,'0'),
        ]
        self.screen_quad = TextBlock(0,0,'1')
        self.init_blocks()

    def init_blocks(self):
        for i in range(self.BLOCKS_PER_ROW):
            bx = i * (Block.WIDTH + 0.2) + 0.3
            self.blocks.append(YellowBlock(bx, 20))
            self.blocks.append(YellowBlock(bx, 20 + Block.HEIGHT + 0.1))
            self.blocks.append(GreenBlock(bx, 20 + 2 * (Block.HEIGHT + 0.1)))
            self.blocks.append(GreenBlock(bx, 20 + 3 * (Block.HEIGHT + 0.1)))
            self.blocks.append(OrangeBlock(bx, 20 + 4 * (Block.HEIGHT + 0.1)))
            self.blocks.append(OrangeBlock(bx, 20 + 5 * (Block.HEIGHT + 0.1)))
            self.blocks.append(RedBlock(bx, 20 + 6 * (Block.HEIGHT + 0.1)))
            self.blocks.append(RedBlock(bx, 20 + 7 * (Block.HEIGHT + 0.1)))

    def lose_life(self, ball):
        self.lives = max(self.lives - 1, 0)
        self.balls.remove(ball)
        self.balls.append(Ball())

        if self.lives <= 0:
            self.over = True

    def draw_lives(self):
        self.lives_label[7].setChar(str(self.lives % 10))
        self.lives_label[6].setChar(str(self.lives // 10))

        for quad in self.lives_label:
            quad.draw()

    def draw_score(self):
        temp_score = self.score
        self.score_label[9].setChar(str(temp_score % 10))
        temp_score = temp_score // 10
        self.score_label[8].setChar(str(temp_score % 10))
        temp_score = temp_score // 10
        self.score_label[7].setChar(str(temp_score % 10))
        temp_score = temp_score // 10
        self.score_label[6].setChar(str(temp_score % 10))
        for quad in self.score_label:
            quad.draw()

    def draw_screen_num(self):
        # Assume nobody is getting past screen 9
        self.screen_quad.setChar(str(self.screen % 10))
        self.screen_quad.draw()

    def loop(self):
        if all(not b.active for b in self.blocks if not isinstance(b, Paddle)):
            self.screen = self.screen + 1
            #self.balls.append(Ball())
            self.balls = [Ball() for _ in range(self.screen)]
            self.init_blocks()


        for ball in self.balls:
            ball.bounced = False
            for block in self.blocks:
                if block.resolveCollision(ball):
                    if (self.score + block.value) // 1000 > self.score // 1000:
                        self.lives = self.lives + 1
                    self.score = self.score + block.value

            if ball.y + ball.radius < self.paddle.y:
                self.lose_life(ball)
            elif ball.y > screen_topy - ball.radius:
                self.paddle.WIDTH = 1.875
                ball.vy = -1 * ball.vy

            if ball.x + ball.radius > screen_rightx or ball.x - ball.radius < screen_leftx:
                ball.vx = -1  * ball.vx

            ball.update()

    def render(self):
        self.draw_lives()
        self.draw_score()
        self.draw_screen_num()

        for block in self.blocks:
            if block.active:
                block.draw()

        for ball in self.balls:
            ball.draw()

    def move_paddle(self, direction):
        self.paddle.move(direction)

    def serve_ball(self):
        for ball in self.balls:
            ball.serve()
        
def key_callback(window, key, scancode, action, mods):
    if action == glfw.PRESS or action == glfw.REPEAT:
        if key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(window, True)
        elif key == glfw.KEY_A:
            game.move_paddle(-1)
        elif key == glfw.KEY_D:
            game.move_paddle(1)
        elif key == glfw.KEY_SPACE:
            game.serve_ball()
        elif key == glfw.KEY_R:
            game.__init__()
        elif key == glfw.KEY_X:
            game.over = True
        elif key == glfw.KEY_P:
            game.paused = not game.paused
        elif key == glfw.KEY_O and game.paused:
            game.loop()
        elif key == glfw.KEY_C:
            global cheating
            cheating = not cheating


def cursor_pos_callback(window, xpos, ypos):
    new_x, new_y = translate_to_world_coords(xpos, ypos)
    game.paddle.setX(new_x - Paddle.WIDTH / 2)
    if cheating:
        game.balls[0].x = new_x
        game.balls[0].y = new_y

def mouse_button_callback(window, button, action, mods):
    if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
        game.serve_ball()

#Initialize
game = Game()
game_over_label = [
            TextBlock(5,11,'G'),
            TextBlock(6,11,'A'),
            TextBlock(7,11,'M'),
            TextBlock(8,11,'E'),
            TextBlock(10,11,'O'),
            TextBlock(11,11,'V'),
            TextBlock(12,11,'E'),
            TextBlock(13,11,'R'),

            TextBlock(1,9.7,'P'),
            TextBlock(2,9.5,'r'),
            TextBlock(3,9.5,'e'),
            TextBlock(4,9.5,'s'),
            TextBlock(5,9.5,'s'),
            TextBlock(7,9.6,'R'),
            TextBlock(9,9.6,'T'),
            TextBlock(10,9.5,'o'),
            TextBlock(12,9.6,'R'),
            TextBlock(13,9.5,'e'),
            TextBlock(14,9.5,'s'),
            TextBlock(15,9.6,'t'),
            TextBlock(16,9.5,'a'),
            TextBlock(17,9.5,'r'),
            TextBlock(18,9.6,'t'),
] 

if not glfw.init():
    exit()

window = glfw.create_window(screen_dimx, screen_dimy, "Breakout", None, None) 
if not window:
    glfw.terminate()
    exit()
glfw.make_context_current(window)

glfw.set_key_callback(window, key_callback)
glfw.set_cursor_pos_callback(window, cursor_pos_callback)
glfw.set_mouse_button_callback(window, mouse_button_callback)

gluOrtho2D(screen_leftx,
            screen_rightx,
            screen_bottomy,
            screen_topy)


glEnable(GL_TEXTURE_2D)
texture_id = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, texture_id)

glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, img_width, img_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)

#Main Loop
while not glfw.window_should_close(window):
    glClearColor(0.0,0.0,0.0,1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    if not game.paused:
        if not game.over:
            game.loop()
        else:
            for char in game_over_label:
                char.draw()

    game.render()
    glfw.swap_buffers(window)
    glfw.poll_events()

glfw.terminate()
