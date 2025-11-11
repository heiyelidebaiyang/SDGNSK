# course_learner.py
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import Config, setup_logging, random_sleep
from api_utils import APIUtils

logger = setup_logging()

class CourseLearner:
    def __init__(self, driver):
        self.driver = driver
        self.api_utils = APIUtils(driver)
    
    def open_course_page(self, course_id, subject_id):
        """打开课程页面并尝试播放视频"""
        try:
            # 构建课程页面URL
            course_url = Config.COURSE_PAGE_URL.format(course_id=course_id, subject_id=subject_id)
            logger.info(f"打开课程页面: {course_url}")
            
            # 打开课程页面
            self.driver.get(course_url)
            
            # 等待页面加载
            WebDriverWait(self.driver, Config.WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 等待视频播放器加载
            time.sleep(Config.SHORT_WAIT)
            
            # 尝试点击播放按钮
            self.click_play_button()
            
            return True
            
        except Exception as e:
            logger.error(f"打开课程页面失败: {str(e)}")
            return False
    
    def refresh_and_play(self, course_id, subject_id):
        """刷新页面并尝试播放视频"""
        try:
            logger.info("刷新页面并重新播放视频...")
            
            # 刷新页面
            self.driver.refresh()
            
            # 等待页面加载
            WebDriverWait(self.driver, Config.WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 等待视频播放器加载
            time.sleep(Config.SHORT_WAIT)
            
            # 尝试点击播放按钮
            self.click_play_button()
            
            logger.info("✅ 页面刷新完成并已重新播放视频")
            return True
            
        except Exception as e:
            logger.error(f"刷新页面并播放视频失败: {str(e)}")
            return False
    
    def click_play_button(self):
        """尝试点击播放按钮"""
        try:
            # 等待一下让播放器完全加载
            time.sleep(2)
            
            # 使用配置的播放按钮选择器
            for selector in Config.PLAY_BUTTON_SELECTORS:
                play_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if play_buttons:
                    play_buttons[0].click()
                    logger.info(f"✅ 已点击播放按钮: {selector}")
                    return True
            
            # 如果以上按钮都没找到，尝试通用的播放按钮
            generic_play_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'play') or contains(text(), '播放') or contains(text(), 'Play')]")
            if generic_play_buttons:
                generic_play_buttons[0].click()
                logger.info("✅ 已点击通用播放按钮")
                return True
            
            logger.warning("未找到播放按钮")
            return False
            
        except Exception as e:
            logger.error(f"点击播放按钮失败: {str(e)}")
            return False
    
    def navigate_to_college(self):
        """导航回学院首页，保持会话状态"""
        try:
            # 导航回学院首页
            self.driver.get(Config.COLLEGE_HOME_URL)
            
            # 等待页面加载
            WebDriverWait(self.driver, Config.WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info("已导航回学院首页")
            
        except Exception as e:
            logger.error(f"导航回学院首页失败: {str(e)}")
            # 如果导航失败，尝试刷新当前页面
            try:
                self.driver.refresh()
                logger.info("已刷新当前页面")
            except:
                pass
    
    def check_study_completion(self):
        """检查学习是否已完成（达到100%）"""
        try:
            _, _, progress = self.api_utils.get_study_hours()
            if progress >= 100:
                logger.info("🎉 学习已完成，进度达到100%")
                return True
            return False
        except Exception as e:
            logger.error(f"检查学习进度失败: {str(e)}")
            return False
    
    def check_course_completion(self, course_id, subject_id):
        """检查特定课程是否已完成"""
        try:
            # 获取课程列表
            courses = self.api_utils.get_courses(subject_id)
            
            # 查找当前课程
            for course in courses:
                if course['id'] == course_id:
                    if not course['need_study']:
                        logger.info(f"✅ 课程已完成确认: {course['title']}")
                        return True
                    else:
                        logger.info(f"⚠️ 课程未完成: {course['title']}")
                        return False
            
            logger.warning(f"未找到课程: {course_id}")
            return False
            
        except Exception as e:
            logger.error(f"检查课程完成状态失败: {str(e)}")
            return False
    
    def countdown_timer(self, seconds):
        """显示倒计时"""
        for i in range(seconds, 0, -1):
            logger.info(f"⏰ 倒计时: {i}秒")
            time.sleep(1)
        logger.info("⏰ 倒计时结束")
    
    def learn_course(self, course_info, subject_id):
        """学习课程 - 打开页面后发送开始学习API，然后每5秒上报一次进度，最后确认课程完成状态"""
        try:
            logger.info(f"开始学习: {course_info['title']}")
            
            # 检查课程状态
            if not course_info['need_study']:
                logger.info("✅ 课程已完成，跳过")
                return True
            
            # 检查随堂测试
            if course_info['has_test']:
                logger.info("❌ 课程有随堂测试，跳过")
                return False
            
            # 先打开课程页面并尝试播放视频
            if not self.open_course_page(course_info['id'], subject_id):
                logger.warning("打开课程页面失败，但继续尝试开始学习")
            
            # 开始学习 - 在打开课程页面后调用开始学习API
            start_result = self.api_utils.start_study(course_info['id'])
            if not start_result:
                logger.warning("开始学习API调用失败")
                return False
            
            logger.info("✅ 开始学习API调用成功")
            
            # 模拟学习过程：每5秒上报一次进度，studyTimes为累计值
            total_duration = course_info['duration_seconds']
            if total_duration <= 0:
                logger.warning("课程时长为0，跳过")
                return False
            
            logger.info(f"课程总时长: {total_duration}秒 ({total_duration//60}分{total_duration%60}秒)")
            
            # 计算需要上报的次数和每次上报的时长
            report_interval = Config.PROGRESS_INTERVAL  # 上报间隔
            study_times_per_report = Config.PROGRESS_DURATION  # 每次上报时长
            
            # 计算总上报次数 - 最后一次上报在视频结束前指定秒数
            remaining_duration = total_duration - Config.LAST_REPORT_BEFORE_END  # 减去最后指定秒数
            total_reports = (remaining_duration + study_times_per_report - 1) // study_times_per_report
            
            logger.info(f"预计上报次数: {total_reports}次，每次累计上报{study_times_per_report}秒")
            logger.info(f"最后一次上报后，视频将自动播放最后{Config.LAST_REPORT_BEFORE_END}秒")
            
            # 累计已上报的时长（无论成功与否）
            total_reported_time = 0
            
            for report_count in range(1, total_reports + 1):
                # 计算本次上报的累计时长
                total_reported_time = min(total_reported_time + study_times_per_report, remaining_duration)
                
                # 上报学习进度 - 使用累计时长
                success = self.api_utils.report_progress(course_info['id'], total_reported_time)
                
                progress_percent = (total_reported_time / total_duration) * 100
                
                if success:
                    logger.info(f"✅ 进度上报 {report_count}/{total_reports}: 累计 {total_reported_time}秒 (总进度: {progress_percent:.1f}%)")
                else:
                    logger.warning(f"❌ 进度上报失败: {report_count}/{total_reports}，累计 {total_reported_time}秒 (总进度: {progress_percent:.1f}%)")
                
                # 如果不是最后一次，等待指定间隔
                if report_count < total_reports:
                    logger.info(f"等待{report_interval}秒后继续...")
                    time.sleep(report_interval)
            
            # 最后一次上报后，刷新页面并播放视频，让视频自动播放最后指定秒数
            logger.info(f"最后一次上报完成，刷新页面并播放视频，等待{Config.FINAL_VIDEO_WAIT}秒让视频播放结束...")
            self.refresh_and_play(course_info['id'], subject_id)
            
            # 显示倒计时
            logger.info("✅ 页面刷新完成并已重新播放视频")
            self.countdown_timer(Config.FINAL_VIDEO_WAIT)
            
            # 结束学习
            end_result = self.api_utils.end_study(course_info['id'])
            
            # 检查结束学习API的返回结果
            if end_result and end_result.get('success'):
                logger.info("✅ 课程学习完成")
                
                # 等待一下，让服务器有时间更新状态
                time.sleep(Config.SHORT_WAIT)
                
                # 确认课程完成状态
                course_completed = self.check_course_completion(course_info['id'], subject_id)
                
                if course_completed:
                    logger.info(f"✅ 课程 {course_info['title']} 已确认完成")
                else:
                    logger.warning(f"⚠️ 课程 {course_info['title']} 可能未完全完成，但继续流程")
                
                # 学习完成后跳转回学院首页，保持会话状态
                self.navigate_to_college()
                
                # 检查学习进度是否已完成
                if Config.CHECK_PROGRESS_AFTER_COURSE:
                    if self.check_study_completion():
                        return "COMPLETED"  # 特殊返回值表示学习已完成
                
                return True
            else:
                # 结束学习API返回失败
                error_msg = "未知错误"
                if end_result and 'data' in end_result:
                    error_data = end_result['data']
                    if isinstance(error_data, dict) and 'message' in error_data:
                        error_msg = error_data['message']
                    else:
                        error_msg = str(error_data)
                elif end_result and 'error' in end_result:
                    error_msg = end_result['error']
                
                logger.error(f"❌ 结束学习API返回失败: {error_msg}")
                logger.error("该课程未完成学习")
                
                # 即使结束学习失败，也跳转回学院首页
                self.navigate_to_college()
                
                return False
                
        except Exception as e:
            logger.error(f"学习课程时出错: {str(e)}")
            
            # 出错时也尝试跳转回学院首页
            try:
                self.navigate_to_college()
            except:
                pass
            
            return False