# login.py
import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import Config, setup_logging, random_sleep
from PIL import Image
import io
import webbrowser

logger = setup_logging()

def take_captcha_screenshot(driver):
    """截取验证码图片并保存"""
    try:
        # 等待验证码图片加载
        captcha_element = WebDriverWait(driver, Config.WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "yanzhengma"))
        )
        
        # 方法1：直接截取验证码元素
        captcha_screenshot = captcha_element.screenshot_as_png
        image = Image.open(io.BytesIO(captcha_screenshot))
        image_path = "captcha.png"
        image.save(image_path)
        logger.info(f"验证码已保存至 {image_path}")
        
        # 尝试打开图片
        try:
            webbrowser.open(image_path)
        except Exception as e:
            logger.warning(f"无法自动打开验证码图片：{str(e)}")
            logger.info(f"请手动打开 {image_path} 查看验证码")
        
        return image_path
           

    except Exception as e:
        
        return None

def delete_image(image_path: str):
    """删除指定路径的图片"""
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            logger.info(f"已删除 {image_path}")
    except Exception as e:
        logger.warning(f"删除图片失败：{str(e)}")

def get_user_info(driver):
    """获取用户信息"""
    try:
        result = driver.execute_script("""
            return new Promise((resolve, reject) => {
                var xhr = new XMLHttpRequest();
                xhr.open('POST', arguments[0], true);
                xhr.setRequestHeader('Content-Type', 'application/json');
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4) {
                        if (xhr.status === 200) {
                            try {
                                var response = JSON.parse(xhr.responseText);
                                if (response.success && response.data) {
                                    resolve(response.data);
                                } else {
                                    reject(new Error('API返回数据格式错误'));
                                }
                            } catch (e) {
                                reject(new Error('解析响应数据失败: ' + e.message));
                            }
                        } else {
                            reject(new Error('HTTP错误: ' + xhr.status));
                        }
                    }
                };
                
                xhr.onerror = function() {
                    reject(new Error('网络请求失败'));
                };
                
                xhr.send();
            });
        """, Config.USER_INFO_URL)
        
        if result and 'idCardHash' in result:
            name = result.get('name', '未知用户')
            id_card_hash = result['idCardHash']
            logger.info(f"✅ 获取用户信息成功: {name}")
            return id_card_hash
            
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
    
    return None

def dtdjzx_login(driver, username: str, password: str, max_retries: int = Config.LOGIN_RETRY_COUNT) -> bool:
    """执行登录流程 - 提供多次登录机会"""
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"开始第 {attempt}/{max_retries} 次登录尝试...")
            
            # 每次尝试都重新访问登录页面
            driver.get(Config.LOGIN_URL)
            
            # 等待页面加载
            WebDriverWait(driver, Config.WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "loginForm"))
            )
            random_sleep(2, 3)
            
            # 填写用户名密码
            username_field = driver.find_element(By.ID, "username")
            password_field = driver.find_element(By.ID, "password")
            
            # 清空字段并重新输入
            username_field.clear()
            password_field.clear()
            
            username_field.send_keys(username)
            password_field.send_keys(password)
            logger.info("已填写用户名密码")
            
            # 截取验证码并输入
            captcha_path = take_captcha_screenshot(driver)
            if not captcha_path:
                logger.error("无法获取验证码图片，登录失败")
                if attempt < max_retries:
                    logger.info(f"等待{Config.LOGIN_RETRY_DELAY}秒后重试...")
                    time.sleep(Config.LOGIN_RETRY_DELAY)
                    continue
                else:
                    return False
            
            validate_code = input("请查看验证码图片并输入: ").strip()
            validate_field = driver.find_element(By.ID, "validateCode")
            validate_field.clear()
            validate_field.send_keys(validate_code)
            
            # 删除验证码图片
            delete_image(captcha_path)
            
            # 点击登录
            driver.find_element(By.CLASS_NAME, "js-submit").click()
            logger.info("已提交登录")
            
            # 等待登录完成
            time.sleep(Config.SHORT_WAIT)
            
            # 检查是否登录成功
            if Config.LOGIN_URL in driver.current_url:
                logger.warning(f"第 {attempt} 次登录失败，可能用户名、密码或验证码错误")
                
                if attempt < max_retries:
                    logger.info(f"等待{Config.LOGIN_RETRY_DELAY}秒后重试...")
                    time.sleep(Config.LOGIN_RETRY_DELAY)
                    continue
                else:
                    logger.error("登录尝试次数已用完，登录失败")
                    return False
            
            # 跳转到学院
            college_link = WebDriverWait(driver, Config.WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href*="gbwlxy.dtdjzx.gov.cn"]'))
            )
            college_link.click()
            
            # 切换到新窗口
            WebDriverWait(driver, Config.WAIT_TIMEOUT).until(EC.number_of_windows_to_be(2))
            driver.switch_to.window(driver.window_handles[-1])
            
            # 等待学院页面加载并获取用户信息
            WebDriverWait(driver, Config.LONG_WAIT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            id_card_hash = get_user_info(driver)
            if id_card_hash:
                driver.id_card_hash = id_card_hash
                logger.info(f"✅ 第 {attempt} 次登录成功，用户ID: {id_card_hash}")
                return True
            else:
                logger.warning(f"第 {attempt} 次登录后无法获取用户信息")
                if attempt < max_retries:
                    logger.info(f"等待{Config.LOGIN_RETRY_DELAY}秒后重试...")
                    time.sleep(Config.LOGIN_RETRY_DELAY)
                    continue
                else:
                    return False
                
        except Exception as e:
            logger.error(f"第 {attempt} 次登录失败: {str(e)}")
            
            if attempt < max_retries:
                logger.info(f"等待{Config.LOGIN_RETRY_DELAY}秒后重试...")
                time.sleep(Config.LOGIN_RETRY_DELAY)
            else:
                logger.error("登录尝试次数已用完，登录失败")
    
    return False