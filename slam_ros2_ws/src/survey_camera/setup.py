from setuptools import find_packages, setup

package_name = 'survey_camera'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fzc17',
    maintainer_email='kennethubert17@gmai.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "camera_node = survey_camera.camera_node:main",
            "web_bridge = survey_camera.web_bridge_node:main",
        ],
    },
)
