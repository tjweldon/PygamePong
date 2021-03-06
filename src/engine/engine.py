import math
import random
import time

import pygame

from src.game_state.pongEntities import GameState, Ball, Paddle
from src.lib.physics.dynamics import Movable
from src.lib.spaces.orientedplane import OrientedPlane
from src.lib.spaces.vector import Vector


def changeColour(ball):
    randomRGB = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    ball.colour = randomRGB


def increaseX(ball):
    ball.vx += random.randint(50, 100)


def increaseY(ball):
    ball.vy += random.randint(50, 100)


def current_time():
    """
    Returns the current time.
    """
    return time.time()


def timeSince(when):
    """
    Returns the value of current_time minus a given value.
    """
    return current_time() - when


def updateGameState(gameState: GameState) -> GameState:
    """
    Checks event queue for user input.
    Tracks position and collision of each ball.
    Updates total score value based on return value from each ball.
    Tracks paddle and collision with walls.
    """
    e = pygame.event.poll()
    keys = pygame.key.get_pressed()

    if e.type == pygame.QUIT:
        gameState.gameOn = False

    if e.type == pygame.KEYDOWN and keys[pygame.K_SPACE]:
        gameState.spawnNewBall()

    if keys[pygame.K_RETURN]:
        gameState.spawnNewBall()

    for ball in gameState.liveBalls:
        if ball.x > gameState.width:
            gameState.liveBalls.remove(ball)

    if len(gameState.liveBalls) == 0:
        gameState.setGameOver()

    for ball in gameState.liveBalls:
        gameState.scoreValue = updateBall(ball, gameState)
    updatePaddle(gameState.paddle, gameState.border, gameState.height)

    return gameState


def paddleBounce(ball: Ball, paddle: Paddle):
    """
    Calculates a return angle for a ball colliding with the paddle.
    Rebound angle is determined by where the ball strikes the paddle.
    """
    paddleCOM = paddle.y + int(paddle.height * 0.5)
    speed = ball.getVelocity().getMagnitude()
    newSpeed = int(speed) + random.randint(-25, 50)
    newSpeed = max(newSpeed, 100)
    offset = -(paddleCOM - ball.y) * 2 / paddle.height
    reboundAngle = offset * math.pi / 3

    newVelocity = Vector.fromPolarCoOrds(-newSpeed, -reboundAngle)
    ball.setVelocity(newVelocity)


def wallBounce(ball: Ball, normal: Vector):
    """
    Inverts the x axis of a ball velocity vector.
    Increments the x value a random amount.
    """
    plane = OrientedPlane(normal)
    velocity = plane.reflect(ball.getVelocity())
    ball.setVelocity(velocity)


def updateBall(ball: Ball, gamestate: GameState):
    """
    Updates x and y position of the ball based on original positions combined with time differential.
    Detects collision with paddle or walls and reverses travel direction.
    Increments Score Value for display on score board.
    Destroys the ball if it travels off screen right.
    """
    now = current_time()
    paddle = gamestate.paddle
    height = gamestate.height
    border = gamestate.border
    scrValue = gamestate.scoreValue
    blocks = gamestate.blocks

    if ball.timeOfLastUpdate is None:
        timeSinceLastUpdate = 0.0
    else:
        timeSinceLastUpdate = timeSince(ball.timeOfLastUpdate)

    ball.timeOfLastUpdate = now
    nextPosition = getNextPosition(ball, timeSinceLastUpdate)

    hitboxes =[]
    for block in blocks:
        hitboxes.append(block.getHitBox())
    blockIndex = ball.getHitBox().collidelist(hitboxes)
    if blockIndex >= 0:
        block = blocks[blockIndex]
        positionDelta: Vector = ball.getPosition().diff(block.getCentre())
        theta = math.acos(positionDelta.normalise().x)
        verticalDistance = block.getDimensionsVector().getMagnitude() // 2 * math.sin(theta)
        verticalCollision = abs(verticalDistance) > block.getHeight() // 2

        if verticalCollision:
            normal = Vector(0, positionDelta.y).normalise()
        else:
            normal = Vector(positionDelta.x, 0).normalise()

        wallBounce(ball, normal)
        gamestate.blocks.remove(block)

    paddleCollision = ball.getHitBox().colliderect(paddle.getHitBox())
    if paddleCollision:
        paddleBounce(ball, paddle)

    hitBackWall = nextPosition.x < border + ball.RADIUS
    if hitBackWall:
        scrValue += 1
        wallBounce(ball, Vector(1, 0))
        increaseX(ball)

    hitTopWall = nextPosition.y < border + ball.RADIUS
    if hitTopWall:
        scrValue += 1
        wallBounce(ball, Vector(0, 1))

    hitBottomWall = nextPosition.y > height - border - ball.RADIUS
    if hitBottomWall:
        scrValue += 1
        wallBounce(ball, Vector(0, -1))
        print(ball.getPosition())

    move(ball, timeSinceLastUpdate)

    return scrValue


def move(movable: Movable, timeSinceLastUpdate):
    newPosition = getNextPosition(movable, timeSinceLastUpdate)
    movable.setPosition(newPosition)


def getNextPosition(movable: Movable, timeSinceLastUpdate):
    newPosition = movable.getPosition() + movable.getVelocity().scale(timeSinceLastUpdate)
    return newPosition


def updatePaddle(paddle: Paddle, borderSize, height):
    """
    Updates the paddle position and defines the boundaries of the play space.
    Positional tracking is used to prevent paddle leaving the screen, not hitbox collisions.
    """
    upperBound = paddle.height * 0.5 + borderSize
    lowerBound = height - paddle.height * 0.5 - borderSize
    outOfBoundsAbove = pygame.mouse.get_pos()[1] < upperBound
    outOfBoundsBelow = pygame.mouse.get_pos()[1] > lowerBound

    if not outOfBoundsAbove and not outOfBoundsBelow:
        """
        Controls the paddle Y position with the mouse.
        """
        paddle.y = pygame.mouse.get_pos()[1] - paddle.height * 0.5

    elif outOfBoundsAbove:
        """
        Prevent the paddle from moving beyond an upper limit.
        """
        paddle.y = upperBound - paddle.height * 0.5

    elif outOfBoundsBelow:
        """
        Prevent the paddle from moving beyond a lower limit.
        """
        paddle.y = lowerBound - paddle.height * 0.5

    else:
        raise ValueError('ya fucked it')
