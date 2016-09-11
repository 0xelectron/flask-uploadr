echo off
set dir_path = 'path_to_soundcloudrepo'
cd %dir_path%
Powershell.exe -ExecutionPolicy RemoteSigned -NoExit -NonInteractive -windowstyle hidden -file .\runserver.ps1
