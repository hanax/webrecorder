from bottle import request, response, HTTPError
from webrecorder.basecontroller import BaseController

from pywb.utils.timeutils import timestamp_now

import requests
import redis

import traceback


# ============================================================================
class BrowserController(BaseController):
    def init_routes(self):
        @self.app.get('/api/v1/browsers/init_browser')
        def init_browser():
            #TODO move to config
            target = 'http://browsermanager:9020/init_browser'

            params = request.query
            if not params.get('ts'):
                params['ts'] = timestamp_now()

            upsid = params.get('upsid', '')

            print('ups:' + upsid)

            upstream_url = self.manager.browser_redis.get('ups:' + upsid)
            if not upstream_url:
                response.status = 400
                return {'error_message', 'Upstream ID missing or invalid'}

            try:
                res = requests.get(target, params=params)
            except Exception as e:
                traceback.print_exc()
                return {'queue': -1}

            cmd = res.json()

            # queued or other error
            if cmd.get('queue') != 0:
                return {'queue': cmd.get('queue', -1)}

            # set upstream url
            self.manager.browser_redis.hset('ip:' + cmd['ip'],
                                            'upstream_url', upstream_url)

            print(cmd)

            curr_host = request.urlparts.netloc.split(':')[0]
            new_cmd = {'vnc_host': curr_host + ':' + cmd['vnc_port'],
                       'cmd_host': curr_host + ':' + cmd['cmd_port'],
                       'queue': 0
                      }

            return new_cmd


