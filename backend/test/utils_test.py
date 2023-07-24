import unittest
import backend.utils as utils


class MyTestCase(unittest.TestCase):
    def test_encode_file_to_base64(self):
        input_file_name = "room.idf"
        output_file_name = "room_byte64.dat"

        output = open(utils.encode_file_to_base64(input_file_name, output_file_name), 'r')
        output_data = output.read()

        output.close()

        self.assertEqual(utils.encode_file_to_base64(input_file_name), output_data)

    def test_decode_from_base64(self):
        test_base64_file = open('tmp/test.dat', 'r')
        test_idf_file = open('tmp/test.idf', 'rb')

        test_base64_string = test_base64_file.read()
        test_idf_data = test_idf_file.read()

        test_idf_data = test_idf_data.decode('utf-8')

        test_base64_file.close()
        test_idf_file.close()

        decoded_data = utils.decode_from_base64_string(test_base64_string)

        self.assertEqual(test_idf_data, decoded_data)  # add assertion here


if __name__ == '__main__':
    unittest.main()
