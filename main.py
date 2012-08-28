#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.httpserver
import tornado.ioloop
import tornado.web
import os.path
import re
import time
import datetime

import pygments
import pygments.lexers
import pygments.formatters

import PyRSS2Gen

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
            desc = u"Code is my unique faith.",
            folder_blog = './blog/',
            url = 'http://rainmoe.herokuapp.com/'
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class blog:
    @staticmethod
    def readIndex(cu):
        index = []
        li = os.listdir(cu)
        for i in li:
            now = cu + i
            if os.path.isfile(now):
                title = ''
                content = ''
                #Wordpress blog articles
                if re.match(r'^\d+\.txt$', i):
                    id = i.replace('.txt', '')
                    f = open(now)
                    html = f.readlines()
                    f.close()
                    count = 0
                    for j in html:
                        count += 1
                        if re.match(r'<!--more-->', j):
                            break
                        if count == 1:
                            title += '<a href="p/' + id + '">' + j + '</a>'
                        elif count > 2:
                            content += '<p>' + j.replace('<img', '<img style="display:none;"') + '</p>'
                    index.append({'id': id,'title': title, 'content': content})
                #Markdown
                elif re.match(r'^\d+\.md$', i):
                    f = open(now)
                    #index += f.read()
                    f.close()
        return index
    @staticmethod
    def readArticle(cu, id):
        article = {'title': '', 'content': ''}
        txt = cu + id + '.txt'
        md = cu + id + '.md'
        #Wordpress blog articles
        if os.path.isfile(txt):
            f = open(txt)
            html = f.readlines()
            f.close()
            count = 0
            hasPre = False
            for i in html:
                count += 1
                if count == 1:
                    article['title'] += '<a href="p/' + str(id) + '">' + i + '</a>'
                elif count > 2:
                    if re.match(r'</pre>', i):
                        isPre = False
                        #code = pygments.highlight(tmp, pygments.lexers.PythonLexer(), pygments.formatters.HtmlFormatter())
                        #article['content'] += code.encode('utf-8') #unicode(code, 'utf-8')
                    article['content'] += '<p>' + i + '</p>'
                    if re.match(r'<pre', i):
                        hasPre = True
                #if hasPre:
                #    article['content'] += '<style>' + pygments.formatters.HtmlFormatter().get_style_defs('.highlight') + '</style>'
        #Markdown
        elif os.path.isfile(md):
            f = open(md)
            #index += f.read()
            f.close()
        return article

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
        info = {'intv': intv, 'times': int(time.time())}
        self.render("index.html", items = items, info = info)

class pArticle(pBase):
    def get(self, id):
        stime = time.clock()
        item = blog.readArticle(self.application.settings['folder_blog'], id)
        intv = str(round((time.clock() - stime)*1000, 5)) + ' ms'
        info = {'intv': intv, 'times': int(time.time())}
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
            link = 'http://www.rainmoe.com',
            description = self.application.settings['desc'],
            lastBuildDate = datetime.datetime.now(),
            items = items
        )
        self.render("rss.html", rss = rss.to_xml())

def main():
    tornado.httpserver.HTTPServer(Application()).listen(int(os.environ.get('PORT', 8888)))
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
