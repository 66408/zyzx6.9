import random
import string
import datetime
import json
import os
import time
import re  # 用于邮箱格式验证
import shutil  # 添加用于文件操作

# 邮箱格式验证函数
def is_valid_email(email):
    """验证邮箱格式是否有效"""
    # 简单的邮箱格式正则表达式
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

# 保存和读取上次登录用户的函数
def save_last_user(username):
    """保存上次登录的用户名"""
    with open("last_user.txt", "w") as f:
        f.write(username)

def get_last_user():
    """获取上次登录的用户名，如果不存在则返回None"""
    try:
        with open("last_user.txt", "r") as f:
            username = f.read().strip()
            return username if username else None
    except FileNotFoundError:
        return None

# 检查更新状态的函数
def check_update_status():
    """检查程序更新状态，控制更新提示逻辑"""
    status_file = "update_status.txt"
    
    # 读取当前状态（第一次运行时文件不存在）
    try:
        with open(status_file, "r") as f:
            status = f.read().strip()
    except FileNotFoundError:
        status = "first_run"  # 第一次运行标记
    
    # 第一次打开：显示已是最新版本
    if status == "first_run":
        print("=== 版本检查 ===")
        print("当前已是最新版本，无需更新！")
        print("================\n")
        # 更新状态为第二次运行
        with open(status_file, "w") as f:
            f.write("second_run")
        return False
    
    # 第二次打开：显示有更新
    elif status == "second_run":
        print("=== 版本检查 ===")
        print("检测到新版本更新！")
        choice = input("是否进行更新？(y/n): ").strip().lower()
        
        if choice == "y":
            print("开始更新...")
            # 20秒更新倒计时
            for i in range(20, 0, -1):
                print(f"\r更新将在 {i} 秒后完成并自动关闭...", end="")
                time.sleep(1)
            print("\n更新完成！程序将自动关闭。")
            # 重置状态，下次打开回到初始状态
            with open(status_file, "w") as f:
                f.write("first_run")
            # 自动关闭程序
            exit()
        else:
            print("已取消更新，将继续使用当前版本\n")
            # 重置状态，下次打开回到初始状态
            with open(status_file, "w") as f:
                f.write("first_run")
            return False

class User:
    def __init__(self, username, email, password, payment_password=None):
        self.username = username
        self.email = email  # 新增邮箱属性
        self.password = password
        self.payment_password = payment_password or self._generate_default_payment_password()
        self.emeralds = 0
        self.diamonds = 0  # 钻石数量初始化为0
        self.inventory = []
        self.orders = []
        self.transactions = []
        self.default_address = ""  # 用户默认地址
        self.security_questions = []  # 安全问题和答案列表 [(问题, 答案), ...]
        self.shopping_cart = {}  # 购物车: {item_key: (item, quantity)}
        
        # 任务相关属性
        self.daily_checkin = {
            "last_checkin_date": None,  # 上次签到日期
            "streak_days": 0  # 连续签到天数
        }
        self.tasks = {
            "watch_ad": False,  # 看广告任务完成状态
            "buy_item": False   # 购买商品任务完成状态
        }
        
        # 添加SVIP属性
        self.svip = {
            "active": False,
            "type": None,  # 'month', 'quarter', 'year'
            "purchase_date": None,
            "expiry_date": None
        }
        
        # 添加网盘存储路径
        self.cloud_storage_path = f"cloud_storage/{username}"
        # 确保目录存在
        if not os.path.exists(self.cloud_storage_path):
            os.makedirs(self.cloud_storage_path)
        
        # 添加每日随机礼包相关属性
        self.last_random_gift_date = None  # 上次领取随机礼包的日期
    
    def _generate_default_payment_password(self):
        # 生成默认支付密码（用户名前4位+随机数字）
        base = self.username[:4] if len(self.username) >= 4 else self.username
        digits = ''.join(random.choices(string.digits, k=4))
        return base + digits

    def set_payment_password(self, current_password, new_password, confirm_password):
        """修改支付密码，需要验证当前密码并确认新密码"""
        # 验证当前支付密码
        if not self.verify_payment_password(current_password):
            print("当前支付密码错误！")
            return False
            
        # 验证新密码和确认密码是否一致
        if new_password != confirm_password:
            print("两次输入的新密码不一致！")
            return False
            
        # 验证新密码不为空
        if not new_password.strip():
            print("新密码不能为空！")
            return False
            
        # 设置新密码
        self.payment_password = new_password
        print("支付密码修改成功！")
        return True

    def set_password(self, new_password):
        self.password = new_password
        print("登录密码修改成功！")

    def verify_password(self, password):
        return self.password == password

    def verify_payment_password(self, password):
        return self.payment_password == password

    def add_security_question(self, question, answer):
        """添加安全问题和答案，最多10个"""
        if len(self.security_questions) < 10:
            self.security_questions.append((question, answer))
            return True
        return False

    def verify_security_answers(self, answers):
        """验证安全问题答案是否正确"""
        if len(answers) != len(self.security_questions):
            return False
            
        for i, (_, correct_answer) in enumerate(self.security_questions):
            if answers[i] != correct_answer:
                return False
        return True

    def add_emeralds(self, amount):
        self.emeralds += amount
        self._record_transaction(f"获得 {amount} 绿宝石", "收入")

    def add_diamonds(self, amount):
        # 确保钻石数量正确增加
        self.diamonds += amount
        self._record_transaction(f"获得 {amount} 钻石", "收入")

    def subtract_emeralds(self, amount):
        if self.emeralds >= amount:
            self.emeralds -= amount
            self._record_transaction(f"消费 {amount} 绿宝石", "支出")
            return True
        return False

    def subtract_diamonds(self, amount):
        if self.diamonds >= amount:
            self.diamonds -= amount
            self._record_transaction(f"消费 {amount} 钻石", "支出")
            return True
        return False

    def add_item_to_inventory(self, item, quantity=1):
        # 支持添加多个相同物品
        for _ in range(quantity):
            self.inventory.append(item)

    def remove_item_from_inventory(self, item, quantity=1):
        # 支持移除多个相同物品
        removed = 0
        while removed < quantity and item in self.inventory:
            self.inventory.remove(item)
            removed += 1
        return removed == quantity

    def add_order(self, order):
        self.orders.append(order)
        # 购买商品后标记任务完成
        self.tasks["buy_item"] = True

    def _record_transaction(self, description, transaction_type):
        transaction = {
            "id": ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
            "description": description,
            "type": transaction_type,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "balance_emeralds": self.emeralds,
            "balance_diamonds": self.diamonds
        }
        self.transactions.append(transaction)

    def display_transactions(self):
        print("\n=== 交易记录 ===")
        if not self.transactions:
            print("暂无交易记录")
            return
        for i, tx in enumerate(self.transactions, 1):
            print(f"{i}. [{tx['type']}] {tx['description']}")
            print(f"   交易ID: {tx['id']}")
            print(f"   时间: {tx['timestamp']}")
            print(f"   余额: 绿宝石 {tx['balance_emeralds']}, 钻石 {tx['balance_diamonds']}")
            print("---------------------")

    def set_default_address(self, address):
        self.default_address = address
        print("默认地址设置成功！")
        
    def check_delivered_orders(self):
        """检查已到货的订单并添加到背包"""
        current_time = datetime.datetime.now()
        delivered_count = 0
        
        for order in self.orders:
            # 虚拟商品无需等待，购买后立即到账
            if not order.item.is_physical and not order.is_delivered:
                self.add_item_to_inventory(order.item, order.quantity)
                order.is_delivered = True
                delivered_count += 1
                print(f"\n您购买的虚拟商品 {order.item.name} x{order.quantity} 已到账并添加到背包！")
            # 实物商品检查是否到达预计时间
            elif order.item.is_physical and not order.is_delivered and not order.is_refunded and current_time >= order.estimated_arrival_time:
                # 订单已到货，添加到背包
                self.add_item_to_inventory(order.item, order.quantity)
                order.is_delivered = True
                # 记录发货时间为预计送达时间
                order.shipped_time = order.estimated_arrival_time
                delivered_count += 1
                print(f"\n您购买的 {order.item.name} x{order.quantity} 已送达并添加到背包！")
        
        if delivered_count > 0:
            # 保存更新后的数据
            shop = Shop()  # 获取shop实例
            shop.save_data()
    
    # 购物车相关方法
    def _get_item_key(self, item):
        """生成商品的唯一键，用于购物车存储"""
        return f"{item.name}_{item.price}_{item.currency_type}_{'physical' if item.is_physical else 'virtual'}"
    
    def add_to_cart(self, item, quantity=1):
        """添加商品到购物车"""
        key = self._get_item_key(item)
        if key in self.shopping_cart:
            self.shopping_cart[key] = (item, self.shopping_cart[key][1] + quantity)
        else:
            self.shopping_cart[key] = (item, quantity)
        return True
    
    def remove_from_cart(self, item_key, quantity=None):
        """从购物车移除商品，quantity为None时移除全部"""
        if item_key not in self.shopping_cart:
            return False
            
        if quantity is None or quantity >= self.shopping_cart[item_key][1]:
            del self.shopping_cart[item_key]
        else:
            item = self.shopping_cart[item_key][0]
            self.shopping_cart[item_key] = (item, self.shopping_cart[item_key][1] - quantity)
        return True
    
    def clear_cart(self):
        """清空购物车"""
        self.shopping_cart.clear()
    
    def get_cart_total(self):
        """计算购物车中所有商品的总价，按货币类型分类"""
        totals = {"绿宝石": 0, "钻石": 0}
        for item, quantity in self.shopping_cart.values():
            totals[item.currency_type] += item.price * quantity
        return totals
    
    def is_cart_empty(self):
        """检查购物车是否为空"""
        return len(self.shopping_cart) == 0
    
    # 任务相关方法
    def checkin(self):
        """每日签到功能"""
        today = datetime.date.today()
        last_date = self.daily_checkin["last_checkin_date"]
        
        # 检查是否已经签到
        if last_date == today:
            return False, "今天已经签过到了"
            
        # 检查是否连续签到
        if last_date and (today - last_date).days == 1:
            self.daily_checkin["streak_days"] += 1
        else:
            self.daily_checkin["streak_days"] = 1  # 重置连续签到天数
            
        # 根据连续签到天数奖励绿宝石
        if self.daily_checkin["streak_days"] >= 7:
            reward = 50  # 7天以上连续签到奖励
        elif self.daily_checkin["streak_days"] >= 3:
            reward = 30  # 3-6天连续签到奖励
        else:
            reward = 10  # 1-2天连续签到奖励
            
        # 更新签到信息
        self.daily_checkin["last_checkin_date"] = today
        self.add_emeralds(reward)
        
        return True, f"签到成功！获得 {reward} 绿宝石，当前连续签到 {self.daily_checkin['streak_days']} 天"
    
    def reset_daily_tasks(self):
        """重置每日任务（在新的一天登录时调用）"""
        today = datetime.date.today()
        last_checkin = self.daily_checkin["last_checkin_date"]
        
        # 如果最后签到日期不是今天，说明是新的一天，重置任务
        if not last_checkin or last_checkin < today:
            self.tasks = {
                "watch_ad": False,
                "buy_item": False
            }
    
    def complete_task(self, task_name):
        """标记任务为已完成并奖励绿宝石"""
        if task_name not in self.tasks:
            return False, "任务不存在"
            
        if self.tasks[task_name]:
            return False, "该任务已经完成"
            
        # 根据任务类型给予随机绿宝石奖励
        if task_name == "watch_ad":
            reward = random.randint(5, 15)
            self.tasks[task_name] = True
            self.add_emeralds(reward)
            return True, f"完成看广告任务，获得 {reward} 绿宝石！"
        elif task_name == "buy_item":
            reward = random.randint(10, 25)
            self.tasks[task_name] = True
            self.add_emeralds(reward)
            return True, f"完成购买商品任务，获得 {reward} 绿宝石！"
            
        return False, "未知错误"
    
    # SVIP相关方法
    def activate_svip(self, svip_type):
        """激活SVIP会员"""
        self.svip["active"] = True
        self.svip["type"] = svip_type
        self.svip["purchase_date"] = datetime.date.today()
        
        # 设置过期时间
        if svip_type == "month":
            self.svip["expiry_date"] = self.svip["purchase_date"] + datetime.timedelta(days=30)
        elif svip_type == "quarter":
            self.svip["expiry_date"] = self.svip["purchase_date"] + datetime.timedelta(days=90)
        elif svip_type == "year":
            self.svip["expiry_date"] = self.svip["purchase_date"] + datetime.timedelta(days=365)
        
        # 创建专属文件夹
        if not os.path.exists(self.cloud_storage_path):
            os.makedirs(self.cloud_storage_path)
        
        # 添加专属虚拟商品
        self.add_item_to_inventory(Item("SVIP专属礼包", 0, "SVIP", "SVIP会员专属礼包", False))
        
        print(f"🎉 恭喜您已成为SVIP会员！有效期至 {self.svip['expiry_date']}")
    
    def check_svip_status(self):
        """检查SVIP状态，如果过期则取消特权"""
        if self.svip["active"] and self.svip["expiry_date"]:
            today = datetime.date.today()
            if today > self.svip["expiry_date"]:
                # SVIP已过期
                self.svip["active"] = False
                self.svip["type"] = None
                
                # 移除专属虚拟商品（保留专属礼包作为纪念）
                # self.remove_svip_exclusive_items()
                
                print("⚠️ 您的SVIP会员已过期，相关特权已取消")
                return False
            return True
        return False
    
    def remove_svip_exclusive_items(self):
        """移除SVIP专属物品"""
        # 保留专属礼包
        self.inventory = [item for item in self.inventory if not (item.name.startswith("SVIP专属") and item.name != "SVIP专属礼包")]
    
    def is_svip_active(self):
        """检查SVIP是否激活"""
        return self.svip["active"] and self.check_svip_status()
    
    def get_svip_remaining_days(self):
        """获取SVIP剩余天数"""
        if self.svip["active"] and self.svip["expiry_date"]:
            today = datetime.date.today()
            remaining = (self.svip["expiry_date"] - today).days
            return max(0, remaining)
        return 0
    
    # 每日随机礼包功能
    def can_receive_random_gift(self):
        """检查今天是否可以领取随机礼包"""
        today = datetime.date.today()
        return self.last_random_gift_date != today
    
    def receive_random_gift(self):
        """领取每日随机礼包"""
        today = datetime.date.today()
        if self.last_random_gift_date == today:
            return False, "今天已经领取过随机礼包了！"
            
        # 随机决定奖励类型和数量
        gift_type = random.choice(["绿宝石", "钻石"])
        amount = random.randint(10, 50)
        
        # 发放奖励
        if gift_type == "绿宝石":
            self.add_emeralds(amount)
        else:
            self.add_diamonds(amount)
        
        # 更新领取日期
        self.last_random_gift_date = today
        
        return True, f"恭喜！您获得了 {amount} 个{gift_type}！"

class Item:
    def __init__(self, name, price, currency_type, description, is_physical=True, 
                 is_lucky=False, quantity_available=None, delivery_type="1-2天"):
        self.name = name
        self.price = price
        self.currency_type = currency_type
        self.description = description
        self.is_physical = is_physical  # True表示实物商品，False表示虚拟商品
        self.is_lucky = is_lucky  # 是否为抽奖物品
        # 商品可用数量，None表示无限
        self.quantity_available = quantity_available if quantity_available is not None else None
        # 到货时间类型："今天" 或 "1-2天"（仅适用于实物商品）
        self.delivery_type = delivery_type

    def __str__(self):
        item_type = "实物商品" if self.is_physical else "虚拟商品"
        delivery_info = f" (预计{self.delivery_type}送达)" if self.is_physical else ""
        return f"{self.name} - {self.price} {self.currency_type} - {item_type} - {self.description}{delivery_info}"
    
    def __eq__(self, other):
        # 用于比较物品是否相同
        if not isinstance(other, Item):
            return False
        return (self.name == other.name and 
                self.price == other.price and 
                self.currency_type == other.currency_type and
                self.is_physical == other.is_physical)

class Order:
    def __init__(self, item, address=None, quantity=1):
        self.item = item
        self.quantity = quantity  # 购买数量
        self.address = address  # 收货地址（仅适用于实物商品）
        self.order_id = self._generate_order_id()
        self.purchase_time = datetime.datetime.now()
        # 发货时间，初始为None表示未发货
        self.shipped_time = None
        # 根据商品的到货时间类型计算预计送达时间（仅适用于实物商品）
        self.estimated_arrival_time = self._calculate_estimated_arrival(item.delivery_type) if item.is_physical else None
        self.is_refunded = False
        self.is_delivered = False  # 标记订单是否已送达
        self.is_confirmed = False  # 新增：标记订单是否已确认收货（仅适用于实物商品）

    def _generate_order_id(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    def _calculate_estimated_arrival(self, delivery_type):
        # 根据到货时间类型计算预计送达时间
        if delivery_type == "今天":
            # 今天送达：当天的18:00到23:59之间
            today = datetime.datetime.now().date()
            return datetime.datetime.combine(today, datetime.time(random.randint(18, 23), random.randint(0, 59)))
        else:  # 1-2天
            days = random.randint(1, 2)
            return self.purchase_time + datetime.timedelta(days=days)
    
    def is_shipped(self):
        """判断订单是否已发货"""
        return self.shipped_time is not None
    
    def can_refund(self):
        """判断订单是否可以退款：
           - 实物商品：未发货，或已发货但不超过1小时
           - 虚拟商品：不支持退款
        """
        # 虚拟商品不支持退款
        if not self.item.is_physical:
            return False
            
        current_time = datetime.datetime.now()
        
        # 未发货可以退款
        if not self.is_shipped():
            return True
        
        # 已发货但在1小时内可以退款
        if (current_time - self.shipped_time) <= datetime.timedelta(hours=1):
            return True
            
        return False

    def get_formatted_purchase_time(self):
        return self.purchase_time.strftime("%Y-%m-%d %H:%M:%S")

    def get_formatted_estimated_arrival_time(self):
        if self.estimated_arrival_time:
            return self.estimated_arrival_time.strftime("%Y-%m-%d %H:%M:%S")
        return "不适用"
        
    def get_formatted_shipped_time(self):
        if self.shipped_time:
            return self.shipped_time.strftime("%Y-%m-%d %H:%M:%S")
        return "未发货"
    
    def get_total_price(self):
        return self.item.price * self.quantity

class LuckyDraw:
    def __init__(self):
        # 自定义抽奖物品列表
        self.prizes = [
            # 好东西（10%概率）
            Item("传说武器", 0, "抽奖", "攻击力+1000", False, True),  # 虚拟物品
            Item("稀有宠物", 0, "抽奖", "跟随战斗并提供加成", False, True),  # 虚拟物品
            Item("钻石*500", 0, "抽奖", "500钻石奖励", False, True),  # 虚拟物品
            Item("绿宝石*1000", 0, "抽奖", "1000绿宝石奖励", False, True),  # 虚拟物品
            
            # 普通物品（90%概率）
            Item("普通武器", 0, "抽奖", "攻击力+100", False, True),  # 虚拟物品
            Item("普通装备", 0, "抽奖", "防御力+50", False, True),  # 虚拟物品
            Item("钻石*50", 0, "抽奖", "50钻石奖励", False, True),  # 虚拟物品
            Item("绿宝石*100", 0, "抽奖", "100绿宝石奖励", False, True),  # 虚拟物品
            Item("经验药水", 0, "抽奖", "少量经验值", False, True),  # 虚拟物品
            Item("金币袋", 0, "抽奖", "少量金币", False, True)  # 虚拟物品
        ]
    
    def draw(self, user):
        # 消耗100个钻石参与抽奖
        # 先检查钻石是否足够
        if user.diamonds < 100:
            print("钻石不足，无法抽奖（需要100个钻石）！")
            print(f"当前钻石数量: {user.diamonds}")  # 显示当前钻石数量
            return None
            
        # 扣除钻石
        user.subtract_diamonds(100)
        
        print("\n正在抽奖...")
        for i in range(3):
            print(f"\r转动中{i+1}...", end="")
            time.sleep(1)
            
        # 10%概率获得好东西（前4个奖品）
        if random.random() < 0.1:
            prize = random.choice(self.prizes[:4])  # 好东西
            print(f"\n恭喜！抽到了稀有物品：{prize.name} - {prize.description}")
        else:
            prize = random.choice(self.prizes[4:])  # 普通物品
            print(f"\n抽到了：{prize.name} - {prize.description}")
            
        # 特殊物品处理（货币奖励）
        if prize.name == "钻石*500":
            user.add_diamonds(500)
        elif prize.name == "绿宝石*1000":
            user.add_emeralds(1000)
        elif prize.name == "钻石*50":
            user.add_diamonds(50)
        elif prize.name == "绿宝石*100":
            user.add_emeralds(100)
        else:
            user.add_item_to_inventory(prize)
            
        return prize

class Shop:
    def __init__(self):
        self.users = {}
        self.emails = set()  # 用于存储已注册的邮箱，确保唯一
        self.items = []
        self.lucky_draw = LuckyDraw()
        self.load_data()
        # 确保反馈目录存在
        if not os.path.exists("feedback"):
            os.makedirs("feedback")
            
        # 确保云存储目录存在
        if not os.path.exists("cloud_storage"):
            os.makedirs("cloud_storage")
            
        # 添加SVIP套餐
        self.svip_packages = [
            {"type": "month", "price": 90000, "name": "月度SVIP", "desc": "享受一个月的SVIP特权"},
            {"type": "quarter", "price": 100000, "name": "季度SVIP", "desc": "享受一个季度的SVIP特权"},
            {"type": "year", "price": 99999999, "name": "年度SVIP", "desc": "享受一年的SVIP特权"}
        ]

    def load_data(self):
        if os.path.exists("users.json"):
            with open("users.json", "r", encoding="utf-8") as f:
                users_data = json.load(f)
                for username, user_data in users_data.items():
                    user = User(username, user_data["email"], user_data["password"], user_data["payment_password"])
                    user.emeralds = user_data["emeralds"]
                    user.diamonds = user_data["diamonds"]  # 加载钻石数量
                    user.default_address = user_data.get("default_address", "")
                    user.security_questions = user_data.get("security_questions", [])
                    
                    # 恢复签到数据
                    if "daily_checkin" in user_data:
                        checkin_data = user_data["daily_checkin"]
                        if checkin_data["last_checkin_date"]:
                            user.daily_checkin["last_checkin_date"] = datetime.date.fromisoformat(checkin_data["last_checkin_date"])
                        user.daily_checkin["streak_days"] = checkin_data.get("streak_days", 0)
                    
                    # 恢复任务数据
                    user.tasks = user_data.get("tasks", {
                        "watch_ad": False,
                        "buy_item": False
                    })
                    
                    # 恢复背包
                    for item_data in user_data["inventory"]:
                        item = Item(
                            item_data["name"], 
                            item_data["price"], 
                            item_data["currency_type"], 
                            item_data["description"],
                            item_data.get("is_physical", True),  # 加载商品类型
                            item_data.get("is_lucky", False),
                            item_data.get("quantity_available"),
                            item_data.get("delivery_type", "1-2天")
                        )
                        user.inventory.append(item)
                    
                    # 恢复订单
                    for order_data in user_data["orders"]:
                        item = Item(
                            order_data["item"]["name"], 
                            order_data["item"]["price"], 
                            order_data["item"]["currency_type"], 
                            order_data["item"]["description"],
                            order_data["item"].get("is_physical", True),  # 加载商品类型
                            quantity_available=order_data["item"].get("quantity_available"),
                            delivery_type=order_data["item"].get("delivery_type", "1-2天")
                        )
                        order = Order(item, order_data.get("address"), order_data.get("quantity", 1))
                        order.order_id = order_data["order_id"]
                        order.purchase_time = datetime.datetime.fromisoformat(order_data["purchase_time"])
                        order.estimated_arrival_time = datetime.datetime.fromisoformat(order_data["estimated_arrival_time"]) if order_data.get("estimated_arrival_time") else None
                        order.is_refunded = order_data["is_refunded"]
                        order.is_delivered = order_data.get("is_delivered", False)
                        order.is_confirmed = order_data.get("is_confirmed", False)  # 加载确认收货状态
                        # 恢复发货时间
                        if "shipped_time" in order_data and order_data["shipped_time"]:
                            order.shipped_time = datetime.datetime.fromisoformat(order_data["shipped_time"])
                        user.orders.append(order)
                    
                    # 恢复交易记录
                    user.transactions = user_data.get("transactions", [])
                    
                    # 恢复购物车
                    for key, cart_item in user_data.get("shopping_cart", {}).items():
                        item_data = cart_item["item"]
                        item = Item(
                            item_data["name"],
                            item_data["price"],
                            item_data["currency_type"],
                            item_data["description"],
                            item_data.get("is_physical", True),  # 加载商品类型
                            quantity_available=item_data.get("quantity_available"),
                            delivery_type=item_data.get("delivery_type", "1-2天")
                        )
                        user.shopping_cart[key] = (item, cart_item["quantity"])
                    
                    # 恢复SVIP信息
                    if "svip" in user_data:
                        svip_data = user_data["svip"]
                        user.svip["active"] = svip_data.get("active", False)
                        user.svip["type"] = svip_data.get("type")
                        if svip_data.get("purchase_date"):
                            user.svip["purchase_date"] = datetime.date.fromisoformat(svip_data["purchase_date"])
                        if svip_data.get("expiry_date"):
                            user.svip["expiry_date"] = datetime.date.fromisoformat(svip_data["expiry_date"])
                    
                    # 恢复随机礼包日期
                    if "last_random_gift_date" in user_data and user_data["last_random_gift_date"]:
                        user.last_random_gift_date = datetime.date.fromisoformat(user_data["last_random_gift_date"])
                    
                    self.users[username] = user
                    self.emails.add(user_data["email"])  # 添加邮箱到集合，确保唯一性检查
        
        # 加载商品数据
        if os.path.exists("items.json"):
            with open("items.json", "r", encoding="utf-8") as f:
                items_data = json.load(f)
                for item_data in items_data:
                    # 处理quantity_available
                    quantity_available = item_data.get("quantity_available")
                    if quantity_available == "None":
                        quantity_available = None
                        
                    item = Item(
                        item_data["name"], 
                        item_data["price"], 
                        item_data["currency_type"], 
                        item_data["description"],
                        item_data.get("is_physical", True),  # 加载商品类型
                        quantity_available=quantity_available,
                        delivery_type=item_data.get("delivery_type", "1-2天")
                    )
                    self.items.append(item)
        else:
            # 添加默认商品，设置为无限数量
            self.add_item(Item("稀有武器", 100, "绿宝石", "一把强大的武器", False))  # 虚拟商品
            self.add_item(Item("高级装备", 50, "钻石", "一套高品质装备", True))  # 实物商品
            self.add_item(Item("经验药水", 30, "绿宝石", "提升经验获取速度", False))  # 虚拟商品
            self.add_item(Item("钻石礼包", 200, "钻石", "大量钻石奖励", False))  # 虚拟商品

    def save_data(self):
        users_data = {}
        for username, user in self.users.items():
            user_data = {
                "email": user.email,  # 保存邮箱信息
                "password": user.password,
                "payment_password": user.payment_password,
                "emeralds": user.emeralds,
                "diamonds": user.diamonds,  # 确保钻石数量被保存
                "default_address": user.default_address,
                "security_questions": user.security_questions,
                "daily_checkin": {
                    "last_checkin_date": user.daily_checkin["last_checkin_date"].isoformat() if user.daily_checkin["last_checkin_date"] else None,
                    "streak_days": user.daily_checkin["streak_days"]
                },
                "tasks": user.tasks,
                "inventory": [{
                    "name": item.name,
                    "price": item.price,
                    "currency_type": item.currency_type,
                    "description": item.description,
                    "is_physical": item.is_physical,  # 保存商品类型
                    "is_lucky": item.is_lucky,
                    "quantity_available": item.quantity_available,
                    "delivery_type": item.delivery_type
                } for item in user.inventory],
                "orders": [{
                    "item": {
                        "name": order.item.name,
                        "price": order.item.price,
                        "currency_type": order.item.currency_type,
                        "description": order.item.description,
                        "is_physical": order.item.is_physical,  # 保存商品类型
                        "quantity_available": order.item.quantity_available,
                        "delivery_type": order.item.delivery_type
                    },
                    "quantity": order.quantity,
                    "address": order.address,
                    "order_id": order.order_id,
                    "purchase_time": order.purchase_time.isoformat(),
                    "shipped_time": order.shipped_time.isoformat() if order.shipped_time else None,
                    "estimated_arrival_time": order.estimated_arrival_time.isoformat() if order.estimated_arrival_time else None,
                    "is_refunded": order.is_refunded,
                    "is_delivered": order.is_delivered,
                    "is_confirmed": order.is_confirmed  # 保存确认收货状态
                } for order in user.orders],
                "transactions": user.transactions,
                # 保存购物车数据
                "shopping_cart": {
                    key: {
                        "item": {
                            "name": item.name,
                            "price": item.price,
                            "currency_type": item.currency_type,
                            "description": item.description,
                            "is_physical": item.is_physical,  # 保存商品类型
                            "quantity_available": item.quantity_available,
                            "delivery_type": item.delivery_type
                        },
                        "quantity": quantity
                    } for key, (item, quantity) in user.shopping_cart.items()
                },
                # 保存SVIP信息
                "svip": {
                    "active": user.svip["active"],
                    "type": user.svip["type"],
                    "purchase_date": user.svip["purchase_date"].isoformat() if user.svip["purchase_date"] else None,
                    "expiry_date": user.svip["expiry_date"].isoformat() if user.svip["expiry_date"] else None
                },
                # 保存随机礼包日期
                "last_random_gift_date": user.last_random_gift_date.isoformat() if user.last_random_gift_date else None
            }
            users_data[username] = user_data
        
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
        
        # 保存商品数据
        items_data = [{
            "name": item.name,
            "price": item.price,
            "currency_type": item.currency_type,
            "description": item.description,
            "is_physical": item.is_physical,  # 保存商品类型
            # 保存quantity_available
            "quantity_available": item.quantity_available,
            # 保存到货时间类型
            "delivery_type": item.delivery_type
        } for item in self.items]
        
        with open("items.json", "w", encoding="utf-8") as f:
            json.dump(items_data, f, ensure_ascii=False, indent=2)

    def register_user(self, username, email, password):
        if username in self.users:
            print("用户名已存在！")
            return False
        
        if email in self.emails:
            print("该邮箱已被注册！")
            return False
        
        # 创建用户
        user = User(username, email, password)
        self.users[username] = user
        self.emails.add(email)  # 将邮箱添加到集合中，用于后续检查
        
        print(f"用户 {username} 注册成功！")
        print("请设置安全问题，以便密码找回（至少2个，最多10个）")
        
        # 设置安全问题，默认至少2个
        question_count = 0
        while question_count < 10:
            # 达到2个后询问是否继续添加
            if question_count >= 2:
                choice = input(f"已设置{question_count}个安全问题，是否继续添加？(y/n): ").strip().lower()
                if choice != 'y':
                    break
            
            print(f"\n设置第{question_count + 1}个安全问题")
            question = input("请输入安全问题 (输入0返回主菜单): ")
            if question == '0':
                # 如果还没设置够2个，不允许退出
                if question_count < 2:
                    print("至少需要设置2个安全问题！")
                    continue
                else:
                    print("返回主菜单...")
                    break
            
            answer = input("请输入答案: ")
            if answer == '0':
                print("答案不能为0！")
                continue
                
            if user.add_security_question(question, answer):
                print("安全问题添加成功！")
                question_count += 1
            else:
                print("最多只能设置10个安全问题！")
                break
        
        # 检查是否设置了足够的安全问题
        if len(user.security_questions) < 2:
            print("至少需要设置2个安全问题才能完成注册！")
            del self.users[username]  # 删除未完成注册的用户
            self.emails.remove(email)  # 从邮箱集合中移除
            return False
        
        print(f"您的默认支付密码是: {user.payment_password}")
        print("建议登录后修改支付密码以保障账户安全")
        self.save_data()
        return True

    def login_user(self, username, password):
        if username not in self.users:
            print("用户不存在！")
            return None
        user = self.users[username]
        if user.password != password:
            print("密码错误！")
            return None
        print(f"用户 {username} 登录成功！")
        
        # 登录时检查是否有已到货的订单
        user.check_delivered_orders()
        
        # 登录时重置每日任务（如果是新的一天）
        user.reset_daily_tasks()
        
        # 检查SVIP状态
        user.check_svip_status()
        
        # 登录成功后保存当前用户为上次登录用户
        save_last_user(username)
        return user

    def forgot_password(self, username):
        """处理忘记密码流程"""
        if username not in self.users:
            print("用户不存在！")
            return False
            
        user = self.users[username]
        print("\n=== 密码找回 ===")
        print("请回答以下安全问题以验证身份")
        
        # 获取用户的安全问题并验证答案
        answers = []
        for i, (question, _) in enumerate(user.security_questions, 1):
            answer = input(f"问题 {i}: {question} ")
            if answer == '0':
                print("返回主菜单...")
                return False
            answers.append(answer)
        
        # 验证答案是否正确
        if user.verify_security_answers(answers):
            print("身份验证成功！")
            
            # 重置密码
            new_password = input("请输入新密码: ")
            if new_password == '0':
                print("返回主菜单...")
                return False
                
            confirm_password = input("请再次输入新密码: ")
            if confirm_password == '0':
                print("返回主菜单...")
                return False
                
            if new_password == confirm_password:
                user.set_password(new_password)
                self.save_data()
                print("密码重置成功，请使用新密码登录")
                return True
            else:
                print("两次输入的密码不一致，密码重置失败")
                return False
        else:
            print("安全问题答案不正确，密码找回失败")
            return False

    def logout_user(self, username):
        if username in self.users:
            print(f"用户 {username} 已退出登录！")
            return True
        return False

    def delete_user(self, username, password):
        # 确认注销提示
        confirm = input("确定要注销账户吗？此操作不可恢复！(y/n): ")
        if confirm.lower() != 'y':
            print("已取消注销操作")
            return False
            
        if username not in self.users:
            print("用户不存在！")
            return False
        
        user = self.users[username]
        if user.password != password:
            print("密码错误！注销失败！")
            return False
        
        # 从用户字典中删除用户
        del self.users[username]
        self.emails.remove(user.email)  # 从邮箱集合中移除
        print(f"用户 {username} 已成功注销！")
        
        # 如果删除的是上次登录的用户，清除记录
        last_user = get_last_user()
        if last_user == username:
            try:
                os.remove("last_user.txt")
            except:
                pass
        
        # 立即保存数据，确保删除操作被持久化
        self.save_data()
        return True

    def change_username(self, old_username, user, new_username):
        # 检查新用户名是否已存在
        if new_username in self.users:
            print("新用户名已被使用！")
            return False
            
        # 将用户数据从旧用户名迁移到新用户名
        del self.users[old_username]
        self.users[new_username] = user
        user.username = new_username
        
        # 如果修改的是上次登录的用户，更新记录
        last_user = get_last_user()
        if last_user == old_username:
            save_last_user(new_username)
        
        print(f"用户名已成功修改为: {new_username}")
        self.save_data()
        return True

    def add_item(self, item):
        self.items.append(item)
        self.save_data()

    def create_custom_item(self):
        print("\n=== 创建自定义商品 ===")
        print("输入 '0' 可返回主菜单")
        
        name = input("请输入商品名称: ")
        if name == '0':
            print("返回主菜单...")
            return
            
        while True:
            price_input = input("请输入商品价格 (输入0返回主菜单): ")
            if price_input == '0':
                print("返回主菜单...")
                return
            try:
                price = int(price_input)
                if price > 0:
                    break
                print("价格必须大于0")
            except ValueError:
                print("请输入有效的数字")
        
        while True:
            currency = input("请输入货币类型 (绿宝石/钻石) (输入0返回主菜单): ").strip()
            if currency == '0':
                print("返回主菜单...")
                return
            if currency in ["绿宝石", "钻石"]:
                break
            print("请输入'绿宝石'或'钻石'")
        
        # 新增：选择商品类型（实物/虚拟）
        while True:
            print("\n请选择商品类型:")
            print("1. 实物商品（需要配送，支持退款）")
            print("2. 虚拟商品（无需配送，不支持退款）")
            type_choice = input("请选择 (输入0返回主菜单): ").strip()
            
            if type_choice == '0':
                print("返回主菜单...")
                return
            elif type_choice == '1':
                is_physical = True
                break
            elif type_choice == '2':
                is_physical = False
                break
            else:
                print("请输入1或2选择商品类型")
                
        description = input("请输入商品描述 (输入0返回主菜单): ")
        if description == '0':
            print("返回主菜单...")
            return
        
        # 输入商品数量
        while True:
            quantity_input = input("请输入商品数量 (输入0表示无限，输入其他数字表示具体数量): ")
            if quantity_input == '0':
                quantity_available = None  # 0表示无限
                break
            try:
                quantity_available = int(quantity_input)
                if quantity_available > 0:
                    break
                print("数量必须大于0")
            except ValueError:
                print("请输入有效的数字")
        
        # 选择到货时间（仅适用于实物商品）
        delivery_type = "1-2天"  # 默认值
        if is_physical:
            while True:
                print("\n请选择预计到货时间:")
                print("1. 今天")
                print("2. 1-2天")
                delivery_choice = input("请选择 (输入0返回主菜单): ").strip()
                
                if delivery_choice == '0':
                    print("返回主菜单...")
                    return
                elif delivery_choice == '1':
                    delivery_type = "今天"
                    break
                elif delivery_choice == '2':
                    delivery_type = "1-2天"
                    break
                else:
                    print("请输入1或2选择到货时间")
                
        new_item = Item(
            name, 
            price, 
            currency, 
            description, 
            is_physical,  # 设置商品类型
            quantity_available=quantity_available,
            delivery_type=delivery_type
        )
        self.add_item(new_item)
        item_type = "实物商品" if is_physical else "虚拟商品"
        print(f"自定义{item_type} '{name}' 创建成功！{f'预计{delivery_type}送达' if is_physical else ''}")
        input("按回车键返回主菜单...")

    def display_items(self):
        print("\n=== 商品列表 ===")
        if not self.items:
            print("暂无商品")
        else:
            for i, item in enumerate(self.items, 1):
                item_type = "实物商品" if item.is_physical else "虚拟商品"
                quantity_text = "无限" if item.quantity_available is None else f"{item.quantity_available}个"
                delivery_info = f" | 预计{item.delivery_type}送达" if item.is_physical else ""
                print(f"{i}. {item.name} - {item.price} {item.currency_type} - {item_type} - {item.description}")
                print(f"   剩余: {quantity_text}{delivery_info}")
        print("\n输入 '0' 返回主菜单")
        choice = input("请选择: ")
        if choice == '0':
            return

    def display_assets(self, user):
        print("\n=== 资产信息 ===")
        print(f"邮箱: {user.email}")  # 显示用户邮箱
        print(f"绿宝石: {user.emeralds}")
        print(f"钻石: {user.diamonds}")  # 显示钻石数量
        print(f"支付密码: {user.payment_password}")  # 仅演示用，实际应用不应显示完整密码
        print(f"默认地址: {user.default_address if user.default_address else '未设置'}")
        
        # 显示SVIP状态
        if user.is_svip_active():
            remaining = user.get_svip_remaining_days()
            print(f"💎 SVIP状态: {user.svip['type']}会员，剩余{remaining}天")
        else:
            print("SVIP状态: 非会员")
            
        print("\n输入 '0' 返回主菜单")
        choice = input("请选择: ")
        if choice == '0':
            return

    def process_payment(self, user, item, quantity):
        total_price = item.price * quantity
        
        # 显示支付确认信息
        print("\n=== 支付确认 ===")
        print(f"商品: {item.name}")
        print(f"类型: {'实物商品' if item.is_physical else '虚拟商品'}")
        print(f"单价: {item.price} {item.currency_type}")
        print(f"数量: {quantity}")
        print(f"总价: {total_price} {item.currency_type}")
        if item.is_physical:
            print(f"预计送达: {item.delivery_type}")
        else:
            print("交付方式: 立即到账")
        print(f"当前余额: {user.emeralds} 绿宝石, {user.diamonds} 钻石")
        
        # 显示退款政策
        if item.is_physical:
            print("退款政策: 未发货可随时退款，已发货后1小时内可退款")
        else:
            print("退款政策: 虚拟商品不支持退款")
        
        # 确认支付
        confirm = input("确认支付？(y/n，输入0返回主菜单): ").strip().lower()
        if confirm == '0':
            print("返回主菜单...")
            return False, None
        if confirm != 'y':
            print("已取消支付")
            input("按回车键返回主菜单...")
            return False, None
            
        address = None
        # 地址输入（仅适用于实物商品）
        if item.is_physical:
            print("\n=== 收货地址 ===")
            if user.default_address:
                print(f"默认地址: {user.default_address}")
                use_default = input("是否使用默认地址？(y/n，输入0返回主菜单): ").strip().lower()
                if use_default == '0':
                    print("返回主菜单...")
                    return False, None
                if use_default == 'y':
                    address = user.default_address
                else:
                    address = input("请输入新地址 (输入0返回主菜单): ")
                    if address == '0':
                        print("返回主菜单...")
                        return False, None
                    set_default = input("是否将此地址设为默认地址？(y/n，输入0返回主菜单): ").strip().lower()
                    if set_default == '0':
                        print("返回主菜单...")
                        return False, None
                    if set_default == 'y':
                        user.set_default_address(address)
            else:
                address = input("请输入收货地址 (输入0返回主菜单): ")
                if address == '0':
                    print("返回主菜单...")
                    return False, None
                set_default = input("是否将此地址设为默认地址？(y/n，输入0返回主菜单): ").strip().lower()
                if set_default == '0':
                    print("返回主菜单...")
                    return False, None
                if set_default == 'y':
                    user.set_default_address(address)
        
        # 验证支付密码
        max_attempts = 3
        for attempt in range(max_attempts):
            payment_password = input("请输入支付密码 (输入0返回主菜单): ")
            if payment_password == '0':
                print("返回主菜单...")
                return False, None
            if user.verify_payment_password(payment_password):
                # 验证通过，处理扣款
                if item.currency_type == "绿宝石":
                    if not user.subtract_emeralds(total_price):
                        print("绿宝石不足！")
                        input("按回车键返回主菜单...")
                        return False, None
                else:
                    if not user.subtract_diamonds(total_price):
                        print("钻石不足！")
                        input("按回车键返回主菜单...")
                        return False, None
                return True, address
            else:
                remaining = max_attempts - attempt - 1
                if remaining > 0:
                    print(f"支付密码错误！您还有 {remaining} 次尝试机会")
                else:
                    print("支付密码错误次数过多，支付已取消")
                    input("按回车键返回主菜单...")
        return False, None

    def purchase_item(self, user):
        print("\n=== 购买商品 ===")
        print("输入 '0' 可返回主菜单")
        
        self.display_items()
        try:
            item_index_input = input("请输入要购买的商品编号 (输入0返回主菜单): ")
            if item_index_input == '0':
                print("返回主菜单...")
                return
            item_index = int(item_index_input)
            
            if item_index < 1 or item_index > len(self.items):
                print("无效的商品编号！")
                input("按回车键返回主菜单...")
                return

            item = self.items[item_index - 1]
            
            # 检查商品是否有数量限制
            max_quantity = float('inf')
            if item.quantity_available is not None:
                max_quantity = item.quantity_available
                if max_quantity <= 0:
                    print("该商品已售罄！")
                    input("按回车键返回主菜单...")
                    return
            
            # 输入购买数量，增加数量限制检查
            while True:
                quantity_input = input(f"请输入购买 {item.name} 的数量 (至少1个，最多{max_quantity if max_quantity != float('inf') else '无限'}个，输入0返回主菜单): ")
                if quantity_input == '0':
                    print("返回主菜单...")
                    return
                try:
                    quantity = int(quantity_input)
                    if quantity >= 1 and quantity <= max_quantity:
                        break
                    print(f"数量必须在1到{max_quantity if max_quantity != float('inf') else '无限'}之间")
                except ValueError:
                    print("请输入有效的数字！")

            # 询问是直接购买还是加入购物车
            print("\n1. 直接购买")
            print("2. 加入购物车")
            print("0. 返回主菜单")
            action_choice = input("请选择操作: ")
            
            if action_choice == '0':
                print("返回主菜单...")
                return
            elif action_choice == '1':
                # 直接购买流程
                # 处理支付流程
                payment_success, address = self.process_payment(user, item, quantity)
                if not payment_success:
                    return

                # 支付成功，创建订单
                order = Order(item, address, quantity)
                user.add_order(order)
                
                # 减少商品可用数量
                if item.quantity_available is not None:
                    item.quantity_available -= quantity

                print("\n支付成功！")
                print(f"订单号: {order.order_id}")
                print(f"商品: {item.name}")
                print(f"数量: {quantity}")
                print(f"单价: {item.price} {item.currency_type}")
                print(f"总价: {order.get_total_price()} {item.currency_type}")
                
                if item.is_physical:
                    print(f"收货地址: {address}")
                    print(f"预计送达时间: {order.get_formatted_estimated_arrival_time()}")
                    print("商品送达后将自动添加到您的背包")
                    print("您需要在收到商品后确认收货")
                    print("退款规则：未发货可随时退款，已发货后1小时内可退款")
                else:
                    print("虚拟商品已自动添加到您的背包")
                    print("退款规则：虚拟商品不支持退款")
                
                # 检查购买商品任务是否已完成
                if not user.tasks["buy_item"]:
                    success, message = user.complete_task("buy_item")
                    if success:
                        print(message)
                
                self.save_data()
                input("按回车键返回主菜单...")
            elif action_choice == '2':
                # 加入购物车
                # 检查购物车中已有数量 + 新数量是否超过限制
                current_in_cart = 0
                item_key = user._get_item_key(item)
                if item_key in user.shopping_cart:
                    current_in_cart = user.shopping_cart[item_key][1]
                    
                if item.quantity_available is not None and current_in_cart + quantity > item.quantity_available:
                    print(f"购物车中已有 {current_in_cart} 个该商品，最多还能添加 {item.quantity_available - current_in_cart} 个！")
                    input("按回车键返回主菜单...")
                    return
                    
                user.add_to_cart(item, quantity)
                print(f"\n已将 {item.name} x{quantity} 加入购物车！")
                self.save_data()
                
                # 询问是否继续购物
                continue_shopping = input("是否继续购物？(y/n): ").strip().lower()
                if continue_shopping != 'y':
                    print("返回主菜单...")
                    input("按回车键返回主菜单...")
            else:
                print("无效选择！")
                input("按回车键返回主菜单...")
        except ValueError:
            print("请输入有效的数字！")
            input("按回车键返回主菜单...")

    def display_inventory(self, user):
        # 查看背包前先检查是否有已到货的订单
        user.check_delivered_orders()
        
        print("\n=== 背包 ===")
        if not user.inventory:
            print("背包为空！")
        else:
            # 统计物品数量
            item_counts = {}
            for item in user.inventory:
                key = (item.name, item.price, item.currency_type, item.is_physical)
                if key not in item_counts:
                    item_counts[key] = {"item": item, "count": 0}
                item_counts[key]["count"] += 1
                
            # 显示物品及数量
            for i, (_, data) in enumerate(item_counts.items(), 1):
                item = data["item"]
                count = data["count"]
                item_type = "实物商品" if item.is_physical else "虚拟商品"
                
                # 查找对应的订单号
                order_id = "无订单"
                for order in user.orders:
                    if (order.item.name == item.name and 
                        order.item.price == item.price and 
                        order.item.currency_type == item.currency_type and 
                        order.item.is_physical == item.is_physical and
                        not order.is_refunded and
                        order.is_delivered):
                        order_id = order.order_id
                        break
                        
                print(f"{i}. {item.name} x{count} - {item_type} - {item.description} (订单号: {order_id})")
        
        print("\n输入 '0' 返回主菜单")
        choice = input("请选择: ")
        if choice == '0':
            return

    def display_orders(self, user, return_after_display=True):
        # 查看订单前先检查是否有已到货的订单
        user.check_delivered_orders()
        
        print("\n=== 订单记录 ===")
        if not user.orders:
            print("暂无订单！")
        else:
            for order in user.orders:
                status = ""
                if order.is_refunded:
                    status = "（已退款）"
                elif order.is_delivered:
                    if order.is_confirmed:
                        status = "（已确认收货）"
                    else:
                        status = "（已送达，待确认收货）"
                else:
                    # 检查是否已过预计送达时间但未标记为已送达
                    if order.item.is_physical and datetime.datetime.now() >= order.estimated_arrival_time:
                        status = "（已到货，待确认收货）"
                    else:
                        status = "（配送中）"
                
                # 显示退款状态
                refund_status = ""
                if not order.is_refunded and order.item.is_physical:  # 只有实物商品可能退款
                    if order.can_refund():
                        time_left = ""
                        if order.is_shipped():
                            time_passed = datetime.datetime.now() - order.shipped_time
                            if time_passed < datetime.timedelta(hours=1):
                                time_remaining = datetime.timedelta(hours=1) - time_passed
                                minutes = int(time_remaining.total_seconds() // 60)
                                time_left = f"，剩余{minutes}分钟可申请退款"
                        refund_status = f"（可申请退款{time_left}）"
                    else:
                        refund_status = "（已超过退款时限）"
                elif not order.item.is_physical:
                    refund_status = "（虚拟商品不支持退款）"
                        
                print(f"订单号: {order.order_id}{status}{refund_status}")
                print(f"商品: {order.item.name}")
                print(f"类型: {'实物商品' if order.item.is_physical else '虚拟商品'}")
                print(f"数量: {order.quantity}")
                print(f"单价: {order.item.price} {order.item.currency_type}")
                print(f"总价: {order.get_total_price()} {order.item.currency_type}")
                print(f"购买时间: {order.get_formatted_purchase_time()}")
                print(f"发货时间: {order.get_formatted_shipped_time()}")
                if order.item.is_physical:
                    print(f"收货地址: {order.address}")
                    print(f"预计送达: {order.get_formatted_estimated_arrival_time()}")
                else:
                    print("交付状态: 已到账")
                print("---------------------")
        
        if return_after_display:
            print("\n输入 '0' 返回主菜单")
            choice = input("请选择: ")
            if choice == '0':
                return True
        return False

    def refund_order(self, user):
        print("\n=== 申请退款 ===")
        print("退款规则：实物商品未发货可随时退款，已发货后1小时内可退款；虚拟商品不支持退款")
        print("输入 '0' 可返回主菜单")
        
        # 显示订单并检查是否需要返回
        if self.display_orders(user, return_after_display=False):
            return
            
        order_id = input("请输入要退款的订单号 (输入0返回主菜单): ")
        if order_id == '0':
            print("返回主菜单...")
            return
            
        for order in user.orders:
            if order.order_id == order_id:
                # 检查是否为虚拟商品
                if not order.item.is_physical:
                    print("虚拟商品不支持退款！")
                    input("按回车键返回主菜单...")
                    return
                
                # 检查是否已退款
                if order.is_refunded:
                    print("该订单已退款！")
                    input("按回车键返回主菜单...")
                    return
                    
                # 检查是否可以退款
                if not order.can_refund():
                    if order.is_shipped():
                        time_passed = datetime.datetime.now() - order.shipped_time
                        hours = time_passed.total_seconds() // 3600
                        minutes = (time_passed.total_seconds() % 3600) // 60
                        print(f"该商品已发货超过1小时（已发货{int(hours)}小时{int(minutes)}分钟），无法申请退款！")
                    else:
                        print("该商品无法申请退款！")
                    input("按回车键返回主菜单...")
                    return
                
                # 可以退款，执行退款流程
                item = order.item
                quantity = order.quantity
                total_price = order.get_total_price()
                
                # 确认退款
                confirm = input(f"确认要退款 {item.name} x{quantity} 吗？(y/n，输入0返回主菜单): ").strip().lower()
                if confirm == '0':
                    print("返回主菜单...")
                    return
                if confirm != 'y':
                    print("已取消退款")
                    input("按回车键返回主菜单...")
                    return
                
                if item.currency_type == "绿宝石":
                    user.add_emeralds(total_price)
                else:
                    user.add_diamonds(total_price)

                order.is_refunded = True
                
                # 退款后恢复商品数量
                if item.quantity_available is not None:
                    item.quantity_available += quantity

                print(f"退款成功！{total_price} {item.currency_type} 已返还到您的账户")
                self.save_data()
                input("按回车键返回主菜单...")
                return

        print("订单不存在！")
        input("按回车键返回主菜单...")

    # 新增：确认收货功能
    def confirm_receipt(self, user):
        print("\n=== 确认收货 ===")
        print("只有已送达但未确认的实物商品订单可以确认收货")
        print("输入 '0' 可返回主菜单")
        
        # 先检查是否有已到货的订单
        user.check_delivered_orders()
        
        # 筛选可确认收货的订单
        confirmable_orders = [
            order for order in user.orders 
            if order.item.is_physical and order.is_delivered and not order.is_confirmed and not order.is_refunded
        ]
        
        if not confirmable_orders:
            print("没有可确认收货的订单！")
            input("按回车键返回主菜单...")
            return
        
        # 显示可确认收货的订单
        print("\n可确认收货的订单：")
        for i, order in enumerate(confirmable_orders, 1):
            print(f"{i}. 订单号: {order.order_id}")
            print(f"   商品: {order.item.name} x{order.quantity}")
            print(f"   送达时间: {order.get_formatted_estimated_arrival_time()}")
            print("---------------------")
        
        try:
            choice = input("请输入要确认收货的订单编号 (输入0返回主菜单): ")
            if choice == '0':
                print("返回主菜单...")
                return
                
            order_index = int(choice) - 1
            if 0 <= order_index < len(confirmable_orders):
                order = confirmable_orders[order_index]
                
                # 确认操作
                confirm = input(f"确认收到 {order.item.name} 吗？(y/n): ").strip().lower()
                if confirm == 'y':
                    order.is_confirmed = True
                    print(f"已确认收到 {order.item.name}！")
                    self.save_data()
                else:
                    print("已取消确认收货操作")
            else:
                print("无效的订单编号！")
        except ValueError:
            print("请输入有效的数字！")
            
        input("按回车键返回主菜单...")

    def earn_emeralds_by_typing(self, user):
        print("\n=== 文字输入获取绿宝石 ===")
        print("输入 '0' 可返回主菜单")
        text = input("请输入一段文字（至少10个字符）：")
        
        if text == '0':
            print("返回主菜单...")
            return
            
        if len(text) >= 10:
            emeralds = random.randint(5, 15)
            user.add_emeralds(emeralds)
            print(f"恭喜！您获得了 {emeralds} 绿宝石！")
            self.save_data()
        else:
            print("输入的文字太短，请至少输入10个字符。")
            
        input("按回车键返回主菜单...")

    # 绿宝石广告获取功能
    def earn_emeralds_by_ad(self, user):
        print("\n=== 观看广告获取绿宝石 ===")
        print("输入 '0' 可返回主菜单")
        try:
            choice = input("是否观看广告？(y/n，输入0返回主菜单): ").strip().lower()
            
            if choice == '0':
                print("返回主菜单...")
                return
            if choice != 'y':
                print("已取消观看广告")
                input("按回车键返回主菜单...")
                return
                
            print("广告播放中... (30秒)")
            for i in range(30, 0, -1):
                print(f"\r剩余时间: {i}秒", end="")
                time.sleep(1)
            print()
            
            print("广告播放完毕！")
            if random.random() < 0.8:
                emeralds = random.randint(10, 25)
                user.add_emeralds(emeralds)
                print(f"恭喜！您获得了 {emeralds} 绿宝石！")
                
                # 完成看广告任务
                if not user.tasks["watch_ad"]:
                    success, message = user.complete_task("watch_ad")
                    if success:
                        print(message)
            else:
                print("广告奖励失败，再接再厉！")
                
            self.save_data()
            
        except Exception as e:
            print(f"\n发生错误: {str(e)}")
        
        input("按回车键返回主菜单...")

    # 钻石广告获取功能
    def earn_diamonds_by_ad(self, user):
        print("\n=== 观看广告获取钻石 ===")
        print("输入 '0' 可返回主菜单")
        try:
            choice = input("是否观看广告？(y/n，输入0返回主菜单): ").strip().lower()
            
            if choice == '0':
                print("返回主菜单...")
                return
            if choice != 'y':
                print("已取消观看广告")
                input("按回车键返回主菜单...")
                return
                
            print("广告播放中... (30秒)")
            for i in range(30, 0, -1):
                print(f"\r剩余时间: {i}秒", end="")
                time.sleep(1)
            print()
            
            print("广告播放完毕！")
            if random.random() < 0.5:
                diamonds = random.randint(5, 15)
                user.add_diamonds(diamonds)
                print(f"恭喜！您获得了 {diamonds} 钻石！")
                print(f"当前钻石数量: {user.diamonds}")  # 显示当前钻石数量
            else:
                print("很遗憾，本次广告未获得钻石奖励。")
                
            self.save_data()
            
        except Exception as e:
            print(f"\n发生错误: {str(e)}")
        
        input("按回车键返回主菜单...")

    # 绿宝石充值功能
    def recharge_emeralds(self, user):
        print("\n=== 充值绿宝石 ===")
        print("输入 '0' 可返回主菜单")
        try:
            amount_input = input("请输入充值绿宝石数量: ")
            if amount_input == '0':
                print("返回主菜单...")
                return
            amount = int(amount_input)
            if amount > 0:
                user.add_emeralds(amount)
                print(f"成功充值 {amount} 绿宝石！当前绿宝石数量: {user.emeralds}")
                self.save_data()
            else:
                print("充值数量必须大于0！")
        except ValueError:
            print("请输入有效的数字！")
        input("按回车键返回主菜单...")

    # 钻石充值功能
    def recharge_diamonds(self, user):
        print("\n=== 充值钻石 ===")
        print("输入 '0' 可返回主菜单")
        try:
            amount_input = input("请输入充值钻石数量: ")
            if amount_input == '0':
                print("返回主菜单...")
                return
            amount = int(amount_input)
            if amount > 0:
                # 直接修改钻石属性，确保立即生效
                user.diamonds += amount
                # 记录交易
                user._record_transaction(f"充值获得 {amount} 钻石", "收入")
                # 明确显示充值后的钻石数量
                print(f"成功充值 {amount} 钻石！当前钻石数量: {user.diamonds}")
                # 立即保存数据，确保修改被持久化
                self.save_data()
            else:
                print("充值数量必须大于0！")
        except ValueError:
            print("请输入有效的数字！")
        input("按回车键返回主菜单...")

    # 显示官方网站
    def show_official_website(self):
        print("\n=== 官方网站 ===")
        print("官方网站: https://zyzx.py.com/")
        print("官方网站2: file:///C:/Users/%E6%88%91%E7%9A%84%E4%B8%96%E7%95%8C%E7%94%A8%E6%88%B7/Downloads/index.html")
        print("官方网站3: https://www.uemo.net/tools/preview/id/6004（推荐）")
        print("\n输入 '0' 返回主菜单")
        choice = input("请选择: ")
        if choice == '0':
            return

    # 显示反馈功能，支持输入文字提交
    def show_feedback_link(self):
        print("\n=== 功能反馈 ===")
        print("请输入您的反馈内容（输入0返回主菜单）：")
        feedback_text = input()
        
        if feedback_text == '0':
            print("返回主菜单...")
            return
            
        if not feedback_text.strip():
            print("反馈内容不能为空！")
            input("按回车键返回主菜单...")
            return
            
        try:
            # 生成唯一的反馈文件名（基于时间戳）
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            feedback_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            filename = f"feedback/feedback_{timestamp}_{feedback_id}.txt"
            
            # 写入反馈内容
            with open(filename, "w", encoding="utf-8") as f:
                # 记录反馈者（如果已登录）
                if hasattr(self, 'current_user') and self.current_user:
                    f.write(f"反馈用户: {self.current_user.username} (邮箱: {self.current_user.email})\n")
                f.write(f"反馈时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("--- 反馈内容 ---\n")
                f.write(feedback_text)
            
            print("感谢您的反馈！我们会认真处理您的建议。")
        except Exception as e:
            print(f"提交反馈时发生错误: {str(e)}")
            
        input("按回车键返回主菜单...")

    # 抽奖功能
    def use_lucky_draw(self, user):
        print("\n=== 幸运抽奖机 ===")
        print("每次抽奖消耗100钻石，10%概率获得稀有物品")
        # 显示当前钻石数量，让用户清晰了解余额
        print(f"当前钻石数量: {user.diamonds}")
        print("输入 '0' 可返回主菜单")
        
        # 先检查钻石是否足够，避免用户输入密码后才发现不足
        if user.diamonds < 100:
            print("钻石不足，无法抽奖（需要100个钻石）！")
            input("按回车键返回主菜单...")
            return
        
        # 确认支付
        confirm = input("确认抽奖？(y/n，输入0返回主菜单): ").strip().lower()
        if confirm == '0':
            print("返回主菜单...")
            return
        if confirm != 'y':
            print("已取消抽奖")
            input("按回车键返回主菜单...")
            return
            
        # 验证支付密码
        max_attempts = 3
        for attempt in range(max_attempts):
            payment_password = input("请输入支付密码 (输入0返回主菜单): ")
            if payment_password == '0':
                print("返回主菜单...")
                return
            if user.verify_payment_password(payment_password):
                # 再次检查钻石数量，防止并发问题
                if user.diamonds < 100:
                    print("钻石不足，无法抽奖（需要100个钻石）！")
                    print(f"当前钻石数量: {user.diamonds}")
                    input("按回车键返回主菜单...")
                    return
                    
                # 执行抽奖逻辑
                self.lucky_draw.draw(user)
                self.save_data()
                input("按回车键返回主菜单...")
                return
            else:
                remaining = max_attempts - attempt - 1
                if remaining > 0:
                    print(f"支付密码错误！您还有 {remaining} 次尝试机会")
                else:
                    print("支付密码错误次数过多，操作已取消")
                    input("按回车键返回主菜单...")
                    return

    # 购物车相关功能
    def display_shopping_cart(self, user):
        """显示购物车内容"""
        print("\n=== 购物车 ===")
        
        if user.is_cart_empty():
            print("购物车为空！")
            print("\n1. 继续购物")
            print("0. 返回主菜单")
            choice = input("请选择: ")
            if choice == '1':
                self.purchase_item(user)
            elif choice == '0':
                print("返回主菜单...")
            return
            
        # 显示购物车中的商品
        cart_items = list(user.shopping_cart.items())
        for i, (key, (item, quantity)) in enumerate(cart_items, 1):
            # 显示商品可用数量
            item_type = "实物商品" if item.is_physical else "虚拟商品"
            quantity_text = "无限" if item.quantity_available is None else f"{item.quantity_available}个"
            delivery_info = f" | 预计{item.delivery_type}送达" if item.is_physical else ""
            refund_info = " | 支持退款" if item.is_physical else " | 不支持退款"
            print(f"{i}. {item.name} x{quantity} - {item_type}")
            print(f"   单价: {item.price} {item.currency_type}")
            print(f"   小计: {item.price * quantity} {item.currency_type}")
            print(f"   描述: {item.description}")
            print(f"   剩余库存: {quantity_text}{delivery_info}{refund_info}")
            print("---------------------")
        
        # 显示总计
        totals = user.get_cart_total()
        print(f"总计: 绿宝石 {totals['绿宝石']}, 钻石 {totals['钻石']}")
        
        # 操作选项
        print("\n1. 修改商品数量")
        print("2. 删除商品")
        print("3. 清空购物车")
        print("4. 结算")
        print("5. 继续购物")
        print("0. 返回主菜单")
        
        choice = input("请选择操作: ")
        if choice == '0':
            print("返回主菜单...")
            return
        elif choice == '1':
            # 修改商品数量
            try:
                item_num = int(input("请输入要修改的商品编号: ")) - 1
                if 0 <= item_num < len(cart_items):
                    key, (item, current_quantity) = cart_items[item_num]
                    
                    # 获取最大可购买数量
                    max_quantity = float('inf')
                    if item.quantity_available is not None:
                        max_quantity = item.quantity_available
                    
                    while True:
                        new_quantity = input(f"请输入新的数量 (至少1个，最多{max_quantity if max_quantity != float('inf') else '无限'}个，0为删除): ")
                        try:
                            new_quantity = int(new_quantity)
                            if new_quantity == 0:
                                user.remove_from_cart(key)
                                print("商品已从购物车中删除")
                                break
                            elif new_quantity >= 1 and new_quantity <= max_quantity:
                                user.add_to_cart(item, new_quantity - current_quantity)
                                print(f"商品数量已更新为 {new_quantity}")
                                break
                            else:
                                print(f"数量必须在1到{max_quantity if max_quantity != float('inf') else '无限'}之间")
                        except ValueError:
                            print("请输入有效的数字")
                    self.save_data()
                else:
                    print("无效的商品编号")
            except ValueError:
                print("请输入有效的数字")
            # 重新显示购物车
            self.display_shopping_cart(user)
        elif choice == '2':
            # 删除商品
            try:
                item_num = int(input("请输入要删除的商品编号: ")) - 1
                if 0 <= item_num < len(cart_items):
                    key, _ = cart_items[item_num]
                    user.remove_from_cart(key)
                    print("商品已从购物车中删除")
                    self.save_data()
                else:
                    print("无效的商品编号")
            except ValueError:
                print("请输入有效的数字")
            # 重新显示购物车
            self.display_shopping_cart(user)
        elif choice == '3':
            # 清空购物车
            confirm = input("确定要清空购物车吗？(y/n): ").strip().lower()
            if confirm == 'y':
                user.clear_cart()
                print("购物车已清空")
                self.save_data()
            # 重新显示购物车
            self.display_shopping_cart(user)
        elif choice == '4':
            # 结算购物车
            self.checkout_cart(user)
        elif choice == '5':
            # 继续购物
            self.purchase_item(user)
        else:
            print("无效选择！")
            self.display_shopping_cart(user)
    
    def checkout_cart(self, user):
        """结算购物车中的商品"""
        if user.is_cart_empty():
            print("购物车为空，无法结算！")
            input("按回车键返回主菜单...")
            return
            
        # 检查购物车中商品数量是否超过可用数量
        for key, (item, quantity) in user.shopping_cart.items():
            if item.quantity_available is not None and quantity > item.quantity_available:
                print(f"商品 {item.name} 库存不足，最多只能购买 {item.quantity_available} 个！")
                input("按回车键返回主菜单...")
                return
        
        # 显示结算信息
        print("\n=== 购物车结算 ===")
        totals = user.get_cart_total()
        
        print("购物车商品:")
        for key, (item, quantity) in user.shopping_cart.items():
            item_type = "实物商品" if item.is_physical else "虚拟商品"
            delivery_info = f" (预计{item.delivery_type}送达)" if item.is_physical else " (立即到账)"
            refund_info = " (支持退款)" if item.is_physical else " (不支持退款)"
            print(f"- {item.name} x{quantity}: {item.price * quantity} {item.currency_type} - {item_type}{delivery_info}{refund_info}")
        
        print(f"\n总计: 绿宝石 {totals['绿宝石']}, 钻石 {totals['钻石']}")
        print(f"当前余额: 绿宝石 {user.emeralds}, 钻石 {user.diamonds}")
        
        # 检查余额是否足够
        if totals['绿宝石'] > user.emeralds or totals['钻石'] > user.diamonds:
            print("余额不足，无法结算！")
            input("按回车键返回主菜单...")
            return
        
        address = None
        # 地址输入（如果有实物商品）
        has_physical_items = any(item.is_physical for item, _ in user.shopping_cart.values())
        if has_physical_items:
            print("\n=== 收货地址 ===")
            if user.default_address:
                print(f"默认地址: {user.default_address}")
                use_default = input("是否使用默认地址？(y/n，输入0返回主菜单): ").strip().lower()
                if use_default == '0':
                    print("返回主菜单...")
                    return
                if use_default == 'y':
                    address = user.default_address
                else:
                    address = input("请输入新地址 (输入0返回主菜单): ")
                    if address == '0':
                        print("返回主菜单...")
                        return
                    set_default = input("是否将此地址设为默认地址？(y/n，输入0返回主菜单): ").strip().lower()
                    if set_default == '0':
                        print("返回主菜单...")
                        return
                    if set_default == 'y':
                        user.set_default_address(address)
            else:
                address = input("请输入收货地址 (输入0返回主菜单): ")
                if address == '0':
                    print("返回主菜单...")
                    return
                set_default = input("是否将此地址设为默认地址？(y/n，输入0返回主菜单): ").strip().lower()
                if set_default == '0':
                    print("返回主菜单...")
                    return
                if set_default == 'y':
                    user.set_default_address(address)
        
        # 验证支付密码
        max_attempts = 3
        for attempt in range(max_attempts):
            payment_password = input("请输入支付密码 (输入0返回主菜单): ")
            if payment_password == '0':
                print("返回主菜单...")
                return
            if user.verify_payment_password(payment_password):
                # 验证通过，处理扣款
                if not user.subtract_emeralds(totals['绿宝石']):
                    print("绿宝石不足！")
                    input("按回车键返回主菜单...")
                    return
                if not user.subtract_diamonds(totals['钻石']):
                    print("钻石不足！")
                    input("按回车键返回主菜单...")
                    return
                
                # 为购物车中的每个商品创建订单
                order_ids = []
                for item, quantity in user.shopping_cart.values():
                    # 虚拟商品不需要地址
                    order_address = address if item.is_physical else None
                    order = Order(item, order_address, quantity)
                    user.add_order(order)
                    
                    order_info = f"{item.name} (订单号: {order.order_id}"
                    if item.is_physical:
                        order_info += f", 预计{order.get_formatted_estimated_arrival_time()}送达)"
                    else:
                        order_info += ", 已到账)"
                    order_ids.append(order_info)
                    
                    # 减少商品可用数量
                    if item.quantity_available is not None:
                        item.quantity_available -= quantity
                
                # 清空购物车
                user.clear_cart()
                
                print("\n支付成功！")
                print("已下单商品:")
                for order_info in order_ids:
                    print(f"- {order_info}")
                
                if has_physical_items:
                    print(f"收货地址: {address}")
                    print("实物商品送达后将自动添加到您的背包，您需要确认收货")
                    print("退款规则：实物商品未发货可随时退款，已发货后1小时内可退款；虚拟商品不支持退款")
                else:
                    print("所有虚拟商品已自动添加到您的背包")
                    print("退款规则：虚拟商品不支持退款")
                
                # 检查购买商品任务是否已完成
                if not user.tasks["buy_item"]:
                    success, message = user.complete_task("buy_item")
                    if success:
                        print(message)
                
                self.save_data()
                input("按回车键返回主菜单...")
                return
            else:
                remaining = max_attempts - attempt - 1
                if remaining > 0:
                    print(f"支付密码错误！您还有 {remaining} 次尝试机会")
                else:
                    print("支付密码错误次数过多，支付已取消")
                    input("按回车键返回主菜单...")
                    return
    
    # 任务系统功能
    def show_emerald_tasks(self, user):
        """显示获取绿宝石的任务列表"""
        print("\n=== 获取绿宝石任务中心 ===")
        print("完成以下任务可获得随机数量的绿宝石奖励")
        print("-------------------------------------")
        
        # 显示签到状态
        today = datetime.date.today()
        last_checkin = user.daily_checkin["last_checkin_date"]
        checkin_status = "已完成" if last_checkin == today else "未完成"
        checkin_reward = "10-50"  # 根据连续天数变化
        
        print(f"1. 每日签到 - 状态: {checkin_status}")
        print(f"   奖励: {checkin_reward} 绿宝石 (连续签到奖励更多)")
        print(f"   当前连续签到: {user.daily_checkin['streak_days']} 天")
        
        # 显示看广告任务
        ad_status = "已完成" if user.tasks["watch_ad"] else "未完成"
        print(f"\n2. 观看一次广告 - 状态: {ad_status}")
        print("   奖励: 5-15 绿宝石")
        
        # 显示购买商品任务
        buy_status = "已完成" if user.tasks["buy_item"] else "未完成"
        print(f"\n3. 购买一个商品 - 状态: {buy_status}")
        print("   奖励: 10-25 绿宝石")
        
        print("\n操作选项:")
        print("1. 执行签到")
        print("2. 去观看广告")
        print("3. 去购买商品")
        print("0. 返回主菜单")
        
        choice = input("请选择操作: ")
        if choice == '0':
            print("返回主菜单...")
            return
        elif choice == '1':
            # 执行签到
            success, message = user.checkin()
            print(message)
            self.save_data()
            input("按回车键返回任务中心...")
            self.show_emerald_tasks(user)
        elif choice == '2':
            # 去观看广告
            self.earn_emeralds_by_ad(user)
            self.show_emerald_tasks(user)
        elif choice == '3':
            # 去购买商品
            self.purchase_item(user)
            self.show_emerald_tasks(user)
        else:
            print("无效选择！")
            input("按回车键返回任务中心...")
            self.show_emerald_tasks(user)
            
    # SVIP会员中心
    def purchase_svip(self, user):
        """购买SVIP会员"""
        print("\n=== SVIP会员中心 ===")
        print("开通SVIP会员，享受专属特权：")
        print("1. 专属网盘功能（10GB云存储空间）")
        print("2. 所有虚拟商品永久归属")
        print("3. 专属SVIP标识")
        print("4. 每日额外奖励")
        print("5. 专属客服支持")
        print("------------------------")
        
        # 显示当前SVIP状态
        if user.is_svip_active():
            remaining = user.get_svip_remaining_days()
            print(f"💎 您已是SVIP会员，剩余有效期: {remaining}天")
        else:
            print("您还不是SVIP会员")
        
        # 显示套餐选项
        print("\n请选择SVIP套餐：")
        for i, package in enumerate(self.svip_packages, 1):
            print(f"{i}. {package['name']} - {package['price']}钻石 - {package['desc']}")
        
        print("0. 返回主菜单")
        
        try:
            choice = int(input("请选择套餐: "))
            if choice == 0:
                return
                
            if choice < 1 or choice > len(self.svip_packages):
                print("无效的选择！")
                input("按回车键返回...")
                return
                
            package = self.svip_packages[choice - 1]
            price = package["price"]
            
            # 检查钻石是否足够
            if user.diamonds < price:
                print(f"钻石不足！需要{price}钻石，您当前有{user.diamonds}钻石")
                input("按回车键返回...")
                return
                
            # 确认购买
            confirm = input(f"确认花费{price}钻石购买{package['name']}吗？(y/n): ").strip().lower()
            if confirm != 'y':
                print("已取消购买")
                input("按回车键返回...")
                return
                
            # 扣除钻石
            user.subtract_diamonds(price)
            
            # 激活SVIP
            user.activate_svip(package["type"])
            
            # 记录交易
            user._record_transaction(f"购买{package['name']}", "支出")
            
            self.save_data()
            print(f"🎉 恭喜您已成为{package['name']}会员！")
            input("按回车键返回主菜单...")
            
        except ValueError:
            print("请输入有效的数字！")
            input("按回车键返回...")
    
    def cloud_storage(self, user):
        """网盘功能"""
        if not user.is_svip_active():
            print("⚠️ 此功能仅对SVIP会员开放")
            input("按回车键返回主菜单...")
            return
            
        print("\n=== SVIP专属网盘 ===")
        print(f"存储路径: {user.cloud_storage_path}")
        print("1. 上传文件")
        print("2. 下载文件")
        print("3. 删除文件")
        print("4. 查看文件列表")
        print("5. 创建文件夹")
        print("0. 返回主菜单")
        
        try:
            choice = int(input("请选择操作: "))
            if choice == 0:
                return
                
            if choice == 1:
                self.upload_file(user)
            elif choice == 2:
                self.download_file(user)
            elif choice == 3:
                self.delete_file(user)
            elif choice == 4:
                self.list_files(user)
            elif choice == 5:
                self.create_folder(user)
            else:
                print("无效的选择！")
                input("按回车键返回...")
                
        except ValueError:
            print("请输入有效的数字！")
            input("按回车键返回...")
    
    def upload_file(self, user):
        """上传文件到网盘"""
        print("\n=== 上传文件 ===")
        file_path = input("请输入要上传的文件路径（输入0返回）: ")
        
        if file_path == '0':
            return
            
        if not os.path.exists(file_path):
            print("文件不存在！")
            input("按回车键返回...")
            return
            
        file_name = os.path.basename(file_path)
        dest_path = os.path.join(user.cloud_storage_path, file_name)
        
        try:
            shutil.copy(file_path, dest_path)
            print(f"文件 '{file_name}' 上传成功！")
        except Exception as e:
            print(f"上传失败: {str(e)}")
            
        input("按回车键返回...")
    
    def download_file(self, user):
        """从网盘下载文件"""
        print("\n=== 下载文件 ===")
        files = os.listdir(user.cloud_storage_path)
        
        if not files:
            print("网盘为空！")
            input("按回车键返回...")
            return
            
        print("网盘文件列表:")
        for i, file in enumerate(files, 1):
            file_path = os.path.join(user.cloud_storage_path, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path) // 1024  # KB
                print(f"{i}. {file} ({size} KB)")
            else:
                print(f"{i}. {file} (文件夹)")
        
        try:
            choice = int(input("请选择要下载的文件（输入0返回）: "))
            if choice == 0:
                return
                
            if choice < 1 or choice > len(files):
                print("无效的选择！")
                input("按回车键返回...")
                return
                
            file_name = files[choice - 1]
            file_path = os.path.join(user.cloud_storage_path, file_name)
            if os.path.isdir(file_path):
                print("无法下载文件夹，请选择文件！")
                input("按回车键返回...")
                return
                
            dest_path = input("请输入保存路径（包含文件名）: ")
            
            shutil.copy(file_path, dest_path)
            print(f"文件 '{file_name}' 下载成功！")
        except Exception as e:
            print(f"下载失败: {str(e)}")
        except ValueError:
            print("请输入有效的数字！")
            
        input("按回车键返回...")
    
    def delete_file(self, user):
        """删除网盘文件"""
        print("\n=== 删除文件 ===")
        files = os.listdir(user.cloud_storage_path)
        
        if not files:
            print("网盘为空！")
            input("按回车键返回...")
            return
            
        print("网盘文件列表:")
        for i, file in enumerate(files, 1):
            file_path = os.path.join(user.cloud_storage_path, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path) // 1024  # KB
                print(f"{i}. {file} ({size} KB)")
            else:
                print(f"{i}. {file} (文件夹)")
        
        try:
            choice = int(input("请选择要删除的文件（输入0返回）: "))
            if choice == 0:
                return
                
            if choice < 1 or choice > len(files):
                print("无效的选择！")
                input("按回车键返回...")
                return
                
            file_name = files[choice - 1]
            file_path = os.path.join(user.cloud_storage_path, file_name)
            
            confirm = input(f"确定要永久删除 '{file_name}' 吗？(y/n): ").strip().lower()
            if confirm != 'y':
                print("已取消删除")
                input("按回车键返回...")
                return
                
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"文件 '{file_name}' 已删除！")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"文件夹 '{file_name}' 已删除！")
        except Exception as e:
            print(f"删除失败: {str(e)}")
        except ValueError:
            print("请输入有效的数字！")
            
        input("按回车键返回...")
    
    def list_files(self, user):
        """列出网盘文件"""
        print("\n=== 网盘文件列表 ===")
        files = os.listdir(user.cloud_storage_path)
        
        if not files:
            print("网盘为空！")
        else:
            total_size = 0
            for file in files:
                file_path = os.path.join(user.cloud_storage_path, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path) // 1024  # KB
                    total_size += size
                    print(f"- {file} ({size} KB)")
                else:
                    print(f"- {file} (文件夹)")
            
            # 显示存储空间使用情况（固定10GB）
            print(f"\n存储空间: {total_size//1024}MB/10240MB 已使用")
        
        input("\n按回车键返回...")
    
    def create_folder(self, user):
        """创建文件夹"""
        print("\n=== 创建文件夹 ===")
        folder_name = input("请输入文件夹名称（输入0返回）: ")
        
        if folder_name == '0':
            return
            
        folder_path = os.path.join(user.cloud_storage_path, folder_name)
        
        try:
            os.makedirs(folder_path, exist_ok=True)
            print(f"文件夹 '{folder_name}' 创建成功！")
        except Exception as e:
            print(f"创建失败: {str(e)}")
            
        input("按回车键返回...")
    
    # 每日随机礼包功能
    def receive_random_gift(self, user):
        """领取每日随机礼包"""
        if user.can_receive_random_gift():
            success, message = user.receive_random_gift()
            print(message)
            if success:
                self.save_data()
        else:
            print("今天已经领取过随机礼包了，明天再来吧！")
        input("按回车键返回主菜单...")

def main():
    # 程序启动时检查更新状态
    check_update_status()
    
    shop = Shop()
    current_user = None
    # 保存当前用户引用，用于反馈功能
    shop.current_user = None

    while True:
        print("\n=== 游戏商店 ===")
        
        if current_user is None:
            print("1. 注册")
            print("2. 登录")
            print("3. 官方网站")
            print("4. 反馈")
            print("5. 退出")
            
            # 检查是否有上次登录的用户
            last_user = get_last_user()
            if last_user and last_user in shop.users:
                # 提示是否继续使用上次的用户
                choice = input(f"检测到上次登录用户: {last_user}，是否继续使用该用户？(y/n): ").strip().lower()
                
                if choice == 'y':
                    # 使用上次的用户，只需输入密码
                    password = input(f"请输入 {last_user} 的密码: ")
                    current_user = shop.login_user(last_user, password)
                    shop.current_user = current_user  # 更新当前用户引用
                    if current_user is None:
                        input("按回车键返回主菜单...")
                elif choice == 'n':
                    # 不使用上次的用户，显示正常登录选项
                    choice = input("请选择操作 (1.注册 / 2.登录 / 3.官方网站 / 4.反馈 / 5.退出): ")
                    
                    if choice == "1":
                        print("\n=== 用户注册 ===")
                        print("输入 '0' 可返回主菜单")
                        # 先输入邮箱
                        while True:
                            email = input("请输入邮箱: ")
                            if email == '0':
                                print("返回主菜单...")
                                break
                            if not is_valid_email(email):
                                print("请输入有效的邮箱格式！")
                                continue
                            if email in shop.emails:
                                print("该邮箱已被注册！")
                                continue
                            # 邮箱验证通过，继续输入用户名
                            username = input("请输入用户名: ")
                            if username == '0':
                                print("返回主菜单...")
                                break
                            password = input("请输入密码: ")
                            if password == '0':
                                print("返回主菜单...")
                                break
                            # 注册用户
                            shop.register_user(username, email, password)
                            input("按回车键返回主菜单...")
                            break
                    elif choice == "2":
                        print("\n=== 用户登录 ===")
                        print("输入 '0' 可返回主菜单")
                        username = input("请输入用户名: ")
                        if username == '0':
                            print("返回主菜单...")
                            continue
                            
                        # 密码输入和忘记密码选项
                        while True:
                            print("\n1. 输入密码登录")
                            print("2. 忘记密码")
                            print("0. 返回主菜单")
                            login_choice = input("请选择: ")
                            
                            if login_choice == "1":
                                password = input("请输入密码: ")
                                current_user = shop.login_user(username, password)
                                shop.current_user = current_user  # 更新当前用户引用
                                if current_user is None:
                                    input("按回车键继续...")
                                else:
                                    break
                            elif login_choice == "2":
                                shop.forgot_password(username)
                                input("按回车键继续...")
                            elif login_choice == "0":
                                print("返回主菜单...")
                                break
                            else:
                                print("无效选择！")
                                
                        if current_user is None:
                            input("按回车键返回主菜单...")
                    elif choice == "3":
                        shop.show_official_website()
                    elif choice == "4":
                        shop.show_feedback_link()
                    elif choice == "5":
                        print("感谢使用，再见！")
                        break
                    else:
                        print("无效选择！")
                        input("按回车键返回主菜单...")
                else:
                    print("无效输入！")
                    input("按回车键返回主菜单...")
            else:
                # 没有上次登录的用户，显示正常登录选项
                choice = input("请选择: ")
                
                if choice == "1":
                    print("\n=== 用户注册 ===")
                    print("输入 '0' 可返回主菜单")
                    # 先输入邮箱
                    while True:
                        email = input("请输入邮箱: ")
                        if email == '0':
                            print("返回主菜单...")
                            break
                        if not is_valid_email(email):
                            print("请输入有效的邮箱格式！")
                            continue
                        if email in shop.emails:
                            print("该邮箱已被注册！")
                            continue
                        # 邮箱验证通过，继续输入用户名
                        username = input("请输入用户名: ")
                        if username == '0':
                            print("返回主菜单...")
                            break
                        password = input("请输入密码: ")
                        if password == '0':
                            print("返回主菜单...")
                            break
                        # 注册用户
                        shop.register_user(username, email, password)
                        input("按回车键返回主菜单...")
                        break
                elif choice == "2":
                    print("\n=== 用户登录 ===")
                    print("输入 '0' 可返回主菜单")
                    username = input("请输入用户名: ")
                    if username == '0':
                        print("返回主菜单...")
                        continue
                        
                    # 密码输入和忘记密码选项
                    while True:
                        print("\n1. 输入密码登录")
                        print("2. 忘记密码")
                        print("0. 返回主菜单")
                        login_choice = input("请选择: ")
                        
                        if login_choice == "1":
                            password = input("请输入密码: ")
                            current_user = shop.login_user(username, password)
                            shop.current_user = current_user  # 更新当前用户引用
                            if current_user is None:
                                input("按回车键继续...")
                            else:
                                break
                        elif login_choice == "2":
                            shop.forgot_password(username)
                            input("按回车键继续...")
                        elif login_choice == "0":
                            print("返回主菜单...")
                            break
                        else:
                            print("无效选择！")
                                
                    if current_user is None:
                        input("按回车键返回主菜单...")
                elif choice == "3":
                    shop.show_official_website()
                elif choice == "4":
                    shop.show_feedback_link()
                elif choice == "5":
                    print("感谢使用，再见！")
                    break
                else:
                    print("无效选择！")
                    input("按回车键返回主菜单...")
        else:
            print(f"欢迎回来，{current_user.username}")
            # 显示SVIP状态
            if current_user.is_svip_active():
                remaining = current_user.get_svip_remaining_days()
                print(f"💎 SVIP会员 剩余{remaining}天")
            
            print(f"当前资产: 绿宝石 {current_user.emeralds}, 钻石 {current_user.diamonds}")
            print("1. 充值")
            print("2. 获取绿宝石(此功能已被禁用)")
            print("3. 绿宝石任务中心")
            print("4. 获取钻石(此功能已被禁用)")
            print("5. 查看商品")
            print("6. 购买商品")
            print("7. 购物车")
            print("8. 创建自定义商品")
            print("9. 查看背包")
            print("10. 查看订单")
            print("11. 申请退款")
            print("12. 确认收货")
            print("13. 查看资产")
            print("14. 查看交易记录")
            print("15. 设置支付密码")
            print("16. 设置默认地址")
            print("17. 使用抽奖机")
            print("18. 官方网站")
            print("19. 反馈")
            print("20. 注销账户")
            print("21. 退出登录")
            print("22. 修改登录密码")
            print("23. 修改用户名")
            # 添加SVIP菜单项
            print("24. SVIP会员中心")
            print("25. 专属网盘")
            # 添加每日随机礼包菜单项
            print("26. 每日随机礼包")
            
            choice = input("请选择: ")
            
            if choice == "1":
                print("\n=== 充值中心 ===")
                print("1. 充值绿宝石")
                print("2. 充值钻石")
                print("0. 返回主菜单")
                sub_choice = input("请选择: ")
                
                if sub_choice == "1":
                    shop.recharge_emeralds(current_user)
                elif sub_choice == "2":
                    shop.recharge_diamonds(current_user)
                elif sub_choice == "0":
                    print("返回主菜单...")
                else:
                    print("无效选择！")
                    input("按回车键返回主菜单...")
            elif choice == "999999999999=== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ====== 获取绿宝石 ===":
                print("\n=== 获取绿宝石 ===")
                print("1. 输入文字")
                print("2. 观看广告")
                print("0. 返回主菜单")
                sub_choice = input("请选择: ")
                
                if sub_choice == "1":
                    shop.earn_emeralds_by_typing(current_user)
                elif sub_choice == "2":
                    shop.earn_emeralds_by_ad(current_user)
                elif sub_choice == "0":
                    print("返回主菜单...")
                else:
                    print("无效选择！")
                    input("按回车键返回主菜单...")
            elif choice == "3":
                shop.show_emerald_tasks(current_user)
            elif choice == "(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)(此功能已被禁用)114514":
                print("\n=== 获取钻石 ===")
                print("1. 观看广告 (50%概率获得钻石)")
                print("0. 返回主菜单")
                sub_choice = input("请选择: ")
                
                if sub_choice == "1":
                    shop.earn_diamonds_by_ad(current_user)
                elif sub_choice == "0":
                    print("返回主菜单...")
                else:
                    print("无效选择！")
                    input("按回车键返回主菜单...")
            elif choice == "5":
                shop.display_items()
            elif choice == "6":
                shop.purchase_item(current_user)
            elif choice == "7":
                shop.display_shopping_cart(current_user)
            elif choice == "8":
                shop.create_custom_item()
            elif choice == "9":
                shop.display_inventory(current_user)
            elif choice == "10":
                shop.display_orders(current_user)
            elif choice == "11":
                shop.refund_order(current_user)
            elif choice == "12":  # 新增：确认收货功能
                shop.confirm_receipt(current_user)
            elif choice == "13":
                shop.display_assets(current_user)
            elif choice == "14":
                print("\n=== 查看交易记录 ===")
                print("输入 '0' 可返回主菜单")
                current_user.display_transactions()
                choice = input("\n请输入0返回主菜单: ")
                if choice == '0':
                    continue
            elif choice == "15":
                print("\n=== 设置支付密码 ===")
                print("输入 '0' 可返回主菜单")
                current_pwd = input("请输入当前支付密码: ")
                if current_pwd == '0':
                    print("返回主菜单...")
                    continue
                    
                new_pwd = input("请输入新的支付密码: ")
                if new_pwd == '0':
                    print("返回主菜单...")
                    continue
                    
                confirm_pwd = input("请再次输入新的支付密码: ")
                if confirm_pwd == '0':
                    print("返回主菜单...")
                    continue
                    
                if current_user.set_payment_password(current_pwd, new_pwd, confirm_pwd):
                    shop.save_data()
                
                input("按回车键返回主菜单...")
            elif choice == "16":
                print("\n=== 设置默认地址 ===")
                print("输入 '0' 可返回主菜单")
                address = input("请输入默认地址: ")
                if address == '0':
                    print("返回主菜单...")
                    continue
                current_user.set_default_address(address)
                shop.save_data()
                input("按回车键返回主菜单...")
            elif choice == "17":
                shop.use_lucky_draw(current_user)
            elif choice == "18":
                shop.show_official_website()
            elif choice == "19":
                shop.show_feedback_link()
            elif choice == "20":
                print("\n=== 注销账户 ===")
                print("输入 '0' 可返回主菜单")
                password = input("请输入账户密码确认注销: ")
                if password == '0':
                    print("返回主菜单...")
                    continue
                if shop.delete_user(current_user.username, password):
                    current_user = None  # 确保当前用户引用被清除
                    shop.current_user = None  # 更新当前用户引用
                    input("按回车键返回主菜单...")
                else:
                    input("按回车键返回主菜单...")
            elif choice == "21":
                shop.logout_user(current_user.username)
                current_user = None
                shop.current_user = None  # 更新当前用户引用
                input("按回车键返回主菜单...")
            elif choice == "22":
                print("\n=== 修改登录密码 ===")
                print("输入 '0' 可返回主菜单")
                current_pwd = input("请输入当前密码: ")
                if current_pwd == '0':
                    print("返回主菜单...")
                    continue
                if current_user.verify_password(current_pwd):
                    new_pwd = input("请输入新密码: ")
                    if new_pwd == '0':
                        print("返回主菜单...")
                        continue
                    confirm_pwd = input("请再次输入新密码: ")
                    if confirm_pwd == '0':
                        print("返回主菜单...")
                        continue
                    if new_pwd == confirm_pwd:
                        current_user.set_password(new_pwd)
                        shop.save_data()
                        print("请重新登录")
                        current_user = None  # 强制重新登录
                        shop.current_user = None  # 更新当前用户引用
                        input("按回车键返回主菜单...")
                    else:
                        print("两次输入的密码不一致！")
                        input("按回车键返回主菜单...")
                else:
                    print("当前密码错误！")
                    input("按回车键返回主菜单...")
            elif choice == "23":
                print("\n=== 修改用户名 ===")
                print("输入 '0' 可返回主菜单")
                current_pwd = input("请输入当前密码验证身份: ")
                if current_pwd == '0':
                    print("返回主菜单...")
                    continue
                if current_user.verify_password(current_pwd):
                    old_username = current_user.username
                    new_username = input("请输入新用户名: ")
                    if new_username == '0':
                        print("返回主菜单...")
                        continue
                    if shop.change_username(old_username, current_user, new_username):
                        print("请重新登录")
                        current_user = None  # 强制重新登录
                        shop.current_user = None  # 更新当前用户引用
                        input("按回车键返回主菜单...")
                    else:
                        input("按回车键返回主菜单...")
                else:
                    print("密码错误，无法修改用户名！")
                    input("按回车键返回主菜单...")
            elif choice == "24":
                shop.purchase_svip(current_user)
            elif choice == "25":
                shop.cloud_storage(current_user)
            elif choice == "26":
                # 每日随机礼包功能
                shop.receive_random_gift(current_user)
            else:
                print("无效选择！")
                input("按回车键返回主菜单...")

if __name__ == "__main__":
    main()