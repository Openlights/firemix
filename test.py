import unittest
import string

import core.mixer
import core.networking

import lib.pattern
import lib.color_fade
import lib.playlist
import lib.scene

divider = '------'


class TestExample(unittest.TestCase):

    def setUp(self):
        print divider
        print('Starting test: ' + self.id().split('.')[-2] + ' ' + self.id().split('.')[-1])
        print divider

    def tearDown(self):
        print divider
        print('Ending test: ' + self.id().split('.')[-2] + ' ' + self.id().split('.')[-1])
        print divider

    def test_example(self):
        self.assertTrue(True)


class TestScene(unittest.TestCase):
    def setUp(self):
        print divider
        print('Starting test: ' + self.id().split('.')[-2] + ' ' + self.id().split('.')[-1])
        print divider

    def tearDown(self):
        print divider
        print('Ending test: ' + self.id().split('.')[-2] + ' ' + self.id().split('.')[-1])
        print divider

    def test_extents(self):
        # TODO lib.scene.extents()
        pass

    def test_centerpoint(self):
        #TODO lib.scene.center_point()
        pass


class TestPlaylist(unittest.TestCase):
    def setUp(self):
        print divider
        print('Starting test: ' + self.id().split('.')[-2] + ' ' + self.id().split('.')[-1])
        print divider

    def tearDown(self):
        print divider
        print('Ending test: ' + self.id().split('.')[-2] + ' ' + self.id().split('.')[-1])
        print divider

    def test_slugify_changes_to_lowercase(self):
        test_chars = set([i for i in string.ascii_uppercase])
        print 'test_chars: '
        print test_chars
        test_string = lib.playlist.slugify('GHJK')
        print 'test_string: ' + test_string
        self.assertFalse(string_contains_characters(test_string, test_chars))
        self.assertEqual(test_string, 'ghjk')

    # TODO determine behavior expected
    # def test_slugify_changes_spaces_to_hyphens(self):
    #     test_chars = set([' '])
    #     test_string = lib.playlist.slugify('     ')
    #     print 'test_string: ' + test_string
    #     self.assertFalse(string_contains_characters(test_string, test_chars))
    #     self.assertEqual(test_string, '-----')

    def test_slugify_removes_nonalpha(self):
        test_string = lib.playlist.slugify('~!@#$%^&*()+=')
        print 'test_string: ' + test_string
        self.assertTrue(test_string.isalnum() or not test_string)

    #TODO test tabs and other whitespace handling
        #test_chars = set([i for i in string.whitespace])

if __name__ == "__main__":
    unittest.main()


def string_contains_characters(testString, set):
    """
    Tests if a given string contains any of the characters in the given set
    :param testString: string to test
    :param set: set of characters to check for the presence of in testString
    :return: True if characters are present in string; else False
    """
    for char in set:
        if char in testString:
            return True
    return False
