# Salve este arquivo como: pathfinding.py
import collections

def bfs_next_step(start, target, maze):
    """Encontra o próximo passo do caminho mais curto de start a target usando BFS."""
    sx, sy = start
    if start == target:
        return (0, 0)
    
    rows, cols = len(maze), len(maze[0])
    q = collections.deque([(sx, sy)])
    prev = {(sx, sy): None}

    while q:
        x, y = q.popleft()
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < cols and 0 <= ny < rows and maze[ny][nx] != 1 and (nx, ny) not in prev:
                prev[(nx, ny)] = (x, y)
                if (nx, ny) == target:
                    cur = (nx, ny)
                    while prev[cur] is not None and prev[cur] != (sx, sy):
                        cur = prev[cur]
                    return (cur[0] - sx, cur[1] - sy)
                q.append((nx, ny))
    return (0, 0)

def find_nearest_walkable_global(maze, x, y):
    """Encontra a célula caminhável mais próxima de (x, y)."""
    rows, cols = len(maze), len(maze[0])
    ix, iy = int(x), int(y)
    if 0 <= ix < cols and 0 <= iy < rows and maze[iy][ix] != 1:
        return ix, iy
    q = collections.deque([(ix, iy)])
    visited = {(ix, iy)}
    while q:
        cx, cy = q.popleft()
        for dx, dy in [(1,0),(-1,0),(0,1),(-1,0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < cols and 0 <= ny < rows and (nx, ny) not in visited:
                if maze[ny][nx] != 1: return (nx, ny)
                visited.add((nx, ny))
                q.append((nx, ny))
    return (cols//2, rows//2)

