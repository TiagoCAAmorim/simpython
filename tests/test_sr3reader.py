"""
sr3reader module tests
"""

from pathlib import Path
from collections import Counter
from datetime import datetime
import unittest

import context  # noqa # pylint: disable=unused-import
from rsimpy.cmg.sr3reader import Sr3Reader


def only_in_first(list_1, list_2):
    """Elements only in first list"""
    return list(set(list_1) - set(list_2))


def have_same_elements(list1, list2):
    """Lists have same elements"""
    return Counter(list1) == Counter(list2)


def _test_equal_lists(self, true_result, file_read, partial_true_result=False):
    missing = only_in_first(true_result, file_read)
    surplus = only_in_first(file_read, true_result)
    error_list = []
    if len(missing) > 0:
        error_list.append(f"\n  Missing: {', '.join([str(a) for a in missing])}")
    if len(surplus) > 0:
        error_list.append(f"\n  Surplus: {', '.join([str(a) for a in surplus])}")
    error_msg = "".join(error_list)

    if partial_true_result:
        self.assertEqual(missing, [], error_msg)
    else:
        self.assertTrue(have_same_elements(file_read, true_result), error_msg)


class TestSr3Reader(unittest.TestCase):
    """Tests Sr3Reader functionalities"""

# MARK: Elements
    def test_read_elements(self):
        """Tests reading the elements of a file"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file, auto_read=False)
        sr3.read()

        true_result = [
            "I11",
            "I11-W",
            "I12",
            "I12-W",
            "I13",
            "I13-W",
            "I14",
            "I14-W",
            "I15",
            "I15-W",
            "I16",
            "I16-W",
            "I17",
            "I17-W",
            "P11",
            "P12",
            "P13",
            "P14",
            "P15",
            "P16",
        ]
        file_read = sr3.elements.get("well").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            "Default-Group-PRO",
            "Default-Group-INJ",
            "FIELD-PRO",
            "FIELD-INJ",
            "I-PLAT1-PRO",
            "I-PLAT1-INJ",
            "I-PLAT-TLD-PRO",
            "I-PLAT-TLD-INJ",
            "P-PLAT1-PRO",
            "P-PLAT1-INJ",
            "P-PLAT-TLD-PRO",
            "P-PLAT-TLD-INJ",
            "PLAT1-PRO",
            "PLAT1-INJ",
            "PLAT-TLD-PRO",
            "PLAT-TLD-INJ",
        ]
        file_read = sr3.elements.get("group").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = ["FIELD"]
        file_read = sr3.elements.get("sector").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            "P11{23,25,49}",
            "I11{31,10,40}",
            "P12{12,31,36}",
            "P13{28,24,48}",
            "P14{36,17,34}",
            "P15{23,20,40}",
            "P16{13,14,41}",
            "I12{14,18,43}",
            "I13{26,14,36}",
            "I14{23,10,42}",
            "I15{38,9,24}",
            "I16{12,22,42}",
            "I17{7,26,41}",
            "I11-W{31,10,40}",
            "I12-W{14,18,43}",
            "I13-W{26,14,36}",
            "I14-W{23,10,42}",
            "I15-W{38,9,24}",
            "I16-W{12,22,42}",
            "I17-W{7,26,41}",
        ]
        file_read = sr3.elements.get("layer").keys()
        _test_equal_lists(self, true_result, file_read, True)

        true_result = ["MATRIX", "FRACTURE"]
        file_read = sr3.elements.get("grid").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            "CO2",
            "N2 toCH4",
            "C2HtoNC5",
            "C6ttoC19",
            "C29toC63",
            "WATER"
        ]
        file_read = sr3.properties.get_components_list().values()
        _test_equal_lists(self, true_result, file_read)

# MARK: Properties
    def test_read_properties(self):
        """Tests reading the properties of a file"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file)

        true_result = [
            "WELLSTATE",
            "WELLOPMO",
            "WHP",
            "BHP",
            "BLOCKP",
            "MOBWTDATP",
            "BHTEMP",
            "WHTEMP",
            "ONFRAC",
            "CGLIFT",
            "OILVOLSC",
            "GASVOLSC",
            "WATVOLSC",
            "INLVOLSC",
            "WTGVOLSC",
            "OILVOLRC",
            "GASVOLRC",
            "WATVOLRC",
            "BHFVOLRC",
            "WELLOTIME",
            "OILRATSC",
            "GASRATSC",
            "WATRATSC",
            "INLRATSC",
            "WTGRATSC",
            "OILRATRC",
            "GASRATRC",
            "WATRATRC",
            "BHFRATRC",
            "LIQVOLSC",
            "LIQRATSC",
            "OILMOLSC",
            "GASMOLSC",
            "WTGMOLSC",
            "OILMOLRSC",
            "GASMOLRSC",
            "WTGMOLRSC",
            "OILCMOLSC(CO2)",
            "OILCMOLSC(N2 toCH4)",
            "OILCMOLSC(C2HtoNC5)",
            "OILCMOLSC(C6ttoC19)",
            "OILCMOLSC(C29toC63)",
            "OILMOLRSC(CO2)",
            "OILMOLRSC(N2 toCH4)",
            "OILMOLRSC(C2HtoNC5)",
            "OILMOLRSC(C6ttoC19)",
            "OILMOLRSC(C29toC63)",
            "GASCMOLSC(CO2)",
            "GASCMOLSC(N2 toCH4)",
            "GASCMOLSC(C2HtoNC5)",
            "GASCMOLSC(C6ttoC19)",
            "GASCMOLSC(C29toC63)",
            "GASMOLRSC(CO2)",
            "GASMOLRSC(N2 toCH4)",
            "GASMOLRSC(C2HtoNC5)",
            "GASMOLRSC(C6ttoC19)",
            "GASMOLRSC(C29toC63)",
            "INLCMOLSC(CO2)",
            "INLCMOLSC(N2 toCH4)",
            "INLCMOLSC(C2HtoNC5)",
            "INLCMOLSC(C6ttoC19)",
            "INLCMOLSC(C29toC63)",
            "INLMOLRSC(CO2)",
            "INLMOLRSC(N2 toCH4)",
            "INLMOLRSC(C2HtoNC5)",
            "INLMOLRSC(C6ttoC19)",
            "INLMOLRSC(C29toC63)",
            "WTGCMOLSC(CO2)",
            "WTGCMOLSC(N2 toCH4)",
            "WTGCMOLSC(C2HtoNC5)",
            "WTGCMOLSC(C6ttoC19)",
            "WTGCMOLSC(C29toC63)",
            "WTGMOLRSC(CO2)",
            "WTGMOLRSC(N2 toCH4)",
            "WTGMOLRSC(C2HtoNC5)",
            "WTGMOLRSC(C6ttoC19)",
            "WTGMOLRSC(C29toC63)",
            "OILCMASSC(CO2)",
            "OILCMASSC(N2 toCH4)",
            "OILCMASSC(C2HtoNC5)",
            "OILCMASSC(C6ttoC19)",
            "OILCMASSC(C29toC63)",
            "OILMASRSC(CO2)",
            "OILMASRSC(N2 toCH4)",
            "OILMASRSC(C2HtoNC5)",
            "OILMASRSC(C6ttoC19)",
            "OILMASRSC(C29toC63)",
            "GASCMASSC(CO2)",
            "GASCMASSC(N2 toCH4)",
            "GASCMASSC(C2HtoNC5)",
            "GASCMASSC(C6ttoC19)",
            "GASCMASSC(C29toC63)",
            "GASMASRSC(CO2)",
            "GASMASRSC(N2 toCH4)",
            "GASMASRSC(C2HtoNC5)",
            "GASMASRSC(C6ttoC19)",
            "GASMASRSC(C29toC63)",
            "INLCMASSC(CO2)",
            "INLCMASSC(N2 toCH4)",
            "INLCMASSC(C2HtoNC5)",
            "INLCMASSC(C6ttoC19)",
            "INLCMASSC(C29toC63)",
            "INLMASRSC(CO2)",
            "INLMASRSC(N2 toCH4)",
            "INLMASRSC(C2HtoNC5)",
            "INLMASRSC(C6ttoC19)",
            "INLMASRSC(C29toC63)",
            "WTGCMASSC(CO2)",
            "WTGCMASSC(N2 toCH4)",
            "WTGCMASSC(C2HtoNC5)",
            "WTGCMASSC(C6ttoC19)",
            "WTGCMASSC(C29toC63)",
            "WTGMASRSC(CO2)",
            "WTGMASRSC(N2 toCH4)",
            "WTGMASRSC(C2HtoNC5)",
            "WTGMASRSC(C6ttoC19)",
            "WTGMASRSC(C29toC63)",
            "LP","QW","QG","QW_RC","QO","QL","QO_RC","NP","UPTIME","QG_RC","WP","GP"
        ]
        file_read = sr3.properties.get("well").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            "OILVOLSC",
            "GASVOLSC",
            "WATVOLSC",
            "INLVOLSC",
            "WTGVOLSC",
            "OILVOLRC",
            "GASVOLRC",
            "WATVOLRC",
            "BHFVOLRC",
            "OILRATSC",
            "GASRATSC",
            "WATRATSC",
            "INLRATSC",
            "WTGRATSC",
            "OILRATRC",
            "GASRATRC",
            "WATRATRC",
            "BHFRATRC",
            "VOIDRATRC",
            "LIQVOLSC",
            "LIQRATSC",
            "WELLOTIME",
            "NOPWING",
            "PMPRES",
            "GIMPRES",
            "WIMPRES",
            "PSPRES",
            "GISPRES",
            "WISPRES",
            "ONFRAC",
            "OILMOLSC",
            "GASMOLSC",
            "WTGMOLSC",
            "OILMOLRSC",
            "GASMOLRSC",
            "WTGMOLRSC",
            "OILCMOLSC(CO2)",
            "OILCMOLSC(N2 toCH4)",
            "OILCMOLSC(C2HtoNC5)",
            "OILCMOLSC(C6ttoC19)",
            "OILCMOLSC(C29toC63)",
            "OILMOLRSC(CO2)",
            "OILMOLRSC(N2 toCH4)",
            "OILMOLRSC(C2HtoNC5)",
            "OILMOLRSC(C6ttoC19)",
            "OILMOLRSC(C29toC63)",
            "GASCMOLSC(CO2)",
            "GASCMOLSC(N2 toCH4)",
            "GASCMOLSC(C2HtoNC5)",
            "GASCMOLSC(C6ttoC19)",
            "GASCMOLSC(C29toC63)",
            "GASMOLRSC(CO2)",
            "GASMOLRSC(N2 toCH4)",
            "GASMOLRSC(C2HtoNC5)",
            "GASMOLRSC(C6ttoC19)",
            "GASMOLRSC(C29toC63)",
            "INLCMOLSC(CO2)",
            "INLCMOLSC(N2 toCH4)",
            "INLCMOLSC(C2HtoNC5)",
            "INLCMOLSC(C6ttoC19)",
            "INLCMOLSC(C29toC63)",
            "INLMOLRSC(CO2)",
            "INLMOLRSC(N2 toCH4)",
            "INLMOLRSC(C2HtoNC5)",
            "INLMOLRSC(C6ttoC19)",
            "INLMOLRSC(C29toC63)",
            "WTGCMOLSC(CO2)",
            "WTGCMOLSC(N2 toCH4)",
            "WTGCMOLSC(C2HtoNC5)",
            "WTGCMOLSC(C6ttoC19)",
            "WTGCMOLSC(C29toC63)",
            "WTGMOLRSC(CO2)",
            "WTGMOLRSC(N2 toCH4)",
            "WTGMOLRSC(C2HtoNC5)",
            "WTGMOLRSC(C6ttoC19)",
            "WTGMOLRSC(C29toC63)",
            "OILCMASSC(CO2)",
            "OILCMASSC(N2 toCH4)",
            "OILCMASSC(C2HtoNC5)",
            "OILCMASSC(C6ttoC19)",
            "OILCMASSC(C29toC63)",
            "OILMASRSC(CO2)",
            "OILMASRSC(N2 toCH4)",
            "OILMASRSC(C2HtoNC5)",
            "OILMASRSC(C6ttoC19)",
            "OILMASRSC(C29toC63)",
            "GASCMASSC(CO2)",
            "GASCMASSC(N2 toCH4)",
            "GASCMASSC(C2HtoNC5)",
            "GASCMASSC(C6ttoC19)",
            "GASCMASSC(C29toC63)",
            "GASMASRSC(CO2)",
            "GASMASRSC(N2 toCH4)",
            "GASMASRSC(C2HtoNC5)",
            "GASMASRSC(C6ttoC19)",
            "GASMASRSC(C29toC63)",
            "INLCMASSC(CO2)",
            "INLCMASSC(N2 toCH4)",
            "INLCMASSC(C2HtoNC5)",
            "INLCMASSC(C6ttoC19)",
            "INLCMASSC(C29toC63)",
            "INLMASRSC(CO2)",
            "INLMASRSC(N2 toCH4)",
            "INLMASRSC(C2HtoNC5)",
            "INLMASRSC(C6ttoC19)",
            "INLMASRSC(C29toC63)",
            "WTGCMASSC(CO2)",
            "WTGCMASSC(N2 toCH4)",
            "WTGCMASSC(C2HtoNC5)",
            "WTGCMASSC(C6ttoC19)",
            "WTGCMASSC(C29toC63)",
            "WTGMASRSC(CO2)",
            "WTGMASRSC(N2 toCH4)",
            "WTGMASRSC(C2HtoNC5)",
            "WTGMASRSC(C6ttoC19)",
            "WTGMASRSC(C29toC63)",
            "WP","QO","UPTIME","QG","QW","QW_RC","QG_RC","QO_RC","NP","QL","GP","LP"
        ]
        file_read = sr3.properties.get("group").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            "OILSECSU",
            "GASSECSU",
            "WATSECSU",
            "INLSECSU",
            "OILSECRECO",
            "GASSECRECO",
            "WATSECRECO",
            "INLSECRECO",
            "WAQCUMSEC",
            "OILSECPRCM",
            "WATSECPRCM",
            "GASSECPRCM",
            "INLSECPRCM",
            "WTGSECPRCM",
            "WATSECINCM",
            "GASSECINCM",
            "OILSECPRRT",
            "WATSECPRRT",
            "GASSECPRRT",
            "INLSECPRRT",
            "WTGSECPRRT",
            "WATSECINRT",
            "GASSECINRT",
            "PVCUMSEC",
            "HPVCUMSEC",
            "PRSCUMSEC",
            "PHHCUMSEC",
            "PDTVSEC",
            "PTDCUMSEC",
            "AVGTEMPSEC",
            "OILSECRECU",
            "WATSECRECU",
            "GASSECRECU",
            "OILSECAVSA",
            "WATSECAVSA",
            "GASSECAVSA",
            "OILMLPSC",
            "GASMLPSC",
            "WTGMLPSC",
            "INLMLPSC",
            "OILCMLPSC(CO2)",
            "OILCMLPSC(N2 toCH4)",
            "OILCMLPSC(C2HtoNC5)",
            "OILCMLPSC(C6ttoC19)",
            "OILCMLPSC(C29toC63)",
            "GASCMLPSC(CO2)",
            "GASCMLPSC(N2 toCH4)",
            "GASCMLPSC(C2HtoNC5)",
            "GASCMLPSC(C6ttoC19)",
            "GASCMLPSC(C29toC63)",
            "INLCMLPSC(CO2)",
            "INLCMLPSC(N2 toCH4)",
            "INLCMLPSC(C2HtoNC5)",
            "INLCMLPSC(C6ttoC19)",
            "INLCMLPSC(C29toC63)",
            "WTGCMLPSC(CO2)",
            "WTGCMLPSC(N2 toCH4)",
            "WTGCMLPSC(C2HtoNC5)",
            "WTGCMLPSC(C6ttoC19)",
            "WTGCMLPSC(C29toC63)",
            "GASCMLISC(CO2)",
            "GASCMLISC(N2 toCH4)",
            "GASCMLISC(C2HtoNC5)",
            "GASCMLISC(C6ttoC19)",
            "GASCMLISC(C29toC63)",
            "OILMOLIP(CO2)",
            "OILMOLIP(N2 toCH4)",
            "OILMOLIP(C2HtoNC5)",
            "OILMOLIP(C6ttoC19)",
            "OILMOLIP(C29toC63)",
            "GASMOLIP(CO2)",
            "GASMOLIP(N2 toCH4)",
            "GASMOLIP(C2HtoNC5)",
            "GASMOLIP(C6ttoC19)",
            "GASMOLIP(C29toC63)",
            "INLMOLIP(CO2)",
            "INLMOLIP(N2 toCH4)",
            "INLMOLIP(C2HtoNC5)",
            "INLMOLIP(C6ttoC19)",
            "INLMOLIP(C29toC63)",
            "OILCOMMOL(CO2)",
            "OILCOMMOL(N2 toCH4)",
            "OILCOMMOL(C2HtoNC5)",
            "OILCOMMOL(C6ttoC19)",
            "OILCOMMOL(C29toC63)",
            "GASCOMMOL(CO2)",
            "GASCOMMOL(N2 toCH4)",
            "GASCOMMOL(C2HtoNC5)",
            "GASCOMMOL(C6ttoC19)",
            "GASCOMMOL(C29toC63)",
            "AQUCOMMOL(CO2)",
            "AQUCOMMOL(N2 toCH4)",
            "AQUCOMMOL(C2HtoNC5)",
            "AQUCOMMOL(C6ttoC19)",
            "AQUCOMMOL(C29toC63)",
            "AQUCOMMOL(WATER)",
            "OILSECRECOO",
            "GASSECRECOO",
            "WATSECRECOO",
            "INLSECRECOO",
            "VOIP"
        ]
        file_read = sr3.properties.get("sector").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = ["STATUS"]
        file_read = sr3.properties.get("layer").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            "ICSTBC",
            "ICSTCG",
            "ICSTGN",
            "ICSTPS",
            "ICSTPB",
            "IPSTCS",
            "IPSTBT",
            "IPSTAC",
            "BLOCKDEPTH",
            "BLOCKPVOL",
            "BVOL",
            "PERMI",
            "PERMJ",
            "PERMK",
            "TRMI",
            "TRMJ",
            "TRMK",
            "TRLI",
            "TRLJ",
            "TRLK",
            "BSWCRIT",
            "BSGCRIT",
            "BSORW",
            "BSORG",
            "BSWCON",
            "BSGCON",
            "BSOIRW",
            "BSOIRG",
            "BSLCON",
            "BKRWIRO",
            "BKROCW",
            "BKRWRO",
            "BKROCRW",
            "PCWMAX",
            "PCWSHF",
            "BKRGCL",
            "BKROGCG",
            "BKRGRL",
            "BKROGCRG",
            "PCGMAX",
            "POR",
            "NET/GROSS",
            "MODBVOL",
            "KRSETN",
            "SO",
            "SG",
            "SW",
            "PRES",
            "VISO",
            "VISG",
            "VISW",
            "Z(CO2)",
        ]
        file_read = sr3.properties.get("grid").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            "ELTSCUM",
            "ELTSRATE",
            "TSTEPCUM",
            "NCYCCUM",
            "SOLITCUM",
            "TSCUTCUM",
            "DELTIME",
            "NCYCPTS",
            "SOLITPN",
            "MBERROR",
            "AVGIMPL",
            "MEMUSAGE",
            "TS_SIZE","TS_CUTS","ELAPSED"
        ]
        file_read = sr3.properties.get("special").keys()
        _test_equal_lists(self, true_result, file_read)

# MARK: Units
    def test_read_units(self):
        """Tests reading the units"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file)

        true_result = {
            "time": "day",
            "temperature": "C",
            "pressure": "kgf/cm2",
            "length": "m",
            "property volume": "m3",
            "permeability": "md",
            "mass": "kg",
            "molar mass": "gmole",
            "viscosity": "cp",
            "energy": "J",
            "well liquid volume": "m3",
            "well gas volume": "m3",
            "well rate time": "day",
            "interfacial tension": "dyne/cm",
            "electrical current": "A",
            "electrical power": "J/day",
            "electrical potential": "V",
            "electrical resistance": "ohm",
            "electrical conductivity": "S/m",
            "electrical energy": "J",
            "temperature difference": "C",
            "diffusion/dispersion coeff.": "cm2/s",
            "concentration": "kg/m3",
            "molar concentration": "gmole/m3",
        }
        file_read = sr3.units.get_current()
        _test_equal_lists(self, true_result.keys(), file_read.keys())
        _test_equal_lists(self, true_result.values(), file_read.values())

        sr3.units.set_current(dimensionality="mass",unit="g")
        file_read = sr3.units.get_current()
        self.assertEqual("g", file_read["mass"])
        file_read = sr3.units.get_current("mass")
        self.assertEqual("g", file_read)

        file_read = sr3.units.get_current("7")
        self.assertEqual("g", file_read)
        file_read = sr3.units.get_current("7-8")
        self.assertEqual("g/gmole", file_read)
        file_read = sr3.units.get_current("-7")
        self.assertEqual("1/g", file_read)
        file_read = sr3.units.get_current("")
        self.assertEqual("", file_read)

        sr3.units.add(old="day", new="week", gain=1./7., offset=0.0)
        sr3.units.set_current(dimensionality="well rate time",unit="week")
        file_read = sr3.properties.unit(property_name="OILRATSC")
        self.assertEqual("m3/week", file_read)

        sr3.properties.set_alias(
            old="OILRATSC",
            new="QO",
            return_error=False)
        sr3.units.set_current(dimensionality="well rate time",unit="day")
        file_read = sr3.properties.unit(property_name="QO")
        self.assertEqual("m3/day", file_read)

        with self.assertRaises(ValueError):
            sr3.properties.set_alias(old="OILRATSC", new="QO")

        with self.assertRaises(ValueError):
            sr3.properties.set_alias(old="OILRATSC", new="OILRATRC")

# MARK: Dates
    def test_read_times(self):
        """Tests reading times and dates"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file)

        file_read = sr3.dates.get_timesteps()
        true_result = list(range(3609))
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.dates.get_dates("group")
        true_result = datetime.strptime("20181002", "%Y%m%d")
        self.assertEqual(true_result, file_read[0])
        true_result = datetime.strptime("20240803", "%Y%m%d")
        self.assertEqual(true_result, file_read[-1])

        file_read = sr3.dates.get_days("well")
        true_result = 30.
        self.assertEqual(true_result, file_read[0])
        true_result = 2162.
        self.assertEqual(true_result, file_read[-1])

        file_read = sr3.dates.get_days("grid")
        true_result = [0., 30.]
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.dates.day2date(day=735.)
        true_result = datetime.strptime("20200906", "%Y%m%d")
        self.assertEqual(true_result, file_read)

        file_read = sr3.dates.day2date(day=[735.])
        true_result = [datetime.strptime("20200906", "%Y%m%d")]
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.dates.date2day(date=datetime.strptime("20200906", "%Y%m%d"))
        true_result = 735.
        self.assertEqual(true_result, file_read)

        file_read = sr3.dates.date2day(date=[datetime.strptime("20200906", "%Y%m%d")])
        true_result = [735.]
        _test_equal_lists(self, true_result, file_read)

# MARK: Element hierarchy
    def test_read_element_hierarchy(self):
        """Tests reading element hierarchy"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file)

        file_read = sr3.elements.get_parent(
            element_type="group",
            element_name="I-PLAT1-PRO")
        true_result = "PLAT1-PRO"
        self.assertEqual(true_result, file_read)

        file_read = sr3.elements.get_parent(
            element_type="layer",
            element_name="P13{28,24,48}")
        true_result = "P13"
        self.assertEqual(true_result, file_read)

        file_read = sr3.elements.get_parent(
            element_type="well",
            element_name="P13")
        true_result = "P-PLAT1-PRO"
        self.assertEqual(true_result, file_read)

        file_read = sr3.elements.get_parent(
            element_type="grid",
            element_name="MATRIX")
        true_result = ""
        self.assertEqual(true_result, file_read)

        file_read = sr3.elements.get_connection(
            element_type="layer",
            element_name="I11{31,10,76}")
        true_result = 99
        self.assertEqual(true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="group",
            element_name="FIELD-INJ")
        true_result = [
            "Default-Group-INJ",
            "I-PLAT1-INJ",
            "I-PLAT-TLD-INJ",
            "P-PLAT1-INJ",
            "P-PLAT-TLD-INJ",
            "PLAT1-INJ",
            "PLAT-TLD-INJ"
        ]
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="group",
            element_name="PLAT1-PRO")
        true_result = ["I-PLAT1-PRO", "P-PLAT1-PRO"]
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="group",
            element_name="Default-Group-PRO")
        true_result = []
        self.assertEqual(true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="well",
            element_name="PLAT1-PRO")
        true_result = sr3.elements.get("well").keys()
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="well",
            element_name="FIELD-PRO")
        true_result = sr3.elements.get("well").keys()
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="well",
            element_name="PLAT1-INJ")
        true_result = []
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="well",
            element_name="I-PLAT1-PRO")
        true_result = [k for k in sr3.elements.get("well").keys() if k[0]=="I"]
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3.elements.get_children(
            element_type="layer",
            element_name="P11")
        true_result = [k for k in sr3.elements.get("layer").keys() if k[:3]=="P11"]
        _test_equal_lists(self, true_result, file_read)


# MARK: Grid sizes
    def test_read_grid_size(self):
        """Tests reading grid sizes"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file)

        file_read = sr3.grid.get_size("nijk")
        true_result = (47, 39, 291)
        self.assertEqual(true_result, file_read)

        file_read = sr3.grid.get_size("n_active")
        true_result = 67241
        self.assertEqual(true_result, file_read)

# MARK: Timeseries
    def test_read_timeseries(self):
        """Tests reading timeseries"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file)

        file_read = sr3.data.get(
            element_type="well",
            properties="BHP",
            elements="P11",
            days=[30., 1085., 2162.])
        file_read = file_read["BHP"].sel(element="P11").values
        true_result = [60627.83967735492 / 98.0665,
                       55779.152843383265 / 98.0665,
                       52595.77029111726 / 98.0665]
        _test_equal_lists(self, true_result, list(file_read))

        sr3.properties.set_alias(
            old="OILRATSC",
            new="QO",
            return_error=False)
        file_read = sr3.data.get(
            element_type="well",
            properties=["QO","BHP"],
            elements=["P14","P11"],
            days=[30., 1085., 2162.])

        file_read_ = file_read["QO"].sel(element="P14").values
        true_result = [0.0,
                       6325.951742655704,
                       4247.476791690085]
        _test_equal_lists(self, true_result, list(file_read_))

        file_read_ = file_read["BHP"].sel(element="P14").values
        true_result = [62718.11721660964 / 98.0665,
                       47094.053970322144 / 98.0665,
                       45799.42941685654 / 98.0665]
        _test_equal_lists(self, true_result, list(file_read_))

        file_read_ = file_read["QO"].sel(element="P11").values
        true_result = [6246.5344882818345,
                       7404.518299614956,
                       6078.931879073354]
        _test_equal_lists(self, true_result, list(file_read_))

        file_read_ = file_read["BHP"].sel(element="P11").values
        true_result = [60627.83967735492 / 98.0665,
                       55779.152843383265 / 98.0665,
                       52595.77029111726 / 98.0665]
        _test_equal_lists(self, true_result, list(file_read_))

        file_read = sr3.data.get(
            element_type="group",
            properties=["NP"],
            elements=["PLAT1-PRO"],
            days=[(2.*1001.0+1008.99)/3.])
        file_read_ = file_read["NP"].sel(element="PLAT1-PRO").values[0]
        true_result = (2.*166546.69278864737+241094.6563692809)/3.
        self.assertAlmostEqual(true_result, float(file_read_))

        sr3.units.set_current(dimensionality="well liquid volume", unit="MMbbl")
        file_read = sr3.data.get(
            element_type="group",
            properties=["NP"],
            elements=["PLAT1-PRO"],
            days=[(2.*1001.0+1008.99)/3.])
        file_read_ = file_read["NP"].sel(element="PLAT1-PRO").values[0]
        self.assertAlmostEqual(true_result * 6.2898108E-6, float(file_read_))

        file_read = sr3.data.get(
            element_type="special",
            properties="ELAPSED",
            days=[30., 1085., 2162.])

        file_read_ = file_read["ELAPSED"].sel(element="").values
        true_result = [140.862025,
                       431.85733,
                       2677.2224149999997]
        _test_equal_lists(self, true_result, list(file_read_))

        file_read_ = file_read["ELAPSED"].values.flatten()
        true_result = [140.862025,
                       431.85733,
                       2677.2224149999997]
        _test_equal_lists(self, true_result, list(file_read_))

        sr3.units.set_current(dimensionality="well liquid volume", unit="bbl")
        sr3.data.to_csv(
            element_type="well",
            properties=["QO","BHP","NP"],
            elements=["P11","P13"],
            filename='test.csv')
        self.assertTrue(Path('test.csv').is_file())
        Path('test.csv').unlink()

# MARK: Gridmaps
    def test_read_gridmaps(self):
        """Tests reading grid properties"""

        test_file = Path("tests/sr3/base_case_3a.sr3")
        sr3 = Sr3Reader(test_file)

        file_read = sr3.data.get(
            element_type="grid",
            properties="NET/GROSS",
            elements="MATRIX",
            days=0.)
        file_read_ = file_read["NET/GROSS"].sel(day=0.).values
        for i in range(sr3.grid.get_size("n_active")):
            self.assertAlmostEqual(file_read_[i], 1)

        with self.assertRaises(ValueError):
            file_read = sr3.data.get(
                element_type="grid",
                properties="NET/GROSS",
                elements="MATRIX",
                days=30.)

        file_read = sr3.data.get(
            element_type="grid",
            properties="PRES",
            elements="MATRIX",
            days=30.)
        file_read_ = file_read["PRES"].sel(day=30.).values
        file_read_list = list(file_read_[:10])
        true_result = [
            63489.766,
            63396.96,
            63545.605,
            63325.547,
            63504.36,
            63737.207,
            63181.977,
            63330.82,
            63547.914,
            64793.88,
        ]
        true_result = [t / 98.0665 for t in true_result]
        for i in range(10):
            self.assertAlmostEqual(round(true_result[i], 3), round(file_read_list[i],3))

        file_read = sr3.data.get(
            element_type="grid",
            properties=["PRES","SO"],
            elements="MATRIX",
            days=[0., 30.])
        file_read_ = file_read["PRES"].sel(day=30.).values
        file_read_list = list(file_read_[:10])
        for i in range(10):
            self.assertAlmostEqual(round(true_result[i], 3), round(file_read_list[i],3))

        file_read = sr3.data.get(
            element_type="grid",
            properties=["SO","PRES","VISO","Z(CO2)"],
            elements="MATRIX",
            days=10.)
        file_read_ = file_read["VISO"].sel(day=10.).values
        file_read_list = list(file_read_[:10])
        true_result = [
            (2 * 0.38856095 + 0.38856095) / 3,
            (2 * 0.3883772 + 0.3883772) / 3,
            (2 * 0.3886714 + 0.3886714) / 3,
            (2 * 0.3882356 + 0.3882356) / 3,
            (2 * 0.38858983 + 0.38858983) / 3,
            (2 * 0.38904962 + 0.38904962) / 3,
            (2 * 0.38795048 + 0.38795048) / 3,
            (2 * 0.38824606 + 0.38824606) / 3,
            (2 * 0.38867596 + 0.38867596) / 3,
            (2 * 0.39111543 + 0.39111543) / 3,
        ]
        for i in range(10):
            self.assertAlmostEqual(true_result[i], file_read_list[i])


if __name__ == "__main__":
    unittest.main()
