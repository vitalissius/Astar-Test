import re
import time
from enum import Enum


class Texture(Enum):
    NONE = 0
    LAND = 1
    WALL = 9


class Point2i:
    def __init__(self, i: int=0, j: int=0):
        self.i = i                                      # Y axis
        self.j = j                                      # X axis

    def __str__(self):
        return "({0}, {1})".format(self.i, self.j)


class Cell:
    def __init__(self, coordinate: Point2i, g: int, h: int, texture: Texture, arrow=None):
        self.coordinate = coordinate
        self.g = g
        self.h = h
        self.f = self.g + self.h
        self.texture = texture
        self.arrow = arrow

    def __str__(self):
        return "Coordinate: {0}; " \
               "g: {1}; " \
               "h: {2}; " \
               "f: {3}; " \
               "Texture: {4}; " \
               "Arrow: {5};".format(self.coordinate, self.g, self.h, self.f, self.texture, self.arrow)


class Pair(object):
    def __init__(self, neighbor: Cell, passable: bool):
        self.neighbor = neighbor
        self.passable = passable


startPoint = Point2i()          # Начальная точка
finishPoint = Point2i()         # Целевая точка

openList = list()               # Открытый список
closeList = list()              # Закрытый список

fieldWidth = 0                  # Ширина поля
fieldLength = 0                 # Длина поля
field = list()                  # Список ячеек, представляющий собой игровое поле

path = list()                   # Список ячеек представляющих собой найденный путь (если существует)


def make_index(i: {int, Point2i}, j: int=None) -> int:      # Создание индекса для ображения к списку ячеек
    if j is None:                                           # с использованием координат (имитация двумерности поля)
        return i.i * fieldLength + i.j
    else:
        return i * fieldLength + j


def read_field_from_file(filename: str) -> None:
    file_content = open(filename).read()                # Прочитать файл и сохранить его содержимое в виде строки
    markers = re.split(r"\D+", file_content)            # Разбить строку на список строк (строки с числами)

    global fieldWidth
    global fieldLength
    fieldWidth = int(markers[0])                        # Первый элемент списка - ширина поля
    fieldLength = int(markers[1])                       # Второй элемент списка - высота поля

    global field
    for i in range(fieldWidth):                         # Создать список ячеек (числа в списке - маркеры текстуры поля)
        for j in range(fieldLength):                    # '2 +' означает пропуск двух первых чисел (ширины и высоты)
            field.append(Cell(Point2i(i, j), 0, 0, Texture(int(markers[2 + make_index(i, j)]))))


def set_start_and_finish_points(start: Point2i, finish: Point2i) -> None:
    global startPoint
    global finishPoint
    startPoint = start
    finishPoint = finish


def calculate_manhattan_distance(current: Point2i) -> int:
    return abs(current.i - finishPoint.i) + abs(current.j - finishPoint.j)


def orthogonal_increment(x: int) -> int:
    return x + 10


def diagonal_increment(x: int) -> int:
    return x + 14


def is_orthogonal_neighbors(n1: Cell, n2: Cell) -> bool:
    return n1.coordinate.i == n2.coordinate.i or n1.coordinate.j == n2.coordinate.j


def point_to_neighbours_north(current: Point2i) -> Point2i:
    return Point2i(current.i - 1, current.j)


def point_to_neighbours_northeast(current: Point2i) -> Point2i:
    return Point2i(current.i - 1, current.j + 1)


def point_to_neighbours_east(current: Point2i) -> Point2i:
    return Point2i(current.i, current.j + 1)


def point_to_neighbours_southeast(current: Point2i) -> Point2i:
    return Point2i(current.i + 1, current.j + 1)


def point_to_neighbours_south(current: Point2i) -> Point2i:
    return Point2i(current.i + 1, current.j)


def point_to_neighbours_southwest(current: Point2i) -> Point2i:
    return Point2i(current.i + 1, current.j - 1)


def point_to_neighbours_west(current: Point2i) -> Point2i:
    return Point2i(current.i, current.j - 1)


def point_to_neighbours_northwest(current: Point2i) -> Point2i:
    return Point2i(current.i - 1, current.j - 1)


def is_finish(cell: Cell) -> bool:
    return cell.coordinate.i == finishPoint.i and cell.coordinate.j == finishPoint.j


def inspect_neighbors(current_point: Point2i) -> None:
    neighbors = list()

    n = point_to_neighbours_north(current_point)
    neighbors.append(Pair(field[make_index(n)], True))

    n = point_to_neighbours_northeast(current_point)
    neighbors.append(Pair(field[make_index(n)],
                          field[make_index(point_to_neighbours_west(n))].texture != Texture.WALL and
                          field[make_index(point_to_neighbours_south(n))].texture != Texture.WALL))

    n = point_to_neighbours_east(current_point)
    neighbors.append(Pair(field[make_index(n)], True))

    n = point_to_neighbours_southeast(current_point)
    neighbors.append(Pair(field[make_index(n)],
                          field[make_index(point_to_neighbours_west(n))].texture != Texture.WALL and
                          field[make_index(point_to_neighbours_north(n))].texture != Texture.WALL))

    n = point_to_neighbours_south(current_point)
    neighbors.append(Pair(field[make_index(n)], True))

    n = point_to_neighbours_southwest(current_point)
    neighbors.append(Pair(field[make_index(n)],
                          field[make_index(point_to_neighbours_north(n))].texture != Texture.WALL and
                          field[make_index(point_to_neighbours_east(n))].texture != Texture.WALL))

    n = point_to_neighbours_west(current_point)
    neighbors.append(Pair(field[make_index(n)], True))

    n = point_to_neighbours_northwest(current_point)
    neighbors.append(Pair(field[make_index(n)],
                          field[make_index(point_to_neighbours_east(n))].texture != Texture.WALL and
                          field[make_index(point_to_neighbours_south(n))].texture != Texture.WALL))

    current_cell = field[make_index(current_point)]
    for elem in neighbors:
        n = elem.neighbor
        in_close_list = n in closeList
        in_open_list = n in openList
        is_passable = (n.texture != Texture.WALL) and elem.passable

        if is_passable:
            if not in_close_list:
                if is_orthogonal_neighbors(current_cell, n):
                    g = orthogonal_increment(current_cell.g)
                else:
                    g = diagonal_increment(current_cell.g)

                h = calculate_manhattan_distance(n.coordinate)

                f = n.g + n.h

                if in_open_list:
                    if f < current_cell.f:
                        n.arrow = current_cell
                        n.g = g
                        n.f = f
                    else:
                        pass
                else:
                    n.arrow = current_cell
                    n.g = g
                    n.h = h
                    n.f = f
                    openList.append(n)
        closeList.append(current_cell)


def search_path() -> bool:
    start_cell = field[make_index(startPoint)]
    start_cell.g = 0
    start_cell.h = 0
    start_cell.f = 0
    openList.append(start_cell)

    while len(openList) != 0:
        current_cell = min(openList, key=lambda cell: cell.g)
        openList.remove(current_cell)
        inspect_neighbors(current_cell.coordinate)
        if is_finish(current_cell):
            path_cell = current_cell
            while path_cell != field[make_index(startPoint)]:
                path.append(path_cell)
                path_cell = path_cell.arrow
            path.append(field[make_index(startPoint)])
            return True
    return False


def print_path():
    path_char = False
    for i in range(fieldWidth):
        for j in range(fieldLength):
            if field[make_index(i, j)].texture == Texture.LAND:
                for k in path:
                    if k.coordinate.i == i and k.coordinate.j == j:
                        print("::", end="")
                        path_char = True
                if not path_char:
                    print("  ", end="")
                path_char = False
            elif field[make_index(i, j)].texture == Texture.WALL:
                print("[]", end="")
        print()


class Data:
    def __init__(self, filename: str, start: Point2i, finish: Point2i):
        self.filename = filename
        self.start = start
        self.finish = finish


dataSet = [Data("markers9x11.txt", Point2i(4, 3), Point2i(4, 7)),
           Data("markers19x19.txt", Point2i(17, 1), Point2i(1, 17)),
           Data("markers20x30.txt", Point2i(1, 1), Point2i(18, 28)),
           Data("markers41x81.txt", Point2i(1, 1), Point2i(39, 79)),
           Data("markers50x80.txt", Point2i(1, 1), Point2i(48, 78)),
           Data("markers20x30-.txt", Point2i(1, 1), Point2i(18, 28)),
           ]


for e in dataSet:
    read_field_from_file(e.filename)
    set_start_and_finish_points(e.start, e.finish)
    time_stamp1 = time.time()
    if search_path():
        time_stamp2 = time.time()
        print("File: {0}\nThe path is found! The length of the path is: {1}".format(e.filename, len(path)))
        print("Time: {0:0.2f} ms".format((time_stamp2 - time_stamp1) * 1000.0))
        print_path()
        print()
    else:
        print("FIle: {0}\nThe path is not found!\n".format(e.filename))
        print_path()
        print()
    path.clear()
    openList.clear()
    closeList.clear()
    field.clear()
