import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from expand_devices import expand
from inspect_project import inspect

class InitialTests(unittest.TestCase):
    def test_cylinder_defaults(self):
        d = expand({'devices': [{'name':'Cyl01','kind':'cylinder'}]})['devices'][0]
        self.assertEqual(d['inputs'], ['HomeSensor','WorkSensor'])
        self.assertEqual(d['outputs'], ['HomeValve','WorkValve'])
        self.assertEqual(d['process_steps_owner'], 'program_section')

    def test_arrival_no_clear_or_delay(self):
        d = expand({'devices':[{'name':'B1','kind':'belt'}]})['devices'][0]
        self.assertFalse(d['wait_sensor_clear_before_next_action'])
        self.assertIsNone(d['stop_delay'])

    def test_explicit_overrides_win(self):
        d = expand({'devices':[{'name':'C1','kind':'cylinder','overrides':{
            'valve':'single_coil','inputs':['HomeSensor'],'outputs':['WorkValve']}}]})['devices'][0]
        self.assertEqual(d['outputs'], ['WorkValve'])

    def test_duplicate_names_rejected(self):
        with self.assertRaises(ValueError):
            expand({'devices':[{'name':'A','kind':'belt'},{'name':'A','kind':'cylinder'}]})

    def test_project_inventory_preserves_source_and_hierarchy(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'example.smc2'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('tree.oem','<Root><Entity Name="Program"><Entity Name="Section"/></Entity></Root>')
                z.writestr('block.xml','<Root><EncryptedFile>opaque</EncryptedFile></Root>')
                z.writestr('../not-extracted.xml','<Root/>')
            original=p.read_bytes(); r=inspect(p)
            self.assertEqual(r['entities'][1]['ancestor_entities'][0]['Name'],'Program')
            self.assertTrue(r['xml_inventory'][1]['protected'])
            self.assertEqual(p.read_bytes(),original)
            self.assertEqual(r['sha256'],hashlib.sha256(original).hexdigest())
            self.assertFalse((Path(directory).parent/'not-extracted.xml').exists())

    def test_size_limit_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'example.smc'
            with zipfile.ZipFile(p,'w') as z:z.writestr('a.xml','<Root>'+('x'*100)+'</Root>')
            self.assertEqual(inspect(p,max_bytes=10)['xml_inventory'][0]['status'],'skipped_size_limit')

if __name__=='__main__':unittest.main()
