# sr3reader/grid.py
"""
connections.py

This module calculates connection transmissibilities.

Classes:
--------
ConnectionsHandler
    A class to handle grid cell connections.

Usage Example:
--------------
conn_handler = ConnectionsHandler(sr3_grid)
transmissibilities = conn_handler.get_transmissibilities()
"""

# - Vectorize NNC face calculation
#   - Check all that are regular connections at once
#   - Check number of points in each face at once.
#   - Calculate face and normals by number of points.
# - Save transmissibilities in a vector.
#   - Initialize with -1.


import numpy as np
from .coordinates import GridCoordHandler


EPSILON = 1 # m
Z_SCALE = 100 # eps_z = eps/z_scale


class ConnectionsHandler:
    """
    A class to handle grid cell connections.

    Parameters
    ----------
    sr3_reader: sr3reader.Sr3Reader
        SR3 reader object.
    auto_read : bool, optional
        If True, reads date information from the SR3 file.
        (default: False)

    Methods
    -------
    read()
        Read all cell connections from the SR3 file.
    get_connections()
        Get all cell connections from the SR3 file.
    get_transmissibilities()
        Get the transmissibilities for all connections.
    set_epsilon(epsilon)
        Set the epsilon value.
    set_z_scale(z_scale)
        Set the z_scale value.
    """

    def __init__(self, sr3_reader, auto_read=False):
        self._connections = None
        self._transmissibilities = None

        self._file = sr3_reader.file
        self._grid = sr3_reader.grid
        self._properties = sr3_reader.properties
        self._data = sr3_reader.data

        if auto_read:
            self.read()

        self.eps = EPSILON
        self.z_scale = Z_SCALE


# MARK: Read Data
    def read(self):
        """Read all cell connections from the SR3 file.

        Returns:
        --------
        connections: np.ndarray
            Array with shape (n_connections, 3) where each row contains the two
            connected cells ("+" face and "-" face) and the connection type
            (1=I, 2=J, 3=K, 4=Mat-Frac). For connections with type 4, the
            cell order is matrix cell and fracture cell.
        """
        con_type = self._file.get_table("SpatialProperties/000000/GRID/ICNTDR")[:]
        cell1 = self._file.get_table("SpatialProperties/000000/GRID/ICTPS1")[:]
        cell2 = self._file.get_table("SpatialProperties/000000/GRID/ICTPS2")[:]

        cell1_ = self._grid.active2complete(cell1)
        cell2_ = self._grid.active2complete(cell2)

        ijk1 = self._grid.n2ijk(cell1_)
        ijk2 = self._grid.n2ijk(cell2_)

        con = np.min(np.stack([con_type, 3*np.ones_like(con_type)], axis=1), axis=1)
        downstream = ijk1[np.arange(ijk1.shape[0]),con-1] <= ijk2[np.arange(ijk2.shape[0]),con-1]

        connections = np.zeros((len(cell1_), 3), dtype=cell1_.dtype)
        connections[downstream] = np.column_stack((
            cell1_[downstream], cell2_[downstream], con_type[downstream]))
        connections[~downstream] = np.column_stack((
            cell2_[~downstream], cell1_[~downstream], con_type[~downstream]))

        self._connections = connections


# MARK: Getters
    def get_connections(self):
        """Get all cell connections from the SR3 file."""
        if self._connections is None:
            self.read()
        return self._connections


    def get_transmissibilities(self, connections=None, add_areas=False, force_recalc=False):
        """
        Calculates the transmissibility for each connection.

        Tran = 1 / (1/Ti + 1/Tj)
        Ti = Ki * NTGi * A.Di / Di.Di
        A.Di = Ax * Dix + Ay * Diy + Az * Diz
        Di.Di = Dix^2 + Diy^2 + Diz^2

        Ki: Permeability of cell i.
        NTGi: Net-to-gross ratio of cell i (does not apply for K connections).
        A: Area of the common face.
        Di: Distance between the center of the cell and the center of the corresponding face.
        Ax, Ay, Az: X-,Y- and Z- projections of the mutual interface area of cell i and cell j
        Dix, Diy,Diz: X-, Y- and Z-components of the distance between the center of cell i.
        and the center of the relevant face of cell i.

        Parameters:
        connections (np.ndarray): Array of shape (n_connections, 3) where each row
            contains the two connected cells ("+" face and "-" face) and the
            connection type (1=I, 2=J, 3=K, 4=Mat-Frac). For connections with
            type 4, the cell order is matrix cell and fracture cell. If None,
            the function will use all connections read from the SR3 file.
        add_areas (bool): If True, the function will calculate the area of the common face
            with a more precise method.
        force_recalc (bool): If True, the function will recalculate the transmissibilities
            even if they were previously calculated.

        Returns:
        np.ndarray: Array of shape (n_connections,) containing the transmissibility
            for each connection."
        """
        if connections is None:
            if self._transmissibilities is None or force_recalc:
                connections = self.get_connections()
                self._transmissibilities = self._get_transmissibilities(
                    connections=connections, add_areas=add_areas)
            return self._transmissibilities

        return self._get_transmissibilities(
            connections=connections, add_areas=add_areas)


# MARK: Setters
    def set_epsilon(self, epsilon):
        """
        Set the epsilon value.

        This values is used as a limit to the distance
        between two cells to consider them as the same.
        The unit is the same unit as the grid the coordinates.
        """
        self.eps = epsilon


    def set_z_scale(self, z_scale):
        """
        Set the z_scale value.

        This values is used to scale the z-coordinate of the
        connections when calculating a distance.
        """
        self.z_scale = z_scale


# MARK: Faces Intersection
    def _get_nnc_face(self, face1, face2):
        """Get the coordinates of the nodes of the non-neighbor connection face."""

        if len(face1.shape) == 3:
            face1 = face1[0]
        if len(face2.shape) == 3:
            face2 = face2[0]

        if np.all(self._get_scaled_norm(face1 - face2, axis=1) < EPSILON):
            return face1

        faces = np.stack((face1, face2), axis=0)

        limits = faces[0][:,2] > faces[1][:,2]

        top_left = faces[1-limits[0]][0]
        bottom_left = faces[0+limits[1]][1]
        bottom_right = faces[0+limits[2]][2]
        top_right = faces[1-limits[3]][3]

        checks = [
            top_left[2] <= bottom_left[2],
            limits[0] != limits[3],
            top_right[2] <= bottom_right[2],
            limits[1] != limits[2],
        ]

        if not np.any(checks):
            raise ValueError("Faces are not connected.")

        face_nodes = []
        if checks[0]:
            face_nodes.append(bottom_left)
            face_nodes.append(top_left)
        else:
            face_nodes.append(self._get_lines_intersection(
                faces[1-limits[0]][[0,3]],
                faces[0+limits[1]][[1,2]]
                ))

        if checks[1]:
            face_nodes.append(self._get_lines_intersection(
                faces[0][[0,3]],
                faces[1][[0,3]]
                ))

        if checks[2]:
            face_nodes.append(top_right)
            face_nodes.append(bottom_right)
        else:
            face_nodes.append(self._get_lines_intersection(
                faces[0+limits[2]][[1,2]],
                faces[1-limits[3]][[0,3]]
                ))

        if checks[3]:
            face_nodes.append(self._get_lines_intersection(
                faces[0][[1,2]],
                faces[1][[1,2]]
                ))

        return np.stack(face_nodes, axis=0)


    def _get_common_face(self, connection):
        cell1, cell2, con_type = connection

        face1_index = 2*con_type - 1
        face2_index = 2*con_type - 2

        face1 = self._grid.coordinates.get(cell1, face1_index)
        face2 = self._grid.coordinates.get(cell2, face2_index)

        return self._get_nnc_face(face1, face2)


    def _get_ad_dd(self, connections, add_areas=False):
        """Calculates the a.d/d.d ratio for each side of the given connections.

        a is the normal of the area common to the two cell faces.
        d is the distance between the center of the cell and the center of the
        corresponding face.

        Parameters:
        connections (np.ndarray): Array of shape (n_connections, 3) where each row
            contains the two connected cells ("+" face and "-" face) and the
            connection type (1=I, 2=J, 3=K, 4=Mat-Frac). For connections with
            type 4, the cell order is matrix cell and fracture cell.
        add_areas (bool): If True, the function will rescale the mean normal vector
            by the sum of the areas of the triangles.

        Returns:
        np.ndarray: Array of shape (n_connections, 2) containing the a.d/d.d ratio
            for each side of the connections.
        """
        cell_centers = np.stack([
            self._grid.coordinates.get_center(connections[:,0]),
            self._grid.coordinates.get_center(connections[:,1])
            ], axis=1)
        con_type = np.stack([
            2*connections[:,2]-1,
            2*connections[:,2]-2
            ], axis=1)

        con_array = connections[:,[0,1]].flatten()
        con_type_array = con_type.flatten()

        faces = np.zeros([cell_centers.shape[0], 2, 4, 3])
        faces_array = faces.reshape((-1,4,3))
        for i in range(6):
            filter_ = con_type_array == i
            if np.any(filter_):
                faces_array[filter_] = self._grid.coordinates.get(con_array[filter_], i)

        face_centers = np.zeros_like(cell_centers)
        face_centers_array = face_centers.reshape((-1, 3))
        face_centers_array[:] = np.mean(faces_array, axis=1)

        normals = np.array([
            ConnectionsHandler._get_plane_properties(
                points=self._get_nnc_face(f[0],f[1]),
                add_areas=add_areas) for f in faces
            ])

        di = face_centers - cell_centers
        di = np.abs(di)

        normals = np.abs(normals)
        normals = np.stack([normals]*2, axis=1)
        ad = np.sum(di * normals, axis=2)
        dd = np.sum(di * di, axis=2)

        return ad/dd


    def _get_transmissibilities(self, connections, add_areas=False):
        """Calculates the transmissibility for each connection.

        Tran = 1 / (1/Ti + 1/Tj)
        Ti = Ki * NTGi * A.Di / Di.Di
        A.Di = Ax * Dix + Ay * Diy + Az * Diz
        Di.Di = Dix^2 + Diy^2 + Diz^2

        Ki: Permeability of cell i.
        NTGi: Net-to-gross ratio of cell i (does not apply for K connections).
        A: Area of the common face.
        Di: Distance between the center of the cell and the center of the corresponding face.
        Ax, Ay, Az: X-,Y- and Z- projections of the mutual interface area of cell i and cell j
        Dix, Diy,Diz: X-, Y- and Z-components of the distance between the center of cell i.
        and the center of the relevant face of cell i.

        Parameters:
        connections (np.ndarray): Array of shape (n_connections, 3) where each row
            contains the two connected cells ("+" face and "-" face) and the
            connection type (1=I, 2=J, 3=K, 4=Mat-Frac). For connections with
            type 4, the cell order is matrix cell and fracture cell.
        add_areas (bool): If True, the function will calculate the area of the common face
        with a more precise method.

        Returns:
        np.ndarray: Array of shape (n_connections,) containing the transmissibility
            for each connection."
        """
        ad_dd = self._get_ad_dd(connections, add_areas=add_areas)

        props = ["PERMI","PERMJ","PERMK"]
        prop_list = self._properties.get(element_type='grid').keys()

        if 'NET/GROSS' in prop_list:
            grid_data = self._data.get(
                "grid", props+['NET/GROSS'], "MATRIX", days=0., active_only=False)
            ntg_vec = grid_data['NET/GROSS']
        else:
            grid_data = self._data.get("grid", props, "MATRIX", days=0., active_only=False)
            ntg_vec = np.ones_like(grid_data['PERMI'])

        perms = np.stack([
            grid_data['PERMI'],
            grid_data['PERMJ'],
            grid_data['PERMK']], axis=0).reshape((3,-1))
        ntgs = np.stack([
            ntg_vec,
            ntg_vec,
            np.ones_like(ntg_vec)], axis=0).reshape((3,-1))

        cells = connections[:,[0,1]].flatten()-1
        cons = np.stack([connections[:,2],connections[:,2]], axis=1).flatten()-1
        perm = np.ones_like(cells, dtype=np.float64)
        ntg = np.ones_like(cells, dtype=np.float64)

        for i in range(3):
            perm[cons==i] = perms[i,cells[cons==i]]
            ntg[cons==i] = ntgs[i,cells[cons==i]]

        t = (perm * ntg * ad_dd.flatten()).reshape((-1,2))
        tran = 1/np.sum(1/t, axis=1)

        return tran


# MARK: Utilities
    def _get_scaled_norm(self, vector, axis=1):
        """
        Calculate the norm of a vector with the z-direction coordinates scaled by a factor.

        Parameters:
            vector (numpy.ndarray): An array of shape ([n], 3) representing 3D coordinates.
            z_scale (float): The scaling factor for the z-direction coordinates.
            axis (int): The axis along which to compute the norm.

        Returns:
            numpy.ndarray: An array of ([n]) norms.
        """
        vector_array = vector.reshape((-1, 3))
        vector_array[:, 2] *= self.z_scale

        return np.linalg.norm(vector, axis=axis)


    def _get_lines_intersection(self, line1, line2):
        """
        Find the closest point between two lines in 3D.

        Parameters:
        line1, line2: Lines defined by two points. (numpy arrays of shape (2, 3))

        Returns:
        closest_point: The closest point to both lines (numpy array of shape (3,))
        """
        p1 = line1[0]
        d1 = line1[1] - line1[0]
        d1 = d1 / np.linalg.norm(d1)

        p2 = line2[0]
        d2 = line2[1] - line2[0]
        d2 = d2 / np.linalg.norm(d2)

        cross_d1_d2 = np.cross(d1, d2)
        cross_d1_d2_norm = np.linalg.norm(cross_d1_d2)
        if cross_d1_d2_norm < 1E-6:
            raise ValueError("The lines are parallel and do not intersect.")

        p2_p1 = p2 - p1

        t1 = np.linalg.det([p2_p1, d2, cross_d1_d2]) / cross_d1_d2_norm**2
        t2 = np.linalg.det([p2_p1, d1, cross_d1_d2]) / cross_d1_d2_norm**2

        closest_line1 = p1 + t1 * d1
        closest_line2 = p2 + t2 * d2

        distance = self._get_scaled_norm(closest_line1 - closest_line2, axis=0)
        if distance > self.eps:
            raise ValueError("The lines are skew and do not intersect.")

        closest_point = (closest_line1 + closest_line2) / 2
        return closest_point


    @staticmethod
    def _get_plane_properties(points, add_areas=False, include_center=False):
        """
        Calculate the normal vector of the plane defined by the given 3D points.

        Parameters:
        points (np.array): A numpy array of shape (n, 3) containing the 3D coordinates
        of the points.
        add_areas (bool): If True, the function will rescale the mean normal vector by
        the sum of the areas of the triangles.
        include_center (bool): If True, the function will return the center of the points.

        Returns:
        np.array: The normal vector of the plane (3,) or the center and normal vector stacked (2,3).
        """
        center = np.mean(points, axis=0)

        normal_vectors = []
        closed_coordinates = np.vstack([points, points[0]])
        for pa, pb in zip(closed_coordinates[:-1], closed_coordinates[1:]):
            normal = np.cross(pa-center, pb-center) / 2
            normal_vectors.append(normal)

        normal_vector = np.sum(normal_vectors, axis=0)
        if add_areas:
            total_area = np.sum(np.linalg.norm(normal_vectors, axis=1))
            normal_vector = normal_vector / np.linalg.norm(normal_vector) * total_area

        if include_center:
            return np.stack((center, normal_vector), axis=0)
        return normal_vector


    @staticmethod
    def _join_array(str_array, sep=' '):
        """Join a 2D array of strings with a separator."""
        if str_array.dtype != np.dtype('<U65'):
            str_array = str_array.astype(str)
        seps = [sep]*str_array.shape[0]
        a = str_array[:,0]
        for i in range(1, str_array.shape[1]):
            a = np.char.add(a, seps)
            a = np.char.add(a, str_array[:,i])
        return a


    def print_sconnect(self, connections, transmissibilities=None):
        """Prints the connection information in the SCONNECT format."""
        cell1 = self._grid.n2ijk(connections[:,0])
        cell2 = self._grid.n2ijk(connections[:,1])
        cell1_str = ConnectionsHandler._join_array(cell1)
        cell2_str = ConnectionsHandler._join_array(cell2)
        if transmissibilities is None:
            transmissibilities = self.get_transmissibilities(connections)
        s = []
        for c1, c2, t in zip(cell1_str, cell2_str, transmissibilities):
            s.append(f' {c1}   {c2}   {t}')
        return s


# MARK: Plotting
    def plot_connection(self, connection):
        """Plot the connection between two cells."""
        face1 = self._grid.coordinates.get(connection[0], 2*connection[-1]-1)
        face2 = self._grid.coordinates.get(connection[1], 2*connection[-1]-2)
        common = self._get_common_face(connection)
        return GridCoordHandler.plot_planes(
            faces=[face1, face2, common],
            labels=[
                self._grid.n2ijk(connection[0]),
                self._grid.n2ijk(connection[1]),
                "Common"])
