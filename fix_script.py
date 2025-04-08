import re  
"with open('mymanage/templates/students/student_practice.html', 'r', encoding='utf-8') as f:"  
"    content = f.read()"  
"content = re.sub(r'// 定义全局变量\\s+let canEnd.*?let pauseStartTime = null;', '', content, flags=re.DOTALL)"  
"with open('mymanage/templates/students/student_practice.html', 'w', encoding='utf-8') as f:"  
"    f.write(content)"  
"print('变量定义修复完成')"  
