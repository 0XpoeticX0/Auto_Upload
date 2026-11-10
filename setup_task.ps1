$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c cd /d E:\Project\youtube_video && python -m app.quran_verse.mix_scheduler --upload" -WorkingDirectory "E:\Project\youtube_video"
$trigger = New-ScheduledTaskTrigger -Daily -At 3:00PM
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "Daily_Quran_Mix_Recitation" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "Task Daily_Quran_Mix_Recitation registered successfully!"
