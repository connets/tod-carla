import matplotlib
matplotlib.use('Agg')
#matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

class RenderManager:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlim(0, 200)
        self.ax.set_ylim(0, 200)
        plt.ion()
        plt.show()

    def update(self, actors):
        print("Updating render...")
        print(f"Number of actors: {len(actors)}")
        plt.pause(0.1)
        return
        if len(self.ax.collections) > 0:
            self.ax.collections.pop(0)
        self.ax.quiver(x, y, dx, dy, angles='xy', scale_units='xy', scale=1, color='r')
        self.fig.canvas.draw_idle()
        plt.pause(0.1)