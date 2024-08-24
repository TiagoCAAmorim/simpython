# simpython
Python code and helpers for my PHD research

## rsimpy
Reservoir simulation files handling.

* **cmg**: collection of modules to read/write _CMG-style_ simulation files.
    * **sr3reader.Sr3Reader**: class that reads SR3 results files.
    * **gridfile.GridFile**: class that reads/writes ascii grid files with the *ALL* format.
* **common**: other modules
    * **template.TemplateProcessor**: class that generates text files based on a template.

### Examples

#### Sr3Reader

```python
from rsimpy.cmg.sr3reader import Sr3Reader

sr3_file_path = "./model.sr3"
sr3 = Sr3Reader(sr3_file_path)

well_ names = sr3.elements.get("well").keys()
group_names = sr3.elements.get("group").keys()
is_2phi2k = "FRACTURE" in sr3.elements.get("grid").keys()

well_timeseries_names = sr3.properties.get("well").keys()
grid_properties_names = sr3.properties.get("grid").keys()

qo_unit_str = sr3.properties.unit("OILRATSC")

group_parent = sr3.elements.get_parent("group","PLAT1-PRO")
p13_group = sr3.elements.get_parent("well","P13")
producers = sr3.elements.get_children("well","PLAT1-PRO")

ni, nj, nk = sr3.grid.get_size("nijk")

well_data = sr3.data.get("well", ["BHP","QO"], ["P11","P13"])
p11_bhp = well_data["BHP"].sel(element="P11").values

elapsed_data = sr3.data.get("special", "ELAPSED", days=[30., 1085., 2162.])
elapsed_values = elapsed_data["ELAPSED"].sel(element="").values

grid_data = sr3.data.get("grid", ["SO","PRES","VISO","Z(CO2)"], "MATRIX", days=10.)
```

#### GridFile

```python
from rsimpy.cmg.gridfile import GridFile

inc_file_path = Path('./grid/POR.inc')
g_file = GridFile(inc_file_path)

n_values = g_file.get_number_values()
keyword_str = g_file.get_keyword().strip()
comments = g_file.get_comments().split('\n')

ni, nj, nk = 12, 23, 33
g_file.set_shape([ni,nj,nk])
sub_grid = ((1,12),(1,12),(29,33))
new_file_path = './grid/POR_sub.inc'
g_file.write(file_path=new_file_path, coord_range=sub_grid)
```