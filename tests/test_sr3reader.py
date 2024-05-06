"""
sr3reader module tests
"""

from pathlib import Path
from collections import Counter
from datetime import datetime
import unittest

import context  # noqa # pylint: disable=unused-import
from simpython.cmg import sr3reader


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

    def test_read_elements(self):
        """Tests reading the elements of a file"""

        test_file = Path(r".\tests\sr3\base_case_3a.sr3").resolve()
        sr3_file = sr3reader.Sr3Reader(test_file)

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
        file_read = sr3_file.get_elements("well").keys()
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
        file_read = sr3_file.get_elements("group").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = ["FIELD"]
        file_read = sr3_file.get_elements("sector").keys()
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
        file_read = sr3_file.get_elements("layer").keys()
        _test_equal_lists(self, true_result, file_read, True)

        true_result = ["MATRIX"]
        file_read = sr3_file.get_elements("grid").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            "CO2",
            "N2 toCH4",
            "C2HtoNC5",
            "C6ttoC19",
            "C29toC63",
            "WATER"
        ]
        c_ = sr3_file._component_list  # pylint: disable=protected-access
        file_read = c_.values()
        _test_equal_lists(self, true_result, file_read)

    def test_read_properties(self):
        """Tests reading the properties of a file"""

        test_file = Path(r".\tests\sr3\base_case_3a.sr3").resolve()
        sr3_file = sr3reader.Sr3Reader(test_file)

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
        file_read = sr3_file.get_properties("well").keys()
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
        file_read = sr3_file.get_properties("group").keys()
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
        file_read = sr3_file.get_properties("sector").keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = ["STATUS"]
        file_read = sr3_file.get_properties("layer").keys()
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
        file_read = sr3_file.get_properties("grid").keys()
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
        file_read = sr3_file.get_properties("special").keys()
        _test_equal_lists(self, true_result, file_read)

    def test_read_units(self):
        """Tests reading the units"""

        test_file = Path(r".\tests\sr3\base_case_3a.sr3").resolve()
        sr3_file = sr3reader.Sr3Reader(test_file)

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
        file_read = sr3_file.get_current_units()
        _test_equal_lists(self, true_result.keys(), file_read.keys())
        _test_equal_lists(self, true_result.values(), file_read.values())

        sr3_file.set_current_unit(dimensionality="mass",unit="g")
        file_read = sr3_file.get_current_units()
        self.assertEqual("g", file_read["mass"])

        sr3_file.add_new_unit(old_unit="m", new_unit="dm", gain=0.1, offset=0.0)
        file_read = sr3_file.get_property_unit(property_name="OILRATSC")
        self.assertEqual("m3/day", file_read)

        sr3_file.set_alias(previous_property="OILRATSC",
                           new_property="QO",
                           check_exists=False)
        file_read = sr3_file.get_property_unit(property_name="QO")
        self.assertEqual("m3/day", file_read)

        with self.assertRaises(ValueError):
            sr3_file.set_alias(previous_property="OILRATSC", new_property="QO")

        with self.assertRaises(ValueError):
            sr3_file.set_alias(previous_property="OILRATSC", new_property="OILRATRC")

        with self.assertRaises(ValueError):
            sr3_file.set_alias(previous_property="NOTVALID", new_property="SOMETHING")

    def test_read_times(self):
        """Tests reading times and dates"""

        test_file = Path(r".\tests\sr3\base_case_3a.sr3").resolve()
        sr3_file = sr3reader.Sr3Reader(test_file)

        file_read = sr3_file.get_timesteps()
        true_result = list(range(3609))
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3_file.get_dates("group")
        true_result = datetime.strptime("20181002", "%Y%m%d")
        self.assertEqual(true_result, file_read[0])
        true_result = datetime.strptime("20240803", "%Y%m%d")
        self.assertEqual(true_result, file_read[-1])

        file_read = sr3_file.get_days("well")
        true_result = 30.
        self.assertEqual(true_result, file_read[0])
        true_result = 2162.
        self.assertEqual(true_result, file_read[-1])

        file_read = sr3_file.get_days("grid")
        true_result = [0., 30.]
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3_file.day2date(day=735.)
        true_result = datetime.strptime("20200906", "%Y%m%d")
        self.assertEqual(true_result, file_read)

        file_read = sr3_file.day2date(day=[735.])
        true_result = [datetime.strptime("20200906", "%Y%m%d")]
        _test_equal_lists(self, true_result, file_read)

        file_read = sr3_file.date2day(date=datetime.strptime("20200906", "%Y%m%d"))
        true_result = 735.
        self.assertEqual(true_result, file_read)

        file_read = sr3_file.date2day(date=[datetime.strptime("20200906", "%Y%m%d")])
        true_result = [735.]
        _test_equal_lists(self, true_result, file_read)

    def test_read_element_hierarchy(self):
        """Tests reading element hierarchy"""

        test_file = Path(r".\tests\sr3\base_case_3a.sr3").resolve()
        sr3_file = sr3reader.Sr3Reader(test_file)

        file_read = sr3_file.get_parent(element_type="group", element_name="I-PLAT1-PRO")
        true_result = "PLAT1-PRO"
        self.assertEqual(true_result, file_read)

        file_read = sr3_file.get_parent(element_type="layer", element_name="P13{28,24,48}")
        true_result = "P13"
        self.assertEqual(true_result, file_read)

        file_read = sr3_file.get_parent(element_type="well", element_name="P13")
        true_result = "P-PLAT1-PRO"
        self.assertEqual(true_result, file_read)

        file_read = sr3_file.get_connection(element_type="layer", element_name="I11{31,10,76}")
        true_result = 99
        self.assertEqual(true_result, file_read)

    def test_read_grid_size(self):
        """Tests reading grid sizes"""

        test_file = Path(r".\tests\sr3\base_case_3a.sr3").resolve()
        sr3_file = sr3reader.Sr3Reader(test_file)

        file_read = sr3_file.get_grid_size()
        true_result = (47, 39, 291)
        self.assertEqual(true_result, file_read)

        file_read = sr3_file.get_active_cells()
        true_result = 67241
        self.assertEqual(true_result, file_read)

    def test_read_timeseries(self):
        """Tests reading timeseries"""

        test_file = Path(r".\tests\sr3\base_case_3a.sr3").resolve()
        sr3_file = sr3reader.Sr3Reader(test_file)

        file_read = sr3_file.get_data(element_type="well",
                                      property_names="BHP",
                                      element_names="P11",
                                      days=[30., 1085., 2162.])
        true_result = [60627.83967735492 / 98.0665,
                       55779.152843383265 / 98.0665,
                       52595.77029111726 / 98.0665]
        _test_equal_lists(self, true_result, list(file_read[:,1]))

        sr3_file.set_alias(previous_property="OILRATSC",
                           new_property="QO",
                           check_exists=False)
        file_read = sr3_file.get_data(element_type="well",
                                      property_names=["QO","BHP"],
                                      element_names=["P14","P11"],
                                      days=[30., 1085., 2162.])
        true_result = [0.0,
                       6325.951742655704,
                       4247.476791690085]
        _test_equal_lists(self, true_result, list(file_read[:,1]))
        true_result = [62718.11721660964 / 98.0665,
                       47094.053970322144 / 98.0665,
                       45799.42941685654 / 98.0665]
        _test_equal_lists(self, true_result, list(file_read[:,2]))
        true_result = [6246.5344882818345,
                       7404.518299614956,
                       6078.931879073354]
        _test_equal_lists(self, true_result, list(file_read[:,3]))
        true_result = [60627.83967735492 / 98.0665,
                       55779.152843383265 / 98.0665,
                       52595.77029111726 / 98.0665]
        _test_equal_lists(self, true_result, list(file_read[:,4]))

        file_read = sr3_file.get_data(element_type="group",
                                      property_names=["NP"],
                                      element_names=["PLAT1-PRO"],
                                      days=[(2.*1001.0+1008.99)/3.])
        true_result = (2.*166546.69278864737+241094.6563692809)/3.
        self.assertEqual(round(true_result,2), round(list(file_read[:,1])[0],2))

        sr3_file.set_current_unit(dimensionality="well liquid volume", unit="MMbbl")
        file_read = sr3_file.get_data(element_type="group",
                                      property_names=["NP"],
                                      element_names=["PLAT1-PRO"],
                                      days=[(2.*1001.0+1008.99)/3.])
        self.assertEqual(round(true_result * 6.2898108E-6,2), round(list(file_read[:,1])[0],2))

        file_read = sr3_file.get_series_order(property_names=["QO","BHP"],
                                      element_names=["P14","P11"])
        true_result = [
            ("P14", "QO"),
            ("P14", "BHP"),
            ("P11", "QO"),
            ("P11", "BHP"),
        ]
        _test_equal_lists(self, true_result, file_read)

    def test_read_gridmaps(self):
        """Tests reading grid properties"""

        test_file = Path(r".\tests\sr3\base_case_3a.sr3").resolve()
        sr3_file = sr3reader.Sr3Reader(test_file)

        file_read = sr3_file.get_grid_data(
            property_names="NET/GROSS",
            element_names="MATRIX",
            day=0.)
        for i in range(sr3_file.get_active_cells()):
            self.assertTrue(file_read[i] - 1 < 0.00001)

        file_read = sr3_file.get_grid_data(
            property_names="PRES",
            element_names="MATRIX",
            day=30.)
        file_read_list = list(file_read[:10,0])
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
            self.assertTrue(abs(round(true_result[i], 2) - round(file_read_list[i],2)) < 0.01)

        file_read = sr3_file.get_data(
            element_type="grid",
            property_names=["PRES","SO"],
            element_names="MATRIX",
            days=30.)
        file_read_list = list(file_read[:10,0])
        for i in range(10):
            self.assertTrue(abs(round(true_result[i], 2) - round(file_read_list[i],2)) < 0.01)


        file_read = sr3_file.get_grid_data(
            property_names=["SO","PRES","VISO","Z(CO2)"],
            element_names="MATRIX",
            day=10.)
        file_read_list = list(file_read[:10,2])
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
            self.assertTrue(abs(round(true_result[i], 4) - round(file_read_list[i],4)) < 1E-4)













if __name__ == "__main__":
    unittest.main()
