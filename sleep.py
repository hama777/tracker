#!/usr/bin/python
# -*- coding: utf-8 -*-

from ast import If
import os
import csv
import datetime
import pandas as pd
import locale
from ftplib import FTP_TLS
from datetime import date,timedelta
import math
import numpy as np

# 25/04/03 v1.34  月別睡眠時間ランキングを20位までにした
version = "1.34"       

# TODO:  pixela

debug = 0     #  1 ... debug
appdir = os.path.dirname(os.path.abspath(__file__))

dataname = "/CSVFile.csv"
datafile = appdir + "/save.txt"
datadir = appdir
templatefile = appdir + "/sleep_templ.htm"
resultfile = appdir + "/sleep.htm"
conffile = appdir + "/tracker.conf"
logfile = appdir + "\\tracker.log"
pastdata = appdir + "/sleeppast.txt"
rawdata = appdir + "/rawdata.txt"
past_pf_dic = []   #  過去の月別時間 pf   辞書  キー  hhmm   値  分

ftp_host = ftp_user = ftp_pass = ftp_url =  ""
df = ""
out = ""
logf = ""
pixela_url = ""
pixela_token = ""

def main_proc():
    global  logf,ftp_url

    locale.setlocale(locale.LC_TIME, '')

    date_settings()
    read_config()
    ftp_url = ftp_url.replace("index.htm","sleep.htm")
    read_data()
    read_pastdata()
    create_df_month()
    parse_template()

    ftp_upload()

#   df の作成
#   df の形式   date  起床基準の日付  date型   start 数値 分単位  end 就寝時刻 分単位  sleep 睡眠時間  
#   就寝時刻12時超に対応するため start end は 0:00 基準の分単位で持つ  ex.  24:10 なら  24*60+10 = 1450
def read_data():
    global df

    date_start = []
    date_end = []
    sleep_list = []
    index_date_list = []
    with open(datafile,encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == "睡眠" :
                t = conv_datetime_to_minute(row[1])
                date_start.append(t)
                t = conv_datetime_to_minute(row[2])
                date_end.append(t)
                tt = row[3].replace("'","")
                tt = conv_hhmm_mm(tt) 
                sleep_list.append(tt)
                s = row[2][0:10]   # 先頭の日付部分のみ取り出す  ex. 2024-01-02
                index_date_list.append(s)

    df = pd.DataFrame(list(zip(index_date_list,date_start,date_end,sleep_list)), 
                      columns = ['date','start','end','sleep'])
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

#  yyyy-mm-dd hh:mm 形式(str型)を分単位の数値に変換する
def conv_datetime_to_minute(dt) :
    hh = int(dt[11:13])   # hh 部分を取り出す
    mm = int(dt[14:])     # mm 部分を取り出す
    return hh * 60 + mm

def read_pastdata():
    global df_past , df_all
    df_past = pd.read_csv(pastdata,  sep='\t')
    date_list = []
    row_list = []
    for index , row in df_past.iterrows() :  
        line_list = []
        for i in range(10) :
            if i == 0 :      #  yymm 
                dt = datetime.datetime.strptime(row.iloc[i] + "/01", '%Y/%m/%d')
                tdate = datetime.date(dt.year, dt.month, dt.day)
                date_list.append(tdate)
            else :
                if not pd.isna(row.iloc[i]) :
                    hh = int(row.iloc[i].split(":")[0])
                    mm = int(row.iloc[i].split(":")[1])
                    tm = hh * 60 + mm 
                    line_list.append(tm)
                else : 
                    line_list.append(np.nan)
            
        row_list.append(line_list)

    columns = ['sleep_ave','sleep_min','sleep_max','start_ave','start_min','start_max','end_ave','end_min','end_max']
    df_all = pd.DataFrame(data=row_list,  index=date_list,  columns=columns)

def daily_graph() :
    for index , row in df.tail(30).iterrows() :    
        str_date = index.strftime("%d")
        stime = int(row['sleep'])

        out.write(f"['{str_date}',[{conv_time_to_graph_str(stime)}]],")

#   月別平均睡眠時間グラフ
def month_graph() :
    for dt , row in df_month.iterrows() :  
        date_str = f'{dt.year-2000}/{dt.month:02}' 
        tm = int(row['sleep_ave'])
        hh = tm // 60
        mm = tm % 60
        out.write(f"['{date_str}',[{hh},{mm},0]],")

#   月別平均就寝時刻グラフ
def month_start_time_graph() :
    for dt , row in df_month.iterrows() :  
        date_str = f'{dt.year-2000}/{dt.month:02}' 
        if math.isnan(row['start_ave']) :
            continue
        tm = int(row['start_ave'])
        hh = tm // 60
        if hh < 8 :              # 24:00 を超える場合があるため
            hh = hh + 24
        mm = tm % 60
        out.write(f"['{date_str}',[{hh},{mm},0]],")

#   月別平均起床時刻グラフ
def month_end_time_graph() :
    for dt , row in df_month.iterrows() :  
        date_str = f'{dt.year-2000}/{dt.month:02}' 
        if math.isnan(row['end_ave']) :
            continue
        tm = int(row['end_ave'])
        hh = tm // 60
        mm = tm % 60
        out.write(f"['{date_str}',[{hh},{mm},0]],")

def start_time_graph() :
    for index , row in df.tail(90).iterrows() :    
        str_date = f'{index.strftime("%m")}/{index.strftime("%d")}'
        out.write(f"['{str_date}',[{conv_time_to_graph_str(row['start'])}]],")

def end_time_graph() :
    for index , row in df.tail(90).iterrows() :    
        str_date = f'{index.strftime("%m")}/{index.strftime("%d")}'
        out.write(f"['{str_date}',[{conv_time_to_graph_str(row['end'])}]],")

#   日別睡眠時間ランキング
def ranking_sleep_time_max() :
    sort_df = df.copy()
    sort_df = sort_df.sort_values('sleep',ascending=False)
    ranking_sleep_time_com(sort_df)

def ranking_sleep_time_30_max() :
    sort_df = df.tail(30)
    sort_df = sort_df.sort_values('sleep',ascending=False)
    ranking_sleep_time_com(sort_df)

def ranking_sleep_time_min() :
    sort_df = df.copy()
    sort_df = sort_df.sort_values('sleep',ascending=True)
    ranking_sleep_time_com(sort_df)

def ranking_sleep_time_30_min() :
    sort_df = df.tail(30)
    sort_df = sort_df.sort_values('sleep',ascending=True)
    ranking_sleep_time_com(sort_df)

#   日別睡眠時間ランキング 出力処理
def ranking_sleep_time_com(sort_df) :
    i = 0 
    for index , row in sort_df.head(10).iterrows() :  
        i = i + 1 
        str_date = f'{index.strftime("%y")}/{index.strftime("%m")}/{index.strftime("%d")} ({index.strftime("%a")})'
        if index.date() == lastdate :      # 最終データなら赤字にする
            str_date = f'<span class=red>{str_date}</span>'

        stime = int(row['sleep'])
        hh = int(stime / 60)
        mm = stime % 60
        out.write(f"<tr><td align='right'>{i}</td><td align='right'>{hh}:{mm:02}</td><td>{str_date}</td></tr>")

#   月別平均睡眠時間ランキング
def rank_month_sleep_max(col) :
    sort_df = df_month.sort_values('sleep_ave',ascending=False)
    rank_month_sleep_com(sort_df,col)

def rank_month_sleep_min(col) :
    sort_df = df_month.sort_values('sleep_ave',ascending=True)
    rank_month_sleep_com(sort_df,col)

def rank_month_sleep_com(sort_df,col) :
    i = 0 
    for dt , row in sort_df.head(20).iterrows() :  
        i += 1
        if multi_col(i,col,10) :
            continue 
        date_str = f'{dt.year}/{dt.month:02}' 
        if dt.year == today_date.year and dt.month == today_date.month :
            date_str = f'<span class=red>{date_str}</span>'
        hhmm = conv_time_to_str(row['sleep_ave'])
        out.write(f"<tr><td align='right'>{i}</td><td align='right'>{hhmm}</td><td>{date_str}</td></tr>")

#  月の情報をdfで保持する
#  df_month  カラム  yymm start_ave end_ave sleep_ave start_max end_max sleep_max start_min end_min sleep_min
#            yymm は int  sleep 等は分単位 int 
def create_df_month() :
    global  df_month

    m_ave = df.resample(rule = "ME").mean()
    m_max = df.resample(rule = "ME").max()
    m_min = df.resample(rule = "ME").min()
    result = pd.concat([m_ave, m_max,m_min], axis=1)
    result.columns = ['start_ave','end_ave','sleep_ave','start_max','end_max','sleep_max','start_min','end_min','sleep_min']
    df_month = pd.concat([df_all,result ], axis=0)

#  月別情報テーブル
def month_info_table() :
    col_list = ['sleep_ave','sleep_min','sleep_max','start_ave','start_min','start_max',
                'end_ave','end_min','end_max']

    for dt , row in df_month.iterrows() :  
        if dt.year < 2024  :       #  2024年以降のみ表示
            continue
        yy = dt.year
        mm = dt.month

        out.write(f'<tr><td>{yy}/{mm:02}</td>')
        for col in col_list :
            v = conv_time_to_str(row[col])
            out.write(f'<td  align="right">{v}</td>')

        out.write('</tr>\n')

    all_statistics()

def all_statistics() :
    sleep_ave = int(df['sleep'].mean())
    min_sleep = df['sleep'].min()
    max_sleep = df['sleep'].max()
    start  = conv_time_to_str(int(df['start'].mean()))
    min_start = conv_time_to_str(df['start'].min())
    max_start = conv_time_to_str(df['start'].max())
    end  = conv_time_to_str(int(df['end'].mean()))
    min_end  = conv_time_to_str(df['end'].min())
    max_end  = conv_time_to_str(df['end'].max())
    out.write(f'<tr><td class=all>全体</td><td class=all align="right">{sleep_ave//60}:{sleep_ave%60:02}</td>'
              f'<td class=all align="right">{min_sleep//60}:{min_sleep%60:02}</td>'
              f'<td class=all align="right">{max_sleep//60}:{max_sleep%60:02}</td>'
              f'<td class=all align="right">{start}</td>'
              f'<td class=all>{min_start}</td><td class=all>{max_start}</td>'
              f'<td class=all align="right">{end}</td>'
              f'<td class=all>{min_end}</td><td class=all>{max_end}</td></tr>\n')

#   時刻 int を形式 hh:mm の文字列に変換する
def conv_time_to_str(timedata) :
    hh = int(timedata) // 60
    mm = int(timedata) % 60
    s = f'{hh}:{mm:02}'
    return s

#   時刻 int をグラフ用の形式 hh,mm,0 の文字列に変換する
def conv_time_to_graph_str(timedata) :
    hh = int(timedata) // 60
    mm = int(timedata) % 60
    s = f'{hh},{mm},0'
    return s

def date_settings():
    global  today_date,today_mm,today_dd,today_yy,lastdate,today_datetime
    today_datetime = datetime.datetime.today()
    today_date = datetime.date.today()
    today_mm = today_date.month
    today_dd = today_date.day
    today_yy = today_date.year
    lastdate = today_date - timedelta(days=1)

def conv_hhmm_mm(hhmm) :
    if hhmm == "" :
        return 0
    hh,mm = hhmm.split(":")
    return int(hh) * 60 + int(mm)

#   yy/mm 形式の文字列を入力し int型の yymm を返す
def conv_yymm(yymm) :
    yy,mm = yymm.split("/")
    return int(yy) * 100 + int(mm)

def ftp_upload() : 
    if debug == 1 :
        return 
    with FTP_TLS(host=ftp_host, user=ftp_user, passwd=ftp_pass) as ftp:
        ftp.storbinary('STOR {}'.format(ftp_url), open(resultfile, 'rb'))

def today(s):
    global today_date
    d = today_datetime.strftime("%m/%d %H:%M")
    s = s.replace("%today%",d)
    out.write(s)
    today = date.today()

#   複数カラムの場合の判定
#     n  ...  何行目か     col ... 何カラム目か  limit ... 行数
#     表示しない場合(continueする場合) true を返す
def multi_col(n,col,limit) :
    if col == 1 :
        if n > limit :
            return True
    if col == 2 :
        if n <= limit :
            return True
    return False

def parse_template() :
    global out 
    f = open(templatefile , 'r', encoding='utf-8')
    out = open(resultfile,'w' ,  encoding='utf-8')
    for line in f :
        if "%daily_graph%" in line :
            daily_graph()
            continue
        if "%month_graph%" in line :
            month_graph()
            continue
        if "%month_start_graph%" in line :
            month_start_time_graph()
            continue
        if "%month_end_graph%" in line :
            month_end_time_graph()
            continue
        if "%start_time_graph%" in line :
            start_time_graph()
            continue
        if "%end_time_graph%" in line :
            end_time_graph()
            continue
        if "%month_info%" in line :
            month_info_table()
            continue
        if "%rank_sleep_max% " in line :
            ranking_sleep_time_max()
            continue
        if "%rank_sleep_30_max% " in line :
            ranking_sleep_time_30_max()
            continue
        if "%rank_sleep_min% " in line :
            ranking_sleep_time_min()
            continue
        if "%rank_sleep_30_min% " in line :
            ranking_sleep_time_30_min()
            continue
        if "%rank_month_sleep_max1%" in line :
            rank_month_sleep_max(1)
            continue
        if "%rank_month_sleep_max2%" in line :
            rank_month_sleep_max(2)
            continue
        if "%rank_month_sleep_min1%" in line :
            rank_month_sleep_min(1)
            continue
        if "%rank_month_sleep_min2%" in line :
            rank_month_sleep_min(2)
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
