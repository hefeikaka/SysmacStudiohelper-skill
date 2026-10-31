"""Boundary regressions, including the real 64-axis plus five-control failure."""
import unittest
import xml.etree.ElementTree as ET
from check_fb_limits import check_xml,check_iec,NS

class ParameterLimitsTests(unittest.TestCase):
    def source(self,inputs,outputs=0,inouts=0):
        groups=[('VAR_INPUT',inputs),('VAR_OUTPUT',outputs),('VAR_IN_OUT',inouts)]
        return 'FUNCTION_BLOCK Example\n'+''.join(g+'\n'+''.join(f'Value{i} : BOOL;\n' for i in range(n))+'END_VAR\n' for g,n in groups)+'//{st}\n// VAR_INPUT fake : BOOL; END_VAR\n//{end}\nEND_FUNCTION_BLOCK\n'

    def test_real_failure_first_overflow_axis60(self):
        flags=['UseAxisInputs','Restart','SettingsPreparedBySend','RequireFreshWindow','SuppressIdleSamples']
        s='FUNCTION_BLOCK Acquire\nVAR_INPUT\n'+''.join(f'{n}: BOOL;\n' for n in flags)+''.join(f'Axis{i:02}: _sAXIS_REF;\n' for i in range(1,65))+'END_VAR\nEND_FUNCTION_BLOCK'
        infos,errors=check_iec(s)
        self.assertEqual(infos[0]['counts']['VAR_INPUT'],69)
        self.assertEqual(errors[0]['firstOverLimit'],'Axis60')

    def test_64_allowed_65_rejected(self):
        self.assertFalse(check_iec(self.source(64))[1])
        self.assertTrue(check_iec(self.source(65))[1])

    def test_groups_are_independent(self):
        self.assertFalse(check_iec(self.source(64,64,64))[1])
        self.assertEqual(check_iec(self.source(1,65))[1][0]['group'],'VAR_OUTPUT')
        self.assertEqual(check_iec(self.source(1,0,65))[1][0]['group'],'VAR_IN_OUT')

    def test_array_is_one_pin_and_comments_do_not_count(self):
        s=self.source(1).replace('Value0 : BOOL;','Values : ARRAY[0..1000] OF PM_LargeStruct;')+'\n(* VAR_INPUT\nFake : BOOL; END_VAR *)'
        info,errors=check_iec(s)
        self.assertEqual(info[0]['counts']['VAR_INPUT'],1);self.assertFalse(errors)

    def test_eight_axes_five_controls_is_safe(self):
        self.assertFalse(check_iec(self.source(13))[1])

    def test_multiple_sections_xml_count_direct_variables(self):
        root=ET.Element(NS+'Project');fb=ET.SubElement(root,NS+'FunctionBlock',name='Example');p=ET.SubElement(fb,NS+'Parameters')
        for count in [32,33]:
            group=ET.SubElement(p,NS+'InputVars')
            for i in range(count):ET.SubElement(group,NS+'Variable',name=f'Input{i}')
        _,errors=check_xml(root);self.assertEqual(errors[0]['count'],65)

    def test_iec_comma_declarations(self):
        s='FUNCTION_BLOCK Example VAR_INPUT '+','.join(f'x{i}' for i in range(65))+': BOOL; END_VAR END_FUNCTION_BLOCK'
        self.assertEqual(check_iec(s)[1][0]['count'],65)

if __name__=='__main__':unittest.main()
