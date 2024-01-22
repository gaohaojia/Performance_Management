import time
import datetime
import csv
import shutil

import key_io
import db_connector
import wecom_request
import push_data
import leaders_name

# 每轮循环等待时间
SLEEP_TIME = 0

# 是否打印日志
PRINT_INFO = True

# 获取上周日期
def get_last_wek_weekday(n):
    today_info = datetime.date.today()

    one_day = datetime.timedelta(days=1)
    seven_day = datetime.timedelta(days=7)

    last_week_day = today_info - seven_day
    last_week_day_n = last_week_day.weekday()

    if last_week_day_n < n:
        while last_week_day.weekday() != n:
            last_week_day += one_day
    else:
        while last_week_day.weekday() != n:
            last_week_day -= one_day

    return last_week_day

# 工作量登记处理函数
def sp_processor(db: db_connector.Connector, access_token, sp_no_list):

    # 判断审批是否都处理
    all_data = []
    for sp_no in sp_no_list:
        data = wecom_request.get_approval_data(access_token, sp_no)
        if data['sp_status'] == 1:
            if PRINT_INFO:
                print("\r存在未处理的工作量登记审批！")
            return None
        if data['sp_status'] != 2:
            continue
        all_data.append(data)
    
    # 遍历审批列表
    for data in all_data:
        user_name = wecom_request.get_name(access_token, data['applyer']['userid'])
        sql = 'SELECT id FROM member WHERE name=\'{}\''.format(user_name)
        user_sql_id = db.run_select(sql)[0][0]
        for content_data in data['apply_data']['contents'][1]['value']['children']:
            event = content_data['list'][0]['value']['text']
            start_time = content_data['list'][1]['value']['date_range']['new_begin']
            start_date = time.strftime("%Y/%m/%d", time.localtime(start_time))
            total_time = content_data['list'][1]['value']['date_range']['new_duration'] / 3600.0
            if total_time <= 0:
                continue
            sql = 'INSERT INTO performance (name, date, event, performance) VALUES ({}, \'{}\', \'{}\', {});'.format(user_sql_id, start_date, event, total_time)
            db.run_insert(sql)
            print("\r成功为{}添加{}点工作量".format(user_name, total_time), end="")
    
    return "success"


def main():

    # 循环次数
    loop_time = 0
    
    # 获取密钥
    SQL_KEY = key_io.get_SQL_KEY()
    WECOM_KEY = key_io.get_WECOM_KEY()
    if SQL_KEY is None or WECOM_KEY is None:
        return
    
    # 设置数据类型
    app_access_token = wecom_request.get_access_token(WECOM_KEY['corpid'], WECOM_KEY['AppSecret'])
    wecom_request.set_template(app_access_token, WECOM_KEY['AgentId'])
    
    # 连接数据库
    db = db_connector.Connector(SQL_KEY)
    if db.status == "error":
        print("数据库连接失败！")
        return
    
    # 上次成功操作的的时间
    time_key = key_io.get_time()
    submit_last_time = time_key["submit_last_time"] # 工作量登记审批
    query_last_time = time_key["query_last_time"] # 工作量查询审批
    news_last_time = time_key["news_last_time"] # 周报审批
    
    while True:
        if PRINT_INFO:
            print("睡眠等待中...", end="")
        time.sleep(SLEEP_TIME)

        # 避免频繁请求access_token
        if loop_time % 100 == 0:
            access_token = wecom_request.get_access_token(WECOM_KEY['corpid'], WECOM_KEY['corpsecret'])
            app_access_token = wecom_request.get_access_token(WECOM_KEY['corpid'], WECOM_KEY['AppSecret'])
            address_access_token = wecom_request.get_access_token(WECOM_KEY['corpid'], WECOM_KEY['AddressSecret'])
            if PRINT_INFO:
                print("\r刷新token成功")
        


        ##### 工作量登记处理部分 #####
        now_time = int(time.time())
        if PRINT_INFO:
            print("\r工作量登记处理中...", end="")
        # 请求审批id
        sp_no_list = wecom_request.get_sp_no_list(access_token, WECOM_KEY['submit_template_id'], submit_last_time, now_time, "")

        # 判断是否存在审批
        if len(sp_no_list) != 0:
            if not sp_processor(db, access_token, sp_no_list) is None:
                submit_last_time = now_time
        else:
            if PRINT_INFO:
                print("\r没有未处理的工作量登记审批")
            submit_last_time = now_time



        ##### 数据推送处理部分 #####
        if PRINT_INFO:
            print("\r数据推送处理中...", end="")
        user_id = wecom_request.get_all_user_id(address_access_token)
        now_date = datetime.date.today()

        # 获取所有队员工作量
        member_list = [] # 已处理列表
        result_list = [] # 结果列表
        leader_user_id = [] # 队长和项管的user_id
        last_week_cnt = 0 # 上周工作人数
        for user in user_id:

            if PRINT_INFO:
                print("\r处理完成{}".format(time.time()), end="")

            # 判断是否已处理过
            if user['userid'] in member_list:
                continue
            member_list.append(user['userid'])

            # 根据userid获取name
            name = wecom_request.get_name(app_access_token, user['userid'])
            
            # 判断是否为队长或项管
            if name in leaders_name.get_leaders_name():
                leader_user_id.append(user['userid'])
                continue

            # 判断数据库中是否存在该name
            sql = 'SELECT id FROM member WHERE name=\'{}\' AND (position <> 11 AND position <> 10)'.format(name)
            try:
                name_id = db.run_select(sql)[0][0]
            except:
                continue
            sql = 'SELECT date, event, performance FROM performance WHERE name={}'.format(name_id)
            data = db.run_select(sql)

            # 计算各项数据
            last_week_time, last_90day_time, total_time = 0, 0, 0
            has_last_week = False
            for i in data:
                total_time += i[2]
                if (now_date - i[0]).days <= 90:
                    last_90day_time += i[2]
                if (i[0] - get_last_wek_weekday(0)).days >= 0:
                    last_week_time += i[2]
                    has_last_week = True
            if has_last_week:
                last_week_cnt += 1
            result_list.append([name, round(last_week_time, 1), round(last_90day_time, 1), round(total_time, 1), user['userid']])

        # 按工作量排序
        result_list.sort(key=lambda result:result[3], reverse=True)

        # 写入工作量信息
        f = open('writing', 'w', newline="")
        csv_writer = csv.writer(f)
        csv_writer.writerow(["姓名", "上周工作量", "最近90天工作量", "总工作量", "排名"])

        # 给队员添加数据
        if PRINT_INFO:
            print("\r给队员添加数据中...                 ", end="")
        for idx in range(len(result_list)):

            # 计算排名
            rank_rate = (idx + 1) / len(result_list)
            rank = push_data.calculate_rank(rank_rate)
            
            # 写入csv
            csv_writer.writerow([*result_list[idx], rank])

            # 添加数据
            items = push_data.get_member_items(result_list[idx][2], result_list[idx][3], rank)
            push_info = wecom_request.push_data(app_access_token, WECOM_KEY['AgentId'], result_list[idx][4], items)
            if push_info['errcode'] != 0:
                print(push_info)

        f.close()
        if PRINT_INFO:
            print("\r写入工作量信息成功")

        # 将写完的结果保存，防止被覆盖
        shutil.copy('writing', r'info.csv')

        for user_id in leader_user_id:
            items = push_data.get_leaders_items(last_week_cnt, round(sum(i[3] for i in result_list) / len(result_list), 1), max(i[3] for i in result_list))
            wecom_request.push_data(app_access_token, WECOM_KEY['AgentId'], user_id, items)


        
        ##### 工作量查询回复部分 #####
        now_time = int(time.time())
        if PRINT_INFO:
            print("\r工作量查询回复处理中...", end="")
        # 获取审批内容
        sp_no_list = wecom_request.get_sp_no_list(access_token, WECOM_KEY['query_template_id'], query_last_time, now_time, "")
        if len(sp_no_list) == 0:
            if PRINT_INFO:
                print("\r无审批                 ")
        query_last_time = now_time

        # 判断审批是否都处理
        all_sp_data = []
        for sp_no in sp_no_list:
            sp_data = wecom_request.get_approval_data(access_token, sp_no)
            all_sp_data.append(sp_data)
        
        # 遍历审批列表
        for sp_data in all_sp_data:
            user_name = wecom_request.get_name(access_token, sp_data['applyer']['userid'])
            
            # 判断数据库中是否存在该name
            sql = 'SELECT id FROM member WHERE name=\'{}\''.format(user_name)
            try:
                name_id = db.run_select(sql)[0][0]
            except:
                wecom_request.send_message(app_access_token, sp_data['applyer']['userid'], WECOM_KEY['AgentId'], "### 工作量细则查询 \n[{}]\n>暂无您的工作量，有任何疑问请联系队长或填写[意见反馈](https://www.wenjuan.com/s/UZBZJveSUq/)。".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
                continue

            # 判断是否有工作量
            sql = 'SELECT date, event, performance FROM performance WHERE name={}'.format(name_id)
            user_data = db.run_select(sql)
            if len(user_data) == 0:
                wecom_request.send_message(app_access_token, sp_data['applyer']['userid'], WECOM_KEY['AgentId'], "### 工作量细则查询 \n[{}]\n>暂无您的工作量，有任何疑问请联系队长或填写[意见反馈](https://www.wenjuan.com/s/UZBZJveSUq/)。".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
                continue

            msg = "### 工作量细则查询 \n[{}]\n".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
            cnt = 0
            for i in user_data:
                cnt += 1
                msg += ">时间：<font color=\"info\">{}</font>  \n内容：{}  \n  \n工作量：<font color=\"warning\">{}</font>  \n".format(*i)
                if cnt >= 10:
                    wecom_request.send_message(app_access_token, sp_data['applyer']['userid'], WECOM_KEY['AgentId'], msg)
                    cnt = 0
                    msg = ""
            msg += "如有疑问，请填写[意见反馈](https://www.wenjuan.com/s/UZBZJveSUq/)。"
            wecom_request.send_message(app_access_token, sp_data['applyer']['userid'], WECOM_KEY['AgentId'], msg)
            


        ##### 周报回复部分 #####
        now_time = int(time.time())
        if PRINT_INFO:
            print("\r周报回复处理中...", end="")
        # 获取审批内容
        sp_no_list = wecom_request.get_sp_no_list(access_token, WECOM_KEY['news_template_id'], news_last_time, now_time, "")
        if len(sp_no_list) == 0:
            if PRINT_INFO:
                print("\r无审批                 ")
        news_last_time = now_time

        # 判断审批是否都处理
        all_sp_data = []
        for sp_no in sp_no_list:
            sp_data = wecom_request.get_approval_data(access_token, sp_no)
            all_sp_data.append(sp_data)
        
        # 遍历审批列表
        for sp_data in all_sp_data:
            member_data_list = []
            with open("info.csv") as csvfile:
                csv_data = csv.reader(csvfile)
                for row in csv_data:
                    member_data_list.append(row)
            msg = "### 战队周报 \n[{}]\n".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
            for member_data in member_data_list:
                msg += ">{} {} {} {}\n".format(member_data[0], member_data[1], member_data[2], member_data[3])
            wecom_request.send_message(app_access_token, sp_data['applyer']['userid'], WECOM_KEY['AgentId'], msg)
        
        loop_time += 1
        key_io.save_time(submit_last_time, query_last_time, news_last_time)
        if PRINT_INFO:
            print("\r完成一次循环")
    

if __name__ == "__main__":
    while True:
        try:
            main()
        except:
            time.sleep(60)