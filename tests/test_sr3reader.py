"""
sr3reader module tests
"""

from pathlib import Path
from collections import Counter
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
        error_list.append(f"Missing: {','.join(missing)}")
    if len(surplus) > 0:
        error_list.append(f"Surplus: {','.join(surplus)}")
    error_msg = " ".join(error_list)

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
        file_read = (
            sr3_file._component_list.values()  # pylint: disable=protected-access
        )
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


if __name__ == "__main__":
    unittest.main()
