# sr3reader/grid.py
"""
coordinates.py

This module handles grid coordinates.

Classes:
--------
GridCoordHandler
    A class to handle grid coordinates.

Usage Example:
--------------
coord_handler = GridCoordHandler(sr3_file, sr3_grid)
face_coordinates = coord_handler.get([12,34], face='I-')
"""

from matplotlib import pyplot as plt
import numpy as np


# Nodes of the cell faces
NODE_NUM = {
    None: [0, 1, 2, 3, 4, 5, 6, 7],

    'I-': [3, 7, 4, 0],
    'I+': [2, 6, 5, 1],
    'J-': [0, 4, 5, 1],
    'J+': [3, 7, 6, 2],
    'K-': [0, 1, 2, 3],
    'K+': [4, 5, 6, 7],

    0:    [3, 7, 4, 0],  # I-
    1:    [2, 6, 5, 1],  # I+
    2:    [0, 4, 5, 1],  # J-
    3:    [3, 7, 6, 2],  # J+
    4:    [0, 1, 2, 3],  # K-
    5:    [4, 5, 6, 7],  # K+
    }


class GridCoordHandler:
    """
    A class to handle grid coordinates.

    Parameters
    ----------
    sr3_file : sr3reader.Sr3Handler
        SR3 file object.
    sr3_grid : sr3reader.GridHandler
        Grid object.
    auto_read : bool, optional
        If True, reads coordinates data from sr3 file. Default is False.

    Methods
    -------
    read()
        Reads coordinates data from sr3 file.
    get()
        Get coordinates of nodes of a cell or cells.
    get_center()
        Get coordinates of the center of a cell or cell face.
    """

    def __init__(self, sr3_file, sr3_grid, auto_read=False):
        self._file = sr3_file
        self._grid = sr3_grid

        self._blocks = None
        self._nodes = None

        if auto_read:
            self.read()

# MARK: Read Data
    def read(self):
        """
        Reads coordinates data from sr3 file.

        Data is stored in the BLOCKS and NODES tables. BLOCKS holds the indexes of the nodes
        that form each cell block. NODES holds the coordinates of the nodes.

        if BLOCKS is not found in the sr3 file, assumes a regular grid, with contiguous nodes
        between the cells (no non-neighbor connections). In this case, the spatial coordinates
        are read in the X, Y, and ZCORNCRCN tables.

        blocks : np.array (ni*nj*nk, 8)
            Indexes of the nodes that form each cell block.
        nodes : np.array (#nodes, 3)
            Coordinates of the nodes.
        """
        blocks, nodes = self._get_blocks_nodes()
        self._blocks = blocks
        self._nodes = nodes


    def _get_blocks_nodes(self):
        """
        Returns blocks and nodes from sr3 file.

        """
        if self._file.get_table("SpatialProperties/000000/GRID/BLOCKS") is not None:
            blocks = self._file.get_table("SpatialProperties/000000/GRID/BLOCKS")[:].reshape(-1, 8)
            nodes = self._file.get_table("SpatialProperties/000000/GRID/NODES")[:].reshape(-1, 3)
            return blocks, nodes

        def _build_blocks(grid):
            """Builds Blocks table for a regular grid."""
            ni = grid.get_size('ni')
            nj = grid.get_size('nj')
            nk = grid.get_size('nk')

            blocks = np.zeros((ni*nj*nk, 8), dtype=np.int32)

            ijk = grid.n2ijk(np.arange(1, ni*nj*nk+1))

            blocks[:, 0] = ijk[:,0] + (ijk[:,1]-1)*(ni+1) + (ijk[:,2]-1)*(ni+1)*(nj+1)
            blocks[:, 4] = blocks[:, 0] + (ni+1)*(nj+1)
            blocks[:, [3,7]] = blocks[:, [0,4]] + ni + 1
            blocks[:, [1,2,5,6]] = blocks[:, [0,3,4,7]] + 1

            if grid.get_size('n_cells') > ni*nj*nk:
                blocks = np.concatenate([blocks, blocks])
            return blocks

        def _build_nodes(grid, sr3_file):
            """Builds Nodes table for a regular grid."""
            ni = grid.get_size('ni')
            nj = grid.get_size('nj')
            nk = grid.get_size('nk')

            nodes = np.zeros(((ni+1)*(nj+1)*(nk+1),3), dtype=np.float64)

            x_coord = sr3_file.get_table("SpatialProperties/000000/GRID/XCORNCRCN")[:]
            y_coord = sr3_file.get_table("SpatialProperties/000000/GRID/YCORNCRCN")[:]
            z_coord = sr3_file.get_table("SpatialProperties/000000/GRID/ZCORNCRCN")[:]

            nodes[:,0] = x_coord
            nodes[:,1] = y_coord
            nodes[:,2] = z_coord

            return nodes

        blocks = _build_blocks(self._grid)
        nodes = _build_nodes(self._grid, self._file)

        return blocks, nodes


# MARK: Getters

    def get(self, cells, face=None):
        """Get coordinates of nodes of a cell or cells.

        The cell numbering is as follows:
                    K-
                0--------1            x--> I
               /|       /|           /|
              / |      / |          / |
             /  |  J- /  |         v  v
            3--------2   |        J   K
            |   |    |   |
        I-  |   4----|---5  I+
            |  / J+  |  /
            | /      | /
            |/       |/
            7--------6
               K+

        Nodes are ordered in the faces so that the normal vector points
        in the same direction as the coordinate system.

        Parameters
        ----------
        cell : int, list of int or np.ndarray
            Cell number(s) (complete index).
        face : int, str or None
            Face of the cell. If None, all nodes of the cell are returned.
            Valid values are "I-", "I+", "J-", "J+", "K-", "K+", or
            0, 1, 2, 3, 4, 5 for I-, I+, J-, J+, K-, K+, respectively.

        Returns
        -------
        np.ndarray
            Coordinates of nodes of the cell(s).
        """
        if self._blocks is None:
            self.read()

        if face not in NODE_NUM:
            raise ValueError(f"Invalid face: {face}.")
        edge_n = NODE_NUM[face]

        if isinstance(cells, (int, np.integer)):
            cells = np.array([cells])
        elif isinstance(cells, list):
            cells = np.array(cells)

        return self._nodes[self._blocks[cells-1][:,edge_n]-1]


    def get_center(self, cells, face=None):
        """Get coordinates of the center of a cell or cell face."""
        return np.mean(self.get(cells, face), axis=1)


# MARK: Plotting
    @staticmethod
    def plot_planes(faces, labels=None, marker='o', verbose=False):
        """Plot a panel with the faces projected to the XYZ planes."""
        fig, axes = plt.subplots(2, 2, figsize=(10, 10))
        axes = axes.flatten()

        def plot_face(ax, coordinates, x_axis=0, y_axis=1,
                    x_axis_label='X', y_axis_label='Y', label=None,
                    invert_yaxis=False):
            closed_coordinates = np.vstack([coordinates, coordinates[0]])
            ax.plot(closed_coordinates[:, x_axis], closed_coordinates[:, y_axis],
                    marker=marker, label=label)
            ax.set_xlabel(x_axis_label)
            ax.set_ylabel(y_axis_label)
            if invert_yaxis:
                ax.invert_yaxis()
            ax.grid(True)
            if labels is not None:
                ax.legend()

        x_axis = [0, 0, 1]
        y_axis = [1, 2, 2]
        x_label = ['X', 'X', 'Y']
        y_label = ['Y', 'Z', 'Z']

        for x, y, x_label, y_label, ax in zip(x_axis, y_axis, x_label, y_label, axes[:3]):
            for i,face in enumerate(faces):
                if labels is not None:
                    label = str(labels[i])
                else:
                    label = f'{i}'
                if len(face.shape) == 3:
                    face = face[0]
                plot_face(ax, face, x, y, x_label, y_label, label, invert_yaxis=(y_label=='Z'))

        for spine in axes[-1].spines.values():
            spine.set_visible(False)
        axes[-1].grid(False)
        axes[-1].set_xticks([])
        axes[-1].set_yticks([])

        def plot_3d(ax, coordinates):
            if len(coordinates.shape) == 3:
                coordinates = coordinates[0]
            x = coordinates[:, 0]
            y = coordinates[:, 1]
            z = coordinates[:, 2]

            # x and y arrays must consist of at least 3 unique points
            # if len(np.unique(coordinates[:,[0,1]], axis=0)) > 2:
            try:
                ax.plot_trisurf(x, y, z, alpha=0.3)
            except Exception as e: # pylint: disable=broad-except
                if verbose:
                    print(e)

            if marker != '':
                ax.scatter(x, y, z, marker='o')

            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')

            ax.set_box_aspect([1.0, 1.0, 0.7])
            ax.invert_zaxis()

        ax_3d = fig.add_subplot(2, 2, 4, projection='3d')
        for face in faces:
            plot_3d(ax_3d, face)

        plt.tight_layout()
        return axes
