import unittest
import xml.etree.ElementTree as E
from check_identifier_conflicts import validate

def root(body):
    return E.fromstring('<Project xmlns="www.iec.ch/public/TC65SC65BWG7TF10">'+body+'</Project>')

class Checks(unittest.TestCase):
    def test_native_failures(self):
        r=root('<Variable name="MQTT"/><Variable name="Limit"/><TypeName>mqtt\\Client_v2_0</TypeName>')
        self.assertEqual(validate(r),['INSTRUCTION_NAME_CONFLICT: Limit','NAMESPACE_NAME_CONFLICT: MQTT'])
    def test_case_insensitive(self):
        self.assertEqual(validate(root('<Variable name="lImIt"/><Variable name="MqTt"/>'),['mqtt']),['INSTRUCTION_NAME_CONFLICT: lImIt','NAMESPACE_NAME_CONFLICT: MqTt'])
    def test_specific_names_pass(self):
        self.assertEqual(validate(root('<Variable name="MqttTransport"/><Variable name="ReplayLimit"/><TypeName>mqtt\\Client_v2_0</TypeName>')),[])
    def test_comments_and_type_names_not_declarations(self):
        self.assertEqual(validate(root('<Variable name="Port"><Documentation>MQTT Limit</Documentation><TypeName>LIMIT</TypeName></Variable>')),[])
    def test_system_prefix_local_and_pin(self):
        r=root('<Vars><Variable name="P_AxisCount"/></Vars><Parameters><InputVars><InterfaceVariable name="p_Reset"/></InputVars></Parameters>')
        self.assertEqual(validate(r),['RESERVED_SYSTEM_PREFIX: P_AxisCount','RESERVED_SYSTEM_PREFIX: p_Reset'])
    def test_system_reference_is_not_user_declaration(self):
        self.assertEqual(validate(root('<ExternalVars><Variable name="P_First_Run"/></ExternalVars>')),[])
    def test_member_and_safe_argument_name(self):
        self.assertEqual(validate(root('<Member name="P_Test"/><Variable name="ArgAxisCount"/>')),['RESERVED_SYSTEM_PREFIX: P_Test'])
    def test_prefix_only(self):
        self.assertEqual(validate(root('<Variable name="PM_Value"/><Variable name="Map_Position"/><Variable name="ArgReset"><Documentation>P_Reset</Documentation></Variable>')),[])
    def test_pou_and_type_names(self):
        self.assertEqual(validate(root('<FunctionBlock name="P_Block"/><DataTypeDecl name="p_Data"/>')),['RESERVED_SYSTEM_PREFIX: P_Block','RESERVED_SYSTEM_PREFIX: p_Data'])

if __name__=='__main__':unittest.main()
