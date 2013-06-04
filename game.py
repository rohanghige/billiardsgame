#!/usr/bin/python
import pygame
from pygame.locals import *

import Box2D as b2

SCREENW = 600
SCREENH = 360
PPM = 30 # pixels/meter
fPPM = 1.0*PPM

TARGET_FPS = 60
TIME_STEP = 1.0/TARGET_FPS

DEBUG = False
#DEBUG = True

b2.b2_velocityThreshold = 0.0

def toScreen(pos):
	if isinstance(pos, b2.b2Vec2): pos = pos.tuple()
	return (int(pos[0] * PPM) + PPM*2, int(pos[1] * PPM + PPM*2))

class Entity:
	def draw(self, display):
		pass
	def update(self):
		pass
	def on_collision(self, other):
		pass

class Wall(Entity):
	def __init__(self, world, x, y, w, h):
		bodyDef = b2.b2BodyDef()
		bodyDef.position = (x + w/2.0, y + h/2.0)
		self.body = world.CreateBody(bodyDef)
		shapeDef = b2.b2PolygonDef()
		shapeDef.SetAsBox(w/2.0, h/2.0)
		shapeDef.friction = 0.4
		shapeDef.restitution = 1
		self.body.CreateShape(shapeDef)
		self.body.userData = self
	def draw(self, display):
		if not DEBUG: return
		for shape in self.body:
			pos = self.body.position
			vertices = [(v[0] + pos.x, v[1] + pos.y) for v in shape.vertices]
			vertices = [toScreen(v) for v in vertices]
			pygame.draw.polygon(display, Color("white"), vertices, 1)

class PolyWall(Entity):
	def __init__(self, world, x, y, vertices):
		bodyDef = b2.b2BodyDef()
		bodyDef.position = (x, y)
		self.body = world.CreateBody(bodyDef)
		shapeDef = b2.b2PolygonDef()
		shapeDef.setVertices_tuple(vertices)
		shapeDef.friction = 0.4
		shapeDef.restitution = 1
		self.body.CreateShape(shapeDef)
		self.body.userData = self
	def draw(self, display):
		if not DEBUG: return
		for shape in self.body:
			pos = self.body.position
			vertices = [(v[0] + pos.x, v[1] + pos.y) for v in shape.vertices]
			vertices = [toScreen(v) for v in vertices]
			pygame.draw.polygon(display, Color("white"), vertices, 1)

class Ball(Entity):
	colors = [
		Color("white"),
		Color("yellow"),
		Color("blue"),
		Color("red"),
		Color("purple"),
		Color("orange"),
		Color("green"),
		Color("brown"),
		Color(30, 30, 30)
	]
	def __init__(self, world, number, x, y):
		self.kill = False
		self.number = number
		if number > 8:
			self.color = self.colors[number - 8]
			self.stripe = True
		else:
			self.color = self.colors[number]
			self.stripe = False
		bodyDef = b2.b2BodyDef()
		bodyDef.position = (x, y)
		bodyDef.linearDamping = 0.9
		self.body = world.CreateBody(bodyDef)
		shapeDef = b2.b2CircleDef()
		shapeDef.radius = 0.3
		shapeDef.density = 1.7
		shapeDef.friction = 0.03
		shapeDef.restitution = 0.95
		self.body.CreateShape(shapeDef)
		self.body.SetMassFromShapes()
		self.body.userData = self
	def __repr__(self):
		return "Ball(world, %d, %.2f, %.2f)" % (self.number, self.body.position.x, self.body.position.y)
	def update(self):
		if self.body.linearVelocity.LengthSquared() < 0.01:
			self.body.PutToSleep()
		if self.kill:
			self.body.PutToSleep()
			if self.number > 0:
				world = self.body.GetWorld()
				world.DestroyBody(self.body)
			else:
				self.body.position = b2.b2Vec2(4, 4)
				self.kill = False
	def draw(self, display):
		for shape in self.body:
			pos = toScreen(self.body.position)
			radius = int(shape.radius * PPM)
			color = self.color
			display.blit(Ball.shadow_image, (pos[0] - 13, pos[1] - 11))
			if self.stripe:
				pygame.draw.circle(display, color, pos, radius, 0)
				pygame.draw.circle(display, Color("white"), pos, int(shape.radius * 0.75 * PPM), 0)
			else:
				pygame.draw.circle(display, color, pos, radius, 0)
			display.blit(Ball.shading_image, (pos[0] - 9, pos[1] - 9))
			if DEBUG and self.body.isSleeping:
				pygame.draw.circle(display, Color(255, 0, 255), pos, radius, 1)
	def hit(self, impulseVector):
		self.body.ApplyImpulse(impulseVector, self.body.position)
	def on_collision(self, other):
		if isinstance(other, Pocket):
			if DEBUG: print "KILL"
			self.kill = True

class Pocket(Entity):
	def __init__(self, world, x, y):
		bodyDef = b2.b2BodyDef()
		bodyDef.position = (x, y)
		self.body = world.CreateBody(bodyDef)
		shapeDef = b2.b2CircleDef()
		shapeDef.radius = 0.25
		shapeDef.isSensor = True
		self.body.CreateShape(shapeDef)
		self.body.userData = self
	def draw(self, display):
		if not DEBUG: return
		for shape in self.body:
			pos = toScreen(self.body.position)
			radius = int(shape.radius * PPM)
			pygame.draw.circle(display, Color("white"), pos, radius, 1)

class MyContactListener(b2.b2ContactListener):
	def __init__(self): super(MyContactListener, self).__init__() 
	def Add(self, point):
		obj1 = point.shape1.GetBody().userData
		obj2 = point.shape2.GetBody().userData
		if DEBUG: print "on_collision:", obj1, obj2
		if isinstance(obj1, Entity):
			obj1.on_collision(obj2)
		if isinstance(obj2, Entity):
			obj2.on_collision(obj1)


class Game:
	def __init__(self):
		pygame.init()
		self.display = pygame.display.set_mode((SCREENW, SCREENH))
		pygame.display.set_caption("Billiards Game")
		self.clock = pygame.time.Clock()
		self.load()
	def run(self):
		self.running = True
		while self.running:
			self.clock.tick(TARGET_FPS)
			for e in pygame.event.get():
				if e.type == pygame.QUIT:
					self.running = False
				elif e.type == pygame.MOUSEBUTTONDOWN:
					self.on_mousedown(e.pos)
			self.update()
			self.draw(self.display)
			pygame.display.flip()
	# begin game-specific code
	def load(self):
		worldBB = b2.b2AABB()
		worldBB.lowerBound = (-10, -10)
		worldBB.upperBound = (30, 30)
		self.world = b2.b2World(worldBB, (0, 0), True)
		self.contactListener = MyContactListener()
		self.world.SetContactListener(self.contactListener)
		
		self.bgimage = pygame.image.load("table.png").convert()

		#top left
		PolyWall(self.world, 0, -1, ((-0.3, 0), (7.5, 0), (7.5, 1), (0.7, 1)))
		#top right
		PolyWall(self.world, 0, -1, ((8.5, 0), (16.3, 0), (15.3, 1), (8.5, 1)))
		#bottom left
		PolyWall(self.world, 0, 8, ((0.7, 0), (7.5, 0), (7.5, 1), (-0.3, 1)))
		#bottom right
		PolyWall(self.world, 0, 8, ((8.5, 0), (15.3, 0), (16.3, 1), (8.5, 1)))
		#left
		PolyWall(self.world, -1, 0, ((0, -0.3), (1, 0.7), (1, 7.3), (0, 8.3)))
		#right
		PolyWall(self.world, 16, 0, ((0, 0.7), (1, -0.3), (1, 8.3), (0, 7.3)))

		Pocket(self.world, -0.3, -0.3)
		Pocket(self.world, 8, -0.5)
		Pocket(self.world, 16.4, -0.3)
		Pocket(self.world, -0.3, 8.4)
		Pocket(self.world, 8, 8.5)
		Pocket(self.world, 16.4, 8.4)

		Ball.shadow_image = pygame.image.load("ball-shadow.png").convert_alpha()
		Ball.shading_image = pygame.image.load("ball-shading.png").convert_alpha()

		Ball(self.world, 1, 10, 4)
		Ball(self.world, 2, 10.5, 4.3)
		Ball(self.world, 3, 10.5, 3.7)
		Ball(self.world, 4, 11, 4.6)
		Ball(self.world, 9, 11, 4)
		Ball(self.world, 5, 11, 3.4)
		Ball(self.world, 6, 11.5, 4.3)
		Ball(self.world, 7, 11.5, 3.7)
		Ball(self.world, 8, 12, 4)

		self.cue = Ball(self.world, 0, 4, 4)
		self.ready = True
	def update(self):
		self.world.Step(TIME_STEP, 10, 10)
		for body in self.world:
			if isinstance(body.userData, Entity):
				body.userData.update()

		if not self.ready:
			allSleeping = True
			for body in self.world:
				if isinstance(body.userData, Ball) and not body.isSleeping:
					allSleeping = False
					break
			if allSleeping: self.ready = True
	def draw(self, display):
		display.blit(self.bgimage, (0, 0))

		for body in self.world:
			if isinstance(body.userData, Entity):
				body.userData.draw(display)

		if self.ready:
			cuePos = toScreen(self.cue.body.position)
			lineStart = b2.b2Vec2(cuePos[0], cuePos[1])
			mouse = pygame.mouse.get_pos()
			mouseOffset = b2.b2Vec2(mouse[0], mouse[1]) - lineStart
			mouseOffset.Normalize()
			lineEnd = lineStart + (mouseOffset * SCREENW)
			lineStart += mouseOffset * 13
			pygame.draw.line(display, Color("white"), lineStart.tuple(), lineEnd.tuple())
	def on_mousedown(self, pos):
		if not self.ready: return
		worldMouse = b2.b2Vec2(pos[0] / fPPM - 2, pos[1] / fPPM - 2)
		#Pocket(self.world, worldMouse.x, worldMouse.y)
		offset = worldMouse - self.cue.body.position
		offset.Normalize()
		self.cue.hit(offset * 10)
		self.ready = False

if __name__ == "__main__":
	app = Game()
	app.run()
