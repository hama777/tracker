#!/usr/bin/python
# -*- coding: utf-8 -*-

from ast import If
import os
import csv
import datetime
import pandas as pd
import locale
import shutil
#import math
from ftplib import FTP_TLS
from datetime import date,timedelta
import numpy as np

version = "0.29"       # 24/03/15
debug = 0     #  1 ... debug
appdir = os.path.dirname(os.path.abspath(__file__))

dataname = "/CSVFile.csv"
datafile = ""
backfile = appdir + "/save.txt"
datadir = appdir
templatefile = appdir + "/tracker_templ.htm"
resultfile = appdir + "/tracker.htm"
conffile = appdir + "/tracker.conf"
logfile = appdir + "\\tracker.log"

ftp_host = ftp_user = ftp_pass = ftp_url =  ""
df = ""
out = ""
logf = ""
pixela_url = ""
pixela_token = ""
end_year = 2024  #  データが存在する最終年

lastdate = ""    #  最終データ日付
lasthh = 0       #  何時までのデータか
df = ""

last_dd = 0
daily_data = []  #  日ごとのデータ リスト  各要素は (date, ptime) をもつリスト
daily_df = ""    #  日ごとのデータ df
daily_all_df = ""    #  日ごとのデータ df
today_date = ""   # 今日の日付  date型

def main_proc():
    global  datafile,logf,today_date
    locale.setlocale(locale.LC_TIME, '')
    logf = open(logfile,'a',encoding='utf-8')
    logf.write("\n=== start %s === \n" % datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    today_date = datetime.datetime.today()
    read_config()

    read_data()
    totalling_daily_data()
    parse_template()
    ftp_upload()
    post_process_datafile()
    #daily_graph()
    logf.write("\n=== end   %s === \n" % datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    logf.close()

def read_data():
    global df,datafile

    datafile = datadir + dataname
    date_list = []
    process_list = []
    if debug == 1 :
        if not os.path.isfile(datafile) :
            datafile = backfile
    if not os.path.isfile(datafile) :
        logf.write("\n datafile not found \n" )
        logf.write("\n=== end   %s === \n" % datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        logf.close()
        exit()

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
    file = datadir + "/report.png"
    if os.path.isfile(file) :
        os.remove(file)

#   1日ごとの練習時間を集計し  date ptime のカラムを持つ df  daily_all_df を作成する
#   daily_all_df は ptime が 0 の日(データ)も含む
def totalling_daily_data() :
    global daily_all_df

    df_daily  = df.resample('D')['ptime'].sum()
    date_list = []
    ptime_list = []
    start_date  = datetime.date(2024, 1, 1)
    target_date = start_date
    end_date = datetime.date.today()
    #  start_date から昨日まで全日付をチェックする
    while target_date  < end_date:
        str_date = target_date.strftime("%Y-%m-%d")
        try:
            ptime = df_daily.loc[str_date]
        except KeyError:          #  日付のデータがなければ ptime は 0
            ptime = 0 
        date_list.append(target_date)
        ptime_list.append(ptime)
        target_date +=  datetime.timedelta(days=1)


    daily_all_df = pd.DataFrame(list(zip(date_list,ptime_list)), columns = ['date','ptime'])
    daily_all_df['date'] = pd.to_datetime(daily_all_df["date"])

#  7日間の移動平均
def daily_movav() :
    mov_ave_dd = 7
    df_movav  =  daily_all_df.copy()
    df_movav['ptime']  = df_movav['ptime'].rolling(mov_ave_dd).mean()
    for _ , row in df_movav.iterrows() :
        ptime = row['ptime']
        if pd.isna(ptime) :
            continue
        dd = row['date'].strftime("%m/%d")
        out.write(f"['{dd}',{row['ptime']:5.0f}],") 


#   過去30日間の1日ごとの練習時間をグラフにする
def daily_graph() :
    df30 = daily_all_df.tail(30)
    for _ , row in df30.iterrows() :
        date_str = row['date'].strftime('%d')
        out.write(f"['{date_str}',{row['ptime']:5.0f}],")


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

#  サマリ
def cur_mon_info() :
    df_tmp = daily_all_df[daily_all_df['date'] >= datetime.datetime(2024,3,1)]
    df_tmp = df_tmp.reset_index()
    cur_max = df_tmp['ptime'].max()
    cur_maxix = df_tmp['ptime'].idxmax()
    mdate = df_tmp.iloc[cur_maxix]['date'].strftime('%m/%d (%a)')
    df_month = daily_all_df.groupby(pd.Grouper(key='date', freq='M')).sum()
    cur_ptime = df_month.iloc[-1]['ptime']
    out.write(f'')
    out.write(f'<tr><td>今月</td><td align="right">{cur_ptime//60}:{cur_ptime%60:02}</td>')
    ave = int(cur_ptime/datetime.date.today().day)
    out.write(f'<td>{ave//60}:{ave%60:02}</td><td>{cur_max}({mdate})</td></tr>')

    df_tmp = daily_all_df[(daily_all_df['date'] >= datetime.datetime(2024,2,1)) & (daily_all_df['date'] < datetime.datetime(2024,3,1))]
    df_tmp = df_tmp.reset_index()
    cur_max = df_tmp['ptime'].max()
    cur_maxix = df_tmp['ptime'].idxmax()
    mdate = df_tmp.iloc[cur_maxix]['date'].strftime('%m/%d (%a)')

    prev_ptime = df_month.iloc[-2]['ptime']
    # today = datetime.datetime.today()
    # this_month = datetime.datetime(today.year, today.month, 1)
    # last_month_end = this_month - datetime.timedelta(days=1)
    # dd = last_month_end.day
    out.write(f'<tr><td>先月</td><td align="right">{prev_ptime//60}:{prev_ptime%60:02}</td> ')
    ave = int(prev_ptime/last_month_days())
    out.write(f'<td>{ave//60}:{ave%60:02}</td><td>{cur_max}({mdate})</td></tr>')

    df30 = daily_all_df.copy()
    df30 = df30.tail(30)
    ptime30 = df30['ptime'].sum()
    out.write(f'<tr><td>30日</td><td>{ptime30//60}:{ptime30%60:02}</td> ')
    ave = int(ptime30/30)
    out.write(f'<td>{ave//60}:{ave%60:02}</td>')

    sort_df = df30.sort_values('ptime',ascending=False)
    max_ptime = sort_df['ptime'].iloc[0]
    max_date = sort_df['date'].iloc[0].strftime('%m/%d (%a)')
    out.write(f'<td>{max_ptime}({max_date})</td></tr>')

#   前月の日数
def last_month_days() :
    this_month = datetime.datetime(today_date.year, today_date.month, 1)
    last_month_end = this_month - datetime.timedelta(days=1)
    return(last_month_end.day)

#   月別情報
def month_info()  :
    #  年月  合計時間  1日平均時間  最大時間   無練習日率
    #  暫定    年は考慮していない
    curmm = 1
    endmm = today_date.month
    while curmm <= endmm :
        start = datetime.datetime(2024, curmm, 1)
        end = datetime.datetime(2024, curmm+1, 1)
        df_mm = daily_all_df[(daily_all_df['date'] >= start) & (daily_all_df['date'] < end )]
        p_sum = df_mm['ptime'].sum()
        p_ave = df_mm['ptime'].mean()
        p_max = df_mm['ptime'].max()
        out.write(f'<tr><td align="right">{curmm}</td><td align="right">{p_sum//60}:{p_sum%60:02}</td>'
                  f'<td align="right">{p_ave:5.1f}</td><td align="right">{p_max//60}:{p_max%60:02}</td><td></td></tr>\n')
        curmm += 1 

def ranking() :
    sort_df = daily_all_df.copy()
    sort_df = sort_df.sort_values('ptime',ascending=False)
    i = 0 
    for _ , row in sort_df.iterrows() :
        i += 1 
        date_str = row['date'].strftime('%m/%d (%a)')
        hh = row['ptime'] // 60
        mm = row['ptime'] % 60
        time_str = f'{hh:02}:{mm:02}'
        out.write(f"<tr><td align='right'>{i}</td><td align='right'>{time_str}</td><td>{date_str}</td></tr>")
        if i >= 10 :
            break


def ftp_upload() : 
    if debug == 1 :
        return 
    with FTP_TLS(host=ftp_host, user=ftp_user, passwd=ftp_pass) as ftp:
        ftp.storbinary('STOR {}'.format(ftp_url), open(resultfile, 'rb'))

def today(s):
    d = today_date.strftime("%m/%d %H:%M")
    s = s.replace("%today%",d)
    out.write(s)

def curdate(s) :
    d = f'{lastdate} {lasthh}時'
    s = s.replace("%lastdate%",d)
    out.write(s)

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
        if "%daily_movav%" in line :
            daily_movav()
            continue
        if "%month_info%" in line :
            month_info()
            continue
        if "%ranking%" in line :
            ranking()
            continue
        if "%lastdate%" in line :
            curdate(line)
            continue
        if "%version%" in line :
            s = line.replace("%version%",version)
            out.write(s)
            continue
        if "%today%" in line :
            today(line)
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
    debug = int(conf.readline().strip())
    conf.close()


# ----------------------------------------------------------
main_proc()
