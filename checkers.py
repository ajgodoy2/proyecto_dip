"""
checkers.py
A simple checkers engine written in Python with the pygame 1.9.1 libraries.
Here are the rules I am using: http://boardgames.about.com/cs/checkersdraughts/ht/play_checkers.htm
I adapted some code from checkers.py found at 
http://itgirl.dreamhosters.com/itgirlgames/games/Program%20Leaders/ClareR/Checkers/checkers.py starting on line 159 of my program.
This is the final version of my checkers project for Programming Workshop at Marlboro College. The entire thing has been rafactored and made almost completely object oriented.
Funcitonalities include:
- Having the pieces and board drawn to the screen
- The ability to move pieces by clicking on the piece you want to move, then clicking on the square you would
  like to move to. You can change you mind about the piece you would like to move, just click on a new piece of yours.
- Knowledge of what moves are legal. When moving pieces, you'll be limited to legal moves.
- Capturing
- DOUBLE capturing etc.
- Legal move and captive piece highlighting
- Turn changes
- Automatic kinging and the ability for them to move backwords
- Automatic check for and end game. 
- A silky smoooth 60 FPS!
Everest Witman - May 2014 - Marlboro College - Programming Workshop 
"""

import pygame, sys
from pygame.locals import *
import cv2, numpy, imutils
import pyautogui
import numpy as np

pygame.font.init()

##COLORS##
#             R    G    B 
WHITE    = (255, 255, 255)
BLUE     = (  0,   0, 255)
RED      = (255,   0,   0)
BLACK    = (  0,   0,   0)
GOLD     = (255, 215,   0)
HIGH     = (160, 190, 255)

##DIRECTIONS##
NORTHWEST = "northwest"
NORTHEAST = "northeast"
SOUTHWEST = "southwest"
SOUTHEAST = "southeast"

class Game:
	"""
	The main game control.
	"""

	def __init__(self, invert, record, playback):
		self.graphics = Graphics(invert, record, playback)
		self.board = Board()
		
		self.turn = BLUE
		self.selected_piece = None # a board location. 
		self.hop = False
		self.selected_legal_moves = []

	def setup(self):
		"""Draws the window and board at the beginning of the game"""
		self.graphics.setup_window()

	def event_loop(self):
		"""
		The event loop. This is where events are triggered 
		(like a mouse click) and then effect the game state.
		"""
		self.mouse_pos = self.graphics.board_coords(pygame.mouse.get_pos()) # what square is the mouse in?
		if self.selected_piece != None:
			self.selected_legal_moves = self.board.legal_moves(self.selected_piece, self.hop)

		for event in pygame.event.get():

			if event.type == QUIT:
				self.terminate_game()

			if event.type == MOUSEBUTTONDOWN:
				if self.hop == False:
					if self.board.location(self.mouse_pos).occupant != None and self.board.location(self.mouse_pos).occupant.color == self.turn:
						self.selected_piece = self.mouse_pos

					elif self.selected_piece != None and self.mouse_pos in self.board.legal_moves(self.selected_piece):

						self.board.move_piece(self.selected_piece, self.mouse_pos)
					
						if self.mouse_pos not in self.board.adjacent(self.selected_piece):
							self.board.remove_piece((self.selected_piece[0] + (self.mouse_pos[0] - self.selected_piece[0]) / 2, self.selected_piece[1] + (self.mouse_pos[1] - self.selected_piece[1]) / 2))
						
							self.hop = True
							self.selected_piece = self.mouse_pos

						else:
							self.end_turn()

				if self.hop == True:					
					if self.selected_piece != None and self.mouse_pos in self.board.legal_moves(self.selected_piece, self.hop):
						self.board.move_piece(self.selected_piece, self.mouse_pos)
						self.board.remove_piece((self.selected_piece[0] + (self.mouse_pos[0] - self.selected_piece[0]) / 2, self.selected_piece[1] + (self.mouse_pos[1] - self.selected_piece[1]) / 2))

					if self.board.legal_moves(self.mouse_pos, self.hop) == []:
							self.end_turn()

					else:
						self.selected_piece = self.mouse_pos


	def update(self):
		"""Calls on the graphics class to update the game display."""
		try:
			self.graphics.update_display(self.board, self.selected_legal_moves, self.selected_piece)
		except pygame.error:
			if self.graphics.record:
				self.graphics.record.release()
				self.terminate_game()

	def terminate_game(self):
		"""Quits the program and ends the game."""
		pygame.quit()
		sys.exit

	def main(self):
		""""This executes the game and controls its flow."""
		self.setup()

		while True: # main game loop
			self.event_loop()
			self.update()

	def end_turn(self):
		"""
		End the turn. Switches the current player. 
		end_turn() also checks for and game and resets a lot of class attributes.
		"""
		if self.turn == BLUE:
			self.turn = RED
		else:
			self.turn = BLUE

		self.selected_piece = None
		self.selected_legal_moves = []
		self.hop = False

		if self.check_for_endgame():
			if self.turn == BLUE:
				self.graphics.draw_message("RED WINS!")
			else:
				self.graphics.draw_message("BLUE WINS!")

	def check_for_endgame(self):
		"""
		Checks to see if a player has run out of moves or pieces. If so, then return True. Else return False.
		"""
		for x in xrange(8):
			for y in xrange(8):
				if self.board.location((x,y)).color == BLACK and self.board.location((x,y)).occupant != None and self.board.location((x,y)).occupant.color == self.turn:
					if self.board.legal_moves((x,y)) != []:
						return False

		return True

class Graphics:
	def __init__(self, facing_down, record, playback):
		print(record, playback)
		self.caption = "Checkers"

		self.fps = 60
		self.clock = pygame.time.Clock()

		self.window_size = 640
		self.screen = pygame.display.set_mode((self.window_size, self.window_size))
		self.background = pygame.image.load('resources/board.640.png')

		self.square_size = self.window_size / 8
		self.piece_size = self.square_size / 2

		self.message = False
		self.num_reds = 0
		
		self.mouse_pressed = False
		if not playback:
			self.camera = cv2.VideoCapture(-1)
			# May be required to avoid exposure messing with the detection?
			self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
			self.camera.set(cv2.CAP_PROP_EXPOSURE, 0.025)
		else:
			self.camera = cv2.VideoCapture("vid.avi")

		self.facing_down = facing_down
		if record:
			self.record = cv2.VideoWriter('vid.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 10, (640, 480))
		else:
			self.record = None

	def setup_window(self):
		"""
		This initializes the window and sets the caption at the top.
		"""
		pygame.init()
		pygame.display.set_caption(self.caption)

	def update_display(self, board, legal_moves, selected_piece):
		"""
		This updates the current display.
		"""
		self.screen.blit(self.background, (0,0))
		
		self.highlight_squares(legal_moves, selected_piece)
		self.draw_board_pieces(board)

		if self.message:
			self.screen.blit(self.text_surface_obj, self.text_rect_obj)
			
		# Get video frame from camera
		_, frame = self.camera.read()
		if self.record:
		    self.record.write(frame)

		frame = cv2.resize(frame, (640, 640)) # resize webcam frame to full screen
		frame = np.rot90(frame)
		# HACK: Without at least one .flip, the drawn circles do not appear...
		frame = cv2.flip(frame, 1)
		if not self.facing_down:
			frame = cv2.flip(frame, 1) # Flip image again if looking front
		
		# HSV limits for markers
		greenLower = (45, 0, 0)
		greenUpper = (95, 4, 255)
		redLower = (25, 0, 0)
		redUpper = (35, 4, 255)

		hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

		# get mask for green marker
		mask_green = cv2.inRange(hsv, greenLower, greenUpper) 

		# erode and dilate masks to remove small blobs
		mask_green = cv2.erode(mask_green, None, iterations=1)
		mask_green = cv2.dilate(mask_green, None, iterations=1)

		# get mask for red marker
		mask_red = cv2.inRange(hsv, redLower, redUpper) 

		# erode and dilate masks to remove small blobs
		mask_red = cv2.erode(mask_red, None, iterations=1)
		mask_red = cv2.dilate(mask_red, None, iterations=1)

		cnts_green = cv2.findContours(mask_green.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		cnts_green = imutils.grab_contours(cnts_green)
		cnts_red = cv2.findContours(mask_red.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		cnts_red = imutils.grab_contours(cnts_red)

		center = None
		drawn = False
		if len(cnts_red) > 0: # red light is on, click
			# find the largest contour in the mask, then use
			# it to compute the minimum enclosing circle and
			# centroid
			c = max(cnts_red, key=cv2.contourArea)
			((x, y), radius) = cv2.minEnclosingCircle(c)
			M = cv2.moments(c)
			center = None
			if M["m00"] != 0:
				center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

			# only proceed if the radius meets a minimum size
			if radius > 5 and center:
				# draw the circle and centroid on the frame
				cv2.circle(frame, (int(x), int(y)), int(radius),
					(0, 0, 255), 2)
				cv2.circle(frame, center, 5, (0, 0, 255), -1)
				# cv2.putText(frame, "CLICK", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
				drawn = True
				if self.num_reds > 3:
					pyautogui.click()
				else:
					self.num_reds += 1
				print(self.num_reds)
		if len(cnts_green) > 0 and not drawn: # green light is on BUT RED LIGHT IS NOT
			# find the largest contour in the mask, then use
			# it to compute the minimum enclosing circle and
			# centroid
			c = max(cnts_green, key=cv2.contourArea)
			((x, y), radius) = cv2.minEnclosingCircle(c)
			M = cv2.moments(c)
			center = None
			if M["m00"] != 0:
				center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

			# only proceed if the radius meets a minimum size
			if radius > 5 and center:
				# draw the circle and centroid on the frame
				cv2.circle(frame, (int(x), int(y)), int(radius),
					(0, 255, 0), 2)
				cv2.circle(frame, center, 5, (0, 255, 0), -1)
				# cv2.putText(frame, "NO CLICK", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
				drawn = True
				self.num_reds = 0
		
		if drawn:
			pygame.mouse.set_pos(y, x)

		frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		frame = pygame.surfarray.make_surface(frame)
		frame.set_alpha(120)
		
		#mask = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB) 
		#mask = pygame.surfarray.make_surface(mask)
		#mask.set_alpha(120)
		
		#self.screen.blit(pygame.surfarray.make_surface(mask_temp), (0,0)) # add frame on screen
		self.screen.blit(frame, (0,0)) # add frame on screen

		pygame.display.update()
		self.clock.tick(self.fps)

	def draw_board_squares(self, board):
		"""
		Takes a board object and draws all of its squares to the display
		"""
		for x in xrange(8):
			for y in xrange(8):
				pygame.draw.rect(self.screen, board[x][y].color, (x * self.square_size, y * self.square_size, self.square_size, self.square_size), )
	
	def draw_board_pieces(self, board):
		"""
		Takes a board object and draws all of its pieces to the display
		"""
		for x in xrange(8):
			for y in xrange(8):
				if board.matrix[x][y].occupant != None:
					pygame.draw.circle(self.screen, board.matrix[x][y].occupant.color, self.pixel_coords((x,y)), self.piece_size) 

					if board.location((x,y)).occupant.king == True:
						pygame.draw.circle(self.screen, GOLD, self.pixel_coords((x,y)), int (self.piece_size / 1.7), self.piece_size / 4)


	def pixel_coords(self, board_coords):
		"""
		Takes in a tuple of board coordinates (x,y) 
		and returns the pixel coordinates of the center of the square at that location.
		"""
		return (board_coords[0] * self.square_size + self.piece_size, board_coords[1] * self.square_size + self.piece_size)

	def board_coords(self, (pixel_x, pixel_y)):
		"""
		Does the reverse of pixel_coords(). Takes in a tuple of of pixel coordinates and returns what square they are in.
		"""
		return (pixel_x / self.square_size, pixel_y / self.square_size)	

	def highlight_squares(self, squares, origin):
		"""
		Squares is a list of board coordinates. 
		highlight_squares highlights them.
		"""
		for square in squares:
			pygame.draw.rect(self.screen, HIGH, (square[0] * self.square_size, square[1] * self.square_size, self.square_size, self.square_size))	

		if origin != None:
			pygame.draw.rect(self.screen, HIGH, (origin[0] * self.square_size, origin[1] * self.square_size, self.square_size, self.square_size))

	def draw_message(self, message):
		"""
		Draws message to the screen. 
		"""
		self.message = True
		self.font_obj = pygame.font.Font('freesansbold.ttf', 44)
		self.text_surface_obj = self.font_obj.render(message, True, HIGH, BLACK)
		self.text_rect_obj = self.text_surface_obj.get_rect()
		self.text_rect_obj.center = (self.window_size / 2, self.window_size / 2)

class Board:
	def __init__(self):
		self.matrix = self.new_board()

	def new_board(self):
		"""
		Create a new board matrix.
		"""

		# initialize squares and place them in matrix

		matrix = [[None] * 8 for i in xrange(8)]

		# The following code block has been adapted from
		# http://itgirl.dreamhosters.com/itgirlgames/games/Program%20Leaders/ClareR/Checkers/checkers.py
		for x in xrange(8):
			for y in xrange(8):
				if (x % 2 != 0) and (y % 2 == 0):
					matrix[y][x] = Square(WHITE)
				elif (x % 2 != 0) and (y % 2 != 0):
					matrix[y][x] = Square(BLACK)
				elif (x % 2 == 0) and (y % 2 != 0):
					matrix[y][x] = Square(WHITE)
				elif (x % 2 == 0) and (y % 2 == 0): 
					matrix[y][x] = Square(BLACK)

		# initialize the pieces and put them in the appropriate squares

		for x in xrange(8):
			for y in xrange(3):
				if matrix[x][y].color == BLACK:
					matrix[x][y].occupant = Piece(RED)
			for y in xrange(5, 8):
				if matrix[x][y].color == BLACK:
					matrix[x][y].occupant = Piece(BLUE)

		return matrix

	def board_string(self, board):
		"""
		Takes a board and returns a matrix of the board space colors. Used for testing new_board()
		"""

		board_string = [[None] * 8] * 8 

		for x in xrange(8):
			for y in xrange(8):
				if board[x][y].color == WHITE:
					board_string[x][y] = "WHITE"
				else:
					board_string[x][y] = "BLACK"


		return board_string
	
	def rel(self, dir, (x,y)):
		"""
		Returns the coordinates one square in a different direction to (x,y).
		===DOCTESTS===
		>>> board = Board()
		>>> board.rel(NORTHWEST, (1,2))
		(0,1)
		>>> board.rel(SOUTHEAST, (3,4))
		(4,5)
		>>> board.rel(NORTHEAST, (3,6))
		(4,5)
		>>> board.rel(SOUTHWEST, (2,5))
		(1,6)
		"""
		if dir == NORTHWEST:
			return (x - 1, y - 1)
		elif dir == NORTHEAST:
			return (x + 1, y - 1)
		elif dir == SOUTHWEST:
			return (x - 1, y + 1)
		elif dir == SOUTHEAST:
			return (x + 1, y + 1)
		else:
			return 0

	def adjacent(self, (x,y)):
		"""
		Returns a list of squares locations that are adjacent (on a diagonal) to (x,y).
		"""

		return [self.rel(NORTHWEST, (x,y)), self.rel(NORTHEAST, (x,y)),self.rel(SOUTHWEST, (x,y)),self.rel(SOUTHEAST, (x,y))]

	def location(self, (x,y)):
		"""
		Takes a set of coordinates as arguments and returns self.matrix[x][y]
		This can be faster than writing something like self.matrix[coords[0]][coords[1]]
		"""

		return self.matrix[x][y]

	def blind_legal_moves(self, (x,y)):
		"""
		Returns a list of blind legal move locations from a set of coordinates (x,y) on the board. 
		If that location is empty, then blind_legal_moves() return an empty list.
		"""

		if self.matrix[x][y].occupant != None:
			
			if self.matrix[x][y].occupant.king == False and self.matrix[x][y].occupant.color == BLUE:
				blind_legal_moves = [self.rel(NORTHWEST, (x,y)), self.rel(NORTHEAST, (x,y))]
				
			elif self.matrix[x][y].occupant.king == False and self.matrix[x][y].occupant.color == RED:
				blind_legal_moves = [self.rel(SOUTHWEST, (x,y)), self.rel(SOUTHEAST, (x,y))]

			else:
				blind_legal_moves = [self.rel(NORTHWEST, (x,y)), self.rel(NORTHEAST, (x,y)), self.rel(SOUTHWEST, (x,y)), self.rel(SOUTHEAST, (x,y))]

		else:
			blind_legal_moves = []

		return blind_legal_moves

	def legal_moves(self, (x,y), hop = False):
		"""
		Returns a list of legal move locations from a given set of coordinates (x,y) on the board.
		If that location is empty, then legal_moves() returns an empty list.
		"""

		blind_legal_moves = self.blind_legal_moves((x,y)) 
		legal_moves = []

		if hop == False:
			for move in blind_legal_moves:
				if hop == False:
					if self.on_board(move):
						if self.location(move).occupant == None:
							legal_moves.append(move)

						elif self.location(move).occupant.color != self.location((x,y)).occupant.color and self.on_board((move[0] + (move[0] - x), move[1] + (move[1] - y))) and self.location((move[0] + (move[0] - x), move[1] + (move[1] - y))).occupant == None: # is this location filled by an enemy piece?
							legal_moves.append((move[0] + (move[0] - x), move[1] + (move[1] - y)))

		else: # hop == True
			for move in blind_legal_moves:
				if self.on_board(move) and self.location(move).occupant != None:
					if self.location(move).occupant.color != self.location((x,y)).occupant.color and self.on_board((move[0] + (move[0] - x), move[1] + (move[1] - y))) and self.location((move[0] + (move[0] - x), move[1] + (move[1] - y))).occupant == None: # is this location filled by an enemy piece?
						legal_moves.append((move[0] + (move[0] - x), move[1] + (move[1] - y)))

		return legal_moves

	def remove_piece(self, (x,y)):
		"""
		Removes a piece from the board at position (x,y). 
		"""
		self.matrix[x][y].occupant = None

	def move_piece(self, (start_x, start_y), (end_x, end_y)):
		"""
		Move a piece from (start_x, start_y) to (end_x, end_y).
		"""

		self.matrix[end_x][end_y].occupant = self.matrix[start_x][start_y].occupant
		self.remove_piece((start_x, start_y))

		self.king((end_x, end_y))

	def is_end_square(self, coords):
		"""
		Is passed a coordinate tuple (x,y), and returns true or 
		false depending on if that square on the board is an end square.
		===DOCTESTS===
		>>> board = Board()
		>>> board.is_end_square((2,7))
		True
		>>> board.is_end_square((5,0))
		True
		>>>board.is_end_square((0,5))
		False
		"""

		if coords[1] == 0 or coords[1] == 7:
			return True
		else:
			return False

	def on_board(self, (x,y)):
		"""
		Checks to see if the given square (x,y) lies on the board.
		If it does, then on_board() return True. Otherwise it returns false.
		===DOCTESTS===
		>>> board = Board()
		>>> board.on_board((5,0)):
		True
		>>> board.on_board(-2, 0):
		False
		>>> board.on_board(3, 9):
		False
		"""

		if x < 0 or y < 0 or x > 7 or y > 7:
			return False
		else:
			return True


	def king(self, (x,y)):
		"""
		Takes in (x,y), the coordinates of square to be considered for kinging.
		If it meets the criteria, then king() kings the piece in that square and kings it.
		"""
		if self.location((x,y)).occupant != None:
			if (self.location((x,y)).occupant.color == BLUE and y == 0) or (self.location((x,y)).occupant.color == RED and y == 7):
				self.location((x,y)).occupant.king = True 

class Piece:
	def __init__(self, color, king = False):
		self.color = color
		self.king = king

class Square:
	def __init__(self, color, occupant = None):
		self.color = color # color is either BLACK or WHITE
		self.occupant = occupant # occupant is a Square object


def main():
	game = Game(invert="--down" in sys.argv, record="--rec" in sys.argv, playback="--playback" in sys.argv)
	game.main()

if __name__ == "__main__":
	main()
