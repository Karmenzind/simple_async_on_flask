# coding: utf-8

import os
import treq
from twisted.internet import epollreactor
from twisted.internet import reactor, task
from twisted.web.client import HTTPConnectionPool

try:
    epollreactor.install()
except Exception as e:
    print(e)


class LocalTreq:
    def __init__(self, **kw):
        self.req_generated = self.req_made = self.req_done = self.failed = 0
        self.cooperator = task.Cooperator()
        self.pool = HTTPConnectionPool(reactor)

    def run(self, _=None):
        self.cooperator.cooperate(self.requests_generator())
        reactor.callLater(1, self.counter)
        reactor.run()

    def counter(self):
        print("PID {} | Requests: {} | generated | {} sent | {} OK | {} failed".format(os.getpid(),
                                                                                       self.req_generated,
                                                                                       self.req_made,
                                                                                       self.req_done,
                                                                                       self.failed))
        self.req_generated = self.req_made = self.req_done = self.failed = 0
        reactor.callLater(1, self.counter)

    def body_received(self, resp):
        if resp == b'OK' or resp == b'FAIL':
            self.req_done += 1

    def error_received(self, error_msg):
        self.failed += 1
        print(error_msg)

    def request_done(self, response):
        deferred = response.content()
        self.req_made += 1
        deferred.addCallback(self.body_received)
        deferred.addErrback(self.error_received)
        return deferred

    def request(self):
        deferred = treq.post(url='http://127.0.0.1:5000/',
                             pool=self.pool)
        deferred.addCallback(self.request_done)
        return deferred

    def requests_generator(self):
        while True:
            deferred = self.request()
            self.req_generated += 1

            yield None


if __name__ == '__main__':
    # 'http://127.0.0.1:5000/login',
    # data = '''{"username": "user1", "password": "pwd1"}'''
    LocalTreq().run()

