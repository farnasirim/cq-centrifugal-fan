from setuptools import setup, find_packages


name = "cq_centrifugal_fan"
desc = "Parametric centrifugal fan builder in CadQuery"

setup(
    name=name,
    version='0.1.0',
    author='farnasirim',
    author_email='farnasirim@gmail.com',
    description=desc,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/farnasirim/cq-centrifugal-fan',
    packages=find_packages(exclude=('tests', 'scripts')),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
