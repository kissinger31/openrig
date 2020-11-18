import unittest
import os
import shutil
import sun_module


class TestModule(unittest.TestCase):
    def setUp(self):
        self.root = os.path.join(os.path.dirname(__file__), '__temp_test_data')
        print("Creating local temp folder", self.root)
        try:
            os.mkdir(self.root)
        except OSError:
            pass

    def tearDown(self):
        if os.path.exists(self.root):
            print("Removing local temp folder and data", self.root)
            shutil.rmtree(self.root)

    def test_something(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
