import math
import numpy as np
from eppy.modeleditor import IDF


class Room_Helper:
    """
    Helper class for usage in simulation.py for idf-operations regarding the dimensions of a room to simulate.
    Main function to use: update_room_size
    """

    idf_output_path = "tmp/adjustedIDF.idf"

    def __init__(self, idf_file, epw_file, idd_file):
        IDF.setiddname(idd_file)
        self.IDF = IDF(idf_file, epw_file)
        self.floor = self.get_floor()
        self.ceiling = self.get_ceiling()
        self.walls = self.get_walls()
        self.windows = self.get_windows()
        self.building = self.get_building()

    def get_floor(self):
        """
        Gets the floor surface object out of an idf file
        :return: floor surface object
        """
        return [f for f in self.IDF.idfobjects['BuildingSurface:Detailed'.upper()]
                if f.Surface_Type == 'Floor'][0]

    def get_ceiling(self):
        """
        Gets the ceiling surface object out of an idf file
        :return: ceiling surface object
        """
        return [c for c in self.IDF.idfobjects['BuildingSurface:Detailed'.upper()]
                if c.Surface_Type == 'Ceiling'][0]

    def get_walls(self):
        """
        Gets the wall surface objects out of an idf file
        :return: wall surface objects
        """
        return [w for w in self.IDF.idfobjects['BuildingSurface:Detailed'.upper()]
                if w.Surface_Type == 'Wall']

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

    def get_windowShading(self):
        """
        Gets the WindowShadingControl objects of an idf file
        :return: list of WindowShadingControl objects
        """
        return [s for s in self.IDF.idfobjects['WindowShadingControl']]

    def set_windowShading(self, shadings):
        """
        Sets the WindowShadingControl objects in an idf file
        """
        self.IDF.idfobjects['WindowShadingControl'] = shadings

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

    def readCoords(self, surface):
        """
        Reads all the coordinates of a given surface, can be used for all surface objects
        :param surface: surface object
        :return: numpy array of all coordinates of the given surface
        """
        coords_list = np.array(
            [surface.Vertex_1_Xcoordinate, surface.Vertex_1_Ycoordinate, surface.Vertex_1_Zcoordinate,
             surface.Vertex_2_Xcoordinate, surface.Vertex_2_Ycoordinate, surface.Vertex_2_Zcoordinate,
             surface.Vertex_3_Xcoordinate, surface.Vertex_3_Ycoordinate, surface.Vertex_3_Zcoordinate,
             surface.Vertex_4_Xcoordinate, surface.Vertex_4_Ycoordinate, surface.Vertex_4_Zcoordinate])
        return coords_list

    def writeCoords(self, coords, surface):
        """
        Writes new coordinates in a given surface
        :param coords: array of coordinates
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

    def insertMeterSuffixToCoordinates(self, idf_file):
        """
        Modifies an IDF file by adding a unit suffix to all coordinate specifications.
        This is necessary for correct interpretation by idf viewers.
        The used unit is meters {m}.
        """
        f = open(idf_file, 'r')
        idf_data = f.read()
        f.close()
        idf_data_new = idf_data.replace("coordinate", "coordinate {m}")
        f = open(idf_file, 'w')
        f.write(idf_data_new)
        f.close()

    def getFirstZoneNameFromIDF(self):
        """
        Retrieves the first zone name from the idf file
        :return: Zone name
        """
        zone_name = self.IDF.idfobjects['Zone'][0]
        return zone_name.Name

    def calcNewFloorCoords(self, floor_coords, width_input, length_input, length_vector, width_vector):
        """
        Calculates new coordinates of the floor object
        :param floor_coords: array of floor-coordinates
        :param width_input: new width which should be set
        :param length_input: new length which should be set
        :param length_vector: vector of the length (return of calcLengthVector)
        :param width_vector: vector of the width (return of calcWidthVector)
        :return: new coordinates of the floor as array
        """
        width = self.calcWidth(floor_coords)
        length = self.calcLength(floor_coords)
        width_adj_ratio = self.calcWidthAdjRatio(width_input, width)
        length_adj_ratio = self.calcLengthAdjRatio(length_input, length)
        vertex_1 = floor_coords[0:3]
        vertex_2 = floor_coords[3:6]
        vertex_3 = floor_coords[6:9]
        vertex_4 = floor_coords[9:12]

        # Adjusting coordinates to the new room size
        new_vertex_1 = vertex_1  # upper left corner
        # -> See GlobalGeometryRules: Starting Vertex Position = UpperLeftCorner
        new_vertex_2 = vertex_2 + width_vector * (width_adj_ratio - 1)
        new_vertex_3 = vertex_3 + width_vector * (width_adj_ratio - 1) + length_vector * (length_adj_ratio - 1)
        new_vertex_4 = vertex_4 + length_vector * (length_adj_ratio - 1)

        new_floor_coords = np.concatenate((new_vertex_1, new_vertex_2, new_vertex_3, new_vertex_4))
        return new_floor_coords

    # New coordinates are built from previously calculated floor coordinates.
    # These are shifted along the Z-axis in accordance with the room height.
    # Vertices 2 and 4 must be swapped, as floor vertices are in clockwise order, ceiling vertices in counterclockwise.

    def calcNewCeilingCoords(self, new_floor_coords, height_input):
        """
        Calculates new coordinates of the ceiling object
        :param new_floor_coords: array of the new floor-coordinates
        :param height_input: new height which should be set
        :return: new coordinates of the ceiling as array
        """
        height = height_input
        new_ceiling_coords = new_floor_coords.copy()
        for num in range(2, 12, 3):
            new_ceiling_coords[num] = height

        copy_new_ceiling_coords = new_ceiling_coords.copy()
        ceiling_vertex_1 = copy_new_ceiling_coords[6:9]
        ceiling_vertex_3 = copy_new_ceiling_coords[0:3]
        new_ceiling_coords[0:3] = ceiling_vertex_1
        new_ceiling_coords[6:9] = ceiling_vertex_3

        return new_ceiling_coords

    def calcWidth(self, floor_coords):
        """
        Calculates the room dimensions for the room width
        :param floor_coords: floorCoords of base idf file
        :return: width of room
        """
        width = math.sqrt((floor_coords[0] - floor_coords[3]) ** 2 + (floor_coords[1] - floor_coords[4]) ** 2)
        return width

    def calcLength(self, floor_coords):
        """
        Calculates the room dimensions for the room length
        :param floor_coords: floorCoords of base idf file
        :return: length of room
        """
        length = math.sqrt((floor_coords[0] - floor_coords[9]) ** 2 + (floor_coords[1] - floor_coords[10]) ** 2)
        return length

    def calcHeight(self, floor_coords, ceiling_coords):
        """
        Calculates the room dimensions for the room height
        :param floor_coords: floorCoords of base idf file
        :param ceiling_coords: ceilingCoords of base idf file
        :return: height of room
        """
        height = ceiling_coords[2] - floor_coords[2]
        return height

    def calcWidthAdjRatio(self, width_input, width):
        """
        Calculates the width adjust-ratio which represents the ratio of the old width to the new one
        :param width_input: new width which should be set
        :param width: calculated width of the base idf file
        :return: width adjust ratio
        """
        width_adj_ratio = width_input / width
        return width_adj_ratio

    def calcLengthAdjRatio(self, length_input, length):
        """
        Calculates the length adjust-ratio which represents the ratio of the old length to the new one
        :param length_input: new length which should be set
        :param length: calculated length of the base idf file
        :return: length adjust ratio
        """
        length_adj_ratio = length_input / length
        return length_adj_ratio

    def calcHeightAdjRatio(self, height_input, height):
        """
        Calculates the height adjust-ratio which represents the ratio of the old height to the new one
        :param height_input: new height which should be set
        :param height: calculated height of the base idf file
        :return: height adjust ratio
        """
        height_adj_ratio = height_input / height
        return height_adj_ratio

    def euclidean_distance_3d(self, p1, p2):
        """
        Calculates the Euclidean distance between two points in 3-dimensional space
        :return: distance between two points
        """
        return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2)

    def move_towards_point_3d(self, p_start, p_end, distance):
        """
        Moves a starting point towards and end point in 3D space for a given distance
        :return: coordinates of the new point
        """
        direction = [p_end[i] - p_start[i] for i in range(len(p_start))]
        length = math.sqrt(sum([d ** 2 for d in direction]))
        direction_scaled = [(distance * d) / length for d in direction]
        return tuple(p_start[i] + direction_scaled[i] for i in range(len(p_start)))

    def calcFloorArea(self):
        """
        Calculates the floor area of the room in m²
        :return: floor area rounded to 3 decimal places
        """
        floor_coords = self.readCoords(self.floor)
        floor_area = self.calcLength(floor_coords) * self.calcWidth(floor_coords)
        return round(floor_area, 3)

    def calcGlazedArea(self):
        """
        Calculates the area covered by window glas in m²
        :return: window area rounded to 3 decimal places
        """
        glazed_area = 0.
        for win in self.windows:
            win_coords = self.readCoords(win)
            length_v = self.euclidean_distance_3d(win_coords[0:3], win_coords[3:6])
            length_h = self.euclidean_distance_3d(win_coords[3:6], win_coords[6:9])
            glazed_area += (length_v * length_h)
        return round(glazed_area, 3)

    def calcWindowToFloorRatio(self):
        """
        Calculates the ratio between glazed area and floor space.
        :return: ratio rounded to 3 decimal places.
        """
        floor_area = self.calcFloorArea()
        glazed_area = self.calcGlazedArea()
        return round(glazed_area / floor_area, 3)

    # Calculate new vertices for all four walls from the new floor and ceiling coordinates
    # Vertex order is assumed to be: upper right corner & clockwise
    # Vertex numbers that belong to the equivalent line in floor and ceiling coordinates are as follows for lines a-d:
    floor_lines = {'a': (0, 3), 'b': (1, 0), 'c': (2, 1), 'd': (3, 2)}
    ceiling_lines = {'a': (2, 3), 'b': (1, 2), 'c': (0, 1), 'd': (3, 0)}

    def calcWallCoords(self, wall_id, new_floor_coords, new_ceiling_coords):
        """
        Calculates the new coordinates for a wall, according to previously calculated floor/ceiling coordinates.
        :param wall_id: ID (0-3) of the wall, used to select the according floor/ceiling lines
        :param new_floor_coords: calculated floor coordinates
        :param new_ceiling_coords: calculated ceiling coordinates
        :return: numpy array of the new coordinates for the wall
        """
        ceiling_points = list(self.ceiling_lines.values())[wall_id]
        floor_points = list(self.floor_lines.values())[wall_id]
        vertex_1 = new_ceiling_coords[ceiling_points[0] * 3: ceiling_points[0] * 3 + 3]
        vertex_2 = new_floor_coords[floor_points[0] * 3: floor_points[0] * 3 + 3]
        vertex_3 = new_floor_coords[floor_points[1] * 3: floor_points[1] * 3 + 3]
        vertex_4 = new_ceiling_coords[ceiling_points[1] * 3: ceiling_points[1] * 3 + 3]
        return np.ravel((vertex_1, vertex_2, vertex_3, vertex_4))

    def calcLengthVector(self, coords):
        """
        Calculates the length vector of the given coordinates
        :param coords: coords for which the length vector should be calculated
        :return: length vector
        """
        vertex_1 = coords[0:3]
        vertex_2 = coords[3:6]
        vertex_3 = coords[6:9]
        vertex_4 = coords[9:12]

        length_vector = vertex_4 - vertex_1

        return length_vector

    def calcWidthVector(self, coords):
        """
        Calculates the width vector of the given coordinates
        :param coords: coords for which the width vector should be calculated
        :return: width vector
        """
        vertex_1 = coords[0:3]
        vertex_2 = coords[3:6]
        vertex_3 = coords[6:9]
        vertex_4 = coords[9:12]

        width_vector = vertex_2 - vertex_1

        return width_vector

    def calHeightVector(self, ceiling_coords, floor_coords):
        """
        Calculates the height vector of the given coordinates
        :param ceiling_coords: coords of the ceiling
        :param floor_coords: coords of the floor
        :return: height vector
        """
        vertex_2_floor = floor_coords[3:6]
        vertex_2_ceiling = ceiling_coords[3:6]

        height_vector = vertex_2_ceiling - vertex_2_floor

        return height_vector

    def getFacadeWall(self, walls):
        """
        Returns the facade wall within an array of wall objects.
        Note that this function assumes there is only one facade and all other walls are adiabatic.
        If there are multiple facades, the first one is returned.
        :param walls: wall objects
        :return: facade wall object
        """
        for wall in walls:
            if "Outdoors" in str(wall):
                return wall

    def calcWindowDimensions(self, window):
        """
        Calculates the horizontal and vertical length of a window as well as its sill height.
        :param window: window objects
        :return: Returns the results rounded to 3 decimal places.
        """
        win_coords = self.readCoords(window)
        length_v = self.euclidean_distance_3d(win_coords[0:3], win_coords[3:6])
        length_h = self.euclidean_distance_3d(win_coords[3:6], win_coords[6:9])
        sill_height = min(win_coords[2], win_coords[5], win_coords[8], win_coords[11])  # min height coord of all edges
        return round(length_h, 3), round(length_v, 3), round(sill_height, 3)

    def generateNewWindowShading(self, windows):
        """
        Generates a list of WindowShadingControl objects with one object for each of the passed windows.
        Replicates the first WindowShadingControl object in the idf file.
        If the file does not contain any shading in advance, or the passed window list does not contain
        any window, an empy list is returned.
        :param windows: list of window objects
        :return: new list of WindowShadingControl objects
        """
        shading_objects = self.get_windowShading()
        if (shading_objects == []) or (windows == []):
            return []
        base_shading = self.IDF.copyidfobject(shading_objects[0])
        shading_objects = []
        for i, window in enumerate(windows):
            new_shading = self.IDF.copyidfobject(base_shading)
            shading_objects.insert(i, new_shading)
            shading_objects[i].Name = "Shading_Control_" + str(i)
            shading_objects[i].Shading_Control_Sequence_Number = str(i + 1)
            shading_objects[i].Fenestration_Surface_1_Name = window.Name
        return shading_objects

    def generateNewWindows(self, walls, floor, ceiling, windows):
        """
        Generates a list of windows according to passed room dimensions.
        Replicates the first window in the windows list to fill the facade with new windows.
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
        wall_coords = self.readCoords(wall)
        wall_llc = wall_coords[3:6]  # lower left corner
        wall_lrc = wall_coords[6:9]  # lower right corner
        wall_length = round(self.euclidean_distance_3d(wall_llc, wall_lrc), 3)

        win_length, win_height, sill_height = self.calcWindowDimensions(windows[0])
        win_number = int(wall_length / win_length)  # number of windows that can be placed on the wall

        room_height = self.readCoords(ceiling)[2] - self.readCoords(floor)[2]
        wall_part_length = round(wall_length / win_number, 3)  # length of the wall part reserved for one window

        windows_coords = []
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

            windows_coords.append((window_ulc, window_llc, window_lrc, window_urc))

        # generate idf fenestration objects based on the first window according to the calculated coordinates

        base_window = self.IDF.copyidfobject(windows[0])
        windows = []
        for i, winCoords in enumerate(windows_coords):
            new_window = self.IDF.copyidfobject(base_window)
            windows.insert(i, new_window)
            windows[i].Name = "Window_" + str(i)
            self.writeCoords(np.ravel(winCoords), windows[i])
        return windows

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

    def updateRoomSize(self, width_input, length_input, height_input):
        """
        Updates the coordinates of floor, ceiling, walls and windows in an idf file according
        to new room dimensions. Saves the updated idf file.
        Regarding windows, the first window in the idf is replicated to fill the facade with new windows.
        If the idf file does not contain any window, this step is skipped.
        :param width_input:  new room width
        :param length_input: new room length
        :param height_input: new room height
        """
        # check input validity
        if (width_input < 1) | (length_input < 1):
            raise ValueError("Invalid input room size. Floors must measure at least 1m x 1m.")
        if height_input < 2:
            raise ValueError("Invalid input room height. Rooms can not have a height of less than 2m.")
        if len(self.walls) != 4:
            raise ValueError("Invalid number of walls in idf file. The idf must specify exactly 4 walls.")

        # read coordinates from idf-file
        floor_coords = self.readCoords(self.floor)
        ceiling_coords = self.readCoords(self.ceiling)
        length_vector = self.calcLengthVector(floor_coords)
        width_vector = self.calcWidthVector(floor_coords)
        height_vector = self.calHeightVector(ceiling_coords, floor_coords)

        # calculate new floor and ceiling coordinates
        new_floor_coords = self.calcNewFloorCoords(floor_coords, width_input, length_input, length_vector, width_vector)
        new_ceiling_coords = self.calcNewCeilingCoords(new_floor_coords, height_input)

        # calculate new wall coordinates
        new_wall_coords = []
        for i in range(0, 4):  # wall 0-3
            new_wall_coords.append(self.calcWallCoords(i, new_floor_coords, new_ceiling_coords))

        # update coordinates in the surface objects of the idf file
        #   floor and ceiling
        self.writeCoords(new_floor_coords, self.floor)
        self.writeCoords(new_ceiling_coords, self.ceiling)
        #   walls
        for i, wall in enumerate(self.walls):
            self.writeCoords(new_wall_coords[i], self.walls[i])

        # calculate and write new windows
        if len(self.windows) > 0:
            new_windows = self.generateNewWindows(self.walls, self.floor, self.ceiling, self.windows)
            self.set_windows(new_windows)

        # generate new window shading for all windows (if shadings exist)
        new_shadings = self.generateNewWindowShading(new_windows)
        self.set_windowShading(new_shadings)

        # save
        self.saveIDF()
