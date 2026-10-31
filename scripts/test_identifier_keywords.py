import unittest
import xml.etree.ElementTree as E
from check_identifier_conflicts import validate,N

class IdentifierKeywords(unittest.TestCase):
    def test_native_reported_step_declaration_is_rejected(self):
        for name in ('Step','STEP','step'):
            with self.subTest(name=name):
                root=E.Element(N+'Project');E.SubElement(root,N+'Variable',name=name)
                self.assertIn('RESERVED_KEYWORD_NAME: '+name,validate(root))

    def test_descriptive_identifiers_remain_legal(self):
        root=E.Element(N+'Project')
        for name in ('SimState','StepIndex','StartStep'):
            E.SubElement(root,N+'Variable',name=name)
        self.assertEqual([],validate(root))

if __name__=='__main__':unittest.main()
