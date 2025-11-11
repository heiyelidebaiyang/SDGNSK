# config.py
import logging
import random
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class Config:
    """配置类"""
    # 登录配置
    USERNAME = ''
    PASSWORD = ''
    LOGIN_RETRY_COUNT = 3
    LOGIN_RETRY_DELAY = 3
    
    # 等待时间配置
    WAIT_TIMEOUT = 30
    SHORT_WAIT = 5
    LONG_WAIT = 60
    RETRY_COUNT = 3
    
    # 浏览器配置
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    HEADLESS_MODE = True  # 是否启用无头模式
    
    # API配置
    API_BASE_URL = "https://gbwlxy.dtdjzx.gov.cn/__api/api"
    SUBJECT_QUERY_URL = f"{API_BASE_URL}/subject/query"
    SUBJECT_COURSE_QUERY_URL = f"{API_BASE_URL}/subject/queryCourse"
    STUDY_START_URL = f"{API_BASE_URL}/study/start"
    STUDY_PROGRESS_URL = f"{API_BASE_URL}/study/progress"
    STUDY_PROGRESS2_URL = "https://gbwlxy.dtdjzx.gov.cn/apiStudy/gwapi/us/api/study/progress2"
    STUDY_END_URL = f"{API_BASE_URL}/study/v2/end"
    USER_INFO_URL = f"{API_BASE_URL}/user/info"
    STATISTICS_URL = f"{API_BASE_URL}/personal/totalStatistics"
    
    # 学习配置
    PROGRESS_INTERVAL = 3  # 5秒上报一次进度
    PROGRESS_DURATION = 300  # 每次上报5分钟的时长
    COURSE_INTERVAL = 5  # 课程间隔10秒
    CHECK_PROGRESS_AFTER_COURSE = True  # 每门课程完成后检查学习进度
    
    # 页面配置
    COURSE_PAGE_URL = "https://gbwlxy.dtdjzx.gov.cn/content#/commend/coursedetail?courseId={course_id}&flag=zt&courseListId={subject_id}"
    COLLEGE_HOME_URL = "https://gbwlxy.dtdjzx.gov.cn/"
    LOGIN_URL = "https://sso.dtdjzx.gov.cn/sso/login"
    
    # 视频播放配置 - 暂时关闭自动播放和倍速
    PLAYBACK_SPEED = 3.0  # 恢复为正常速度
    AUTO_PLAY = True  # 关闭自动播放
    MUTED = False  # 关闭静音
    ENABLE_VIDEO_JS = True  # 总开关，控制是否执行视频相关的JavaScript代码

     # 视频结束配置
    LAST_REPORT_BEFORE_END = 60  # 最后一次上报在视频结束前的秒数
    FINAL_VIDEO_WAIT = 61  # 最后一次上报后等待视频播放结束的秒数
    
    # API重试配置
    API_RETRY_COUNT = 2  # API重试次数
    API_RETRY_DELAY = 0.5  # API重试延迟（秒）
    
    # 播放按钮配置
    PLAY_BUTTON_SELECTORS = [
        "button.vjs-big-play-button",  # 大播放按钮
        "button.vjs-play-control",     # 控制栏播放按钮
    ]
    
    # 日志配置
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_FILE = 'shuake.log'

def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('shuake.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def random_sleep(min_seconds: float = 1, max_seconds: float = 3):
    """随机睡眠时间"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def setup_driver() -> webdriver.Chrome:
    """设置浏览器驱动"""
    chrome_options = Options()
    
    # 基本配置
    chrome_options.add_argument(f'--user-agent={Config.USER_AGENT}')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 隐藏 DevTools 监听信息和其他控制台输出
    chrome_options.add_argument('--log-level=3')  # 只显示致命错误
    chrome_options.add_argument('--disable-logging')  # 禁用日志记录
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    
    # 禁用硬件加速和 USB 检测
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    chrome_options.add_argument('--disable-renderer-backgrounding')
    
    # 无头模式配置
    if Config.HEADLESS_MODE:
        chrome_options.add_argument('--headless')
    
    # 设置环境变量来隐藏更多输出
    os.environ['WDM_LOG_LEVEL'] = '0'  # 设置 WebDriver Manager 日志级别
    os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver