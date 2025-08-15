@echo off
chcp 65001 >nul
echo =====================================
echo 简单字幕视频匹配工具
echo =====================================
echo.

REM 配置区域 - 请根据需要修改
set "SUBTITLE_DIR=F:\1MOV\av1\srt"
set "VIDEO_DIR=F:\1MOV\av1\#整理完成"
set "SUBTITLE_EXT=*.srt"
set "VIDEO_EXT=*.mp4;*.mkv;*.avi;*.mov"

echo 配置信息：
echo 字幕目录：%SUBTITLE_DIR%
echo 视频目录：%VIDEO_DIR%
echo 字幕格式：%SUBTITLE_EXT%
echo 视频格式：%VIDEO_EXT%
echo.

set /p confirm="确认配置正确？(y/n): "
if /i not "%confirm%"=="y" (
    echo 请修改脚本中的配置区域后重新运行。
    pause
    exit /b 0
)

echo.
echo =====================================
echo 扫描文件
echo =====================================
echo.

echo 正在扫描字幕文件...
dir "%SUBTITLE_DIR%\%SUBTITLE_EXT%" /B /S > subtitles_list.txt 2>nul
if %ERRORLEVEL% neq 0 (
    echo 未找到字幕文件！
    pause
    exit /b 1
)

echo 正在扫描视频文件...
(
for %%e in (%VIDEO_EXT%) do (
    dir "%VIDEO_DIR%\%%e" /B /S 2>nul
)
) > videos_list.txt

if not exist videos_list.txt (
    echo 未找到视频文件！
    pause
    exit /b 1
)

REM 检查是否有内容
for %%i in (videos_list.txt) do if %%~zi==0 (
    echo 未找到视频文件！
    pause
    exit /b 1
)

echo.
echo 找到的字幕文件：
type subtitles_list.txt
echo.
echo 找到的视频文件：
type videos_list.txt
echo.

echo =====================================
echo 智能匹配分析
echo =====================================
echo.

echo 正在生成匹配报告...

REM 使用PowerShell进行智能匹配
powershell -ExecutionPolicy Bypass -Command ^
"$subtitles = Get-Content 'subtitles_list.txt'; ^
$videos = Get-Content 'videos_list.txt'; ^
$matches = @(); ^
foreach ($sub in $subtitles) { ^
    $subName = [System.IO.Path]::GetFileNameWithoutExtension($sub); ^
    $subClean = $subName -replace '[^\w\s]', '' -replace '\s+', ' '; ^
    $bestMatch = $null; ^
    $bestScore = 0; ^
    foreach ($vid in $videos) { ^
        $vidName = [System.IO.Path]::GetFileNameWithoutExtension($vid); ^
        $vidClean = $vidName -replace '[^\w\s]', '' -replace '\s+', ' '; ^
        $score = 0; ^
        $subWords = $subClean.Split(' '); ^
        $vidWords = $vidClean.Split(' '); ^
        foreach ($word in $subWords) { ^
            if ($word.Length -gt 2 -and $vidClean -like \"*$word*\") { ^
                $score += $word.Length; ^
            } ^
        } ^
        if ($score -gt $bestScore) { ^
            $bestScore = $score; ^
            $bestMatch = $vid; ^
        } ^
    } ^
    if ($bestMatch -and $bestScore -gt 5) { ^
        $matches += [PSCustomObject]@{ ^
            Subtitle = $sub; ^
            Video = $bestMatch; ^
            Score = $bestScore; ^
            SubtitleName = [System.IO.Path]::GetFileName($sub); ^
            VideoName = [System.IO.Path]::GetFileName($bestMatch) ^
        } ^
    } ^
} ^
Write-Host '匹配结果：'; ^
$matches | ForEach-Object { ^
    Write-Host \"字幕: $($_.SubtitleName) <-> 视频: $($_.VideoName) (评分: $($_.Score))\"; ^
} ^
$matches | Export-Csv -Path 'match_results.csv' -Encoding UTF8 -NoTypeInformation; ^
Write-Host \"详细结果已保存到 match_results.csv\""

echo.
echo =====================================
echo 匹配完成
echo =====================================
echo.

if exist match_results.csv (
    echo 匹配结果已保存到 match_results.csv
    echo.
    echo 操作选项：
    echo 1. 查看详细匹配结果
    echo 2. 生成复制脚本 (保留原文件)
    echo 3. 生成移动脚本 (删除原文件)
    echo 4. 退出
    echo.
    set /p choice="请选择 (1-4): "
    
    if "%choice%"=="1" goto view_results
    if "%choice%"=="2" goto generate_copy_script
    if "%choice%"=="3" goto generate_move_script
    if "%choice%"=="4" goto cleanup
) else (
    echo 未生成匹配结果，可能没有找到合适的匹配。
)

goto cleanup

:view_results
echo.
echo 详细匹配结果：
powershell -ExecutionPolicy Bypass -Command ^
"Import-Csv 'match_results.csv' | Format-Table -AutoSize"
echo.
pause
goto cleanup

:generate_copy_script
echo.
echo 生成复制脚本...
echo @echo off > copy_subtitles.bat
echo chcp 65001 ^>nul >> copy_subtitles.bat
echo echo ===================================== >> copy_subtitles.bat
echo echo 执行字幕复制操作 >> copy_subtitles.bat
echo echo ===================================== >> copy_subtitles.bat
echo echo. >> copy_subtitles.bat

powershell -ExecutionPolicy Bypass -Command ^
"Import-Csv 'match_results.csv' | ForEach-Object { ^
    $videoDir = Split-Path $_.Video; ^
    $videoName = [System.IO.Path]::GetFileNameWithoutExtension($_.Video); ^
    $newSubName = $videoName + '.srt'; ^
    $targetPath = Join-Path $videoDir $newSubName; ^
    Add-Content 'copy_subtitles.bat' \"echo 复制: $($_.SubtitleName) -^> $newSubName\"; ^
    Add-Content 'copy_subtitles.bat' \"copy `\"$($_.Subtitle)`\" `\"$targetPath`\"\"; ^
    Add-Content 'copy_subtitles.bat' 'echo.'; ^
}"

echo echo 复制操作完成！ >> copy_subtitles.bat
echo pause >> copy_subtitles.bat

echo 复制脚本已生成：copy_subtitles.bat
echo 运行该脚本将复制字幕文件到对应视频目录。
goto cleanup

:generate_move_script
echo.
echo 生成移动脚本...
echo @echo off > move_subtitles.bat
echo chcp 65001 ^>nul >> move_subtitles.bat
echo echo ===================================== >> move_subtitles.bat
echo echo 执行字幕移动操作 >> move_subtitles.bat
echo echo ===================================== >> move_subtitles.bat
echo echo 警告：此操作将删除原始字幕文件！ >> move_subtitles.bat
echo set /p confirm="确定要继续吗？(y/n): " >> move_subtitles.bat
echo if /i not "%%confirm%%"=="y" ( >> move_subtitles.bat
echo     echo 操作已取消。 >> move_subtitles.bat
echo     pause >> move_subtitles.bat
echo     exit /b 0 >> move_subtitles.bat
echo ^) >> move_subtitles.bat
echo echo. >> move_subtitles.bat

powershell -ExecutionPolicy Bypass -Command ^
"Import-Csv 'match_results.csv' | ForEach-Object { ^
    $videoDir = Split-Path $_.Video; ^
    $videoName = [System.IO.Path]::GetFileNameWithoutExtension($_.Video); ^
    $newSubName = $videoName + '.srt'; ^
    $targetPath = Join-Path $videoDir $newSubName; ^
    Add-Content 'move_subtitles.bat' \"echo 移动: $($_.SubtitleName) -^> $newSubName\"; ^
    Add-Content 'move_subtitles.bat' \"move `\"$($_.Subtitle)`\" `\"$targetPath`\"\"; ^
    Add-Content 'move_subtitles.bat' 'echo.'; ^
}"

echo echo 移动操作完成！ >> move_subtitles.bat
echo pause >> move_subtitles.bat

echo 移动脚本已生成：move_subtitles.bat
echo 运行该脚本将移动字幕文件到对应视频目录。
goto cleanup

:cleanup
echo.
echo =====================================
echo 清理临时文件
echo =====================================
echo.

if exist subtitles_list.txt del subtitles_list.txt
if exist videos_list.txt del videos_list.txt

echo 生成的文件：
if exist match_results.csv echo - match_results.csv (匹配结果)
if exist copy_subtitles.bat echo - copy_subtitles.bat (复制脚本)
if exist move_subtitles.bat echo - move_subtitles.bat (移动脚本)
echo.
echo 完成！
pause
