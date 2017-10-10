# -*- coding: utf-8 -*-

"""\
Nalu Exodus NetCDF Interface
----------------------------
"""

import netCDF4 as nc
import numpy as np

def nc_convert_names(names_arr):
    """Utility function to convert byte chars to strings.

    Args:
        names_arr (np.ndarry): Numpy string array from NetCDF

    Returns:
        list: A list of strings corresponding to the names
    """
    return [nc.chartostring(x).item().decode() for x in names_arr]

side_set_node_map = dict(
    HEX = {
        1 : [0, 1, 5, 4],
        2 : [1, 2, 6, 5],
        3 : [2, 3, 7, 6],
        4 : [0, 4, 7, 3],
        5 : [0, 3, 2, 1],
        6 : [4, 5, 6, 7]
    },
    TETRA = {
        1 : [0, 1, 3],
        2 : [1, 2, 3],
        3 : [0, 2, 3],
        4 : [0, 1, 2],
    },
    WEDGE = {
        1 : [0, 1, 3, 4],
        2 : [1, 2, 4, 5],
        3 : [0, 2, 3, 5],
        4 : [0, 1, 2],
        5 : [3, 4, 5],
    },
    QUAD4 = {
        1 : [0, 1],
        2 : [1, 2],
        3 : [2, 3],
        4 : [3, 0],
    }
)

class ExodusCDF(object):
    """Nalu Exodus NetCDF Interface

    Interact with a Nalu Exodus-II mesh or results file using the netcdf4
    library.

    Attributes:
        num_blocks (int): Number of blocks present in the file
        num_side_sets (int): Number of side sets present in the file
        blocks (list): Names of the mesh blocks present in the file
        side_sets (list): Names of the side sets present in the file

        elem_conn_map (dict): A mapping from block names to element ID used to
           extract connectivity data

    """

    def __init__(self, filename):
        """
        Args:
            filename (path): Path to the exodus file
        """
        #: string: Filename that is being processed
        self.filename = filename

        #: Dataset: NetCDF msh database object
        self.msh = nc.Dataset(filename, 'r')

        #: int: Dimensionality of the mesh
        self.ndim = self.msh.dimensions["num_dim"].size

        #: int: Total number of elements in the mesh
        self.nelems = self.msh.dimensions["num_elem"].size

        #: int: Total number of nodes in the mesh
        self.nnodes = self.msh.dimensions["num_nodes"].size

        self._process_eb_names()
        self._process_ss_names()

    def _process_eb_names(self):
        """Process element block names"""
        mvars = self.msh.variables
        mdims = self.msh.dimensions
        if "eb_names" in mvars:
            self.blocks = [x.lower()
                           for x in nc_convert_names(
                                   mvars["eb_names"][:])]
        elif 'num_el_blk' in mdims:
            nblk = mdims['num_el_blk'].size
            self.blocks = ["block-%d"%(d+1) for d in range(nblk)]
        else:
            self.blocks = []

        self.elem_conn_map = dict(
            (eb, (i+1)) for i, eb in enumerate(self.blocks))

        num_blks = len(self.blocks)
        self.numel_blk = np.array(
            [self.msh.dimensions["num_el_in_blk%d"%(i+1)].size
             for i in range(num_blks)])
        self.el_start_idx = np.zeros(num_blks)
        for i in range(1, num_blks):
            self.el_start_idx[i] = (
                self.numel_blk[i-1] + self.el_start_idx[i-1])

        self.num_blocks = num_blks

    def _process_ss_names(self):
        """Process element block names"""
        mvars = self.msh.variables
        mdims = self.msh.dimensions
        tmp = mdims.get("num_side_sets", None)
        nssets = tmp.size if tmp else 0
        if nssets > 0:
            ssnames = [x.lower()
                       for x in
                       nc_convert_names(mvars["ss_names"][:])]
            if not ssnames[0]:
                self.side_sets = ["surface-%d"%(d+1)
                                  for d in range(nssets)]
            else:
                self.side_sets = ssnames
        else:
            self.side_sets = []

        self.sset_map = dict(
            (eb, i+1) for i, eb in enumerate(self.side_sets))
        self.num_side_sets = mdims["num_side_sets"].size

    def xco(self, mask=None):
        """Return the x coordinates of the mesh"""
        mvars = self.msh.variables
        if not "coordx" in mvars:
            raise KeyError(
                "No x coordinate field found in mesh: %s"%
                self.filename)
        if not hasattr(self, "_xco"):
            self._xco = self.msh.variables["coordx"][:]
        if mask is None:
            return self._xco
        return self._xco[mask]

    def yco(self, mask=None):
        """Return the y coordinates of the mesh"""
        mvars = self.msh.variables
        if not "coordy" in mvars:
            raise KeyError(
                "No y coordinate field found in mesh: %s"%
                self.filename)
        if not hasattr(self, "_yco"):
            self._yco = self.msh.variables["coordy"][:]
        if mask is None:
            return self._yco
        return self._yco[mask]

    def zco(self, mask=None):
        """Return the z coordinates of the mesh"""
        mvars = self.msh.variables
        if not "coordz" in mvars:
            raise KeyError(
                "No z coordinate field found in mesh: %s"%
                self.filename)
        if not hasattr(self, "_zco"):
            self._zco = self.msh.variables["coordz"][:]
        if mask is None:
            return self._zco
        return self._zco[mask]

    def coords(self, mask=None):
        """Return the numpy array of the mesh coordinates"""
        ndim = self.msh.dimensions["num_dim"].size
        xco = self.xco(mask)
        yco = self.yco(mask)
        if ndim == 3:
            zco = self.zco(mask)
            return np.column_stack((xco, yco, zco))
        else:
            return np.column_stack((xco, yco))

    def elem_nodes(self, blk_name, flatten=True):
        """Element Node ID mapping for a given block

        If ``flatten`` is True, then the method returns a one dimensional numpy
        array containing the unique set of node IDs corresponding to this mesh
        block. If False, then it returns a 2-D list where the inner array
        contains the list of nodes for each element. The shape of the 2-D array
        is (num_elems, num_nodes_per_elem).

        Args:
            blk_name (str): Block name
            flatten (bool): Unique IDs or element connetivity map.

        Returns:
            np.ndarray: A 1-D or 2-D array depending on flatten flag.
        """
        bname = blk_name.lower()
        if not bname in self.blocks:
            raise KeyError("No block name found in mesh: %s"%blk_name)
        conn_name = "connect%d"%self.elem_conn_map[bname]
        elem_ids = self.msh.variables[conn_name][:]-1
        return (np.unique(elem_ids.flatten())
                if flatten else elem_ids)

    def ss_nodes(self, ss_name, flatten=True):
        """Node IDs for a given side set

        If ``flatten`` is True, then the method returns a one dimensional numpy
        array containing the unique set of node IDs corresponding to this mesh
        side set. If False, then it returns a 2-D list where the inner array
        contains the list of nodes for each element. The shape of the 2-D array
        is (num_elems, num_nodes_per_elem).

        Args:
            blk_name (str): Block name
            flatten (bool): Unique IDs or element connectivity map.

        Returns:
            np.ndarray: A 1-D or 2-D array depending on flatten flag.
        """
        mvars = self.msh.variables
        sname = ss_name.lower()
        if not sname in self.side_sets:
            raise KeyError("No side set name found in mesh: %s"%ss_name)

        ssid = self.sset_map[sname]
        sselemvar = "elem_ss%d"%ssid
        sssidevar = "side_ss%d"%ssid

        side_ids = mvars[sssidevar][:]
        assert np.max(side_ids) == np.min(side_ids), (
            "Varying side IDs not supported yet.")
        elem_ids = mvars[sselemvar][:]

        min_eid = np.min(elem_ids)
        blk_id = np.searchsorted(self.el_start_idx, min_eid)
        conn_ids = mvars["connect%d"%blk_id]
        topo = conn_ids.elem_type
        side_nids = side_set_node_map[topo][side_ids[0]]
        offset = 1 if blk_id == 1 else self.numel_blk[blk_id - 1]
        ss_nodes = conn_ids[:][np.ix_(elem_ids-offset, side_nids)] - 1

        return (np.unique(ss_nodes.flatten())
                if flatten else ss_nodes)
