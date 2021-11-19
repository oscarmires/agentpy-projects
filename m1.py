# Model design
import agentpy as ap
import seaborn as sns


class Room(ap.Model):

    def setup(self):
        # Initialize counters
        self.step_count = 0
        self.total_movements = 0

        # Initialize agents
        #   Cleaners
        n_cleaners = self.p.cleaners
        self.cleaners = ap.AgentList(self, n_cleaners)
        #   Tiles
        n_tiles = self.n_tiles = self.p.m * self.p.n
        self.tiles = ap.AgentList(self, n_tiles)
        #   Dirty tiles
        n_dirty = self.n_initially_dirty = int(n_tiles * self.p.dirt)

        # Set conditions (0: clean, 1: cleaning, 2: dirty)
        self.tiles.condition = 0
        self.tiles.isTile = True
        for i in range(n_dirty):
            self.tiles[i].condition = 2
        self.cleaners.target = None
        self.cleaners.isTile = False

        # Create grid
        self.grid = ap.Grid(self, (self.p.m, self.p.n), track_empty=True)
        self.grid.add_agents(self.tiles, random=True, empty=True)
        self.grid.add_agents(self.cleaners, [(1, 1)] * n_cleaners)

    def step(self):
        for cleaner in self.cleaners:
            if cleaner.target:
                target = cleaner.target
                if target.condition == 1:
                    target.condition = 0
                    self.grid.move_to(cleaner, self.grid.positions[target])
                    self.total_movements += 1
                    cleaner.target = None
            else:
                neighbors = self.grid.neighbors(cleaner)
                n_neighbor = len(neighbors)
                rand_pos = self.random.randint(0, n_neighbor - 1)
                neighbor = neighbors.to_list()[rand_pos]

                if neighbor.isTile:
                    if neighbor.condition == 2:
                        cleaner.target = neighbor
                        neighbor.condition = 1
                    elif neighbor.condition == 0:
                        self.grid.move_to(cleaner, self.grid.positions[neighbor])
                        self.total_movements += 1

        self.step_count += 1

        clean = self.tiles.select(self.tiles.condition == 0)
        allClean = len(clean) == self.n_tiles

        if self.step_count == self.p.steps or allClean:
            self.stop()

    def end(self):
        clean_tiles = len(self.tiles.select(self.tiles.condition == 0))
        dirty_tiles = len(self.tiles.select(self.tiles.condition == 2))
        self.report('total_tiles', self.n_tiles)
        self.report('initial_dirty', self.n_initially_dirty)
        self.report('total_clean_at_end', clean_tiles)
        self.report('percentage_cleaned', f'{(self.n_initially_dirty - dirty_tiles) / self.n_initially_dirty * 100}%')
        self.report('time', f'{self.step_count}/{self.p.steps}')


parameters = {
    'dirt': 0.2,  # probability of dirty cells
    'm': 10,  # grid's l
    'n': 10,  # grid's h
    'steps': 500,  # time
    'cleaners': 100
}

# Configure experiment
parameters_multi = dict(parameters)
parameters_multi.update({
    'steps': ap.Values(50, 100, 500),  # time
    'cleaners': ap.Values(1, 5, 20)
})
sample = ap.Sample(parameters_multi)

exp = ap.Experiment(Room, sample, iterations=5)
results = exp.run()

# plot result analysis
sns.set_theme()
sns.lineplot(
    data=results.arrange_reporters(),
    x='steps',
    y='percentage_cleaned',
    hue='cleaners'
)

# print results
columns = ['total_tiles',
           'initial_dirty',
           'total_clean_at_end',
           'percentage_cleaned',
           'time']
print(results['reporters'][columns])
