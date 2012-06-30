#!/usr/bin/env python
#-*- coding: utf8 -*-

#author: lodevil

import urllib
import urllib2
import re


class JWC(object):
    def __init__(self, url='http://jwc.swust.edu.cn'):
        if not url.startswith('http://'):
            url = 'http://' + url
        self.url = self.base_url = url
        self.links = {}
        self._cookie = None

    def open(self):
        rep = urllib2.urlopen(self.url)
        self.url = rep.geturl()
        self._cookie = re.search(r'(\([a-zA-Z0-9]+\))', self.url).groups()[0]
        self._cookieurl = '/'.join(rep.geturl().split('/')[:-1]) + '/'
        return rep.read()

    @staticmethod
    def _get_view_state(data):
        r = re.search(r'name="__VIEWSTATE" value="([^"]+)"', data)
        if r:
            return r.groups()[0]

    def cookie_url(self, u):
        return self._cookieurl + u

    def login(self, username, password):
        data = self.open()
        post = urllib.urlencode({
            '__VIEWSTATE': self._get_view_state(data),
            'TextBox1': username,
            'TextBox2': password,
            'RadioButtonList1': u'学生'.encode('gbk'),
            'Button1': '',
            'lbLanguage': ''
            })
        rep = urllib2.urlopen(self.url, post)
        if 'xs_main.aspx' in rep.geturl():
            self._main_url = rep.geturl()
            data = rep.read().decode('gbk')
            links = re.findall(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', data)
            for link, name in links:
                link = list(link.encode('gbk'))
                for i, c in enumerate(link):
                    if ord(c) > 127:
                        link[i] = urllib.quote(c)
                self.links[name] = ''.join(link)
            urllib2.urlopen(self._cookieurl + 'content.aspx')
            return True
        return False

    def get_scores(self, xn='', xq=''):
        url = self.cookie_url(self.links[u'个人成绩查询'])
        req = urllib2.Request(url, None,
            {'Referer': self._main_url})
        rep = urllib2.urlopen(req)
        data = rep.read()
        post = {'__VIEWSTATE': self._get_view_state(data),
            'ddlXN': xn, 'ddlXQ': xq}
        if not xn:
            post['Button2'] = urllib.quote(u'在校学习成绩查询'.encode('gbk'))
        elif not xq:
            post['Button5'] = urllib.quote(u'按学年查询'.encode('gbk'))
        else:
            post['Button1'] = urllib.quote(u'按学期查询'.encode('gbk'))
        req = urllib2.Request(url, urllib.urlencode(post),
                {'Referer': url})
        rep = urllib2.urlopen(req)
        data = rep.read().decode('gbk')
        table = data[data.find('<table'): data.find('</table>')]
        trs = table.split('<tr')[2:]
        scores = []
        for tr in trs:
            cols = re.findall(r'<td>([^<]*)</td>', tr)
            scores.append({
                'name': cols[3],
                'xf': cols[6],
                'jd': cols[7],
                'score': cols[8]
                })
        avg_i = data.find(u'平均学分绩点：') + len(u'平均学分绩点：')
        avg = data[avg_i: data.find('</b>', avg_i)]
        return {'scores': scores, 'avg': float(avg)}

if __name__ == '__main__':
    jwc = JWC('202.115.175.161')
    username = raw_input(u'username: ')
    password = raw_input(u'password: ')
    if jwc.login(username, password):
        scores = jwc.get_scores('2011-2012', '2')
        for score in scores['scores']:
            print score['name'], score['xf'], score['jd'], score['score']
        print u'平均学分绩点:', scores['avg']
