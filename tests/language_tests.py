from unittest import TestCase
import language

# path_to_itog_file = r'C:\Users\Antua\PycharmProjects\config3\testfile.txt'

class Random(TestCase):
    def test_massiv_detect(self):
        example = '["hello", "world", "TOML"]'
        self.assertEqual(language.parse_array(example), ['hello', 'world', 'TOML'])

    def test_massiv_detect_2(self):  # смешанный массив
        example = '[1, "text", true, [2, "nested"], true]'
        self.assertEqual(language.parse_array(example), [1, 'text', True, [2, 'nested'], True])

    def test_massiv_detect_3(self):  # "вложенный массив"
        example = '[[1, 2], ["a", "b"], [true, false]]'
        self.assertEqual(language.parse_array(example), [[1, 2], ['a', 'b'], [True, False]])

    def test_massiv_detect_4(self):  # "неверный массив"
        example = '[1, invalid, 2]'
        self.assertEqual(language.parse_array(example), None)

    def test_parse(self):
        example = ['[owner]', 'name = "Tom Preston-Werner"', 'dob = 1979-05-27T07:32:00Z', '[database]', 'enabled = '
                                                                                                         'true',
                   'ports = [8000, 8001, 8002]', 'data = [[1, 2, 3], ["a", "b", "c"], [true, false, true]]']

        self.assertEqual(language.parse(example), ({'database': {'data': [[1, 2, 3], ['a', 'b', 'c'], [True, False, True]],
               'enabled': True, 'ports': [8000, 8001, 8002]}, 'owner': {'dob': '1979-05-27T07:32:00Z', 'name': 'Tom Preston-Werner'}}, [], True))

    def test_parse_2(self):  # неправильный toml
        example = ['[owner]', 'name = "Alice"', '[owner]', 'name = "Bob"']
        self.assertEqual(language.parse(example), None)

