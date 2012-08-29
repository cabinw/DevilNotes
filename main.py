#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import re
import time
import datetime

import tornado.httpserver
import tornado.ioloop
import tornado.web

from blog import blog

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", pIndex),
            (r"/page/(\d+)[/]*", pIndex),
            #(r"/os[/]*", pOS),
            (r"/p/(\d+)[/]*", pArticle),
            (r"/rss[/]*", pRSS),
            (r"/feed[/]*", pRSS),
        ]
        settings = dict(
            template_path = os.path.join("templates"),
            static_path = os.path.join("static"),
            xsrf_cookies = True,
            cookie_secret = "",
            autoescape = None,
            title = u"雨萌星",
            desc = u"code is my unique faith.",
            folder_blog = './blog/',
            url = 'http://www.rainmoe.com/',
            paged = 3,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        tornado.web.ErrorHandler = pError

class pBase(tornado.web.RequestHandler):
    def time2ago(self, t):
        intv = time.time()-t
        if intv > 86400:
            return str(int(intv/86400)) + 'days ago'
        elif intv > 3600:
            return str(int(intv/3600)) + 'h ago'
        elif intv > 60:
            return str(int(intv/60)) + 'min ago'
        else:
            return str(int(intv)) + 's ago'
            
    def getTimes(self):
        return int(time.mktime(time.gmtime()))
    
    def plus(self, num):
        return int(num) + 1
    
    def minus(self, num):
        return int(num) - 1
    
    def timesFormat(self, times):
        return datetime.datetime.fromtimestamp(float(times)+3600*8)

class pError(pBase):
    def __init__(self, application, request, status_code):
        tornado.web.RequestHandler.__init__(self, application, request)
        self.set_status(status_code)
    
    def get_error_html(self, status_code, **kwargs):
        if (status_code == 404):
            error = 'Page not found.'
        elif (status_code == 405):
            error = 'Temporary not avaliable.'
        else:
            error = 'Unexpected problem.'
        info = {'intv': '-', 'times': self.getTimes()}
        return self.render_string("error.html", info = info, error = error)

class pIndex(pBase):
    def get(self, page = 1):
        stime = time.clock()
        items = blog.readIndex(self.application.settings, page)
        intv = str((time.clock() - stime)*1000) + ' ms'
        info = {'intv': intv, 'times': self.getTimes()}
        handle = open(self.application.settings['folder_blog'] + 'option/links.txt')
        links = eval(handle.read())
        handle.close()
        self.render("index.html", items = items['index'], info = info, page = page,
            plus = self.plus, minus = self.minus, isPagedEnough = items['isPagedEnough'],
            timesFormat = self.timesFormat, links = links
        )

class pArticle(pBase):
    def get(self, id):
        stime = time.clock()
        item = blog.readArticle(self.application.settings['folder_blog'], id)
        intv = str((time.clock() - stime)*1000) + ' ms'
        info = {'intv': intv, 'times': self.getTimes()}
        self.render("article.html", item = item, info = info, timesFormat = self.timesFormat)

class pOS(pBase):
    def get(self):
        self.render("os.html", items = os.environ)

class pRSS(pBase):
    def get(self):
        rss = blog.outputRSS(self.application.settings)
        self.render("data.html", data = rss)

def main():
    tornado.httpserver.HTTPServer(Application()).listen(int(os.environ.get('PORT', 8888)))
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
