import shutil
import csv
import datetime

import leaders_name

SKIP_DATE_BEGIN = datetime.date(2023, 12, 11)
SKIP_DATE_END = datetime.date(2024, 1, 14)

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

# 计算排名
def calculate_rank(rank_rate):
    if rank_rate <= 0.05:
        rank = "前5%"
    elif rank_rate <= 0.1:
        rank = "前10%"
    elif rank_rate <= 0.2:
        rank = "前20%"
    elif rank_rate <= 0.3:
        rank = "前30%"
    elif rank_rate <= 0.5:
        rank = "前50%"
    else:
        rank = "后50%"
    return rank

# 获取队员推送数据
def get_member_items(last_90day_time, total_time, rank):
    items = [
        {
            "key":"最近90天工作量",
            "data":str(last_90day_time),
        },
        {
            "key":"本赛季总工作量",
            "data":str(total_time),
        },
        {
            "key":"本赛季队内排名",
            "data":rank,
        }
    ]
    return items

# 获取管理层推送数据
def get_leaders_items(last_week_cnt, average_time, max_time):
    items = [
        {
            "key":"上周工作人数",
            "data":str(last_week_cnt),
        },
        {
            "key":"全队平均工作量",
            "data":str(average_time),
        },
        {
            "key":"最高工作量",
            "data":str(max_time),
        }
    ]
    return items

def push_processor(db, wecom_request, address_access_token, app_access_token, WECOM_KEY):
    user_id = wecom_request.get_all_user_id(address_access_token)
    now_date = datetime.date.today()

    # 获取所有队员工作量
    member_list = [] # 已处理列表
    result_list = [] # 结果列表
    leader_user_id = [] # 队长和项管的user_id
    last_week_cnt = 0 # 上周工作人数
    for user in user_id:
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

            # 最近90天工作量
            if SKIP_DATE_BEGIN <= now_date <= SKIP_DATE_END:
                if (SKIP_DATE_END - i[0]).days <= 90:
                    last_90day_time += i[2]
            elif now_date < SKIP_DATE_BEGIN:
                if (now_date - i[0]).days - (SKIP_DATE_END - SKIP_DATE_BEGIN).days <= 90:
                    last_90day_time += i[2]
            else:
                if (now_date - i[0]).days <= 90:
                    last_90day_time += i[2]

            # 最近7天工作量
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
    for idx in range(len(result_list)):
        # 计算排名
        rank_rate = (idx + 1) / len(result_list)
        rank = calculate_rank(rank_rate)
        
        # 写入csv
        csv_writer.writerow([*result_list[idx], rank])
        # 添加数据
        items = get_member_items(result_list[idx][2], result_list[idx][3], rank)
        push_info = wecom_request.push_data(app_access_token, WECOM_KEY['AgentId'], result_list[idx][4], items)
        if push_info['errcode'] != 0:
            print(push_info)
    f.close()
    # 将写完的结果保存，防止被覆盖
    shutil.copy('writing', r'info.csv')
    for user_id in leader_user_id:
        items = get_leaders_items(last_week_cnt, round(sum(i[3] for i in result_list) / len(result_list), 1), max(i[3] for i in result_list))
        wecom_request.push_data(app_access_token, WECOM_KEY['AgentId'], user_id, items)