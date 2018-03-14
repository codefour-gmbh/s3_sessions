import time
import os

from cherrypy.lib.sessions import FileSession
from s3_sessions.sessions import S3Session

if __name__ == '__main__':
    path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(path, '..', 'sessions')

    host = 'https://ds11s3.swisscom.com'
    bucket = 'easyasset-data'
    key = 'sessions-test'

    iterations = 10

    print('Setup FileSession')
    FileSession.setup(storage_path=path, clean_freq=0)
    fileSession = FileSession(storage_path=path)

    print('Setup S3Session')
    S3Session.setup(storage_bucket=bucket,
                    storage_path=key,
                    s3_host=host,
                    clean_freq=0)
    s3Session = S3Session()

    print('Lock FileSession')
    fileSession.acquire_lock()
    start = time.time()
    print('Start FileSession.load() at {}'.format(start))
    for i in range(iterations):
        fileSession.load()

    print('Release FileSession')
    fileSession.release_lock()
    end = time.time()
    print('File load x {0}: {1} seconds'.format(iterations, end - start))

    print('Lock S3Session')
    s3Session.acquire_lock()
    start = time.time()
    print('Start S3Session.load() at {}'.format(start))
    for i in range(iterations):
        s3Session.load()

    print('Release FileSession')
    s3Session.release_lock()
    end = time.time()
    print('S3 load x {0}: {1} seconds'.format(iterations, end - start))

    start = time.time()
    print('Start FileSession.save() at {}'.format(start))
    for i in range(iterations):
        fileSession.acquire_lock()
        fileSession.save()
        fileSession.release_lock()

    end = time.time()
    print('File save x {0}: {1} seconds'.format(iterations, end - start))

    start = time.time()
    print('Start S3Session.save() at {}'.format(start))
    for i in range(iterations):
        s3Session.acquire_lock()
        s3Session.save()
        s3Session.release_lock()

    end = time.time()
    print('S3 save x {0}: {1} seconds'.format(iterations, end - start))
