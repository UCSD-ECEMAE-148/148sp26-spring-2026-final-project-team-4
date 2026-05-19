from setuptools import setup
import os
from glob import glob


package_name = 'ucsd_robocar_nav2_pkg'


def install_tree(source_root, destination_root):
    installed_files = []
    for root, _, files in os.walk(source_root):
        relative_root = os.path.relpath(root, source_root)
        destination_dir = os.path.join(destination_root, relative_root) if relative_root != '.' else destination_root
        for file_name in files:
            installed_files.append((destination_dir, [os.path.join(root, file_name)]))
    return installed_files


data_files = [
    ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
]
data_files.extend(install_tree('urdf', os.path.join('share', package_name, 'urdf')))
data_files.extend(install_tree(os.path.join('ros_data', 'maps'), os.path.join('share', package_name, 'ros_data', 'maps')))

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=data_files,
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='root@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)
