import unittest
import xml.etree.ElementTree as ET
from check_fb_scope import validate, NS


def model(global_fb=False, body='Unit(Data => Snapshot); x := Snapshot.Value;'):
    root = ET.fromstring('''<Project xmlns="www.iec.ch/public/TC65SC65BWG7TF10">
    <Types><GlobalNamespace><FunctionBlock name="Sampler"><Parameters><OutputVars>
    <Variable name="Data"><Type><TypeName>Frame</TypeName></Type></Variable>
    </OutputVars></Parameters></FunctionBlock><Program name="Acquire"><Vars>
    <Variable name="Unit"><Type><InstantlyDefinedType><BaseType><TypeName>Sampler</TypeName>
    </BaseType></InstantlyDefinedType></Type></Variable></Vars><ST/></Program></GlobalNamespace></Types>
    <Instances><GlobalVars><Variable name="Shared"><Type><InstantlyDefinedType><BaseType>
    <TypeName>Frame</TypeName></BaseType></InstantlyDefinedType></Type></Variable></GlobalVars></Instances></Project>''')
    root.find('.//'+NS+'ST').text = body
    if global_fb:
        root.find('.//'+NS+'GlobalVars//'+NS+'TypeName').text = 'Sampler'
    return root


class Checks(unittest.TestCase):
    def test_local_fb_array_and_shared_data_allowed(self):
        self.assertEqual(validate(model()), [])

    def test_global_fb_array_rejected(self):
        self.assertEqual(validate(model(True)), ['GLOBAL_FB: Shared'])

    def test_nested_struct_output_rejected(self):
        self.assertTrue(validate(model(body='x := Unit[2].Data.Value;')))

    def test_array_output_rejected(self):
        self.assertTrue(validate(model(body='x := Unit.Data[2];')))

    def test_whole_output_and_comments_allowed(self):
        self.assertEqual(validate(model(body="Snapshot := Unit[2].Data; (* Unit.Data[2] *) // Unit.Data.X\n s := 'Unit.Data[2]';")), [])


if __name__ == '__main__':
    unittest.main()
