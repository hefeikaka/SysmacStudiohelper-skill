import copy
import unittest
from check_wire_layout import validate

class WireLayoutTests(unittest.TestCase):
    def setUp(self):
        self.packet={'topic':'test','fixed_bytes':10,'fields':[
            {'name':'id','type':'UINT','count':1,'offset':0,'bytes':2},
            {'name':'value','type':'ULINT','count':1,'offset':2,'bytes':8}]}
    def test_valid(self):
        self.assertEqual(validate(self.packet,10),[])
    def test_capacity(self):
        self.assertTrue(validate(self.packet,9))
    def test_overlap(self):
        self.packet['fields'][1]['offset']=1
        self.assertTrue(validate(self.packet))
    def test_wrong_64bit_width(self):
        self.packet['fields'][1]['bytes']=4
        self.assertTrue(validate(self.packet))
    def test_dimensions(self):
        self.packet['fields'][1]['dimensions']=[2,4]
        self.assertTrue(validate(self.packet))
    def test_duplicate(self):
        self.packet['fields'][1]['name']='id'
        self.assertTrue(validate(self.packet))

if __name__=='__main__': unittest.main()
