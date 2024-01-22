import unittest
from app.services.analyzer import file_metadata

class TestAnalyzer(unittest.TestCase):
    def test_file_metadata(self):
        # Assuming there's a known file for testing
        test_filepath = './app/services/analyzer.py'
        metadata = file_metadata(test_filepath)
        self.assertIn('file_size', metadata)
        self.assertIn('created_at', metadata)
        self.assertIn('modified_at', metadata)

# Additional tests would be written similarly

if __name__ == '__main__':
    unittest.main()
