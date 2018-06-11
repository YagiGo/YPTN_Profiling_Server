from requests import get, put
from urllib.parse import quote_plus, unquote_plus
import unittest
import uuid
from urllib.parse import urlparse
class RESTfulAPITest(unittest.TestCase):
    def isSame(self, result1, result2):
        if result1 == result2:
            return True
        else:
            return False

    def test_input_output_urls(self):
        test_sets = ['https://www.yahoo.com']

        for test_url in test_sets:
            key = urlparse(test_url).netloc
            put('http://localhost:5000/input_urls/' + quote_plus(key, encoding='utf-8'), {"data": test_url})

            expected_result = {
                str(uuid.uuid3(name=quote_plus(key.replace('.', ''), encoding='utf-8'), namespace=uuid.NAMESPACE_OID)):test_url
            }
            # print(expected_result[str(uuid.uuid3(name=quote_plus(test_url, encoding='utf-8'), namespace=uuid.NAMESPACE_OID))])
            self.assertEqual(expected_result[str(uuid.uuid3(name=quote_plus(key.replace('.',''), encoding='utf-8'), namespace=uuid.NAMESPACE_OID))],
                                put('http://localhost:5000/input_urls/'+quote_plus(key.replace('.', ''), encoding='utf-8'),{"data":test_url}).json()
                                [str(uuid.uuid3(name=quote_plus(key.replace('.',''), encoding='utf-8'), namespace=uuid.NAMESPACE_OID))])

    def test_profiling(self):
        test_sets = ['https://www.google.com']
        for test_url in test_sets:
            key = urlparse(test_url).netloc
            put('http://localhost:5000/input_urls/' + quote_plus(key, encoding='utf-8'), {"data": test_url})
            self.assertEqual(1,put('http://localhost:5000/profiling/' + quote_plus(key, encoding='utf-8'),
                                                                                                {"data":test_url}))





if __name__ == "__main__":
        unittest.main()