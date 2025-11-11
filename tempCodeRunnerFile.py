# shuake.py
import time
from config import setup_driver, Config, setup_logging
from login import dtdjzx_login
from api_utils import APIUtils
from course_learner import CourseLearner

logger = setup_logging()

class Shuake:
    def __init__(self):
        self.driver = setup_driver()
        self.api_utils = APIUtils(self.driver)
        self.learner = CourseLearner(self.driver)
    
    def start(self):
        """主启动方法"""
        try:
            # 登录 - 提供多次机会
            if not dtdjzx_login(self.driver, Config.USERNAME, Config.PASSWORD, max_retries=Config.LOGIN_RETRY_COUNT):
                logger.error("登录失败，程序退出")
                return False
            
            # 检查学习进度
            total_hours, completed_hours, progress = self.api_utils.get_study_hours()
            if progress >= 100:
                logger.info("🎉 学习已完成")
                return True
            
            logger.info(f"当前进度: {progress:.1f}%")
            
            # 获取专栏并学习
            subjects = self.api_utils.get_subjects()
            for subject in subjects:
                if self.learn_subject(subject):
                    logger.info(f"✅ 专栏完成: {subject['name']}")
                else:
                    logger.warning(f"❌ 专栏学习失败: {subject['name']}")
                
                # 检查总体进度
                _, _, new_progress = self.api_utils.get_study_hours()
                if new_progress >= 100:
                    logger.info("🎉 所有学习完成！")
                    break
            
            return True
            
        except Exception as e:
            logger.error(f"程序执行出错: {str(e)}")
            return False
        finally:
            self.cleanup()
    
    def learn_subject(self, subject):
        """学习单个专栏"""
        try:
            logger.info(f"处理专栏: {subject['name']}")
            
            courses = self.api_utils.get_courses(subject['id'])
            courses_to_study = [c for c in courses if c['need_study'] and not c['has_test']]
            
            if not courses_to_study:
                logger.info("没有需要学习的课程")
                return True
            
            logger.info(f"找到 {len(courses_to_study)} 门需要学习的课程")
            
            success_count = 0
            for course in courses_to_study:
                # 传递subject_id给learner
                result = self.learner.learn_course(course, subject['id'])
                
                if result == "COMPLETED":
                    logger.info("🎉 学习已完成，停止后续课程")
                    return True
                elif result:
                    success_count += 1
                    logger.info(f"进度: {success_count}/{len(courses_to_study)}")
                    
                    # 如果不是最后一门课程，等待指定间隔再开始下一门
                    if success_count < len(courses_to_study):
                        logger.info(f"等待{Config.COURSE_INTERVAL}秒后开始下一门课程...")
                        time.sleep(Config.COURSE_INTERVAL)
            
            logger.info(f"本专栏完成: {success_count}/{len(courses_to_study)}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"学习专栏时出错: {str(e)}")
            return False
    
    def cleanup(self):
        """清理资源"""
        try:
            self.driver.quit()
            logger.info("浏览器已关闭")
        except:
            pass

if __name__ == '__main__':
    shuake = Shuake()
    success = shuake.start()
    if success:
        logger.info("程序执行完成")
    else:
        logger.error("程序执行失败")