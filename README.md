# S3Sessions: A S3 Based Backend for CherryPy Sessions

S3Sessions is a substitute for CherryPy's built-in file backed sessions,
based on the S3Session backend by Taylor Burmeister.

## Installation

Installation should be as easy as:

```
$ pip install s3_sessions
```

To install from source:

```
$ cd /path/to/s3_sessions && pip install . --upgrade
```

## Usage

To use, you first need to import the `S3Session` class:

```
from s3_sessions.sessions import S3Session
```

Then you have to configure your server to use `S3Session` based sessions:

```
cherrypy.config.update({
	'tools.sessions.on': True,
	'tools.sessions.storage_class': S3Session,
	'tools.sessions.storage_path': 's3://path/to/sessions/directory')
})
```

After that, usage should be exactly the same as any other CherryPy sessions
backend, i.e. totally transparent.
