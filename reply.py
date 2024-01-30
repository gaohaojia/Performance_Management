import time
import csv

def reply_query_processor(db, now_time, query_last_time, wecom_request, access_token, app_access_token, WECOM_KEY):
    # 获取审批内容
    sp_no_list = wecom_request.get_sp_no_list(access_token, WECOM_KEY['query_template_id'], query_last_time, now_time, "")
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


def reply_news_processor(now_time, news_last_time, wecom_request, access_token, app_access_token, WECOM_KEY):
    # 获取审批内容
    sp_no_list = wecom_request.get_sp_no_list(access_token, WECOM_KEY['news_template_id'], news_last_time, now_time, "")
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