import time

import submit
import push_data
import reply

import key_io
import db_connector
import wecom_request

# 每轮循环等待时间
SLEEP_TIME = 0

# 是否打印日志
PRINT_INFO = True


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
            if not submit.sp_processor(db, access_token, sp_no_list, wecom_request) is None:
                submit_last_time = now_time
        else:
            if PRINT_INFO:
                print("\r没有未处理的工作量登记审批")
            submit_last_time = now_time



        ##### 数据推送处理部分 #####
        if PRINT_INFO:
            print("\r数据推送处理中...", end="")
        push_data.push_processor(db, wecom_request, address_access_token, app_access_token, WECOM_KEY)


        
        ##### 工作量查询回复部分 #####
        now_time = int(time.time())
        if PRINT_INFO:
            print("\r工作量查询回复处理中...", end="")
        reply.reply_query_processor(db, now_time, query_last_time, wecom_request, access_token, app_access_token, WECOM_KEY)
        query_last_time = now_time
        
            


        ##### 周报回复部分 #####
        now_time = int(time.time())
        if PRINT_INFO:
            print("\r周报回复处理中...", end="")
        reply.reply_news_processor(now_time, news_last_time, wecom_request, access_token, app_access_token, WECOM_KEY)
        news_last_time = now_time



        loop_time += 1
        key_io.save_time(submit_last_time, query_last_time, news_last_time)
    

if __name__ == "__main__":
    while True:
        try:
            main()
        except:
            time.sleep(60)