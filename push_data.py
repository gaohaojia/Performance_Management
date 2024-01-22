
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