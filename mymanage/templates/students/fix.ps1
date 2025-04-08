# 删除重复变量声明  
$content = Get-Content -Path 'student_practice.html' -Raw  
$pattern = "// 定义全局变量[\r\n\s]+let canEnd = false;[\r\n\s]+let isPaused = false;[\r\n\s]+let practiceTimer = null;[\r\n\s]+let pauseStartTime = null;"  
$content = $content -replace $pattern, ""  
