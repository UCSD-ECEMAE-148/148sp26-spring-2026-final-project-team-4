from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'mission_bridge'


def install_tree(source_root, destination_root):
    installed_files = []
    for root, _, files in os.walk(source_root):
        relative_root = os.path.relpath(root, source_root)
        if relative_root != '.':
            destination_dir = os.path.join(destination_root, relative_root)
        else:
            destination_dir = destination_root
        for file_name in files:
            installed_files.append((destination_dir, [os.path.join(root, file_name)]))
    return installed_files


data_files = [
    ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
]
data_files.extend(
    install_tree('resource', os.path.join('share', package_name, 'resource'))
)

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=data_files,
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
