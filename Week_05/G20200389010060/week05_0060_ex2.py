# -*- coding: utf-8 -*-
# @Time    : 2020/4/6 上午11:11
# @Author  : Mat
# @Email   : ZHOUZHENZHU406@pingan.com.cn
# @File    : week06_0060_ex3.py

import requests
from lxml import etree
from snownlp import SnowNLP
import pymysql


class Mysql(object):

    def __init__(self, **kwargs):
        try:
            self.db = pymysql.connect(kwargs['ip'], kwargs['username'], kwargs['password'], kwargs['db'])
            self.cursor = self.db.cursor()
            self.initTable()
        except KeyError as e:
            print(f'{e} is not found' )
        except pymysql.err.InternalError:
            print('没找到数据库')

    def insert(self, **kwargs):
        table = kwargs['table']
        data = kwargs['data']
        keys = ','.join(data.keys())
        values = ','.join(str(s) for s in map(lambda key: f'"{key}"' if type(key) == str else key, data.values()))
        sql = f'INSERT INTO {table} ({keys}) VALUES ({values});'
        self.cursor.execute(sql)
        self.db.commit()

    def initTable(self):
        sql = f'''CREATE TABLE IF NOT EXISTS `book`(
   `name` VARCHAR(255) NOT NULL,
   `score` FLOAT,
   `comment` TEXT,
    `sentiments` FLOAT
)ENGINE=InnoDB DEFAULT CHARSET=UTF8MB4;'''
        self.cursor.execute(sql)

    def close(self):
        self.db.close()


class Douban(object):

    def __init__(self, id):
        self.id = id
        self.comments = []

    def getInfo(self):
        url = f'https://book.douban.com/subject/{self.id}/'
        print(url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
        }
        res = requests.get(url, headers=headers).text
        html = etree.HTML(res)
        score = html.xpath('//strong/text()')
        name = str(html.xpath('//*[@id="wrapper"]/h1/span/text()')[0])
        score = float(score[0].strip()) if len(score) > 0 else None
        return name, score


    def getComments(self, page=1):
        url = f'https://book.douban.com/subject/{self.id}/comments/hot?p={page}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
        }
        res = requests.get(url, headers=headers).text
        html = etree.HTML(res)
        if page == 1:
            count = html.xpath('//*[@id="total-comments"]/text()')
            print(count)
            if len(count) > 0:
                count = int(count[0].split(' ')[1])
            pages = count / 20 if count % 20 == 0 else int(count / 20) + 1
            for i in range(2, pages+1):
                self.getComments(i)
        comments = html.xpath('//*[@id="comments"]/ul/li[1]/div[2]/p/span/text()')
        print(comments)
        self.comments += list(map(lambda comment: comment.replace('\n', ''), comments))



    def nlp(self):
        name, score = self.getInfo()
        print(name,score)
        self.getComments()
        print(self.getComments())
        mysql = Mysql(ip='127.0.0.1', username='root', password='123456', db='douban')
        for comment in self.comments:
            sentiments = SnowNLP(comment).sentiments
            data = {
                'name': name,
                'score': score,
                'comment': comment,
                'sentiments': sentiments
            }
            mysql.insert(table='book', data=data)
        mysql.close()


if __name__ == '__main__':
    "高效能人士的七个习惯"
    douban = Douban('26284789')
    douban.nlp()