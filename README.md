# S3Sessions: S3 Based Backend for CherryPy Sessions

S3Sessions is a substitute for CherryPy's built-in file backed sessions,
based on the internal CherryPy FileSession backend.

Please note that using S3 for session management can come with performance hits,
but places the session files in a highly available and persistent location.

Thanks to the developers of [CherryPy](https://github.com/cherrypy/cherrypy) and [LmdbSession](https://github.com/tburmeister/lmdb_sessions).

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
