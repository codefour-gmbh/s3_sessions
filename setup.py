from distutils.core import setup

VERSION = '0.0.1'

setup(
    name='s3_sessions',
    version=VERSION,
    description='A S3 based backend for CherryPy sessions',
    url='https://github.com/codefour-gmbh/s3_sessions',
    author='Christoph Russ',
    author_email='christoph@codefour.ch',
    install_requires=['cherrypy >= 5.0.1', 'boto3 >= 1.6.0'],
    packages=['s3_sessions']
)
