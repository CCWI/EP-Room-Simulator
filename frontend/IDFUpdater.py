import math
import numpy as np
from eppy.modeleditor import IDF


class IDFUpdater:

    idf_output_path = ""

    def __init__(self, idf_file, epw_file, idd_file):
        IDF.setiddname(idd_file)
        self.IDF = IDF(idf_file, epw_file)
        self.idf_output_path = idf_file
        self.floor = self.get_floor()
        self.ceiling = self.get_ceiling()
        self.building = self.get_building()
        self.windows = self.get_windows()
        self.walls = self.get_walls()

    def get_floor(self):
        """
        Gets the floor surface object out of a idf file
        :return: floor surface object
        """
        return [f for f in self.IDF.idfobjects['BuildingSurface:Detailed'.upper()]
                if f.Surface_Type == 'Floor'][0]

    def get_ceiling(self):
        """
        Gets the ceiling surface object out of a idf file
        :return: ceiling surface object
        """
        return [c for c in self.IDF.idfobjects['BuildingSurface:Detailed'.upper()]
                if c.Surface_Type == 'Ceiling'][0]

    def get_walls(self):
        """
        Gets the wall surface objects out of a idf file
        :return: wall surface objects
        """
        return [w for w in self.IDF.idfobjects['BuildingSurface:Detailed'.upper()]
                if w.Surface_Type == 'Wall']

    def get_building(self):
        """
        Gets the building object out of an idf file
        :return:  building object
        """
        return self.IDF.idfobjects['building'.upper()][0]

    def set_building(self, building):
        """
        Sets the window surface object in an idf file
        """
        self.IDF.idfobjects['Building'][0] = building

    def get_windows(self):
        """
        Gets the fenestration surface objects of an idf file
        :return: list of fenestration surface objects
        """
        return [w for w in self.IDF.idfobjects['FenestrationSurface:Detailed']]

    def set_windows(self, windows):
        """
        Sets the fenestration surface objects in an idf file
        """
        self.IDF.idfobjects['FenestrationSurface:Detailed'] = windows

    def insertMeterSuffixToCoordinates(self, idfFile):
        """
        Modifies an IDF file by adding a unit suffix to all coordinate specifications.
        This is necessary for correct interpretation by idf viewers.
        The used unit is meters {m}.
        """
        f = open(idfFile, 'r')
        idfData = f.read()
        f.close()
        idfData_new = idfData.replace("coordinate", "coordinate {m}")
        f = open(idfFile, 'w')
        f.write(idfData_new)
        f.close()

    def calcLengthVector(self, coords):
        """
        Calculates the length vector of the given coordinates
        :param coords: coordinates for which the length vector should be calculated
        :return: length vector
        """
        vertex_1 = coords[0:3]
        vertex_2 = coords[3:6]
        vertex_3 = coords[6:9]
        vertex_4 = coords[9:12]

        lengthVector = vertex_4 - vertex_1

        return lengthVector

    def calcWidthVector(self, coords):
        """
        Calculates the width vector of the given coordinates
        :param coords: coordinates for which the width vector should be calculated
        :return: width vector
        """
        vertex_1 = coords[0:3]
        vertex_2 = coords[3:6]
        vertex_3 = coords[6:9]
        vertex_4 = coords[9:12]

        widthVector = vertex_2 - vertex_1

        return widthVector

    def calHeightVector(self, ceilingCoords, floorCoords):
        """
        Calculates the height vector of the given coordinates
        :param ceilingCoords: coordinates of the ceiling
        :param floorCoords: coordinates of the floor
        :return: height vector
        """
        vertex_2_floor = floorCoords[3:6]
        vertex_2_ceiling = ceilingCoords[3:6]

        heightVector = vertex_2_ceiling - vertex_2_floor

        return heightVector

    def calcWidthAdjRatio(self, widthInput, width):
        """
        Calculates the width adjust-ratio which represents the ratio of the old width to the new
        :param widthInput: new width which should be set
        :param width: calculated width of the base idf file
        :return: width adjust ratio
        """
        widthAdjRatio = widthInput / width
        return widthAdjRatio

    def calcLengthAdjRatio(self, lengthInput, length):
        """
        Calculates the length adjust-ratio which represents the ratio of the old length to the new
        :param lengthInput: new length which should be set
        :param length: calculated length of the base idf file
        :return: length adjust ratio
        """
        lengthAdjRatio = lengthInput / length
        return lengthAdjRatio

    def calcHeightAdjRatio(self, heightInput, height):
        """
        Calculates the height adjust-ratio which represents the ratio of the old height to the new
        :param heightInput: new height which should be set
        :param height: calculated height of the base idf file
        :return: height adjust ratio
        """
        heightAdjRatio = heightInput / height
        return heightAdjRatio

    def readCoords(self, surface):
        """
        Reads all the coordinates of a given surface, can be used for all surface objects
        :param surface: surface object
        :return: numpy array of all coordinates of the given surface
        """
        coordsList = np.array(
            [surface.Vertex_1_Xcoordinate, surface.Vertex_1_Ycoordinate, surface.Vertex_1_Zcoordinate,
             surface.Vertex_2_Xcoordinate, surface.Vertex_2_Ycoordinate, surface.Vertex_2_Zcoordinate,
             surface.Vertex_3_Xcoordinate, surface.Vertex_3_Ycoordinate, surface.Vertex_3_Zcoordinate,
             surface.Vertex_4_Xcoordinate, surface.Vertex_4_Ycoordinate, surface.Vertex_4_Zcoordinate])
        return coordsList

    def calcNewFloorCoords(self, floorCoords, widthInput, lengthInput, lengthVector, widthVector):
        """
        Calculates new coordinates of the floor object
        :param floorCoords: array of floor-coordinates
        :param widthInput: new width which should be set
        :param lengthInput: new length which should be set
        :param lengthVector: vector of the length (return of calcLengthVector)
        :param widthVector: vector of the width (return of calcWidthVector)
        :return: new coordinates of the floor as array
        """
        width = self.calcWidth(floorCoords)
        length = self.calcLength(floorCoords)
        widthAdjRatio = self.calcWidthAdjRatio(widthInput, width)
        lengthAdjRatio = self.calcLengthAdjRatio(lengthInput, length)
        vertex_1 = floorCoords[0:3]
        vertex_2 = floorCoords[3:6]
        vertex_3 = floorCoords[6:9]
        vertex_4 = floorCoords[9:12]

        # Adjusting coordinates to the new room size
        new_vertex_1 = vertex_1  # upper left corner
        # -> See GlobalGeometryRules: Starting Vertex Position = UpperLeftCorner
        new_vertex_2 = vertex_2 + widthVector * (widthAdjRatio - 1)
        new_vertex_3 = vertex_3 + widthVector * (widthAdjRatio - 1) + lengthVector * (lengthAdjRatio - 1)
        new_vertex_4 = vertex_4 + lengthVector * (lengthAdjRatio - 1)

        newFloorCoords = np.concatenate((new_vertex_1, new_vertex_2, new_vertex_3, new_vertex_4))
        return newFloorCoords

    # New coordinates are built from previously calculated floor coordinates.
    # These are shifted along the Z-axis in accordance with the room height.
    # Vertices 2 and 4 must be swapped, as floor vertices are in clockwise order, ceiling vertices in counterclockwise.

    def calcNewCeilingCoords(self, newFloorCoords, heightInput):
        """
        Calculates new coordinates of the ceiling object
        :param newFloorCoords: array of the new floor-coordinates
        :param heightInput: new height which should be set
        :return: new coordinates of the ceiling as array
        """
        height = heightInput
        newCeilingCoords = newFloorCoords.copy()
        for num in range(2, 12, 3):
            newCeilingCoords[num] = height

        copyNewCeilingCoords = newCeilingCoords.copy()
        ceilingVertex_1_ = copyNewCeilingCoords[6:9]
        ceilingVertex_3_ = copyNewCeilingCoords[0:3]
        newCeilingCoords[0:3] = ceilingVertex_1_
        newCeilingCoords[6:9] = ceilingVertex_3_

        return newCeilingCoords

    def calcWidth(self, floorCoords):
        """
        Calculates the room dimensions for the room width
        :param floorCoords: floorCoords of base idf file
        :return: width of room
        """
        width = math.sqrt((floorCoords[0] - floorCoords[3]) ** 2 + (floorCoords[1] - floorCoords[4]) ** 2)
        return width

    def calcLength(self, floorCoords):
        """
        Calculates the room dimensions for the room length
        :param floorCoords: floorCoords of base idf file
        :return: length of room
        """
        length = math.sqrt((floorCoords[0] - floorCoords[9]) ** 2 + (floorCoords[1] - floorCoords[10]) ** 2)
        return length

    def calcHeight(self, floorCoords, ceilingCoords):
        """
        Calculates the room dimensions for the room height
        :param floorCoords: floorCoords of base idf file
        :param ceilingCoords: ceilingCoords of base idf file
        :return: height of room
        """
        height = ceilingCoords[2] - floorCoords[2]
        return height

    def writeCoords(self, coords, surface):
        """
        Writes new coordinates in a given surface
        :param coords: array of coodinates
        :param surface: surface object for which new coordinates should be set
        """
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

    def generateNewWindowShading(self, windows):
        """
        Generates a list of WindowShadingControl objects with one object for each of the passed windows.
        Replicates the first WindowShadingControl object in the idf file.
        If the file does not contain any shading in advance, or the passed window list does not contain
        any window, an empy list is returned.
        :param windows: list of window objects
        :return: new list of WindowShadingControl objects
        """
        shadingObjects = self.get_windowShading()
        if (shadingObjects == []) or (windows == []):
            return []
        base_shading = self.IDF.copyidfobject(shadingObjects[0])
        shadingObjects = []
        for i, window in enumerate(windows):
            new_shading = self.IDF.copyidfobject(base_shading)
            shadingObjects.insert(i, new_shading)
            shadingObjects[i].Name = "Shading_Control_" + str(i)
            shadingObjects[i].Shading_Control_Sequence_Number = str(i + 1)
            shadingObjects[i].Fenestration_Surface_1_Name = window.Name
        return shadingObjects

    def generateNewWindows(self, walls, floor, ceiling, windows):
        """
        Generates a list of windows according to passed room dimensions.
        Replicates the first window in the passed windows list to fill the fassade with new windows.
        Generates as many windows as fit into the wall depending on its length.
        Sill height and window height are kept constant, unless the room is not high enough.
        In this case, the window height is adjusted to the maximum value that does not exceed the ceiling.
        :param walls: list of wall objects
        :param floor: floor object of the room
        :param ceiling: ceiling object of the room
        :param windows: list of window objects
        :return: new list of window objects
        """

        wall = self.getFacadeWall(walls)
        wallCoords = self.readCoords(wall)
        wall_llc = wallCoords[3:6]  # lower left corner
        wall_lrc = wallCoords[6:9]  # lower right corner
        wall_length = round(self.euclidean_distance_3d(wall_llc, wall_lrc), 3)

        win_length, win_height, sill_height = self.calcWindowDimensions(windows[0])
        win_number = int(wall_length / win_length)  # number of windows that can be placed on the wall

        room_height = self.readCoords(ceiling)[2] - self.readCoords(floor)[2]
        wall_part_length = round(wall_length / win_number, 3)  # length of the wall part reserved for one window

        windowsCoords = []
        for i in range(0, win_number):

            # horizontal placement
            padding = (wall_part_length - win_length) / 2
            window_llc = self.move_towards_point_3d(wall_llc, wall_lrc,
                                                    wall_part_length * i + padding)  # lower left corner
            window_lrc = self.move_towards_point_3d(wall_llc, wall_lrc,
                                                    wall_part_length * (i + 1) - padding)  # lower right corner

            # vertical placement & window height
            window_llc = (window_llc[0], window_llc[1], window_llc[2] + sill_height)  # lower left corner
            window_lrc = (window_lrc[0], window_lrc[1], window_lrc[2] + sill_height)  # lower right corner
            window_ulc = (window_llc[0], window_llc[1], window_llc[2] + win_height)  # upper left corner
            window_urc = (window_lrc[0], window_lrc[1], window_lrc[2] + win_height)  # upper right corner

            if window_llc[2] + win_height >= room_height:  # do not allow the window to exceed the ceiling
                window_ulc = (window_llc[0], window_llc[1], room_height)
                window_urc = (window_lrc[0], window_lrc[1], room_height)

            windowsCoords.append((window_ulc, window_llc, window_lrc, window_urc))

        # generate idf fenestration objects based on the first window according to the calculated coordinates

        base_window = self.IDF.copyidfobject(windows[0])
        windows = []
        for i, winCoords in enumerate(windowsCoords):
            new_window = self.IDF.copyidfobject(base_window)
            windows.insert(i, new_window)
            windows[i].Name = "Window_" + str(i)
            self.writeCoords(np.ravel(winCoords), windows[i])
        return windows

    def move_towards_point_3d(self, p_start, p_end, distance):
        """
        Moves a starting point towards and end point in 3D space for a given distance and returns the new point.
        """
        direction = [p_end[i] - p_start[i] for i in range(len(p_start))]
        length = math.sqrt(sum([d ** 2 for d in direction]))
        direction_scaled = [(distance * d) / length for d in direction]
        return tuple(p_start[i] + direction_scaled[i] for i in range(len(p_start)))

    def calcWindowDimensions(self, window):
        """
        Calculates the horizontal and vertical length of a window as well as its sill height.
        Returns the results rounded to 3 decimal places.
        """
        winCoords = self.readCoords(window)
        length_v = self.euclidean_distance_3d(winCoords[0:3], winCoords[3:6])
        length_h = self.euclidean_distance_3d(winCoords[3:6], winCoords[6:9])
        sill_height = min(winCoords[2], winCoords[5], winCoords[8], winCoords[11])  # min height coord of all edges
        return round(length_h, 3), round(length_v, 3), round(sill_height, 3)

    def set_windowShading(self, shadings):
        """
        Sets the WindowShadingControl objects in an idf file
        """
        self.IDF.idfobjects['WindowShadingControl'] = shadings

    def get_windowShading(self):
        """
        Gets the WindowShadingControl objects of an idf file
        :return: list of WindowShadingControl objects
        """
        return [s for s in self.IDF.idfobjects['WindowShadingControl']]

    def getFacadeWall(self, walls):
        """
        Returns the facade wall within an array of wall objects.
        Note that this function assumes there is only one facade and all other walls are adiabatic.
        If there are multiple facades, the first one is returned.
        """
        for wall in walls:
            if "Outdoors" in str(wall):
                return wall

    def euclidean_distance_3d(self, p1, p2):
        """
        Calculates the euclidean distance between two points in 3-dimensional space
        """
        return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2)

    def calcFloorArea(self):
        """
        Calculates the floor area of the room in m²
        Returns the result rounded to 3 decimal places
        """
        floorCoords = self.readCoords(self.floor)
        floorArea = self.calcLength(floorCoords) * self.calcWidth(floorCoords)
        return round(floorArea, 3)

    def calcGlazedArea(self):
        """
        Calculates the area covered by window glas in m²
        Returns the result rounded to 3 decimal places
        """
        glaced_area = 0.
        for win in self.windows:
            winCoords = self.readCoords(win)
            length_v = self.euclidean_distance_3d(winCoords[0:3], winCoords[3:6])
            length_h = self.euclidean_distance_3d(winCoords[3:6], winCoords[6:9])
            glaced_area += (length_v * length_h)
        return round(glaced_area, 3)

    def calcWindowToFloorRatio(self):
        '''
        Calculates the ratio between glazed area and floor space.
        Returns the result rounded to 3 decimal places.
        '''
        floorArea = self.calcFloorArea()
        glazedArea = self.calcGlazedArea()
        return round(glazedArea / floorArea, 3)

    # Calculate new vertices for all four walls from the new floor and ceiling coordinates
    # Vertex order is assumed to be: upper right corner & clockwise
    # Vertex numbers that belong to the equivalent line in floor and ceiling coordinates are as follows for lines a-d:
    floor_lines = {'a': (0, 3), 'b': (1, 0), 'c': (2, 1), 'd': (3, 2)}
    ceiling_lines = {'a': (2, 3), 'b': (1, 2), 'c': (0, 1), 'd': (3, 0)}

    def calcWallCoords(self, wallID, newFloorCoords, newCeilingCoords):
        """
        Calculates the new coordinates for a wall, according to previously calculated floor/ceiling coordinates.
        :param wallID: ID (0-3) of the wall, used to select the according floor/ceiling lines
        :param newFloorCoords: calculated floor coordinates
        :param newCeilingCoords: calculated ceiling coordinates
        :return: numpy array of the new coordinates for the wall
        """
        ceiling_points = list(self.ceiling_lines.values())[wallID]
        floor_points = list(self.floor_lines.values())[wallID]
        vertex_1 = newCeilingCoords[ceiling_points[0] * 3: ceiling_points[0] * 3 + 3]
        vertex_2 = newFloorCoords[floor_points[0] * 3: floor_points[0] * 3 + 3]
        vertex_3 = newFloorCoords[floor_points[1] * 3: floor_points[1] * 3 + 3]
        vertex_4 = newCeilingCoords[ceiling_points[1] * 3: ceiling_points[1] * 3 + 3]
        return np.ravel((vertex_1, vertex_2, vertex_3, vertex_4))

    def saveIDF(self):
        """
        Saves the current idf data to the file path specified as idf_output_path.
        Inserts meter suffixes {m} to coordinates to allow interpretability by IDF viewers.
        """
        # save to IDF file
        self.IDF.saveas(self.idf_output_path)
        # add {m} suffixes to IDF file
        self.insertMeterSuffixToCoordinates(self.idf_output_path)

    def updateOrientation(self, orientation=0):
        """
        Updates the building orientation in an idf file and saves the updated file.
        :param orientation: building orientation in degrees (0-360), the default value 0 means north oriented
        """
        self.building.North_Axis = orientation
        self.set_building(self.building)
        self.saveIDF()

    def updateRoomSize(self, widthInput, lengthInput, heightInput):
        """
        Updates the coordinates of floor, ceiling, walls and windows in an idf file according
        to new room dimensions. Saves the updated idf file.
        Regarding windows, the first window in the idf is replicated to fill the fassade with new windows.
        If the idf file does not contain any window, this step is skipped.
        :param widthInput:  new room width
        :param lengthInput: new room length
        :param heightInput: new room height
        """
        # check input validity
        if (widthInput < 1) | (lengthInput < 1):
            raise ValueError("Invalid input room size. Floors must measure at least 1m x 1m.")
        if heightInput < 2:
            raise ValueError("Invalid input room height. Rooms can not have a height of less than 2m.")
        if len(self.walls) != 4:
            raise ValueError("Invalid number of walls in idf file. The idf must specify exactly 4 walls.")

        # read coordinates from idf-file
        floorCoords = self.readCoords(self.floor)
        ceilingCoords = self.readCoords(self.ceiling)
        lengthVector = self.calcLengthVector(floorCoords)
        widthVector = self.calcWidthVector(floorCoords)
        heightVector = self.calHeightVector(ceilingCoords, floorCoords)

        # calculate new floor and ceiling coordinates
        newFloorCoords = self.calcNewFloorCoords(floorCoords, widthInput, lengthInput, lengthVector, widthVector)
        newCeilingCoords = self.calcNewCeilingCoords(newFloorCoords, heightInput)

        # calculate new wall coordinates
        newWallCoords = []
        for i in range(0, 4):  # wall 0-3
            newWallCoords.append(self.calcWallCoords(i, newFloorCoords, newCeilingCoords))

        # update coordinates in the surface objects of the idf file
        #   floor and ceiling
        self.writeCoords(newFloorCoords, self.floor)
        self.writeCoords(newCeilingCoords, self.ceiling)
        #   walls
        for i, wall in enumerate(self.walls):
            self.writeCoords(newWallCoords[i], self.walls[i])

        # calculate and write new windows
        if len(self.windows) > 0:
            new_windows = self.generateNewWindows(self.walls, self.floor, self.ceiling, self.windows)
            self.set_windows(new_windows)

        # generate new window shading for all windows (if shadings exist)
        new_shadings = self.generateNewWindowShading(new_windows)
        self.set_windowShading(new_shadings)

        # save
        self.saveIDF()
