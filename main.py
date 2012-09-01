#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import re
import time
import datetime

import tornado.httpserver
import tornado.ioloop
import tornado.web

from config import config

#import pygments
#import pygments.lexers
#import pygments.formatters
import misaka as md
import PyRSS2Gen

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

config = config.dn_config()
engine = sa.create_engine(config['database'] + '?charset=utf8')#, echo = True)

Session = sessionmaker()
Session.configure(bind=engine)
db = Session()

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", pIndex),
            (r"/page/(\d+)[/]*", pIndex),
            #(r"/os[/]*", pOS),
            (r"/p/(\d+)[/]*", pArticle),
            (r"/rss[/]*", pRSS),
            (r"/feed[/]*", pRSS),
            (r"/login[/]*", pLogin),
            (r"/admin/links[/]*", pAdminLinks),
            (r"/admin/add[/]*", pAdminArticleAdd),
            (r"/admin/edit/(\d+)[/]*", pAdminArticleEdit),
        ]
        settings = dict(
            template_path = os.path.join("templates"),
            static_path = os.path.join("static"),
            xsrf_cookies = True,
            cookie_secret = config['cookie_secret'],
            autoescape = None,
            title = config['title'],
            desc = config['description'],
            folder_blog = './blog/',
            url = config['url'],
            paged = config['paged'],
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        tornado.web.ErrorHandler = pError

mBase = declarative_base()

class mPosts(mBase):
    __tablename__ = 'dn_posts'
    __table_args__ = {
        'mysql_charset': 'utf8',
    }
    
    id = sa.Column(sa.Integer, primary_key = True, autoincrement = True)
    title = sa.Column(sa.String(64))
    content = sa.Column(sa.Text)
    times = sa.Column(sa.Integer(12), unique=True)
    
    def __init__(self, title, content, times):
        self.title = title
        self.content = content
        self.times = times

class mComments(mBase):
    __tablename__ = 'dn_comments'
    __table_args__ = {
        'mysql_charset': 'utf8',
    }
    
    id = sa.Column(sa.Integer, primary_key = True, autoincrement = True)
    user = sa.Column(sa.String(64))
    comment = sa.Column(sa.Text)
    times = sa.Column(sa.Integer(12), unique=True)
    
    def __init__(self, user, comment, times):
        self.user = user
        self.comment = comment
        self.times = times

class mLinks(mBase):
    __tablename__ = 'dn_links'
    __table_args__ = {
        'mysql_charset': 'utf8',
    }
    
    id = sa.Column(sa.Integer, primary_key = True, autoincrement = True)
    name = sa.Column(sa.String(64))
    url = sa.Column(sa.Text)
    
    def __init__(self, name, url):
        self.name = name
        self.url = url

class mOptions(mBase):
    __tablename__ = 'dn_options'
    __table_args__ = {
        'mysql_charset': 'utf8',
    }
    
    id = sa.Column(sa.Integer, primary_key = True, autoincrement = True)
    name = sa.Column(sa.String(64))
    value = sa.Column(sa.Text)
    
    def __init__(self, name, value):
        self.name = name
        self.value = value

class blog():
    @staticmethod
    def readIndex(sets, page = 1):
        limit = sets['paged']
        page = int(page)
        index = []
        if page == -1:
            limit = 10
        count = db.query(mPosts).count()
        tmp = db.query(mPosts).order_by(sa.desc(mPosts.times)).offset((page-1)*sets['paged']).limit(limit)
        for i in tmp:
            content = md.html(i.content, extensions=md.EXT_STRIKETHROUGH)
            index.append({'id': i.times, 'title': i.title, 'content': content})
        return {'index': index, 'isPagedEnough': count>page*sets['paged'] and page>0}
    
    @staticmethod
    def readArticle(pid, isPure = False):
        article = {'id': pid, 'title': '', 'content': ''}
        tmp = db.query(mPosts).filter(mPosts.times == pid).first()
        if tmp is None:
            raise tornado.web.HTTPError(404, "Post not found.")
        if isPure:
            content = tmp.content
        else:
            content = md.html(tmp.content, extensions=md.EXT_STRIKETHROUGH)
        article['title'] = tmp.title
        article['content'] = content
        return article

    @staticmethod
    def updateArticle(pid, new):
        tmp = db.query(mPosts).filter(mPosts.times == pid).first()
        if tmp is None:
            raise tornado.web.HTTPError(404, "Post not found.")
        tmp.title = new['title']
        tmp.content = new['content']
        db.commit()

    @classmethod
    def outputRSS(cls, sets):
        tmp = cls.readIndex(sets, -1)
        articles = tmp['index']
        items = []
        for article in articles:
            url = sets['url'] + 'p/' + str(article['id'])
            items.append(PyRSS2Gen.RSSItem(
                title = article['title'],
                link = url,
                description = article['content'],
                guid = PyRSS2Gen.Guid(url),
                pubDate = datetime.datetime.fromtimestamp(float(article['id'])),
            ))
        rss = PyRSS2Gen.RSS2(
            title = sets['title'],
            link = sets['url'],
            description = sets['desc'],
            lastBuildDate = datetime.datetime.now(),
            items = items
        ).to_xml()
        return rss

class pBase(tornado.web.RequestHandler):
    def on_finish(self):
        None
    
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
        return datetime.datetime.fromtimestamp(float(times)+3600*8).date()
    
    def userCurrent(self):
        user = self.get_secure_cookie("login")
        if user:
            return tornado.escape.json_decode(user)
        else:
            return None
    
    def userCurrentSet(self, uname):
        if uname:
            self.set_secure_cookie("login", tornado.escape.json_encode(uname))
        else:
            self.clear_cookie("login")
    
    def userAuth(self, uname, upass):
        return uname == config['admin_username'] and upass == config['admin_password']
    
    def isLogin(self):
        return self.userCurrent() is not None
        
    def isAdmin(self):
        return self.userCurrent() == config['admin_username']
    
    def checkAdmin(self):
        if not self.isAdmin():
            raise tornado.web.HTTPError(404)

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
        stime = time.time()
        items = blog.readIndex(self.application.settings, page)
        intv = str((time.time() - stime)*1000) + ' ms'
        info = {'intv': intv, 'times': self.getTimes()}
        handle = open(self.application.settings['folder_blog'] + 'option/links.txt')
        links = eval(handle.read())
        handle.close()
        self.render("index.html", items = items['index'], info = info, page = int(page),
            plus = self.plus, minus = self.minus, isPagedEnough = items['isPagedEnough'],
            timesFormat = self.timesFormat, links = links, isAdmin = self.isAdmin
        )

class pArticle(pBase):
    def get(self, pid):
        stime = time.time()
        item = blog.readArticle(pid)
        intv = str((time.time() - stime)*1000) + ' ms'
        info = {'intv': intv, 'times': self.getTimes()}
        self.render("article.html", item = item, info = info, timesFormat = self.timesFormat,
            isAdmin = self.isAdmin
        )

class pOS(pBase):
    def get(self):
        info = {'intv': 0, 'times': self.getTimes()}
        self.render("os.html", items = os.environ, info = info)

class pRSS(pBase):
    def get(self):
        rss = blog.outputRSS(self.application.settings)
        self.render("data.html", data = rss)

class pLogin(pBase):
    def get(self):
        if self.isAdmin():
            self.redirect('/admin/add')
        else:
            info = {'intv': 0, 'times': self.getTimes()}
            self.render("login.html", info = info, isLogin = self.isLogin)
        
    def post(self):
        username = self.get_argument("username")
        passwd = self.get_argument("passwd")
        if self.userAuth(username, passwd):
            self.userCurrentSet(username)
            self.redirect('/admin/add')
        else:
            self.redirect('/login')

class pAdminLinks(pBase):
    def get(self):
        self.checkAdmin()
        links = dn_Links().select().order(('id', 'asc'))
        print links
        self.render("admin/links.html", links = links)

class pAdminArticleAdd(pBase):
    def get(self):
        self.checkAdmin()
        info = {'intv': 0, 'times': self.getTimes()}
        self.render("admin/article_add.html", info = info)
        
    def post(self):
        self.checkAdmin()
        title = self.get_argument("title")
        content = self.get_argument("content")
        db.add(mPosts(title, content, self.getTimes()))
        db.commit()
        self.redirect('/')
        
class pAdminArticleEdit(pBase):
    def get(self):
        self.checkAdmin()
        None
        
    def get(self, pid):
        self.checkAdmin()
        item = blog.readArticle(pid, True)
        info = {'intv': 0, 'times': self.getTimes()}
        self.render("admin/article_edit.html", info = info, item = item)
        
    def post(self, pid):
        self.checkAdmin()
        title = self.get_argument("title")
        content = self.get_argument("content")
        blog.updateArticle(pid, {'title': title, 'content': content})
        self.redirect('/p/' + pid)

def install():
    mBase.metadata.create_all(engine)

def main():
    #install()
    tornado.httpserver.HTTPServer(Application()).listen(int(os.environ.get('PORT', 8888)))
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
