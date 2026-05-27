from glob import glob

from setuptools import find_packages, setup

package_name = 'mission_bridge'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/mission_bridge']),
        ('share/mission_bridge', ['package.xml']),
        ('share/mission_bridge/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='evanc',
    maintainer_email='evan.chou@live.com',
    description='Mission bridge nodes: image capture, path recorder, mission trigger.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'image_capture_node = mission_bridge.image_capture_node:main',
            'path_recorder_node = mission_bridge.path_recorder_node:main',
            'mission_trigger_node = mission_bridge.mission_trigger_node:main',
        ],
    },
)
