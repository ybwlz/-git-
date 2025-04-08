with open('mymanage/templates/students/student_practice.html', 'r', encoding='utf-8') as f: 
    content = f.read() 
content = content.replace('        // 定义全局变量\\n        let canEnd = false;\\n        let isPaused = false;\\n        let practiceTimer = null;\\n        let pauseStartTime = null;', ''') 
with open('mymanage/templates/students/student_practice.html', 'w', encoding='utf-8') as f: 
    f.write(content)
