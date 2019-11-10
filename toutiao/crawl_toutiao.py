# -*- coding: utf-8 -*-
import subprocess
import time


def func():
    p = subprocess.run(['scrapy', 'list'], stdout=subprocess.PIPE, encoding='utf8')
    r = p.stdout
    for name in r.split():
        print(name)
        try:
            subprocess.run(['scrapy', 'crawl', name], timeout=60*30)
        except subprocess.TimeoutExpired:
            pass


def main():
    while True:
        func()
        print('one crawl finish, sleep...')
        time.sleep(3600*2)


if __name__ == "__main__":
    main()
