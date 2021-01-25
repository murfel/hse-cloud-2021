import argparse
import http.server
import json
import socketserver
import psycopg2

from typing import Optional, Dict

HOST = None
DB_HOST = ''
DB_NAME = 'servicestatuses'


def db_register():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
    )
    cur = conn.cursor()
    cur.execute('INSERT INTO servicestati VALUES (%s, %s) on conflict do nothing;', (HOST, True))
    conn.commit()
    cur.close()
    conn.close()


def fetch_statuses() -> Optional[Dict[str, bool]]:
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
        )
        cur = conn.cursor()
        cur.execute('SELECT ip, status FROM servicestatuses;')
        statuses_list = cur.fetchall()
        statuses = dict()
        for ip, status in statuses_list:
            statuses[ip] = status
        cur.close()
        conn.close()
        return statuses
    except:
        return None


class MyHandler(http.server.BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        if self.path == '/healthcheck':
            self.do_HEAD()

            statuses = fetch_statuses()
            if statuses is None:
                answer = {'error': 'Database is unavailable'}
            else:
                answer = {'ip': HOST, 'services': {}}
                for ip, status in statuses.items():
                    answer['services'][ip] = 'AVAILABLE' if status else 'NOT AVAILABLE'
            self.wfile.write(bytes(json.dumps(answer), 'utf-8'))


def run():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('host', default='', type=str)
    parser.add_argument('port', default=8001, type=int)
    args = parser.parse_args()
    global HOST
    HOST = args.host
    port = args.port

    db_register()
    with socketserver.TCPServer((HOST, port), MyHandler) as httpd:
        print("serving at {}:{}".format(HOST, port))
        httpd.serve_forever()


if __name__ == '__main__':
    run()
