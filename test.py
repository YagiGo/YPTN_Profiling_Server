from requests import get, put
from urllib.parse import quote_plus, unquote_plus
import unittest
import uuid
class RESTfulAPITest(unittest.TestCase):
    def test_input_output_urls(self):
        test_sets = ['http://www.example.com',
                     'https://www.example.com']
        for test_url in test_sets:
            put('http://localhost:5000/input_urls/' + quote_plus(test_url, encoding='utf-8'), {"data": test_url})

            expected_result = {
                str(uuid.uuid3(name=quote_plus(test_url.replace('.', ''), encoding='utf-8'), namespace=uuid.NAMESPACE_OID)):test_url
            }
            self.assertSetEqual(expected_result[str(uuid.uuid3(name=quote_plus(test_url, encoding='utf-8'), namespace=uuid.NAMESPACE_OID))],
                                put('http://localhost:5000/input_urls/'+quote_plus(test_url.replace('.', ''), encoding='utf-8'),{"data":test_url}).json()
                                [str(uuid.uuid3(name=quote_plus(test_url, encoding='utf-8'), namespace=uuid.NAMESPACE_OID))])

if __name__ == "__main__":
    unittest.main()