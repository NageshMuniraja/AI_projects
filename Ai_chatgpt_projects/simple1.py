class Environment:
    def __init__(self, grid_size=5, obstacles=None, goal=None):
        self.grid_size = grid_size
        self.obstacles = obstacles if obstacles else set()
        self.goal = goal if goal else (grid_size - 1, grid_size - 1)

    def is_within_bounds(self, position):
        x, y = position
        return 0 <= x < self.grid_size and 0 <= y < self.grid_size

    def is_obstacle(self, position):
        return position in self.obstacles

    def is_goal(self, position):
        return position == self.goal


class Agent:
    def __init__(self, environment):
        self.env = environment
        self.position = (0, 0)  # Start at top-left corner

    def possible_moves(self):
        x, y = self.position
        return [(x + dx, y + dy) for dx, dy in
                [(-1, 0), (1, 0), (0, -1), (0, 1)]]

    def valid_moves(self):
        return [pos for pos in self.possible_moves()
                if self.env.is_within_bounds(pos) and not self.env.is_obstacle(pos)]

    def move_towards_goal(self):
        valid_positions = self.valid_moves()
        # Choose the move that minimizes Manhattan distance to the goal
        goal = self.env.goal
        def distance(pos):
            return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])
        next_position = min(valid_positions, key=distance, default=self.position)
        self.position = next_position

    def reached_goal(self):
        return self.env.is_goal(self.position)

    def run(self):
        steps = 0
        while not self.reached_goal():
            self.move_towards_goal()
            steps += 1
            print(f"Step {steps}: Moved to {self.position}")
        print(f"Goal reached at {self.position} in {steps} steps.")


# Example usage:
if __name__ == "__main__":
    obstacles = {(1, 1), (1, 2), (2, 1)}  # Example obstacles
    env = Environment(obstacles=obstacles)
    agent = Agent(env)
    agent.run()
