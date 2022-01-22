import argparse

import numpy as np

ON = 255
OFF = 0
vals = [ON, OFF]
 
def randomGrid(N):
    """returns a grid of NxN random values"""
    return np.random.choice(vals, N*N, p=[0.2, 0.8]).reshape(N, N)

def update(grid, N):
    # copy grid since we require 8 neighbors for calculation and we go line by line
    newGrid = grid.copy()
    for i in range(N):
        for j in range(N):
 
            # compute 8-neighbor sum using toroidal boundary conditions - x and
            # y wrap around so that the simulaton takes place on a toroidal surface.
            total = int((grid[i, (j-1)%N] + grid[i, (j+1)%N] +
                         grid[(i-1)%N, j] + grid[(i+1)%N, j] +
                         grid[(i-1)%N, (j-1)%N] + grid[(i-1)%N, (j+1)%N] +
                         grid[(i+1)%N, (j-1)%N] + grid[(i+1)%N, (j+1)%N])/255)
 
            # apply Conway's rules
            if grid[i, j]  == ON:
                if (total < 2) or (total > 3):
                    newGrid[i, j] = OFF
            else:
                if total == 3:
                    newGrid[i, j] = ON

def main():
    parser = argparse.ArgumentParser(description="Runs Conway's Game of Life simulation.")
    parser.add_argument('--grid-size', dest='N', required=False)
    args = parser.parse_args()

    N = 100
    if args.N and int(args.N) > 8:
        N = int(args.N)
 
    grid = randomGrid(N)
  
    for i in range(1, 10000 + 1):
        update(grid, N)
        if i % 100 == 0:
            print(f'After {i} iterations:')
            print(grid)

if __name__ == '__main__':
    main()
