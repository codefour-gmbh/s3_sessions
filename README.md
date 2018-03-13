# S3Sessions: A S3 Based Backend for CherryPy Sessions

S3Sessions is a substitute for CherryPy's built-in file backed sessions,
based on the internal CherryPy FileSession backend.

## Installation

```
$ pip install s3_sessions
```

Install from source:

```
$ cd /path/to/s3_sessions && pip install . --upgrade
```

## Usage

```
from s3_sessions.sessions import S3Session
```

Cherrypy server config:

```
cherrypy.config.update({
	'tools.sessions.on': True,
	'tools.sessions.storage_class': S3Session,
	'tools.sessions.storage_bucket': 'session_bucket'
	'tools.sessions.storage_path': 'key/path/to/sessions/directory')
})
```
