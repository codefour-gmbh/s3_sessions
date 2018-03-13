import cherrypy
import boto3
import botocore
import os
import io
import time

import six
from six.moves import cPickle as pickle

from cherrypy.lib.sessions import Session
from cherrypy.lib import locking


class S3Session(Session):
    """
    Implementation of a S3 based backend for CherryPy sessions

    storage_bucket
        The s3 bucket where the session will be stored.
    storage_path
        The path inside the s3 bucket where the session will be stored.
        If empty ('' == default), sessions will be stored directly inside the s3 bucket.
    lock_timeout
        A timedelta or numeric seconds indicating how long
        to block acquiring a lock. If None (default), acquiring a lock
        will block indefinitely.
    """

    SESSION_PREFIX = 'session-'
    LOCK_SUFFIX = '.lock'
    pickle_protocol = pickle.HIGHEST_PROTOCOL

    def __init__(self, id=None, **kwargs):
        # The 'storage_bucket' arg is required for file-based sessions.
        if 'storage_bucket' not in kwargs:
            raise KeyError("Missing 'storage_bucket' input in S3Session backend")
        kwargs.setdefault('storage_path', '')
        kwargs.setdefault('lock_timeout', None)
        kwargs.setdefault('s3_host', None)
        kwargs.setdefault('s3_access_key', None)
        kwargs.setdefault('s3_access_secret', None)

        Session.__init__(self, id=id, **kwargs)

        # validate self.lock_timeout
        if isinstance(self.lock_timeout, (int, float)):
            self.lock_timeout = datetime.timedelta(seconds=self.lock_timeout)
        if not isinstance(self.lock_timeout, (datetime.timedelta, type(None))):
            raise ValueError(
                'Lock timeout must be numeric seconds or a timedelta instance.'
            )

        # boto3 client vs resource ...
        self.s3 = boto3.resource('s3', endpoint_url=kwargs['s3_host'],
                                 aws_access_key_id=kwargs['s3_access_key'],
                                 aws_secret_access_key=kwargs['s3_access_secret'])
        self.bucket = self.s3.Bucket(kwargs['storage_bucket'])

    @classmethod
    def setup(cls, **kwargs):
        """Set up the storage system for s3-based sessions.

        This should only be called once per process; this will be done
        automatically when using sessions.init (as the built-in Tool does).
        """
        # The 'storage_bucket' arg is required for file-based sessions.
        if 'storage_bucket' not in kwargs:
            raise KeyError("Missing 'storage_bucket' input in S3Session backend")

        for k, v in kwargs.items():
            setattr(cls, k, v)

    def _get_file_path(self):
        f = os.path.join(self.storage_path, self.SESSION_PREFIX + self.id)
        # if f.startswith('/'):
        #     raise cherrypy.HTTPError(400, 'Invalid session id in cookie.')
        return f

    def _exists(self):
        path = self._get_file_path()
        try:
            self.s3.Object(self.storage_bucket, path).load()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                # The object does not exist.
                return False
            else:
                raise e
        # The object does exist
        return True

    def _load(self, path=None):
        assert self.locked, ('The session load without being locked.  '
                             "Check your tools' priority levels.")
        if path is None:
            path = self._get_file_path()
        try:
            content = self.s3.Object(self.storage_bucket, path).get()['Body'].read()
            return pickle.loads(content)
        except botocore.exceptions.ClientError as e:
            if self.debug:
                cherrypy.log('Error loading the session pickle: %s' %
                             e, 'TOOLS.SESSIONS')
            return None

    def _save(self, expiration_time):
        assert self.locked, ('The session was saved without being locked.  '
                             "Check your tools' priority levels.")
        try:
            # f = io.StringIO(contents)
            pickled_data = pickle.dumps((self._data, expiration_time), self.pickle_protocol)
            self.bucket.put_object(Key=self._get_file_path(), Body=pickled_data)
        except botocore.exceptions.ClientError as e:
            if self.debug:
                cherrypy.log('Error saving the session pickle: %s' %
                             e, 'TOOLS.SESSIONS')
            raise e

    def _delete(self):
        assert self.locked, ('The session deletion without being locked.  '
                             "Check your tools' priority levels.")
        try:
            s3.Object(self.storage_bucket, self._get_file_path()).delete()
        except botocore.exceptions.ClientError as e:
            if self.debug:
                cherrypy.log('Error deleting the session: %s' %
                             e, 'TOOLS.SESSIONS')
            raise e

    def acquire_lock(self, path=None):
        """Acquire an exclusive lock on the currently-loaded session data."""
        if path is None:
            path = self._get_file_path()
        path += self.LOCK_SUFFIX
        checker = locking.LockChecker(self.id, self.lock_timeout)
        while not checker.expired():
            try:
                self.s3.Object(self.storage_bucket, path).load()
            except botocore.exceptions.ClientError as e:
                # explcitly chek for 404 error? e.g. if e.response['Error']['Code'] == "404":
                time.sleep(0.1)
            else:
                self.lock = path
                self.bucket.put_object(Key=path, Body='')
                break
        self.locked = True
        if self.debug:
            cherrypy.log('Lock acquired.', 'TOOLS.SESSIONS')

    def release_lock(self, path=None):
        """Release the lock on the currently-loaded session data."""
        try:
            # TODO: test this ..?!
            # if path is None:
            #     path = self.lock
            # else:
            #     path += self.LOCK_SUFFIX
            s3.Object(self.storage_bucket, self.lock).delete()
        except botocore.exceptions.ClientError as e:
            if self.debug:
                cherrypy.log('Error releaseing the session lock: %s' %
                             e, 'TOOLS.SESSIONS')
            # rather raise this ??
            pass
        self.locked = False

    def clean_up(self):
        """Clean up expired sessions."""
        now = self.now()
        # Iterate over all session files in self.storage_path
        for fname in list(self.bucket.objects.filter(Prefix=self.storage_path)):
            have_session = (
                self.SESSION_PREFIX in fname and
                self.LOCK_SUFFIX not in fname
            )
            if have_session:
                # We have a session file: lock and load it and check
                #   if it's expired. If it fails, nevermind.
                path = fname # os.path.join(self.storage_path, fname)
                self.acquire_lock(path)
                if self.debug:
                    # This is a bit of a hack, since we're calling clean_up
                    # on the first instance rather than the entire class,
                    # so depending on whether you have "debug" set on the
                    # path of the first session called, this may not run.
                    cherrypy.log('Cleanup lock acquired.', 'TOOLS.SESSIONS')

                try:
                    contents = self._load(path)
                    # _load returns None on IOError
                    if contents is not None:
                        data, expiration_time = contents
                        if expiration_time < now:
                            # Session expired: deleting it
                            s3.Object(self.storage_bucket, path).delete()
                finally:
                    self.release_lock(path)

    def __len__(self):
        """Return the number of active sessions."""
        return len([fname for fname in list(self.bucket.objects.filter(Prefix=self.storage_path))
                    if (self.SESSION_PREFIX in fname and
                        self.LOCK_SUFFIX not in fname)])
