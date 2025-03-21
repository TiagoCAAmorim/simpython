# SR3 file strucuture

## Grid

### Properties in _/SpatialProperties/000000/GRID_

|Property |#Values | Information |Description | Comments |
|-|-|-|-|-|
|**Attributes** | | | | |
|NBLOCK | 1 | $8n_in_jn_k$ | Number of cell edges | Together with **NNODES**|
|NNODES | 1 | $3n_{nodes}$ | Number of cell nodes | Unique edges, together with **NBLOCK** |
|NCRCN | 1 | $(n_i+1)(n_j+1)(n_k+1)$ | Number of nodes | Instead of **NBLOCK** and **NNODES** |
|NPTCN | 1 | $n_{con}$ | Number of connections | |
|NPTCS | 1 | $n_{cells}$ | Number of cells | matrix + fracture (if present) |
|NPTPS | 1 | $n_{act}$ | Number of active cells | matrix + fracture (if present) |
|NPTSS | 1 | $n_in_jn_k$ | Number of matrix cells | |
|NSCGSZ | 1 | $n_{sect}$ | Sector geometry array size | |
|**Grid Sizes** | | | | |
|IGNTID | $1$ | $n_i$ | Grid number to NI | |
|IGNTJD | $1$ | $n_j$ | Grid number to NJ | |
|IGNTKD | $1$ | $n_k$ | Grid number to NK | |
|IGNTNC | $2$ | [0, $n_{cells}$] | Grid number to last block CS index | If $n_{cells} > n_in_jn_k \rightarrow$ has fractures |
|**Cell Index** | | | | |
|IPSTCS | $n_{act}$ | Cell number of the active cells | Packed storage to complete storage | Index to transform complete to active only grid properties |
|ICSTPS | $n_{cells}$ | Active cell number of all cells | Complete storage to packed storage | Index to transform active only to complete grid properties |
|**Cell Position** | | | | |
|BLOCKS | $8n_in_jn_k$ | Nodes indexes | Grid Block connectivity of Node Based Corner Point Grid | Together with **NODES** |
|NODES | $3n_{nodes}$ | (x,y,z) node coordinates | Grid Nodes' Coordinates | Together with **BLOCKS** |
|XCORNCRCN | $n_i+1$ | Nodes x-coordinate | Grid Node X Coordinates | Instead of **BLOCKS** and **NODES** |
|YCORNCRCN | $n_i+1$ | Nodes y-coordinate | Grid Node Y Coordinates | Instead of **BLOCKS** and **NODES**  |
|ZCORNCRCN | $n_i+1$ | Nodes z-coordinate | Grid Node Z Coordinates | Instead of **BLOCKS** and **NODES**  |
|BLOCKDEPTH | $n_in_jn_k$ | Cell depth | Grid block depths | |
|**Cell Volumes** | | | | |
|BLOCKSIZE | $3n_in_jn_k$ | $\Delta I$,$\Delta J$,$\Delta K$ lengths | Grid block sizes in three directions | Replaces coordinates in very simple grids |
|BVOL | $n_{act}$ | Bulk volume | Block Volume | Replace by $\Delta I\Delta J\Delta K$ if not present |
|BLOCKPVOL | $n_{act}$ | _Initial_ porous volume | Block pore volume | Equals **BVOL**.**POR**.(1 - **POR**$_{frat}$) in matrix cells |
|**Connections** | | | | |
|ICNTDR | $n_{con}$ | Direction code | Connection direction | 1: I+, 2: J+, 3: K+, 4: Mat-Frat, 6:?? |
|ICTPS1 | $n_{con}$ | first active cell index | Connection to lower packed storage | Cell with lower index in connection |
|ICTPS2 | $n_{con}$ | second active cell index | Connection to upper packed storage | Cell with larger index in connection |
|**Cell Type** | | | | |
|ICSTBC | $n_{cells}$ | Cell condition | Complete storage to block type | 0: active, -1: inative neighbouring, -2: inactive |
|IPSTBT | $n_{act}$ | Cell type | Packed storage to block type | 1: Fracture, 2: Matrix with fracture, 9: Matrix only |
|**Sector Array** | | | | |
|ISECTGEOM | $n_{sect}$ | Sector index | Sector geometry array | **?????** |

**TO-DO**

* Understand ISECTGEOM.
* Check ICNTDR options.
* Check ICSTBC options.
* Check IPSTBT options.
