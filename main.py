#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import re
import time
import datetime

import tornado.httpserver
import tornado.ioloop
import tornado.web

import PyRSS2Gen

from blog import blog

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", pIndex),
            (r"/os[/]*", pOS),
            (r"/p/(\d+)[/]*", pArticle),
            (r"/rss[/]*", pRSS),
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
            url = 'http://rainmoe.herokuapp.com/'
        )
        tornado.web.Application.__init__(self, handlers, **settings)

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
            
class pIndex(pBase):
    def get(self):
        stime = time.clock()
        items = blog.readIndex(self.application.settings['folder_blog'])
        intv = str(round((time.clock() - stime)*1000, 5)) + ' ms'
        info = {'intv': intv, 'times': int(time.mktime(time.gmtime()))}
        self.render("index.html", items = items, info = info)

class pArticle(pBase):
    def get(self, id):
        stime = time.clock()
        item = blog.readArticle(self.application.settings['folder_blog'], id)
        intv = str(round((time.clock() - stime)*1000, 5)) + ' ms'
        info = {'intv': intv, 'times': int(time.mktime(time.gmtime()))}
        self.render("article.html", item = item, info = info)

class pOS(pBase):
    def get(self):
        self.render("os.html", items = os.environ)

class pRSS(pBase):
    def get(self):
        articles = blog.readIndex(self.application.settings['folder_blog'])
        items = []
        for article in articles:
            url = self.application.settings['url'] + 'p/' + article['id']
            items.append(PyRSS2Gen.RSSItem(
                title = article['title'],
                link = url,
                description = article['content'],
                guid = PyRSS2Gen.Guid(url),
                pubDate = datetime.datetime.fromtimestamp(float(article['id'])),
            ))
        rss = PyRSS2Gen.RSS2(
            title = self.application.settings['title'],
            link = self.application.settings['url'],
            description = self.application.settings['desc'],
            lastBuildDate = datetime.datetime.now(),
            items = items
        ).to_xml()
        self.render("rss.html", rss = rss)

def main():
    tornado.httpserver.HTTPServer(Application()).listen(int(os.environ.get('PORT', 8888)))
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
