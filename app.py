#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2012, 邪罗刹
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
# 
# Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# http://opensource.org/licenses/bsd-license.php

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
            (r"/p/(\d+)[/]*", pArticle),
            
            (r"/rss[/]*", pRSS),
            (r"/feed[/]*", pRSS),
            
            (r"/login[/]*", pLogin),
            (r"/logout[/]*", pLoginOut),
            
            (r"/admin/links[/]*", pAdminLinks),
            (r"/admin/links/(\d+)[/]*", pAdminLinks),
            (r"/admin/add[/]*", pAdminArticleAdd),
            (r"/admin/edit[/]*", pAdminArticleList),
            (r"/admin/edit/(\d+)[/]*", pAdminArticleEdit),
            
            #(r"/os[/]*", pOS),
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
            disqus = config['disqus_name'],
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
    times = sa.Column(sa.Integer(12), unique=True) #index
    
    def __init__(self, title, content, times):
        self.title = title
        self.content = content
        self.times = times

class mPostsMeta(mBase):
    __tablename__ = 'dn_posts_meta'
    __table_args__ = {
        'mysql_charset': 'utf8',
    }
    
    id = sa.Column(sa.Integer, primary_key = True, autoincrement = True)
    pid = sa.Column(sa.Integer, index=True) #index
    name = sa.Column(sa.String(12), index=True) #index
    value = sa.Column(sa.Text)
    
    def __init__(self, pid, name, value):
        self.pid = pid
        self.name = name
        self.value = value

# class mComments(mBase):
#     __tablename__ = 'dn_comments'
#     __table_args__ = {
#         'mysql_charset': 'utf8',
#     }
#     
#     id = sa.Column(sa.Integer, primary_key = True, autoincrement = True)
#     user = sa.Column(sa.String(64), index=True) #index
#     comment = sa.Column(sa.Text)
#     times = sa.Column(sa.Integer(12), index=True) #index
#     
#     def __init__(self, user, comment, times):
#         self.user = user
#         self.comment = comment
#         self.times = times

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
    name = sa.Column(sa.String(12), index=True) #index
    value = sa.Column(sa.Text)
    
    def __init__(self, name, value):
        self.name = name
        self.value = value

class blog():
    @staticmethod
    def readIndex(sets, page = 1):
        def shorted(data):
            res = ''
            count = 0
            for i in data.splitlines():
                count += 1
                if count>2:
                    break
                res += i
            return res
        limit = sets['paged']
        page = int(page)
        index = []
        count = db.query(mPosts).count()
        if page == -1:
            tmp = db.query(mPosts).order_by(sa.desc(mPosts.times)).limit(12)
        else:
            tmp = db.query(mPosts).order_by(sa.desc(mPosts.times)).offset((page-1)*sets['paged']).limit(limit)
        for i in tmp:
            content = md.html(shorted(i.content), extensions=md.EXT_STRIKETHROUGH)
            index.append({'id': i.times, 'title': i.title, 'content': content})
        return {'index': index, 'isPagedEnough': count>page*sets['paged'] and page>0}

    @staticmethod
    def readList(limit = 12):
        if limit == -1:
            tmp = db.query(mPosts.times, mPosts.title).order_by(sa.desc(mPosts.times))
        else:
            tmp = db.query(mPosts.times, mPosts.title).order_by(sa.desc(mPosts.times)).limit(limit)
        return tmp

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
    def addArticle(new, getTimes):
        db.add(mPosts(new['title'], new['content'], getTimes()))
        db.commit()
    
    @staticmethod
    def updateArticle(pid, new):
        tmp = db.query(mPosts).filter(mPosts.times == pid).first()
        if tmp is None:
            raise tornado.web.HTTPError(404, "Post not found.")
        tmp.title = new['title']
        tmp.content = new['content']
        db.commit()

    @staticmethod
    def outputRSS(sets):
        articles = db.query(mPosts).order_by(sa.desc(mPosts.times)).limit(12)
        items = []
        for article in articles:
            content = md.html(article.content, extensions=md.EXT_STRIKETHROUGH)
            url = sets['url'] + 'p/' + str(article.times)
            items.append(PyRSS2Gen.RSSItem(
                title = article.title,
                link = url,
                description = content,
                guid = PyRSS2Gen.Guid(url),
                pubDate = datetime.datetime.fromtimestamp(float(article.times)),
            ))
        rss = PyRSS2Gen.RSS2(
            title = sets['title'],
            link = sets['url'],
            description = sets['desc'],
            lastBuildDate = datetime.datetime.now(),
            items = items
        ).to_xml()
        return rss
    
    @staticmethod
    def readLinks(lid = -1, filter = False):
        if lid == -1:
            if filter:
                tmp = db.query(mLinks).filter(mLinks.url != '-')
            else:
                tmp = db.query(mLinks)
        else:
            tmp = db.query(mLinks).filter(mLinks.id == lid).first()
        return tmp
    
    @staticmethod
    def addLink(new):
        db.add(mLinks(new['name'], new['url']))
        db.commit()
    
    @staticmethod
    def updateLink(lid, new):
        tmp = db.query(mLinks).filter(mLinks.id == lid).first()
        if tmp is None:
            raise tornado.web.HTTPError(404, "Link not found.")
        tmp.name = new['name']
        tmp.url = new['url']
        db.commit()

class pBase(tornado.web.RequestHandler):
    stime = 0
    
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
    
    def timesFormatDate(self, times):
        return datetime.datetime.fromtimestamp(float(times)+3600*8).date()

    def timesFormatTime(self, times):
        return datetime.datetime.fromtimestamp(float(times)+3600*8).time()
    
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
        
    def timeCost(self):
        return str((time.time() - self.stime)*1000) + ' ms'
        
class pError(pBase):
    def __init__(self, application, request, status_code):
        tornado.web.RequestHandler.__init__(self, application, request)
        self.set_status(status_code)
    
    def get_error_html(self, status_code, **kwargs):
        self.stime = time.time()
        if (status_code == 404):
            error = 'Page not found.'
        elif (status_code == 405):
            error = 'Temporary not avaliable.'
        else:
            error = 'Unexpected problem.'
        return self.render_string("error.html", error = error)

class pIndex(pBase):
    def get(self, page = 1):
        self.stime = time.time()
        items = blog.readIndex(self.application.settings, page)
        links = blog.readLinks(-1, True)
        self.render("index.html", items = items, page = int(page),
            links = links
        )

class pArticle(pBase):
    def get(self, pid):
        self.stime = time.time()
        item = blog.readArticle(pid)
        self.render("article.html", item = item,
            timec = self.timeCost(stime)
        )

class pOS(pBase):
    def get(self):
        self.stime = time.time()
        self.render("os.html", items = os.environ)

class pRSS(pBase):
    def get(self):
        rss = blog.outputRSS(self.application.settings)
        self.render("data.html", data = rss)

class pLogin(pBase):
    def get(self):
        if self.isAdmin():
            self.redirect('/admin/edit')
        else:
            self.stime = time.time()
            self.render("login.html", isLogin = self.isLogin)
        
    def post(self):
        username = self.get_argument("username")
        passwd = self.get_argument("passwd")
        if self.userAuth(username, passwd):
            self.userCurrentSet(username)
            self.redirect('/admin/add')
        else:
            self.redirect('/login')

class pLoginOut(pBase):
    def get(self):
        self.clear_cookie('login')
        self.redirect('/login')

class pAdminLinks(pBase):
    def get(self, lid = -1):
        self.stime = time.time()
        self.checkAdmin()
        link = False
        if lid != -1:
            link = blog.readLinks(lid)
        links = blog.readLinks()
        self.render("admin/links.html", links = links,
                    lid = lid, link = link)
        
    def post(self, lid = -1):
        self.checkAdmin()
        lid = int(lid)
        name = self.get_argument("name")
        url = self.get_argument("url")
        if lid == -1:
            blog.addLink({'name': name, 'url': url})
        else:
            blog.updateLink(lid, {'name': name, 'url': url})
        self.redirect('/admin/links')

class pAdminArticleAdd(pBase):
    def get(self):
        self.stime = time.time()
        self.checkAdmin()
        self.render("admin/article_add.html")
        
    def post(self):
        self.checkAdmin()
        title = self.get_argument("title")
        content = self.get_argument("content")
        blog.addArticle({'title': title, 'content': content}, self.getTimes)
        self.redirect('/')
        
class pAdminArticleList(pBase):
    def get(self):
        self.stime = time.time()
        self.checkAdmin()
        items = blog.readList(-1)
        self.render("admin/article_list.html", items = items)

class pAdminArticleEdit(pBase): 
    def get(self, pid):
        self.stime = time.time()
        self.checkAdmin()
        item = blog.readArticle(pid, True)
        self.render("admin/article_edit.html", item = item)
        
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
