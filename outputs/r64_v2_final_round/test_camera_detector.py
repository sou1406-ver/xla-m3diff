import unittest
from camera_detector import camera_motion_claim

class CameraDetectorRegression(unittest.TestCase):
    def test_device_exclusions(self):
        captions=[
            'The camera in the center of the scene has become larger.',
            'The black camera on the left side of the table has moved to the right. The blue cup in the center of the table has moved to the left.',
            'A black camera has been added.',
            'The camera on the table has moved to the right.',
            'The security camera has rotated clockwise.',
            'A person is facing the camera.',
            'The digital camera is no longer present.',
        ]
        for s in captions:
            with self.subTest(s=s):self.assertFalse(camera_motion_claim(s))

    def test_camera_motion_and_mixed_sentences(self):
        captions=[
            'The camera has zoomed in, making objects appear larger.',
            'The shooting perspective has slightly shifted to the left.',
            'The camera has rotated slightly clockwise.',
            'The camera angle has changed.',
            'The field of view has become wider.',
            'A black camera was added and the viewpoint has changed.',
            'The security camera is missing. The camera has panned to the left.',
            'The camera on the table has moved, while the shooting perspective has zoomed out.',
        ]
        for s in captions:
            with self.subTest(s=s):self.assertTrue(camera_motion_claim(s))

if __name__=='__main__':unittest.main()
