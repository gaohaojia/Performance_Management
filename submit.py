import time

# 工作量登记处理函数
def sp_processor(db, access_token, sp_no_list, wecom_request):

    # 判断审批是否都处理
    all_data = []
    for sp_no in sp_no_list:
        data = wecom_request.get_approval_data(access_token, sp_no)
        if data['sp_status'] == 1:
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