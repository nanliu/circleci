import unittest

import circleci.utils

class TestUtils(unittest.TestCase):
    def test_digests_to_custom_values(self):
        custom_values = circleci.utils.digests_to_custom_values('test-files/test-values.yaml',
                                                                'test-files/image-versions.log')
        self.assertEqual(
            custom_values,
            '{ "mongo": {"repo": "mongo@sha256","tag": "fa24030aec1989c1df5440562282891b95a92e00e28ed05332e8f0270efe34d1"},"mysql": {"repo": "mysql@sha256","tag": "967a8020398f76f99ba74144e6e661f46003c685192b83d7bb87d026562319ae"} }'
        )
