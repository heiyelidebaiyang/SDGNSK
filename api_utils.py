# api_utils.py
import json
import time
import sys
from config import Config, setup_logging

logger = setup_logging()

class APIUtils:
    """API工具类"""
    
    def __init__(self, driver):
        self.driver = driver
    
    def call_api(self, url, payload, timeout=30000):
        """通用API调用方法"""
        try:
            result = self.driver.execute_script(f"""
                return new Promise((resolve, reject) => {{
                    var xhr = new XMLHttpRequest();
                    xhr.open('POST', arguments[0], true);
                    xhr.setRequestHeader('Content-Type', 'application/json');
                    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                    xhr.timeout = {timeout};
                    
                    xhr.onreadystatechange = function() {{
                        if (xhr.readyState === 4) {{
                            if (xhr.status === 200) {{
                                try {{
                                    var response = JSON.parse(xhr.responseText);
                                    resolve({{success: true, data: response}});
                                }} catch (e) {{
                                    resolve({{success: false, error: '解析响应数据失败: ' + e.message}});
                                }}
                            }} else {{
                                resolve({{success: false, error: 'HTTP错误: ' + xhr.status, status: xhr.status}});
                            }}
                        }}
                    }};
                    
                    xhr.ontimeout = function() {{
                        resolve({{success: false, error: '请求超时'}});
                    }};
                    
                    xhr.onerror = function() {{
                        resolve({{success: false, error: '网络请求失败'}});
                    }};
                    
                    xhr.send(JSON.stringify(arguments[1]));
                }});
            """, url, payload)
            
            return result
            
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_subjects(self):
        """获取专栏列表"""
        payload = {"pagesize": 12, "pagenum": 0}
        result = self.call_api(Config.SUBJECT_QUERY_URL, payload)
        
        subjects = []
        if result and result.get('success') and 'datalist' in result.get('data', {}):
            for subject in result['data']['datalist']:
                subjects.append({
                    "id": str(subject.get('id', '')),
                    "name": subject.get('name', '未知专栏'),
                    "course_count": subject.get('courseCount', 0)
                })
        
        return subjects
    
    def get_courses(self, subject_id):
        """获取专栏课程"""
        id_card_hash = getattr(self.driver, 'id_card_hash', '')
        payload = {
            "subjectId": subject_id,
            "pagesize": 1000,
            "pagenum": 0,
            "idCardHash": id_card_hash
        }
        
        result = self.call_api(Config.SUBJECT_COURSE_QUERY_URL, payload)
        
        courses = []
        if result and result.get('success') and 'datalist' in result.get('data', {}):
            for course in result['data']['datalist']:
                study_status = str(course.get('studyStatus', '0'))
                need_study = not (study_status == '2' or course.get('showStatusMsg') == '已学习')
                
                duration_str = course.get('showCourseDuration', '')
                duration_seconds = self._parse_duration(duration_str)
                
                courses.append({
                    "id": str(course.get('id', '')),
                    "title": course.get('name', '未知课程'),
                    "need_study": need_study,
                    "duration_seconds": duration_seconds,
                    "has_test": course.get('assessementType', '0') != '1'
                })
        
        return courses
    
    def start_study(self, course_id):
        """开始学习"""
        id_card_hash = getattr(self.driver, 'id_card_hash', '')
        payload = {
            "courseId": course_id,
            "idCardHash": id_card_hash,
            "studyType": "VIDEO"
        }
        
        result = self.call_api(Config.STUDY_START_URL, payload)
        return result and result.get('success')
    
    def report_progress(self, course_id, study_times):
        """上报学习进度 - 只在连接断开时重试第一个API"""
        id_card_hash = getattr(self.driver, 'id_card_hash', '')
        
        # 调用第一个API
        payload1 = {
            "userId": id_card_hash,
            "courseCode": course_id,
            "studyTimes": study_times
        }
        
        # 第一次调用第一个API
        result1 = self.call_api(Config.STUDY_PROGRESS2_URL, payload1, timeout=15000)
        
        # 检查是否需要重试（仅在连接断开时）
        if result1 and result1.get('error') and '网络请求失败' in result1.get('error', ''):
            logger.warning("第一个API连接断开，0.5秒后重试...")
            time.sleep(0.5)  # 0.5秒后重试
            result1 = self.call_api(Config.STUDY_PROGRESS2_URL, payload1, timeout=15000)
            if result1 and result1.get('error') and '网络请求失败' in result1.get('error', ''):
                logger.warning("第一个API重试后仍然连接断开，继续执行第二个API")
            else:
                logger.info("第一个API重试成功")
        
        # 调用第二个API（只关注这个API的结果）
        payload2 = {
            "courseId": course_id,
            "idCardHash": id_card_hash,
            "studyTimes": study_times
        }
        result2 = self.call_api(Config.STUDY_PROGRESS_URL, payload2, timeout=15000)
        
        # 检查认证状态
        if result2 and not result2.get('success'):
            error_data = result2.get('data', {})
            error_message = error_data.get('message', '') if isinstance(error_data, dict) else ''
            if "请求未认证" in str(error_message) or "登录超时" in str(error_message):
                logger.error(f"❌ 认证失败: {error_message}")
                logger.error("程序即将退出...")
                time.sleep(2)
                sys.exit(1)
        
        # 只根据第二个API的success字段判断是否成功
        success = result2 and result2.get('success')
        
        return success
    
    def end_study(self, course_id):
        """结束学习 - 返回API的完整结果"""
        id_card_hash = getattr(self.driver, 'id_card_hash', '')
        payload = {
            "courseId": course_id,
            "idCardHash": id_card_hash
        }
        
        result = self.call_api(Config.STUDY_END_URL, payload)
        return result
    
    def get_study_hours(self):
        """获取学时信息"""
        id_card_hash = getattr(self.driver, 'id_card_hash', '')
        payload = {
            "year": 2025,
            "idCardHash": id_card_hash
        }
        
        result = self.call_api(Config.STATISTICS_URL, payload, timeout=60000)
        
        if result and result.get('success'):
            data = result.get('data', {}).get('data', {})
            total_hours = data.get('ANALYSIS_HOURS_NUM', '0')
            completed_hours = str(data.get('totalHours', 0))
            
            if total_hours and completed_hours:
                try:
                    total_num = float(total_hours)
                    completed_num = float(completed_hours)
                    progress_percent = (completed_num / total_num * 100) if total_num > 0 else 0
                    
                    logger.info(f"学时统计 - 总学时: {total_hours}, 已完成: {completed_hours}, 进度: {progress_percent:.1f}%")
                    return total_hours, completed_hours, progress_percent
                except ValueError:
                    pass
        
        logger.warning("获取学时信息失败，使用默认值")
        return "0", "0", 0.0
    
    def _parse_duration(self, duration_str):
        """解析时长字符串为秒数"""
        if not duration_str or ':' not in duration_str:
            return 0
        
        try:
            parts = duration_str.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except:
            pass
        
        return 0