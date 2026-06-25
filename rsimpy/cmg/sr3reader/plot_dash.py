"""Dash wrapper for SR3-backed dashboard components."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from dash import Dash

from rsimpy.common.plot_dash import DashLinePlot, DashMapPlot, DashScatterPlot, DashTable
from rsimpy.common.plot_dashboard import DashMultiPanelDashboard


@dataclass
class DashPanel:
    """Thin wrapper around a Dash app returned by `PlotHandlerDash.dashboard`."""

    app: Dash

    def run(self, host="127.0.0.1", port=8050, debug=False, **kwargs):
        """Start serving the dashboard app."""
        print(f"Dash dashboard available at http://{host}:{port}")
        self.app.run(host=host, port=port, debug=bool(debug), **kwargs)


class PlotHandlerDash:
    """Build Dash map/line/scatter/table components from SR3 data."""

    def __init__(self, sr3_reader):
        self._sr3 = sr3_reader

    @staticmethod
    def _as_list(values):
        if values is None:
            return None
        if isinstance(values, (str, bytes)):
            return [values]
        if hasattr(values, "__iter__"):
            return list(values)
        return [values]

    def _normalize_days(self, days, element_type):
        days_list = self._as_list(days)
        if days_list is None:
            return list(self._sr3.dates.get_days(element_type))
        return [float(d) for d in days_list]

    @staticmethod
    def _normalize_map_selector(selector):
        if isinstance(selector, str):
            return "MATRIX", selector.upper()
        if isinstance(selector, tuple) and len(selector) == 2:
            element, prop = selector
            if str(element).strip().lower() in ("matrix", "fracture"):
                return str(element).strip().upper(), str(prop).strip().upper()
        raise ValueError(
            "Map property selector must be 'PROP' or ('matrix'|'fracture', 'PROP')."
        )

    def _read_grid_property(self, element, property_name, days, active_only):
        sim_data = self._sr3.data.get(
            element_type="grid",
            properties=[property_name],
            elements=[element],
            days=days,
            active_only=active_only,
        )
        return sim_data[property_name].values

    def _build_map_connections(self, selected_complete, days, connection_values=None):
        all_connections = self._sr3.connections.get_connections(as_active=False)

        keep_mask = np.isin(all_connections[:, :2], selected_complete).all(axis=1)
        if not keep_mask.any():
            return None, None
        filtered = all_connections[keep_mask]

        connection_indices = np.searchsorted(selected_complete, filtered[:, :2]).T.astype(int)
        n_conn = connection_indices.shape[1]
        n_days = len(days)
        if connection_values is None:
            vals = self._sr3.connections.get_transmissibilities(filtered)
            vals = vals.reshape(-1, 1)
            vals = np.repeat(vals, n_days, axis=1)
        else:
            vals = np.asarray(connection_values, dtype=float)
            if vals.ndim != 2:
                raise ValueError(
                    "connection_values must have shape (n_connections, n_days) or "
                    "(n_days, n_connections)."
                )
            if vals.shape == (n_conn, n_days):
                pass
            elif vals.shape == (n_days, n_conn):
                vals = vals.T
            else:
                raise ValueError(
                    "connection_values size mismatch. Expected "
                    f"({n_conn}, {n_days}) or ({n_days}, {n_conn}), got {vals.shape}."
                )

        connection_data = vals.T.reshape(1, n_days, n_conn)
        return connection_indices, connection_data

    def _build_map_wells(self, selected_complete):
        all_wells = self._sr3.elements.get("well")
        last_day = self._sr3.dates.get_days("well")[-1:]
        well_data = self._sr3.data.get(
            element_type="well",
            properties=["NP", "GP", "WP"],
            elements=all_wells.keys(),
            days=last_day,
        )

        well_types = {}
        for w in all_wells:
            oil = float(well_data["NP"].sel(element=w).values[-1])
            gas = float(well_data["GP"].sel(element=w).values[-1])
            water = float(well_data["WP"].sel(element=w).values[-1])
            if oil > 1.0:
                well_type = "prod"
            elif gas > 1.0 and water > 1.0:
                well_type = "inj"
            elif gas > 1.0:
                well_type = "injg"
            elif water > 1.0:
                well_type = "injw"
            else:
                well_type = "closed"
            well_types[w] = well_type

        cells = self._sr3.elements.get_layer_data("cell")
        wells = {}
        for well in all_wells:
            well_con = self._sr3.elements.get_children("layer",well)
            well_con = np.array([cells[wc] for wc in well_con if cells[wc] in selected_complete])
            if len(well_con) == 0:
                continue
            well_con = np.searchsorted(selected_complete, well_con).astype(int)
            well_name = f"{well},{well_types[well]}"
            wells[well_name] = well_con

        return wells

    def make_map(
        self,
        properties,
        days=None,
        title="Map",
        grid_values=None,
        connection_values=None,
        add_connections=False,
        add_wells=True,
        width=1000,
        height=700,
    ):
        """Build a `DashMapPlot` from SR3 grid properties or direct arrays.

        Parameters
        ----------
        properties : list[str | tuple]
            Grid property selectors. Each item is `"PROP"` (assumes matrix) or
            `(element, "PROP")` where element is `"matrix"` or `"fracture"`.
        days : list[float] | None
            Days to read. If None, all grid days are used.
        grid_values : np.ndarray | None
            Optional override values with shape `(n_properties, n_days, n_cells)`.
        connection_values : np.ndarray | None
            Optional override with shape `(n_connections, n_days)` or
            `(n_days, n_connections)`.
        """
        selectors = self._as_list(properties)
        if selectors is None or len(selectors) == 0:
            raise ValueError("At least one map property must be provided.")

        normalized = [self._normalize_map_selector(item) for item in selectors]
        elements = {e for e, _ in normalized}
        if len(elements) != 1:
            raise ValueError("All map properties in a single map must use the same element.")
        element = list(elements)[0]

        prop_names = [p for _, p in normalized]
        days = self._normalize_days(days, element_type="grid")
        n_days = len(days)

        completeness = [bool(self._sr3.grid.is_complete(p)) for p in prop_names]
        has_incomplete = not all(completeness)

        active_only = has_incomplete
        selected_complete = self._sr3.grid.get_cell_indexes(
            is_complete=not active_only,
            elements=[element],
        )
        selected_complete = np.asarray(selected_complete, dtype=int)
        n_cells = int(selected_complete.size)

        if grid_values is not None:
            values = np.asarray(grid_values, dtype=float)
            expected = (len(prop_names), n_days, n_cells)
            if values.shape != expected:
                raise ValueError(
                    "grid_values size mismatch. Expected shape "
                    f"{expected}, got {values.shape}."
                )
            grid_data = values
        else:
            props_data = []
            for prop in prop_names:
                arr = self._read_grid_property(
                    element=element,
                    property_name=prop,
                    days=days,
                    active_only=active_only,
                )
                if arr.shape != (n_cells, n_days):
                    raise ValueError(
                        f"Unexpected SR3 shape for '{prop}': got {arr.shape}, "
                        f"expected ({n_cells}, {n_days})."
                    )
                props_data.append(arr.T)
            grid_data = np.stack(props_data, axis=0)

        all_vertices = self._sr3.grid.coordinates.get(face=4)
        vertices = all_vertices[selected_complete - 1]

        ijk = self._sr3.grid.n2ijk(selected_complete)
        _, layer_sizes = np.unique(ijk[:, -1], return_counts=True)

        ijk_int = np.asarray(ijk[:, (0, 1, -1)], dtype=int)
        cell_names = list(
            map(r"({},{},{})".format, ijk_int[:, 0], ijk_int[:, 1], ijk_int[:, 2])
        )

        con_idx = None
        con_data = None
        if add_connections:
            con_idx, con_data = self._build_map_connections(
                selected_complete=selected_complete,
                days=days,
                connection_values=connection_values,
            )

        wells = None
        if add_wells:
            wells = self._build_map_wells(selected_complete=selected_complete)

        day_labels = [str(int(d)) for d in days] if days is not None else None

        return DashMapPlot(
            vertices=vertices,
            layer_sizes=layer_sizes,
            grid_data=grid_data,
            property_names=prop_names,
            cell_names=cell_names,
            connection_indices=con_idx,
            connection_data=con_data,
            connection_property_names=["Transmissibility"] if con_data is not None else None,
            wells=wells,
            day_labels=day_labels,
            width=width,
            height=height,
            title=title,
        )

    def _read_timeseries(self, element_type, element, property_name, days):
        if str(property_name).upper() == "WCUT":
            ql = self._read_timeseries(element_type, element, "QL", days)
            qw = self._read_timeseries(element_type, element, "QW", days)
            ql = np.asarray(ql, dtype=float)
            qw = np.asarray(qw, dtype=float)
            out = np.full_like(ql, np.nan, dtype=float)
            valid = np.isfinite(ql) & np.isfinite(qw) & (np.abs(ql) > 1.0e-12)
            out[valid] = qw[valid] / ql[valid]
            return out

        sim_data = self._sr3.data.get(
            element_type=element_type,
            properties=[property_name],
            elements=[element],
            days=days,
        )
        return np.asarray(sim_data[property_name].sel(element=element).values, dtype=float)

    @staticmethod
    def _parse_secondary_flag(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, np.integer)):
            return bool(value)
        if isinstance(value, str):
            token = value.strip().lower()
            if token in {"y2", "right", "secondary", "2", "true", "yes", "on"}:
                return True
            if token in {"y1", "left", "primary", "1", "false", "no", "off"}:
                return False
        raise ValueError(
            "Series secondary-axis flag must be bool/int or one of: "
            "'y1'|'y2', 'left'|'right', 'primary'|'secondary'."
        )

    @staticmethod
    def _normalize_secondary_y_selection(secondary_y, labels, n_series):
        if secondary_y is None:
            return set()

        label_to_idx = {name: idx for idx, name in enumerate(labels)}
        normalized = set()

        for item in secondary_y:
            if isinstance(item, str):
                key = item.strip()
                if key in label_to_idx:
                    normalized.add(label_to_idx[key])
                    continue
                if key.isdigit():
                    idx = int(key)
                else:
                    raise ValueError(
                        f"Unknown secondary_y label '{item}'. Available labels: {labels}."
                    )
            else:
                idx = int(item)

            if idx < 0 or idx >= n_series:
                raise ValueError(
                    f"secondary_y index {idx} out of range [0, {n_series-1}]."
                )
            normalized.add(idx)

        return normalized

    def make_line(
        self,
        series=None,
        days=None,
        title="Line Plot",
        data=None,
        x_values=None,
        secondary_y=None,
        width=1000,
        height=420,
    ):
        """Build a `DashLinePlot` from SR3 time-series descriptors or direct arrays.

        `series` can be:
        - dict: {"Label": ("well", "P11", "NP")}
        - list: [("well", "P11", "NP"), ...]

        For SR3-backed `series`, each descriptor can also include a fourth item
        to flag secondary axis placement:
        - ("well", "P11", "NP", True)

        `secondary_y` can be a list of series indices (all modes) and, when
        `series` is a dict, it can also include label names.
        """
        if data is not None:
            if x_values is None:
                raise ValueError("x_values must be provided when direct line data is used.")
            y_values = np.asarray(data, dtype=float)
            if y_values.ndim == 1:
                y_values = y_values.reshape(1, -1)
            if y_values.ndim != 2:
                raise ValueError("Direct line data must have shape (n_series, n_points).")
            if y_values.shape[1] != len(np.asarray(x_values)):
                raise ValueError("Direct line data second dimension must match x_values length.")
            names = [f"Series {i+1}" for i in range(y_values.shape[0])]
            return DashLinePlot(
                x_values=np.asarray(x_values),
                y_values=y_values,
                property_names=names,
                secondary_y=secondary_y,
                width=width,
                height=height,
                title=title,
            )

        if series is None:
            raise ValueError("series or direct data must be provided to make_line.")

        if isinstance(series, dict):
            labels = list(series.keys())
            descriptors = list(series.values())
        else:
            descriptors = self._as_list(series)
            labels = [f"Series {i+1}" for i in range(len(descriptors))]

        descriptors = list(descriptors)
        if len(descriptors) == 0:
            raise ValueError("At least one line series must be provided.")

        element_type = str(descriptors[0][0]).strip().lower()
        if element_type == "grid":
            raise ValueError("Line series expects time-series descriptors, not grid descriptors.")

        days = self._normalize_days(days, element_type=element_type)
        x_dates = pd.to_datetime(self._sr3.dates.day2date(days)).to_numpy(dtype="datetime64[ns]")
        y_values = []
        descriptor_secondary = set()
        for idx, desc in enumerate(descriptors):
            if not isinstance(desc, tuple) or len(desc) not in (3, 4):
                raise ValueError(
                    "Each line descriptor must be a tuple: "
                    "(element_type, element_name, property_name[, secondary_axis])."
                )

            use_secondary = False
            if len(desc) == 4:
                use_secondary = self._parse_secondary_flag(desc[3])
            if use_secondary:
                descriptor_secondary.add(idx)

            etype, elem, prop = str(desc[0]).lower(), str(desc[1]), str(desc[2]).upper()
            values = self._read_timeseries(etype, elem, prop, days)
            y_values.append(values)

        user_secondary = self._normalize_secondary_y_selection(
            secondary_y=secondary_y,
            labels=labels,
            n_series=len(descriptors),
        )
        secondary_idx = sorted(descriptor_secondary.union(user_secondary))

        return DashLinePlot(
            x_values=x_dates,
            y_values=np.asarray(y_values, dtype=float),
            property_names=labels,
            secondary_y=secondary_idx,
            width=width,
            height=height,
            title=title,
        )

    def make_scatter(
        self,
        data,
        days=None,
        title="Scatter Plot",
        width=1000,
        height=420,
    ):
        """Build a `DashScatterPlot` from SR3 descriptors or direct XY arrays.

        Descriptor formats accepted in `data` values:
        - ("well", "P11", "NP", "WCUT") for time-series pairs
        - ("grid", "matrix", "POR", "PERMI") for grid-property pairs
        - np.ndarray with shape (n_points, 2)
        """
        if not isinstance(data, dict) or len(data) == 0:
            raise ValueError("Scatter data must be a non-empty dict.")

        scatter_data = {}
        for key, spec in data.items():
            if isinstance(spec, np.ndarray) or (
                hasattr(spec, "shape") and len(np.asarray(spec).shape) == 2
            ):
                arr = np.asarray(spec, dtype=float)
                if arr.ndim != 2 or arr.shape[1] != 2:
                    raise ValueError(
                        f"Direct scatter array '{key}' must have shape (n_points, 2)."
                    )
                scatter_data[str(key)] = arr
                continue

            if not isinstance(spec, tuple) or len(spec) != 4:
                raise ValueError(
                    f"Scatter descriptor '{key}' must be tuple with 4 entries."
                )

            descriptor_type = str(spec[0]).strip().lower()
            if descriptor_type == "grid":
                element = str(spec[1]).strip().upper()
                x_prop = str(spec[2]).strip().upper()
                y_prop = str(spec[3]).strip().upper()

                day_list = self._normalize_days(days, element_type="grid")
                complete_x = self._sr3.grid.is_complete(x_prop)
                complete_y = self._sr3.grid.is_complete(y_prop)
                active_only = not (complete_x and complete_y)

                x_arr = self._read_grid_property(element, x_prop, day_list, active_only)
                y_arr = self._read_grid_property(element, y_prop, day_list, active_only)

                x_flat = x_arr.reshape(-1)
                y_flat = y_arr.reshape(-1)
            else:
                element_type = descriptor_type
                element_name = str(spec[1]).strip()
                x_prop = str(spec[2]).strip().upper()
                y_prop = str(spec[3]).strip().upper()
                day_list = self._normalize_days(days, element_type=element_type)

                x_flat = self._read_timeseries(element_type, element_name, x_prop, day_list)
                y_flat = self._read_timeseries(element_type, element_name, y_prop, day_list)

            if x_flat.shape != y_flat.shape:
                raise ValueError(
                    f"Scatter '{key}' x/y size mismatch: {x_flat.shape} vs {y_flat.shape}."
                )

            valid = np.isfinite(x_flat) & np.isfinite(y_flat)
            scatter_data[str(key)] = np.column_stack([x_flat[valid], y_flat[valid]])

        return DashScatterPlot(
            scatter_data=scatter_data,
            title=title,
            width=width,
            height=height,
        )

    def make_table(
        self,
        series=None,
        days=None,
        title="Table",
        table_data=None,
        page_size=20,
        width=1000,
        height=420,
    ):
        """Build a `DashTable` from SR3 time-series descriptors or direct DataFrame."""
        if table_data is not None:
            if not isinstance(table_data, pd.DataFrame):
                raise ValueError("table_data must be a pandas DataFrame.")
            return DashTable(
                table_data=table_data,
                title=title,
                page_size=page_size,
                width=width,
                height=height,
            )

        descriptors = self._as_list(series)
        if descriptors is None or len(descriptors) == 0:
            raise ValueError("series or table_data must be provided for make_table.")

        element_type = str(descriptors[0][0]).strip().lower()
        days = self._normalize_days(days, element_type=element_type)
        df = pd.DataFrame({"day": days})

        for desc in descriptors:
            if not isinstance(desc, tuple) or len(desc) != 3:
                raise ValueError(
                    "Each table descriptor must be tuple: "
                    "(element_type, element_name, property_name)."
                )
            etype, elem, prop = str(desc[0]).lower(), str(desc[1]), str(desc[2]).upper()
            values = self._read_timeseries(etype, elem, prop, days)
            label = f"{elem}:{prop}"
            df[label] = values

        return DashTable(
            table_data=df,
            title=title,
            page_size=page_size,
            width=width,
            height=height,
        )

    def dashboard(self, maps=None, lines=None, scatter=None, table=None, title="SR3 Dashboard"):
        """Build a grouped Dash dashboard and return a runnable panel wrapper."""
        maps = {} if maps is None else dict(maps)
        lines = {} if lines is None else dict(lines)
        scatter = {} if scatter is None else dict(scatter)
        table = {} if table is None else dict(table)

        wrapper = DashMultiPanelDashboard(
            map_plots=maps,
            line_plots=lines,
            scatter_plots=scatter,
            table_plots=table,
            title=title,
        )
        return DashPanel(app=wrapper.create_app())
