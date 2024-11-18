#!/usr/bin/python
# -*- coding: utf-8 -*-

from ast import If
import os
import csv
import datetime
import pandas as pd
import locale
import shutil
from ftplib import FTP_TLS
from datetime import date,timedelta
import calendar

# 24/11/18 v0.01    日別集計を追加 
version = "0.01"  

# TODO: 

debug = 0     #  1 ... debug
appdir = os.path.dirname(os.path.abspath(__file__))

dataname = "/CSVFile.csv"
datafile = ""
backfile = appdir + "/save.txt"
datadir = appdir
templatefile = appdir + "/dog_templ.htm"
resultfile = appdir + "/dog.htm"
conffile = appdir + "/tracker.conf"
logfile = appdir + "\\tracker.log"
pastdata = appdir + "/pastdata.txt"
rawdata = appdir + "/rawdata.txt"
past_pf_dic = []   #  過去の月別時間 pf   辞書  キー  hhmm   値  分

ftp_host = ftp_user = ftp_pass = ftp_url =  ""
df_pf = ""
out = ""
logf = ""
pixela_url = ""
pixela_token = ""

df_mon_pf = ""   #  過去の月ごとの時間  pf
df_mon_vn = ""   #  過去の月ごとの時間  vn
df_yy_pf = ""    #  年毎の時間  pf
df_yy_vn = ""    #  年毎の時間  vn
month_data_list = []  # 月ごとの情報 (yymm,sum,mean,max,zero) のタプルを要素とするリスト
df_dd = ""    #  日ごとのデータ df  pf 用
today_date = ""   # 今日の日付  datetime型

def main_proc():
    global  datafile,logf

    locale.setlocale(locale.LC_TIME, '')
    logf = open(logfile,'a',encoding='utf-8')
    logf.write("\n=== start %s === \n" % datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    date_settings()
    read_config()
    read_data()
    # read_pastdata()
    
    totalling_daily_data()
    # output_ptime_to_csv()
    # create_month_data()
    # create_year_data_pf()
    # create_year_data_vn()
    parse_template()
    # ftp_upload()
    # post_process_datafile()
    # logf.write("\n=== end   %s === \n" % datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    # logf.close()

def read_data():
    global df_pf,df_vn,datafile,df

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
            if row[0] == "散歩" :
                date_list.append(row[1])
                tt = row[3].replace("'","")
                tt = conv_hhmm_mm(tt) 
                process_list.append(tt)

    df = pd.DataFrame(list(zip(date_list,process_list)), columns = ['date','ptime'])
#    df_day = df
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
#    df_day = df_day.set_index("date")

    #print(df)

def daily_info() :
    df_tmp = df_dd.tail(30)
    for index , row in df_tmp.iterrows() :
        date_str = index.strftime("%m/%d(%a) %H:%M")
        out.write(f'<tr><td>{date_str}</td><td align="right">{row["ptime"]}</td></tr>')

def detail_info() :
    df_tmp = df.tail(30)
    for index , row in df_tmp.iterrows() :
        date_str = index.strftime("%m/%d(%a) %H:%M")
        out.write(f'<tr><td>{date_str}</td><td align="right">{row["ptime"]}</td></tr>')


#   1日ごとの練習時間を集計し  date ptime のカラムを持つ df  df_dd を作成する
#   df_dd は ptime が 0 の日(データ)も含む     date は 2024年1月1日から実行前日まで
def totalling_daily_data() :
    global df_dd

    df_tmp  = df.resample('D')['ptime'].sum()
    date_list = []
    ptime_list = []
    start_date  = datetime.date(2024, 1, 1)
    target_date = start_date
    end_date = datetime.date.today()
    #  start_date から昨日まで全日付をチェックする
    while target_date  < end_date:
        str_date = target_date.strftime("%Y-%m-%d")
        try:
            ptime = df_tmp.loc[str_date]
        except KeyError:          #  日付のデータがなければ ptime は 0
            ptime = 0 

        date_list.append(target_date)
        ptime_list.append(ptime)
        target_date +=  datetime.timedelta(days=1)

    df_dd = pd.DataFrame(list(zip(date_list,ptime_list)), columns = ['date','ptime'])
    df_dd['date'] = pd.to_datetime(df_dd["date"])
    df_dd = df_dd.set_index("date")
    print(df_dd)

# 月ごとの情報 month_data_list と df_mon_pf を作成する
# month_data_list は (yymm,sum,mean,max,zero) のタプルを要素とするリスト
def create_month_data() :
    global df_mon_pf,df_mon_vn,month_data_list

    curmm = 1
    endmm = today_date.month
    while curmm <= endmm :
        start = datetime.datetime(2024, curmm, 1)
        end = datetime.datetime(2024, curmm+1, 1)
        df_mm = df_dd[(df_dd['date'] >= start) & (df_dd['date'] < end )]
        count  = df_mm['ptime'].count()
        if count == 0 :    #  データがなければ終了   月初の場合
            break 
        p_sum = df_mm['ptime'].sum()
        p_ave = df_mm['ptime'].mean()
        p_max = df_mm['ptime'].max()
        v_sum = df_mm['vtime'].sum()
        v_ave = df_mm['vtime'].mean()
        v_max = df_mm['vtime'].max()

        df_ptime_zero = (df_mm['ptime'] == 0)   # 時間が0 の日数
        ptime_zero = df_ptime_zero.sum()
        df_vtime_zero = (df_mm['vtime'] == 0)   # 時間が0 の日数
        vtime_zero = df_vtime_zero.sum()
        yymm = 24 * 100 + curmm
        tp = (yymm,p_sum,p_ave,p_max,ptime_zero,v_sum,v_ave,v_max,vtime_zero)
        month_data_list.append(tp)

        df_tmp_pf = pd.DataFrame({'yymm': [yymm], 'time': [p_sum]})
        df_mon_pf = pd.concat([df_mon_pf, df_tmp_pf])
        df_tmp_vn = pd.DataFrame({'yymm': [yymm], 'time': [v_sum]})
        df_mon_vn = pd.concat([df_mon_vn, df_tmp_vn])
        curmm += 1 

    df_mon_pf = df_mon_pf.reset_index(drop=True)
    df_mon_vn = df_mon_vn.reset_index(drop=True)
    #print(df_mon_vn)

def create_year_data_pf() :
    global df_yy_pf
    df_yy_pf = create_year_data_com(df_mon_pf)

def create_year_data_vn() :
    global df_yy_vn
    df_yy_vn = create_year_data_com(df_mon_vn)

def create_year_data_com(df_mon) :
    cur = 0
    ptime = 0 
    ptime_list = []
    yy_list = []
    for _ , row in df_mon.iterrows() :
        yymm = row['yymm']
        yy = int(yymm / 100)
        if yy == cur :
            ptime = ptime + row['time']
        else :
            if cur != 0 :
                ptime_list.append(ptime)
            cur = yy
            yy_list.append(yy)
            ptime = row['time']
    ptime_list.append(ptime)
    df_yy = pd.DataFrame(list(zip(yy_list,ptime_list)), columns = ['yy','time'])
    return(df_yy)
    #print(df_yy_pf)

def date_settings():
    global  today_date,today_mm,today_dd,today_yy,yesterday,today_datetime
    today_datetime = datetime.datetime.today()
    today_date = datetime.date.today()
    today_mm = today_date.month
    today_dd = today_date.day
    today_yy = today_date.year
    yesterday = today_date - timedelta(days=1)

#   pf と vn で過去データの数が違うので df は別に持つ
def read_pastdata():
    global df_mon_pf,df_mon_vn
    yymmpf_list = []
    yymmvn_list = []
    pf_list = []
    vn_list = []
    f = open(pastdata,'r', encoding='utf-8')
    for line in f :
        line = line.strip()
        n = line.split("\t")
        if len(n) == 2 :
            dateyymm,vn = line.split("\t")
            pf = ""
        else :
            dateyymm,vn,pf = line.split("\t")
        vn = conv_hhmm_mm(vn)
        pf = conv_hhmm_mm(pf)
        yymm = conv_yymm(dateyymm)
        if yymm >= 2001 :     # pf は 20年1月から
            yymmpf_list.append(yymm)
            pf_list.append(pf)
        yymmvn_list.append(yymm)
        vn_list.append(vn)

    f.close()
    df_mon_pf = pd.DataFrame(list(zip(yymmpf_list,pf_list)), columns = ['yymm','time'])
    df_mon_vn = pd.DataFrame(list(zip(yymmvn_list,vn_list)), columns = ['yymm','time'])
    #print(df_mon_vn)

#  hh:mm 形式の文字列を渡し、分単位に変換した数値を返す
def conv_hhmm_mm(hhmm) :
    if hhmm == "" :
        return 0
    hh,mm = hhmm.split(":")
    return int(hh) * 60 + int(mm)

#   yy/mm 形式の文字列を入力し int型の yymm を返す
def conv_yymm(yymm) :
    yy,mm = yymm.split("/")
    return int(yy) * 100 + int(mm)
    
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


#   rawdata ファイルに yy/mm/dd,ptime,vtime の形式で全データを出力する
#   バックアップ用途
def output_ptime_to_csv():
    f = open(rawdata,'w',encoding='utf-8')
    for _ , row in df_dd.iterrows() :    
        date_str = row['date'].strftime("%Y/%m/%d")
        f.write(f"{date_str},{row['ptime']},{row['vtime']}\n")
    f.close()

#  7日間の移動平均
#  TODO:  30日間等期限つきにする
def daily_movav_com(type) :
    mov_ave_dd = 7
    df_movav  =  df_dd.copy()
    if type == 0 :
        df_movav['mvave']  = df_movav['ptime'].rolling(mov_ave_dd).mean()
    else :
        df_movav['mvave']  = df_movav['vtime'].rolling(mov_ave_dd).mean()
    for _ , row in df_movav.iterrows() :
        ptime = row['mvave']
        if pd.isna(ptime) :
            continue
        dd = row['date'].strftime("%m/%d")
        out.write(f"['{dd}',{ptime:5.0f}],") 

#   過去30日間の1日ごとの練習時間をグラフにする
def daily_graph() :
    df30 = df_dd.tail(30)
    for _ , row in df30.iterrows() :
        date_str = row['date'].strftime('%d')
        out.write(f"['{date_str}',{row['ptime']:5.0f}],")

def daily_graph_vn() :
    df30 = df_dd.tail(30)
    for _ , row in df30.iterrows() :
        date_str = row['date'].strftime('%d')
        out.write(f"['{date_str}',{row['vtime']:5.0f}],")

#   前月の日数
def last_month_days() :
    this_month = datetime.datetime(today_date.year, today_date.month, 1)
    last_month_end = this_month - datetime.timedelta(days=1)
    return(last_month_end.day)

# 分単位の数値を渡し  hh:mm 形式の文字列を返す
def minutes_to_hhmm(mm) :
    hhmm = f'{mm//60}:{mm%60:02}'
    return hhmm

#   月別情報
def month_info()  :
    #  年月  合計時間  1日平均時間  最大時間   無練習日率
    #  TODO: 年は考慮していない
    
    for item in month_data_list :
        yymm,sum,ave,max,zero,vsum,vave,vmax,vzero = item
        yy = int(yymm / 100)
        mm =  yymm % 100
        if mm  == today_mm :   #  今月なら 前日まで
            td = today_dd -1 
        else :
            td = calendar.monthrange(yy, mm)[1]   # 月の日数を取得 (月の初日の曜日, 月の日数)のタプルを返す。

        out.write(f'<tr><td align="right">{yymm}</td><td align="right">{minutes_to_hhmm(sum)}</td>'
                  f'<td align="right">{ave:5.1f}</td><td align="right">{minutes_to_hhmm(max)}</td>'
                  f'<td align="right">{zero}</td>'
                  f'<td align="right">{zero/td * 100:5.2f}</td>'
                  f'<td align="right">{minutes_to_hhmm(vsum)}</td>'
                  f'<td align="right">{vave:5.1f}</td><td align="right">{minutes_to_hhmm(vmax)}</td>'
                  f'<td align="right">{vzero}</td>'
                  f'<td align="right">{vzero/td * 100:5.2f}</td></tr>\n')
    all_statistics()

def all_statistics() :
    pf_ave = df_dd['ptime'].mean()
    vn_ave = df_dd['vtime'].mean()

    zero_day_p = 0 
    zero_day_v = 0 
    max_p = 0
    max_v = 0 
    for item in month_data_list :
        yymm,sum,ave,max,zero,vsum,vave,vmax,vzero = item
        zero_day_p += zero
        zero_day_v += vzero
        if max > max_p :
            max_p = max
        if vmax > max_v :
            max_v = vmax

    from_dd  = datetime.date(year=2024, month=1, day=1)
    td = today_date - from_dd

    out.write(f'<tr><td class=all>全体</td><td class=all align="right">--</td>'
                f'<td class=all align="right">{pf_ave:5.1f}</td>'
                f'<td class=all align="right">{minutes_to_hhmm(max_p)}</td>'
                f'<td class=all align="right">{zero_day_p}</td>'
                f'<td class=all align="right">{zero_day_p*100/td.days:5.2f}</td>'
                f'<td class=all align="right">--</td>'
                f'<td class=all align="right">{vn_ave:5.1f}</td>'
                f'<td class=all align="right">{minutes_to_hhmm(max_v)}</td>'
                f'<td class=all align="right">{zero_day_v}</td>'
                f'<td class=all align="right">{zero_day_v*100/td.days:5.2f}</td></tr>\n')

#   月ごとの時間グラフ
def month_graph_com(df_mon) :
    for _ , row in df_mon.iterrows() :
        yymm = int(row['yymm'])
        yy = int(yymm / 100) + 2000
        mm = yymm % 100
        if yy == today_yy and mm == today_mm :
            n = today_dd - 1
        else :
            n = calendar.monthrange(yy, mm)[1]   # 月の日数
        r = int(row['time']) / n 
        out.write(f"['{row['yymm']}',{r}],")

#   年ごとの時間グラフ
def year_graph_com(df_yy) :
    for _ , row in df_yy.iterrows() :
        yy = row['yy']
        ptime = row['time'] 
        if yy == (today_yy - 2000) :
            start = datetime.date(yy+2000,1,1)   # 1/1
            dd = today_date - start         # 1/1 からの日数
            ptime = ptime  / dd.days
        else :
            ptime = ptime  / 365

        out.write(f"['{yy}',{ptime}],")

#   ランキング
def ranking() :
    sort_df = df_dd.copy()
    sort_df = sort_df.sort_values('ptime',ascending=False)
    i = 0 
    for _ , row in sort_df.iterrows() :
        i += 1 
        date_str = row['date'].strftime('%m/%d (%a)')
        if row['date'].date() == yesterday :   # row['date'] はdatetime型なのでdate()で日付部分のみ
            date_str = f'<span class=red>{date_str}</span>'
        hh = row['ptime'] // 60
        mm = row['ptime'] % 60
        time_str = f'{hh:02}:{mm:02}'
        out.write(f"<tr><td align='right'>{i}</td><td align='right'>{time_str}</td><td>{date_str}</td></tr>")
        if i >= 10 :
            break

def ranking_month() :
    sort_df = df_dd.copy()
    sort_df = sort_df.tail(30)
    sort_df = sort_df.sort_values('ptime',ascending=False)
    i = 0 
    for _ , row in sort_df.iterrows() :
        i += 1 
        date_str = row['date'].strftime('%m/%d (%a)')
        if row['date'].date() == yesterday :   # row['date'] はdatetime型なのでdate()で日付部分のみ
            date_str = f'<span class=red>{date_str}</span>'
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
    d = today_datetime.strftime("%m/%d %H:%M")
    s = s.replace("%today%",d)
    out.write(s)

def parse_template() :
    global out 
    f = open(templatefile , 'r', encoding='utf-8')
    out = open(resultfile,'w' ,  encoding='utf-8')
    for line in f :
        if "%daily_info%" in line :
            daily_info()
            continue
        if "%detail_info%" in line :
            detail_info()
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
