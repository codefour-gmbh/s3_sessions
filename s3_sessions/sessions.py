import cherrypy
import boto3
import os
import pickle

from cherrypy.lib.sessions import Session


class S3Session(Session):
    """
    Implementation of a S3 based backend for CherryPy sessions

    storage_path
        The s3 path where the session will be stored.
    lock_timeout
        A timedelta or numeric seconds indicating how long
        to block acquiring a lock. If None (default), acquiring a lock
        will block indefinitely.
    """

    SESSION_PREFIX = 'session-'
    LOCK_SUFFIX = '.lock'
    pickle_protocol = pickle.HIGHEST_PROTOCOL

    def __init__(self, id=None, **kwargs):
        # The 'storage_path' arg is required for file-based sessions.
        kwargs['storage_path'] = os.path.abspath(kwargs['storage_path'])
        kwargs.setdefault('lock_timeout', None)

        Session.__init__(self, id=id, **kwargs)

        # validate self.lock_timeout
        if isinstance(self.lock_timeout, (int, float)):
            self.lock_timeout = datetime.timedelta(seconds=self.lock_timeout)
        if not isinstance(self.lock_timeout, (datetime.timedelta, type(None))):
            raise ValueError(
                'Lock timeout must be numeric seconds or a timedelta instance.'
            )

    @classmethod
    def setup(cls, **kwargs):
        """Set up the storage system for s3-based sessions.

        This should only be called once per process; this will be done
        automatically when using sessions.init (as the built-in Tool does).
        """
        # The 'storage_path' arg is required for file-based sessions.
        kwargs['storage_path'] = os.path.abspath(kwargs['storage_path'])

        for k, v in kwargs.items():
            setattr(cls, k, v)
