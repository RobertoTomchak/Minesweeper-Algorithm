"""
    Defines the Algorithm class, that plays the minesweeper game
    This algorithm is based on a technique called CSP. For more, check: https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwi_oLWVmpWEAxUZvJUCHUImCfgQFnoECBoQAQ&url=https%3A%2F%2Fdash.harvard.edu%2Fbitstream%2Fhandle%2F1%2F14398552%2FBECERRA-SENIORTHESIS-2015.pdf&usg=AOvVaw0FlHm9LAFdmLemHYEIdDg-&opi=89978449
    obs: the algorithm supposes that there's no "?" in the board, since it requires player influence. If there are any "?" in the board, the algorithm will most likely lose
"""
from Board import Board
from collections import deque
from random import randint, choice


'''
Queue: class that extends the deque class, just to add some useful methods
'''
class Queue(deque):
    '''
    empty: checks if queue is empty
    @parameters:
        self
    @return: True if empty; False otherwise
    '''
    def empty(self):
        return not(len(self))
    

    '''
    dequeue: removes first element from queue, and returns it
    @parameters:
        self
    @return: first element of queue
    '''
    def dequeue(self):
        x = self[0]
        self.popleft()
        return x
  


"""
Algorithm: class that defines the minesweeper solver
    @attributtes:
        plays: a queue with all saved plays. The use of a queue helps the algorithm play faster.
        board: the board of the game (but only the symbols, since it's all the player can see)
        board_size: dimensions of board (n_rows, n_columns)
        return_strategy: True if should return which strategy was used in the play; False otherwise
"""
class Algorithm:
    def __init__(self, board, n_rows, n_columns, return_strategy=False):
        self.plays = Queue()
        self.board = board
        self.board_size = (n_rows, n_columns)
        self.return_strategy = return_strategy
        return None
    

    """
    first_play: defines what the first play will be (always a left click)
    @parameters:
        self
        board: the board of the game
    @return: a tuple (x,y) with the coordinates of the tile to be clicked
    """
    def first_play(self):
        # for now, the tile is choosen randomly
        return (randint(0, self.board_size[0]-1), randint(0, self.board_size[1]-1))
    

    """
    play: makes a play in the board (either a left or right click)
    @parameters:
        self
        board: the board of the game
    @return: a tuple (x, y, action), with the coordinates of the choosen tile and the type of action
    """
    def play(self):
        # if any valid plays are available, make them
        while not self.plays.empty():
            x, y, action, strategy = self.plays.dequeue()
            if self.board[x][y] in "X":
                return (x, y, action, strategy) if self.return_strategy else (x, y, action)
            
        # if no plays available, finds possible plays
        equations = self.get_equations()

        # checks for trivial cases (all adjacent tiles have to be marked or all be freed)
        for eq in equations:
            # remaining unknowns are bombs
            if len(eq["variables"]) == eq["result"]:
                for var in eq["variables"]:
                    self.plays.append((var[0], var[1], "right", "s"))
            # remaining unknowns are non-bombs
            elif eq["result"] == 0:
                for var in eq["variables"]:
                    self.plays.append((var[0], var[1], "left", "s"))
        if not self.plays.empty():
            x, y, action, strategy = self.plays.dequeue()
            return (x, y, action, strategy) if self.return_strategy else (x, y, action)
        
        # if no possible plays were found, go for second strategy
        for i, row in enumerate(self.board):
            for j, tile in enumerate(row):
                # only looks for plays in unknown tiles
                if tile not in "X":
                    continue

                # get equations where this tile is in
                tile_equations = []
                for eq in equations:
                    if (i,j) in eq["variables"]:
                        tile_equations.append(eq)
                conclusions = self.solve_equations(tile_equations)
                for var in conclusions:
                    # no conclusion
                    if conclusions[var] == -1:
                        continue
                    # no bomb
                    if conclusions[var] == 0:
                        a, b = var
                        self.plays.append((a, b, "left", "c"))
                    # bomb
                    else:
                        a, b = var
                        self.plays.append((a, b, "right", "c"))
        if not self.plays.empty():
            x, y, action, strategy = self.plays.dequeue()
            return (x, y, action, strategy) if self.return_strategy else (x, y, action)

        # if none of the strategies worked, guesses a random tile to free
        unknowns = []  # get tiles that are unknown
        for i, row in enumerate(self.board):
            for j, tile in enumerate(row):
                if tile in "X?":
                    unknowns.append((i, j))
        x, y = choice(unknowns)
        return (x, y, "left", "r") if self.return_strategy else (x, y, "left")
        

    """
    get_equations: gets all equations of possible bombs and non-bombs placement
    @parameters:
        self
        board: the board of the game
    @return: a list with all equations
    """
    def get_equations(self):
        # an equation is a dict with "variables" (list of coordinates of tiles) and a "result" (what their sum should be)
        # 1 -> has bomb, 0 -> no bomb
        equations = []
        for i, row in enumerate(self.board):
            for j, tile in enumerate(row):
                # only creates equations based on freed tiles that touch bombs
                if tile in "X?!0":
                    continue

                # get coordinates of unknown tiles and how many unmarked bombs are left
                adj_tiles = self.adjacent_tiles(i, j)
                unknown_tiles = []
                n_marked_adjacents = 0
                for a,b in adj_tiles:
                    tile_symbol = self.board[a][b]
                    if tile_symbol in "X":
                        unknown_tiles.append((a,b))
                    elif tile_symbol in "!":
                        n_marked_adjacents += 1
                    

                res = int(tile) - n_marked_adjacents  # how many adjacent tiles have bombs that are still unmarked
                equations.append({"variables": unknown_tiles, "result": res})
        return equations
    

    """
    solve_equations: gets possible solutions to the equations (see get_equations for more)
    @parameters:
        self
        equations: list with all equations
    @return: a dict, where keys are coordinates (x, y) of tiles and values are their conclusion (0 -> no bomb, 1 -> bomb, -1 -> no conclusion)
    """
    def solve_equations(self, equations):
        variables = {}
        i = 0
        for eq in equations:
            for var in eq["variables"]:
                if var not in variables:
                    variables[var] = i
                    i += 1
        aux = i * [0]

        solutions = []
        self.generate_solutions(equations, variables, aux, 0, solutions)

        # no solutions found
        if len(solutions) == 0:
            return {}
        
        answer = solutions[0]
        for solution in solutions[1:]:
            for i in range(len(solution)):
                if answer[i] != solution[i]:
                    answer[i] = -1

        conclusions = {}
        for var in variables:
            conclusions[var] = answer[variables[var]] 
        return conclusions


    """
    generate_solutions: generates all possible solution to the given system of equations
    @parameters:
        self
        equations: list with all equations
        variables: dict where keys are coordinates (x, y) and values are their position in the aux array
        aux: list with values of the variables (0 -> no bomb, 1 -> bomb). If valid, is added to solutions
        solutions: list with all possible solution to the system of euqations
    @return: None
    """
    def generate_solutions(self, equations, variables, aux, i, solutions):
        if i == len(variables):
            if self.isValid(equations, variables, aux):
                solutions.append(aux.copy())
            return
        
        aux[i] = 0
        self.generate_solutions(equations, variables, aux, i+1, solutions)

        aux[i] = 1
        self.generate_solutions(equations, variables, aux, i+1, solutions)
        
        return None
    

    """
    isValid: checks if given solutions is valid
    @parameters:
        self
        equations: list with all equations
        variables: dict where keys are coordinates (x, y) and values are their position in the aux array
        aux: list with values of the variables (0 -> no bomb, 1 -> bomb)
    @return: True if solution is valid, False otherwise
    """
    def isValid(self, equations, variables, aux):
        for eq in equations:
            ans = 0
            for var in eq["variables"]:
                ans += aux[variables[var]]
            # if any of the equations is not satisfied, it's not valid
            if ans != eq["result"]:
                return False
        return True
    

    '''
    adjacent_tiles: gets tiles adjacent to desired tile
    @parameters:
        self
        x, y: coordinates of tile
    @return: list of coordinates (x,y) of adjacent tiles
    '''
    def adjacent_tiles(self, x, y):
        tiles = []
        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                if 0 <= i < self.board_size[0] and 0 <= j < self.board_size[1] and (i != x or j != y):
                    tiles.append((i, j))
        return tiles