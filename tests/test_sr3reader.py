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
    error_msg = f"Missing elements: {', '.join(missing)}; surplus: {', '.join(surplus)}"

    if partial_true_result:
        self.assertEqual(missing, [], error_msg)
    else:
        self.assertTrue(have_same_elements(file_read, true_result),error_msg)
class TestSr3Reader(unittest.TestCase):
    """Tests Sr3Reader functionalities"""

    def test_read_elements(self):
        """Tests reading the elements of a file"""

        test_file = Path(r'.\tests\sr3\base_case_3a.sr3').resolve()
        sr3_file = sr3reader.Sr3Reader(test_file)

        true_result = ['I11', 'I11-W', 'I12', 'I12-W', 'I13', 'I13-W',
                       'I14', 'I14-W', 'I15', 'I15-W', 'I16', 'I16-W',
                       'I17', 'I17-W',
                       'P11', 'P12', 'P13', 'P14', 'P15', 'P16']
        file_read = sr3_file.get_elements('well').keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = ['Default-Group-PRO','Default-Group-INJ',
                       'FIELD-PRO','FIELD-INJ',
                       'I-PLAT1-PRO','I-PLAT1-INJ',
                       'I-PLAT-TLD-PRO','I-PLAT-TLD-INJ',
                       'P-PLAT1-PRO','P-PLAT1-INJ',
                       'P-PLAT-TLD-PRO','P-PLAT-TLD-INJ',
                       'PLAT1-PRO','PLAT1-INJ',
                       'PLAT-TLD-PRO','PLAT-TLD-INJ']
        file_read = sr3_file.get_elements('group').keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = ['FIELD']
        file_read = sr3_file.get_elements('sector').keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = ['P11{23,25,49}','I11{31,10,40}','P12{12,31,36}','P13{28,24,48}',
                       'P14{36,17,34}','P15{23,20,40}','P16{13,14,41}',
                       'I12{14,18,43}','I13{26,14,36}','I14{23,10,42}','I15{38,9,24}',
                       'I16{12,22,42}','I17{7,26,41}',
                       'I11-W{31,10,40}','I12-W{14,18,43}','I13-W{26,14,36}','I14-W{23,10,42}',
                       'I15-W{38,9,24}','I16-W{12,22,42}','I17-W{7,26,41}']
        file_read = sr3_file.get_elements('layer').keys()
        _test_equal_lists(self, true_result, file_read, True)

        true_result = ['MATRIX']
        file_read = sr3_file.get_elements('grid').keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = ['']
        file_read = sr3_file.get_elements('special').keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = ['CO2','N2 toCH4','C2HtoNC5','C6ttoC19','C29toC63', 'WATER']
        file_read = sr3_file._component_list.values() # pylint: disable=protected-access
        _test_equal_lists(self, true_result, file_read)

        print(f'File open calls: {sr3_file._open_calls}') # pylint: disable=protected-access

    def test_read_properties(self):
        """Tests reading the properties of a file"""

        test_file = Path(r'.\tests\sr3\base_case_3a.sr3').resolve()
        sr3_file = sr3reader.Sr3Reader(test_file)

        true_result = [
            'WELLSTATE','WELLOPMO','WHP','BHP','BLOCKP','MOBWTDATP','BHTEMP','WHTEMP',
            'ONFRAC','CGLIFT','OILVOLSC','GASVOLSC','WATVOLSC','INLVOLSC','WTGVOLSC',
            'OILVOLRC','GASVOLRC','WATVOLRC','BHFVOLRC','WELLOTIME','OILRATSC',
            'GASRATSC','WATRATSC','INLRATSC','WTGRATSC','OILRATRC','GASRATRC','WATRATRC',
            'BHFRATRC','LIQVOLSC','LIQRATSC','OILMOLSC','GASMOLSC','WTGMOLSC','OILMOLRSC',
            'GASMOLRSC','WTGMOLRSC',
            'OILCMOLSC(1)','OILCMOLSC(2)','OILCMOLSC(3)','OILCMOLSC(4)','OILCMOLSC(5)',
            'OILMOLRSC(1)','OILMOLRSC(2)','OILMOLRSC(3)','OILMOLRSC(4)','OILMOLRSC(5)',
            'GASCMOLSC(1)','GASCMOLSC(2)','GASCMOLSC(3)','GASCMOLSC(4)','GASCMOLSC(5)',
            'GASMOLRSC(1)','GASMOLRSC(2)','GASMOLRSC(3)','GASMOLRSC(4)','GASMOLRSC(5)',
            'INLCMOLSC(1)','INLCMOLSC(2)','INLCMOLSC(3)','INLCMOLSC(4)','INLCMOLSC(5)',
            'INLMOLRSC(1)','INLMOLRSC(2)','INLMOLRSC(3)','INLMOLRSC(4)','INLMOLRSC(5)',
            'WTGCMOLSC(1)','WTGCMOLSC(2)','WTGCMOLSC(3)','WTGCMOLSC(4)','WTGCMOLSC(5)',
            'WTGMOLRSC(1)','WTGMOLRSC(2)','WTGMOLRSC(3)','WTGMOLRSC(4)','WTGMOLRSC(5)',
            'OILCMASSC(1)','OILCMASSC(2)','OILCMASSC(3)','OILCMASSC(4)','OILCMASSC(5)',
            'OILMASRSC(1)','OILMASRSC(2)','OILMASRSC(3)','OILMASRSC(4)','OILMASRSC(5)',
            'GASCMASSC(1)','GASCMASSC(2)','GASCMASSC(3)','GASCMASSC(4)','GASCMASSC(5)',
            'GASMASRSC(1)','GASMASRSC(2)','GASMASRSC(3)','GASMASRSC(4)','GASMASRSC(5)',
            'INLCMASSC(1)','INLCMASSC(2)','INLCMASSC(3)','INLCMASSC(4)','INLCMASSC(5)',
            'INLMASRSC(1)','INLMASRSC(2)','INLMASRSC(3)','INLMASRSC(4)','INLMASRSC(5)',
            'WTGCMASSC(1)','WTGCMASSC(2)','WTGCMASSC(3)','WTGCMASSC(4)','WTGCMASSC(5)',
            'WTGMASRSC(1)','WTGMASRSC(2)','WTGMASRSC(3)','WTGMASRSC(4)','WTGMASRSC(5)',
            ]
        true_result = sr3_file._replace_components_property_list(true_result) # pylint: disable=protected-access
        file_read = sr3_file.get_properties('well').keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            'OILVOLSC','GASVOLSC','WATVOLSC','INLVOLSC','WTGVOLSC','OILVOLRC','GASVOLRC',
            'WATVOLRC','BHFVOLRC','OILRATSC','GASRATSC','WATRATSC','INLRATSC','WTGRATSC',
            'OILRATRC','GASRATRC','WATRATRC','BHFRATRC','VOIDRATRC','LIQVOLSC','LIQRATSC',
            'WELLOTIME','NOPWING','PMPRES','GIMPRES','WIMPRES','PSPRES','GISPRES','WISPRES',
            'ONFRAC','OILMOLSC','GASMOLSC','WTGMOLSC','OILMOLRSC','GASMOLRSC','WTGMOLRSC',
            'OILCMOLSC(1)','OILCMOLSC(2)','OILCMOLSC(3)','OILCMOLSC(4)','OILCMOLSC(5)',
            'OILMOLRSC(1)','OILMOLRSC(2)','OILMOLRSC(3)','OILMOLRSC(4)','OILMOLRSC(5)',
            'GASCMOLSC(1)','GASCMOLSC(2)','GASCMOLSC(3)','GASCMOLSC(4)','GASCMOLSC(5)',
            'GASMOLRSC(1)','GASMOLRSC(2)','GASMOLRSC(3)','GASMOLRSC(4)','GASMOLRSC(5)',
            'INLCMOLSC(1)','INLCMOLSC(2)','INLCMOLSC(3)','INLCMOLSC(4)','INLCMOLSC(5)',
            'INLMOLRSC(1)','INLMOLRSC(2)','INLMOLRSC(3)','INLMOLRSC(4)','INLMOLRSC(5)',
            'WTGCMOLSC(1)','WTGCMOLSC(2)','WTGCMOLSC(3)','WTGCMOLSC(4)','WTGCMOLSC(5)',
            'WTGMOLRSC(1)','WTGMOLRSC(2)','WTGMOLRSC(3)','WTGMOLRSC(4)','WTGMOLRSC(5)',
            'OILCMASSC(1)','OILCMASSC(2)','OILCMASSC(3)','OILCMASSC(4)','OILCMASSC(5)',
            'OILMASRSC(1)','OILMASRSC(2)','OILMASRSC(3)','OILMASRSC(4)','OILMASRSC(5)',
            'GASCMASSC(1)','GASCMASSC(2)','GASCMASSC(3)','GASCMASSC(4)','GASCMASSC(5)',
            'GASMASRSC(1)','GASMASRSC(2)','GASMASRSC(3)','GASMASRSC(4)','GASMASRSC(5)',
            'INLCMASSC(1)','INLCMASSC(2)','INLCMASSC(3)','INLCMASSC(4)','INLCMASSC(5)',
            'INLMASRSC(1)','INLMASRSC(2)','INLMASRSC(3)','INLMASRSC(4)','INLMASRSC(5)',
            'WTGCMASSC(1)','WTGCMASSC(2)','WTGCMASSC(3)','WTGCMASSC(4)','WTGCMASSC(5)',
            'WTGMASRSC(1)','WTGMASRSC(2)','WTGMASRSC(3)','WTGMASRSC(4)','WTGMASRSC(5)'
        ]
        true_result = sr3_file._replace_components_property_list(true_result) # pylint: disable=protected-access
        file_read = sr3_file.get_properties('group').keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            'OILSECSU','GASSECSU','WATSECSU','INLSECSU','OILSECRECO','GASSECRECO',
            'WATSECRECO','INLSECRECO','WAQCUMSEC','OILSECPRCM','WATSECPRCM','GASSECPRCM',
            'INLSECPRCM','WTGSECPRCM','WATSECINCM','GASSECINCM','OILSECPRRT','WATSECPRRT',
            'GASSECPRRT','INLSECPRRT','WTGSECPRRT','WATSECINRT','GASSECINRT','PVCUMSEC',
            'HPVCUMSEC','PRSCUMSEC','PHHCUMSEC','PDTVSEC','PTDCUMSEC','AVGTEMPSEC','OILSECRECU',
            'WATSECRECU','GASSECRECU','OILSECAVSA','WATSECAVSA','GASSECAVSA','OILMLPSC','GASMLPSC',
            'WTGMLPSC','INLMLPSC',
            'OILCMLPSC(1)','OILCMLPSC(2)','OILCMLPSC(3)','OILCMLPSC(4)','OILCMLPSC(5)',
            'GASCMLPSC(1)','GASCMLPSC(2)','GASCMLPSC(3)','GASCMLPSC(4)','GASCMLPSC(5)',
            'INLCMLPSC(1)','INLCMLPSC(2)','INLCMLPSC(3)','INLCMLPSC(4)','INLCMLPSC(5)',
            'WTGCMLPSC(1)','WTGCMLPSC(2)','WTGCMLPSC(3)','WTGCMLPSC(4)','WTGCMLPSC(5)',
            'GASCMLISC(1)','GASCMLISC(2)','GASCMLISC(3)','GASCMLISC(4)','GASCMLISC(5)',
            'OILMOLIP(1)','OILMOLIP(2)','OILMOLIP(3)','OILMOLIP(4)','OILMOLIP(5)',
            'GASMOLIP(1)','GASMOLIP(2)','GASMOLIP(3)','GASMOLIP(4)','GASMOLIP(5)',
            'INLMOLIP(1)','INLMOLIP(2)','INLMOLIP(3)','INLMOLIP(4)','INLMOLIP(5)',
            'OILCOMMOL(1)','OILCOMMOL(2)','OILCOMMOL(3)','OILCOMMOL(4)','OILCOMMOL(5)',
            'GASCOMMOL(1)','GASCOMMOL(2)','GASCOMMOL(3)','GASCOMMOL(4)','GASCOMMOL(5)',
            'AQUCOMMOL(1)','AQUCOMMOL(2)','AQUCOMMOL(3)','AQUCOMMOL(4)','AQUCOMMOL(5)','AQUCOMMOL(6)',
            'OILSECRECOO','GASSECRECOO','WATSECRECOO','INLSECRECOO'
        ]
        true_result = sr3_file._replace_components_property_list(true_result) # pylint: disable=protected-access
        file_read = sr3_file.get_properties('sector').keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = ['STATUS']
        file_read = sr3_file.get_properties('layer').keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            'ICSTBC', 'ICSTCG', 'ICSTGN', 'ICSTPS', 'ICSTPB', 'IPSTCS', 'IPSTBT',
            'IPSTAC', 'BLOCKDEPTH', 'BLOCKPVOL', 'BVOL', 'PERMI', 'PERMJ', 'PERMK',
            'TRMI', 'TRMJ', 'TRMK', 'TRLI', 'TRLJ', 'TRLK', 'BSWCRIT', 'BSGCRIT',
            'BSORW', 'BSORG', 'BSWCON', 'BSGCON', 'BSOIRW', 'BSOIRG', 'BSLCON',
            'BKRWIRO', 'BKROCW', 'BKRWRO', 'BKROCRW', 'PCWMAX', 'PCWSHF', 'BKRGCL',
            'BKROGCG', 'BKRGRL', 'BKROGCRG', 'PCGMAX', 'POR', 'NET/GROSS', 'MODBVOL',
            'KRSETN', 'SO', 'SG', 'SW', 'PRES', 'VISO', 'VISG', 'VISW', 'Z(1)'
        ]
        true_result = sr3_file._replace_components_property_list(true_result) # pylint: disable=protected-access
        file_read = sr3_file.get_properties('grid').keys()
        _test_equal_lists(self, true_result, file_read)

        true_result = [
            'ELTSCUM', 'ELTSRATE', 'TSTEPCUM', 'NCYCCUM', 'SOLITCUM', 'TSCUTCUM',
            'DELTIME', 'NCYCPTS', 'SOLITPN', 'MBERROR', 'AVGIMPL', 'MEMUSAGE'
        ]
        file_read = sr3_file.get_properties('special').keys()
        _test_equal_lists(self, true_result, file_read)

        print(f'File open calls: {sr3_file._open_calls}') # pylint: disable=protected-access

    def test_read_units(self):
        """Tests reading the units"""

        test_file = Path(r'.\tests\sr3\base_case_3a.sr3').resolve()
        sr3_file = sr3reader.Sr3Reader(test_file)

        true_result = {
            'time': 'day',
            'temperature': 'C',
            'pressure': 'kgf/cm2',
            'length': 'm',
            'property volume': 'm3',
            'permeability': 'md',
            'mass': 'kg',
            'molar mass': 'gmole',
            'viscosity': 'cp',
            'energy': 'J',
            'well liquid volume': 'm3',
            'well gas volume': 'm3',
            'well rate time': 'day',
            'interfacial tension': 'dyne/cm',
            'electrical current': 'A',
            'electrical power': 'J/day',
            'electrical potential': 'V',
            'electrical resistance': 'ohm',
            'electrical conductivity': 'S/m',
            'electrical energy': 'J',
            'temperature difference': 'C',
            'diffusion/dispersion coeff.': 'cm2/s',
            'concentration': 'kg/m3',
            'molar concentration': 'gmole/m3'
        }
        file_read = sr3_file.get_current_units()
        _test_equal_lists(self, true_result.keys(), file_read.keys())
        _test_equal_lists(self, true_result.values(), file_read.values())


if __name__ == '__main__':
    unittest.main()
