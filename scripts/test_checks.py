"""Regression tests for demonstrated export failures; no third-party dependencies."""
import copy
import unittest
import xml.etree.ElementTree as ET
from check_exports import check_aml, check_axis, check_bindings

class ExportTests(unittest.TestCase):
    def test_aml_misordered_interface(self):
        root = ET.fromstring('<CAEXFile SchemaVersion="2.15"><InternalElement Name="Tags"><SupportedRoleClass/><ExternalInterface Name="Sensor"/></InternalElement></CAEXFile>')
        self.assertFalse(check_aml(root)['passed'])
        parent = root[0]
        parent[:] = [parent[1], parent[0]]
        self.assertTrue(check_aml(root)['passed'])

    def test_aml_broken_endpoint(self):
        root = ET.fromstring('<CAEXFile SchemaVersion="2.15"><InternalElement ID="a"><ExternalInterface Name="p"/><InternalLink RefPartnerSideA="a:p" RefPartnerSideB="absent:p"/></InternalElement></CAEXFile>')
        self.assertFalse(check_aml(root)['passed'])
        root.find('.//InternalLink').set('RefPartnerSideB', 'a:p')
        self.assertTrue(check_aml(root)['passed'])

    def axis(self, speed='100'):
        root = ET.fromstring('<AxisSettings><Data><AxisSettings><AxisSetting/></AxisSettings></Data></AxisSettings>')
        a = root.find('.//AxisSetting')
        for name, value in dict(NexAxisName='ExampleAxis', NexAxisReducerUse='NotUse', NexAxisUnitsNumerator='1000', NexAxisUnitsDenominator='1', NexAxisMaxVelocity=speed, NexAxisStartVelocity='0', NexAxisMaxJogVelocity='50', NexAxisMaxAcceleration='500', NexAxisMaxDeceleration='500').items():
            ET.SubElement(a, name, CurrentValue=value)
        return root

    def test_axis_overflow(self):
        self.assertFalse(check_axis(self.axis('400000000'), 2147483647)['passed'])
        self.assertTrue(check_axis(self.axis(), 2147483647)['passed'])

    def test_axis_missing_limits(self):
        root = self.axis()
        a = root.find('.//AxisSetting')
        a.remove(a.find('NexAxisMaxVelocity'))
        self.assertFalse(check_axis(root, 2147483647)['passed'])

    def test_unknown_limit_is_reported(self):
        self.assertTrue(check_axis(self.axis())['warnings'])

    def test_no_assumed_reducer(self):
        root = self.axis()
        root.find('.//NexAxisReducerUse').set('CurrentValue', 'Use')
        self.assertFalse(check_axis(root, 2147483647)['passed'])

    def program(self):
        return ET.fromstring('<Project xmlns="www.iec.ch/public/TC65SC65BWG7TF10"><Types><GlobalNamespace><Program name="Motion"><ExternalVars constant="true"><Variable name="AxisFeed"><Type><TypeName>_sAXIS_REF</TypeName></Type></Variable></ExternalVars></Program></GlobalNamespace></Types></Project>')

    def contract(self, constant=True):
        return {'programs': {'Motion': {'AxisFeed': {'type': '_sAXIS_REF', 'constant': constant, 'at': '_MC_AX[2]'}}}}

    def test_bound_axis(self):
        self.assertTrue(check_bindings(self.program(), self.contract())['passed'])

    def test_missing_external(self):
        root = self.program()
        program = next(e for e in root.iter() if e.tag.endswith('}Program'))
        program.remove(program[0])
        self.assertFalse(check_bindings(root, self.contract())['passed'])

    def test_constant_default_mismatch(self):
        root = self.program()
        group = next(e for e in root.iter() if e.tag.endswith('}ExternalVars'))
        group.attrib.clear()
        self.assertFalse(check_bindings(root, self.contract())['passed'])
        # FALSE is valid when that is the actual target attribute: do not hardcode TRUE.
        self.assertTrue(check_bindings(root, self.contract(False))['passed'])

    def test_missing_binding_evidence(self):
        contract = self.contract()
        del contract['programs']['Motion']['AxisFeed']['at']
        self.assertFalse(check_bindings(self.program(), contract)['passed'])

if __name__ == '__main__':
    unittest.main()
