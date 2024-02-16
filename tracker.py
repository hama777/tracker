#!/usr/bin/python
# -*- coding: utf-8 -*-

from ast import If
import os
import csv
import datetime
import pandas as pd
import requests
import locale
import shutil
from ftplib import FTP_TLS
from datetime import date,timedelta

version = "0.09"       # 24/02/16
debug = 0     #  1 ... debug
appdir = os.path.dirname(os.path.abspath(__file__))

dataname = "./CSVFile.csv"
datafile = ""
backfile = appdir + "./data.bak"
datadir = appdir
templatefile = appdir + "./tracker_templ.htm"
resultfile = appdir + "./tracker.htm"
conffile = appdir + "./tracker.conf"
logfile = appdir + "\\walk.log"

#  統計情報  {キー  yymm  : 値   辞書   キー max min ave  maxdate mindate}
statinfo = {}
allinfo = {}

datelist = []
steplist = []
yymm_list = []
ave_list = []
max_list = []
min_list = []
ftp_host = ftp_user = ftp_pass = ftp_url =  ""
df = ""
out = ""
logf = ""
pixela_url = ""
pixela_token = ""
end_year = 2024  #  データが存在する最終年

lastdate = ""    #  最終データ日付
allrank = ""     #  歩数ランキング
monrank = ""     #  歩数ランキング  今月
dailyindex = []  #  毎日のグラフ日付
dailystep  = []  #  毎日のグラフ歩数
lasthh = 0       #  何時までのデータか
yearinfo = {}    #  年ごとの平均
df = ""
total_mm_time = 0  # 今月の総時間
total_30_time = 0  # 過去30日の総時間

last_dd = 0
daily_data = []  #  日ごとのデータ リスト  各要素は (date, ptime) をもつリスト


def main_proc():
    global  datafile,logf
    locale.setlocale(locale.LC_TIME, '')
    #logf = open(logfile,'a',encoding='utf-8')
    #logf.write("\n=== start %s === \n" % datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    
    read_config()

    read_data()
    totalling_daily_data()
    parse_template()
    post_process_datafile()
    #daily_graph()
    #logf.write("\n=== end   %s === \n" % datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    #logf.close()

def read_data():
    global df,datafile

    datafile = datadir + dataname
    date_list = []
    process_list = []
    with open(datafile,encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == "ピアノ" :
                date_list.append(row[1])
                tt = row[3].replace("'","")
                hh,mm = tt.split(":")
                tt  = int(hh) * 60 + int(mm)
                process_list.append(tt)

    df = pd.DataFrame(list(zip(date_list,process_list)), columns = ['date','ptime'])
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

def post_process_datafile() :
    if debug == 1 :
        return 
    if os.path.isfile(datafile) :
        shutil.copyfile(datafile, backfile)
        os.remove(datafile)
    file = datadir + "/CSVReport.csv"
    if os.path.isfile(file) :
        os.remove(file)
    file = datadir + "/report.ping"
    if os.path.isfile(file) :
        os.remove(file)

#   過去30日間の1日ごとの練習時間を集計する
def totalling_daily_data() :
    global daily_data,total_mm_time,total_30_time

    df_daily  = df.resample('D')['ptime'].sum()
    today_dd = datetime.date.today()
    cur_month = today_dd.month   #  今月
    start_date = today_dd - datetime.timedelta(days=30)
    while start_date  < today_dd:
        str_date = start_date.strftime("%Y-%m-%d")
        try:
            ptime = df_daily.loc[str_date]
        except KeyError:
            ptime = 0 
        mm = start_date.month
        dd = start_date.day
        item_list = []
        date_str = f'{mm:02}/{dd:02}'
        item_list.append(date_str)
        item_list.append(ptime)
        daily_data.append(item_list)
        if cur_month == mm :   #  今月のデータ
            total_mm_time += ptime
        total_30_time += ptime
        start_date +=  datetime.timedelta(days=1)

#   過去30日間の1日ごとの練習時間をグラフにする
def daily_graph() :
    for item in daily_data :
        date_str,ptimte = item
        out.write(f"['{date_str}',{ptimte:5.0f}],")

def daily_table() :
    global last_dd,total_time 
    pass 

    daily  = df.resample('D')['ptime'].sum()
    total_time = 0 
    for dt,v in daily.items() :
        dt_str = dt.strftime('%m/%d')
        total_time += v
        last_dd = dt.day
        out.write(f'<tr><td>{dt_str}</td><td>{v}</tr>\n')
    #print(last_dd)    

#  今月の情報
def cur_mon_info() :
    hh = total_mm_time // 60 
    mm = total_mm_time % 60 
    out.write(f'<br>今月 合計  {hh}:{mm:02} / ')
    ave = int(total_mm_time/datetime.date.today().day)
    hh = ave // 60 
    mm = ave % 60 
    out.write(f'平均  {hh}:{mm:02} <br>')

    hh = total_30_time // 60 
    mm = total_30_time % 60 
    out.write(f'30日 合計  {hh}:{mm:02} / ')
    ave = int(total_30_time/30)
    hh = ave // 60 
    mm = ave % 60 
    out.write(f'平均  {hh}:{mm:02} ')

def parse_template() :
    global out 
    f = open(templatefile , 'r', encoding='utf-8')
    out = open(resultfile,'w' ,  encoding='utf-8')
    for line in f :
        if "%daily_table%" in line :
            daily_table()
            continue
        if "%daily_graph%" in line :
            daily_graph()
            continue
        if "%cur_mon_info%" in line :
            cur_mon_info()
            continue
        if "%lastdate%" in line :
            curdate(line)
            continue
        if "%version%" in line :
            s = line.replace("%version%",version)
            out.write(s)
            continue
        out.write(line)

    f.close()
    out.close()


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
    conf.close()

def ftp_upload() : 
    if debug == 1 :
        return 
    with FTP_TLS(host=ftp_host, user=ftp_user, passwd=ftp_pass) as ftp:
        ftp.storbinary('STOR {}'.format(ftp_url), open(resultfile, 'rb'))

def today(s):
    d = datetime.datetime.today().strftime("%m/%d %H:%M")
    s = s.replace("%today%",d)
    out.write(s)

def curdate(s) :
    d = f'{lastdate} {lasthh}時'
    s = s.replace("%lastdate%",d)
    out.write(s)

# ----------------------------------------------------------
main_proc()
