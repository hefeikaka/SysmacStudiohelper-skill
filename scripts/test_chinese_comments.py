import unittest
import xml.etree.ElementTree as E
from check_chinese_comments import style_errors,validate


class Checks(unittest.TestCase):
    def test_function_calls_have_inline_comments(self):
        self.assertEqual(style_errors('// ===== 内部入口 =====\n\nInputs(); // 处理输入\nPublish(); // 发送队列\n'), [])

    def test_literal_is_not_comment(self):
        self.assertIn('NO_INLINE_SIMPLE_STATEMENT_COMMENT', style_errors("// ===== 参数 =====\n\nx := '// 中文不是注释';\n"))

    def test_missing_sections(self):
        self.assertIn('NO_CHINESE_SECTION_TITLE',style_errors('x := 1; // 简单赋值'))

    def test_section_and_inline_style(self):
        self.assertEqual(style_errors('// ===== 一、初始化 =====\n\n// 清零状态\nx := 0; // 复位计数\n'),[])

    def test_missing_inline_simple_comment(self):
        self.assertIn('NO_INLINE_SIMPLE_STATEMENT_COMMENT',style_errors('// ===== 一、初始化 =====\n\n// 复位\nx := 0;\n'))

    def test_section_requires_blank_lines(self):
        self.assertIn('SECTION_SPACING: ST line 1',style_errors('// ===== 一、初始化 =====\nx := 0; // 复位\n'))

    def test_variable_documentation(self):
        root=E.fromstring('<Project xmlns="www.iec.ch/public/TC65SC65BWG7TF10"><Variable name="x"><Documentation>实际转矩，0.1%</Documentation></Variable><Member name="y"/></Project>')
        self.assertEqual(validate(root),['NO_CHINESE_VARIABLE_COMMENT: y'])


if __name__=='__main__':unittest.main()
