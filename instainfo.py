#!/usr/bin/python
# -*- coding: utf-8 -*-

import instaloader
import os
import csv

version = "0.01"       

debug = 0     #  1 ... debug
appdir = os.path.dirname(os.path.abspath(__file__))

conffile = appdir + "/insta.conf"
acctdata = appdir + "/acct.txt"
instance = ""

acctinfo = {}

def main_proc():
    global instance
    #read_config() 
    read_acctdata()

    # Instaloader インスタンス作成
    instance = instaloader.Instaloader()
    get_all_acctinfo() 

def get_all_acctinfo() :
    for  acct,v in acctinfo.items() :
        post,follow = get_acctinfo(acct)
        print(acct,post,follow)

def get_acctinfo(acct) :

    # プロフィール取得
    profile = instaloader.Profile.from_username(instance.context, acct)

    # 投稿数、フォロワー数を取得
    post_count = profile.mediacount
    follower_count = profile.followers
    return post_count,follower_count

def read_acctdata() :
    global acctinfo
    with open(acctdata,encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            acct = row[0]
            info = {}
            info['acctname'] = row[1]
            info['start'] = row[2]
            acctinfo[acct] = info
    print(acctinfo)

def read_config() : 
    global ftp_host,ftp_user,ftp_pass,ftp_url,debug,datadir,pixela_url,pixela_token
    if not os.path.isfile(conffile) :
        debug = 1 
        return

    conf = open(conffile,'r', encoding='utf-8')
    ftp_host = conf.readline().strip()
    ftp_user = conf.readline().strip()
    ftp_pass = conf.readline().strip()
    ftp_url = conf.readline().strip()
    datadir = conf.readline().strip()
    pixela_url = conf.readline().strip()
    pixela_token = conf.readline().strip()
    debug = int(conf.readline().strip())
    conf.close()

# ----------------------------------------------------------
main_proc()
