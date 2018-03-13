import cherrypy
import os

from s3_sessions.sessions import S3Session


class Server(object):
    @cherrypy.expose()
    def index(self):
        count = cherrypy.session.get('count', 0) + 1
        cherrypy.session['count'] = count
        return "You have seen this page {} times".format(count)


if __name__ == '__main__':
    path = os.path.abspath(os.path.dirname(__file__))

    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8081,
        'tools.sessions.on': True,
        'tools.sessions.storage_class': S3Session,
        'tools.sessions.s3_host': 'https://ds11s3.swisscom.com',
        'tools.sessions.s3_access_key': os.environ.get('AWS_ACCESS_KEY_ID', None),
        'tools.sessions.s3_access_secret': os.environ.get('AWS_SECRET_ACCESS_KEY', None),
        'tools.sessions.storage_bucket': 'easyasset-data',
        'tools.sessions.storage_path': 'sessions'
    })

    cherrypy.tree.mount(Server(), '/')
    cherrypy.engine.start()
    cherrypy.engine.block()
