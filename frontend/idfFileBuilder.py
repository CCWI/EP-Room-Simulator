"""
IDFileBuilder class in Frontend
The functionality of this class is identical to the RoomHelper.py class in the backend
However this frontend class works without any other components of this project and therefore can be copied to a
seperate project and easily be used for testing purposes, in case the room scaling has to be adapted by the next group.
"""

import math
import numpy
from eppy.modeleditor import IDF


# Input parameters are set by default to the initial dimensions
widthInput = 4.100000000000001
lengthInput = 6.000000000000007
heightInput = 4.0

widthAdj = widthInput - 4.100000000000001
lengthAdj = lengthInput - 6.000000000000007
heightAdj = heightInput - 3.0

# If used for testing: Change file path to local directory
iddfile = "/Applications/EnergyPlus-22-2-0/Energy+.idd"
idffile = "/Users/Project/EnergyPlus_Room_simulation/room.idf"

IDF.setiddname(iddfile)
idf = IDF(idffile)

# Read of surface objects
floor = [f for f in idf.idfobjects['BuildingSurface:Detailed'.upper()]
         if f.Surface_Type == 'Floor'][0]

ceiling = [c for c in idf.idfobjects['BuildingSurface:Detailed'.upper()]
           if c.Surface_Type == 'Ceiling'][0]

walls = [w for w in idf.idfobjects['BuildingSurface:Detailed'.upper()]
         if w.Surface_Type == 'Wall']

windows = [w for w in idf.idfobjects['FenestrationSurface:Detailed']]


# read coordinates of surface
def readCoords(surface):
    coordsList = numpy.array([surface.Vertex_1_Xcoordinate, surface.Vertex_1_Ycoordinate, surface.Vertex_1_Zcoordinate,
                              surface.Vertex_2_Xcoordinate, surface.Vertex_2_Ycoordinate, surface.Vertex_2_Zcoordinate,
                              surface.Vertex_3_Xcoordinate, surface.Vertex_3_Ycoordinate, surface.Vertex_3_Zcoordinate,
                              surface.Vertex_4_Xcoordinate, surface.Vertex_4_Ycoordinate, surface.Vertex_4_Zcoordinate])
    return coordsList


# Write new coordinates in idf-surface-object
def writeCoords(coords, surface):
    surface.Vertex_1_Xcoordinate = coords[0]
    surface.Vertex_1_Ycoordinate = coords[1]
    surface.Vertex_1_Zcoordinate = coords[2]
    surface.Vertex_2_Xcoordinate = coords[3]
    surface.Vertex_2_Ycoordinate = coords[4]
    surface.Vertex_2_Zcoordinate = coords[5]
    surface.Vertex_3_Xcoordinate = coords[6]
    surface.Vertex_3_Ycoordinate = coords[7]
    surface.Vertex_3_Zcoordinate = coords[8]
    surface.Vertex_4_Xcoordinate = coords[9]
    surface.Vertex_4_Ycoordinate = coords[10]
    surface.Vertex_4_Zcoordinate = coords[11]


# Calculate room dimensions
def calcWidth():
    width = math.sqrt((floorCoords[0] - floorCoords[3]) ** 2 + (floorCoords[1] - floorCoords[4]) ** 2)
    return width


def calcLength():
    length = math.sqrt((floorCoords[0] - floorCoords[9]) ** 2 + (floorCoords[1] - floorCoords[10]) ** 2)
    return length


def calcHeight():
    # can be calculated simplified and without Euclidean distance, because the wall is vertical
    height = ceilingCoords[2] - floorCoords[2]
    return height


# Calculation of lenght and width of vectors
def calcWidthVector(coords):
    vertex_1 = coords[0:3]
    vertex_2 = coords[3:6]
    vertex_3 = coords[6:9]
    vertex_4 = coords[9:12]

    widthVector = vertex_2 - vertex_1
    return widthVector


def calcLengthVector(coords):
    vertex_1 = coords[0:3]
    vertex_2 = coords[3:6]
    vertex_3 = coords[6:9]
    vertex_4 = coords[9:12]

    lengthVector = vertex_4 - vertex_1

    return lengthVector


def calHeightVector(ceilingCoords, floorCoords):
    vertex_2_floor = floorCoords[3:6]
    vertex_2_ceiling = ceilingCoords[3:6]

    heightVector = vertex_2_ceiling - vertex_2_floor

    return heightVector


# Calculation of lengths and widths fitting ratios, i.e. the ratio of the new wall length to the old one.
def calcWidthAdjRatio(width):
    widthAdjRatio = widthInput / width
    return widthAdjRatio


def calcLengthAdjRatio(length):
    lengthAdjRatio = lengthInput / length
    return lengthAdjRatio


def calcHeightAdjRatio(height):
    heightAdjRatio = heightInput / height

    return heightAdjRatio


# Calculate the new coordinates of the surfaces
def calcNewFloorCoords(coords):
    width = calcWidth()
    length = calcLength()
    widthAdjRatio = calcWidthAdjRatio(width)
    lengthAdjRatio = calcLengthAdjRatio(length)

    vertex_1 = coords[0:3]
    vertex_2 = coords[3:6]
    vertex_3 = coords[6:9]
    vertex_4 = coords[9:12]

    # Adjust the coordinates to the new room dimensions. The starting point for the floor is the upper left corner.
    # -> GlobalGeometryRules: Starting Vertex Position = UpperLeftCorner
    new_vertex_1 = vertex_1
    new_vertex_2 = vertex_2 + widthVector * (widthAdjRatio - 1)
    new_vertex_3 = vertex_3 + widthVector * (widthAdjRatio - 1) + lengthVector * (lengthAdjRatio - 1)
    new_vertex_4 = vertex_4 + lengthVector * (lengthAdjRatio - 1)

    newFloorCoords = numpy.concatenate((new_vertex_1, new_vertex_2, new_vertex_3, new_vertex_4))
    return newFloorCoords


def calcNewCeilingCoords(newFloorCoords, heightAdj):
    height = heightInput
    newCeilingCoords = newFloorCoords.copy()
    for num in range(2, 12, 3):
        newCeilingCoords[num] = height

    # The arrangement of the vertices differs for the floor and the ceiling.
    # (Vertex 1 floor = Vertex 3 ceiling UND Vertex 3 floor = Vertex 1 ceiling; Vertices 2 und 4 are the same)
    # Since the ceiling is formed from a copy of the floor, the vertices still need to be moved.

    copyNewCeilingCoords = newCeilingCoords.copy()
    ceilingVertex_1_ = copyNewCeilingCoords[6:9]
    ceilingVertex_3_ = copyNewCeilingCoords[0:3]
    newCeilingCoords[0:3] = ceilingVertex_1_
    newCeilingCoords[6:9] = ceilingVertex_3_

    return newCeilingCoords


# From the newly calculated ceiling and floor coordinates, the coordinates of all four walls can be formed.
def calcWall_1_Coords():
    vertex_1 = newCeilingCoords[6:9]
    vertex_2 = newFloorCoords[0:3]
    vertex_3 = newFloorCoords[9:12]
    vertex_4 = newCeilingCoords[9:12]

    wall_1_Coords = numpy.concatenate((vertex_1, vertex_2, vertex_3, vertex_4))
    return wall_1_Coords


def calcWall_2_Coords():
    vertex_1 = newCeilingCoords[3:6]
    vertex_2 = newFloorCoords[3:6]
    vertex_3 = newFloorCoords[0:3]
    vertex_4 = newCeilingCoords[6:9]

    wall_2_Coords = numpy.concatenate((vertex_1, vertex_2, vertex_3, vertex_4))
    return wall_2_Coords


def calcWall_3_Coords():
    vertex_1 = newCeilingCoords[0:3]
    vertex_2 = newFloorCoords[6:9]
    vertex_3 = newFloorCoords[3:6]
    vertex_4 = newCeilingCoords[3:6]

    wall_3_Coords = numpy.concatenate((vertex_1, vertex_2, vertex_3, vertex_4))
    return wall_3_Coords


def calcWall_4_Coords():
    vertex_1 = newCeilingCoords[9:12]
    vertex_2 = newFloorCoords[9:12]
    vertex_3 = newFloorCoords[6:9]
    vertex_4 = newCeilingCoords[0:3]

    wall_4_Coords = numpy.concatenate((vertex_1, vertex_2, vertex_3, vertex_4))
    return wall_4_Coords


def calcNewWindowCoords(coords):
    length = calcLength()
    width = calcWidth()
    height = calcHeight()

    lengthAdjRatio = calcLengthAdjRatio(length)
    widthAdjRatio = calcWidthAdjRatio(width)
    heightAdjRatio = calcHeightAdjRatio(height)

    distanceToWallLeftWindowSide = math.sqrt((coords[3] - floorCoords[9]) ** 2 + (coords[4] - floorCoords[10]) ** 2)
    distanceToWallRightWindowSide = math.sqrt((coords[6] - floorCoords[9]) ** 2 + (coords[7] - floorCoords[10]) ** 2)
    distanceToFloorWindowTop = coords[2] - floorCoords[2]
    distanceToFloorWindowBottom = coords[5] - floorCoords[2]

    newVertex_1 = coords[0:3] \
                  + lengthVector * (lengthAdjRatio - 1) \
                  + widthVector * (widthAdjRatio - 1) * distanceToWallLeftWindowSide / 4.1 \
                  + heightVector * (heightAdjRatio - 1) * distanceToFloorWindowTop / 3
    newVertex_2 = coords[3:6] \
                  + lengthVector * (lengthAdjRatio - 1) \
                  + widthVector * (widthAdjRatio - 1) * distanceToWallLeftWindowSide / 4.1 \
                  + heightVector * (heightAdjRatio - 1) * distanceToFloorWindowBottom / 3
    newVertex_3 = coords[6:9] \
                  + lengthVector * (lengthAdjRatio - 1) \
                  + widthVector * (widthAdjRatio - 1) * distanceToWallRightWindowSide / 4.1 \
                  + heightVector * (heightAdjRatio - 1) * distanceToFloorWindowBottom / 3
    newVertex_4 = coords[9:12] \
                  + lengthVector * (lengthAdjRatio - 1) \
                  + widthVector * (widthAdjRatio - 1) * distanceToWallRightWindowSide / 4.1 \
                  + heightVector * (heightAdjRatio - 1) * distanceToFloorWindowTop / 3

    newWindowCoords = numpy.concatenate((newVertex_1, newVertex_2, newVertex_3, newVertex_4))

    return newWindowCoords


# read coordinates of floor, ceiling and windows of idf-file
floorCoords = readCoords(floor)
ceilingCoords = readCoords(ceiling)

window_1_Coords = readCoords(windows[0])
window_2_Coords = readCoords(windows[1])
window_3_Coords = readCoords(windows[2])

# calculate lenght and with vectors
lengthVector = calcLengthVector(floorCoords)
widthVector = calcWidthVector(floorCoords)
heightVector = calHeightVector(ceilingCoords, floorCoords)

# calculate the new coordinates for floor and ceiling
newFloorCoords = calcNewFloorCoords(floorCoords)
newCeilingCoords = calcNewCeilingCoords(newFloorCoords, heightAdj)

# calculate new coordinates for four walls
newWall_1_Coords = calcWall_1_Coords()
newWall_2_Coords = calcWall_2_Coords()
newWall_3_Coords = calcWall_3_Coords()
newWall_4_Coords = calcWall_4_Coords()

# Calculate the new coordinates of the three Windows
newWindow_1_Coords = calcNewWindowCoords(window_1_Coords)
newWindow_2_Coords = calcNewWindowCoords(window_2_Coords)
newWindow_3_Coords = calcNewWindowCoords(window_3_Coords)

# Update new coordinates in the surface-object in idf-file
# ceiling and floor
writeCoords(newFloorCoords, floor)
writeCoords(newCeilingCoords, ceiling)

# walls 1-4
writeCoords(newWall_1_Coords, walls[0])
writeCoords(newWall_2_Coords, walls[1])
writeCoords(newWall_3_Coords, walls[2])
writeCoords(newWall_4_Coords, walls[3])

# windows 1-3
writeCoords(newWindow_1_Coords, windows[0])
writeCoords(newWindow_2_Coords, windows[1])
writeCoords(newWindow_3_Coords, windows[2])

# Save change in new idf-file
idf.saveas("adjustedIDF1.idf")
