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
#texture_data = image.tobytes("raw", "RGBA", 0, -1)
texture_data = image.tobytes()
img_width, img_height = image.size

#Class / Function Definitions 
def translate_to_world_coords(screenx, screeny):
    x = (screenx / screen_dimx) * screen_rightx
    y = (screeny - screen_dimy / 2) / screen_dimy * screen_topy
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
        # TODO: Bouncing off the top / bottom should not change x direction
        #       Bouncing off the side should not change y direction
        if self.active:
            # Check if ball is hitting the side of a block
            if ((ball.x + ball.radius >= self.x and ball.x < self.x) or \
                    (ball.x - ball.radius <= self.x + self.WIDTH and ball.x > self.x + self.WIDTH)) and \
                    (ball.y > self.y and ball.y < self.y + self.HEIGHT):
                self.active = False
                print(f"""
Ball hit the side of a block
ball.pos = {ball.x},{ball.y}
ball.velocity = {ball.vx},{ball.vy}
ball.speed = {ball.speed}
ball.bounced = {ball.bounced}
self.pos = {self.x},{self.y}
                        """)
                if not ball.bounced: # ball can hit 2 blocks in one frame, but should not bounce off both
                    ball.vx = -1 * ball.vx
                    ball.bounced = True
                return True
            #Check if ball is hitting the top or bottom of the block
            if ((ball.y + ball.radius >= self.y and ball.y <= self.y) or \
                    (ball.y - ball.radius <= self.y + self.HEIGHT and ball.y >= self.y + self.HEIGHT)) and \
                    (ball.x > self.x and ball.x < self.x + self.WIDTH):
                self.active = False
                print(f"""
Ball hit the bottom or top of a block
ball.pos = {ball.x},{ball.y}
ball.velocity = {ball.vx},{ball.vy}
ball.speed = {ball.speed}
ball.bounced = {ball.bounced}
self.pos = {self.x},{self.y}
""")
                if not ball.bounced: # ball can hit 2 blocks in one frame, but should not bounce off both
                    ball.vy = -1 * ball.vy
                    ball.bounced = True
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
    SCALE = 1.25
    WIDTH = 1.5 * SCALE
    HEIGHT = 0.15 * SCALE

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

    def wallCollision(self):
        #Correct for screen borders
        if self.y > screen_topy - self.radius:
            print('cieling collision')
            self.vy = -1 * self.vy
        if self.x < self.radius or self.x > screen_rightx - self.radius:
            print('wall collision')
            self.vx = -1 * self.vx

    def update(self):
        #print(self.vx, self.vy)
        self.x = self.x + self.vx
        self.y = self.y + self.vy

class Game:
    BLOCKS_PER_ROW = 10

    def __init__(self):
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
            TextBlock(8,25,'0'),
        ]
        self.lives_label = [
            TextBlock(10,25,'L'),
            TextBlock(11,25,'I'),
            TextBlock(12,25,'V'),
            TextBlock(13,25,'E'),
            TextBlock(14,25,'S'),
            TextBlock(15,25,':'),
            TextBlock(16,25,'0'),
            TextBlock(17,25,'0'),
        ]
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
        self.lives = self.lives - 1
        self.balls.remove(ball)
        self.balls.append(Ball())

        if self.lives <= 0:
            self.over = True

    def draw_lives(self):
        self.lives_label[7].setChar(str(self.lives % 10))
        self.lives_label[6].setChar(str(self.lives // 10))

        for quad in self.lives_label:
            quad.draw()
    #print('Lives:',self.lives)

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
    #print('Score:',self.score)

    def loop(self):
        if all(not b.active for b in self.blocks if not isinstance(b, Paddle)):
            self.screen = self.screen + 1
            self.balls = [Ball() for i in range(self.screen)]
            self.init_blocks()


        for ball in self.balls:
            ball.bounced = False
            for block in self.blocks:
                if block.resolveCollision(ball):
                    self.score = self.score + block.value
                if block.active:
                    block.draw()

            ball.wallCollision()
            ball.update()
            if ball.y + ball.radius < self.paddle.y:
                self.lose_life(ball)
            ball.draw()

        self.draw_lives()
        self.draw_score()

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

def cursor_pos_callback(window, xpos, ypos):
    new_pos = translate_to_world_coords(xpos, 0)
    new_x = new_pos[0]
    game.paddle.setX(new_x - Paddle.WIDTH / 2)

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

            TextBlock(1,10.1,'P'),
            TextBlock(2,10,'r'),
            TextBlock(3,10,'e'),
            TextBlock(4,10,'s'),
            TextBlock(5,10,'s'),
            TextBlock(7,10,'R'),
            TextBlock(9,10,'T'),
            TextBlock(10,10,'o'),
            TextBlock(12,10,'R'),
            TextBlock(13,10,'e'),
            TextBlock(14,10,'s'),
            TextBlock(15,10,'t'),
            TextBlock(16,10,'a'),
            TextBlock(17,10,'r'),
            TextBlock(18,10,'t'),
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

glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, img_width, img_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)

#Main Loop
while not glfw.window_should_close(window):
    glClearColor(0.0,0.0,0.0,1.0)
    glClear(GL_COLOR_BUFFER_BIT)

    if not game.over:
        game.loop()
    else:
        for char in game_over_label:
            char.draw()

    glfw.swap_buffers(window)
    glfw.poll_events()

glfw.terminate()
