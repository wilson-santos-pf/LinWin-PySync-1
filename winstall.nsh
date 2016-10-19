RequestExecutionLevel admin
!verbose 4

LicenseData "LICENSE"
Name "LocalBox"
Icon "localbox.ico"

!include textlog.nsh

!include LogicLib.nsh
!include MUI2.nsh
!addincludedir .
!include EnumUsersReg.nsh
!include "FileAssociation.nsh"

#trimming based on http://nsis.sourceforge.net/Remove_leading_and_trailing_whitespaces_from_a_string
!define Trim "!insertmacro Trim"
!macro Trim ResultVar String
  Push "${String}"
  Call RemoveFinalSlash
  Pop "${ResultVar}"
!macroend

Function RemoveFinalSlash
  Exch $R1 ; Original string
  Push $R2
trimloop:
  StrCpy $R2 "$R1" 1 -1
  StrCmp "$R2" "\" TrimRight
  Goto Done
trimright:
  StrCpy $R1 "$R1" -1
  Goto trimloop
Done:
  Pop $R2
  Exch $R1
FunctionEnd

# Where we want the files installed on a 'clean' system
InstallDir "$PROGRAMFILES\LocalBox"
# Using the python location for a python interpreter installed by us
InstallDirRegKey HKLM "Software\Python\PythonCore\2.7\InstallPath" ""

Function .onInit
  # using the first python install we can find as install dir
  EnumRegKey $0 HKLM "Software\Python\PythonCore" 0
  ReadRegStr $1 HKLM "Software\Python\PythonCore\$0\InstallPath" ""
  ${If} "$1" != ""
    StrCpy $INSTDIR "$1"
  ${Else}
    EnumRegKey $0 HKCU "Software\Python\PythonCore" 0
    ReadRegStr $1 HKCU "Software\Python\PythonCore\$0\InstallPath" ""
    ${If} "$1" != ""
      StrCpy $INSTDIR "$1"
    ${EndIf}
  ${EndIf}
  ${LogSetFileName} "install.log"
  ${LogSetOn}
  UserInfo::GetAccountType
  pop $0
  ${If} $0 != "admin" ;Require admin rights on NT4+
      MessageBox mb_iconstop "Administrator rights required!"
      SetErrorLevel 740 ;ERROR_ELEVATION_REQUIRED
      ${LogText} "Tried instalation without being administrator."
      Quit
  ${EndIf}

FunctionEnd

Function .onVerifyInstDir
  ${LogText} "INSTDIR: $INSTDIR"
  EnumRegKey $0 HKLM "Software\Python\PythonCore" 0
  ReadRegStr $1 HKLM "Software\Python\PythonCore\$0\InstallPath" ""
  ${Trim} "$2" "$1"
  ${LogText} "HKLM: $2"
  StrCmp "$2" "" curuser compare
  curuser:
    EnumRegKey $0 HKCU "Software\Python\PythonCore" 0
    ReadRegStr $1 HKCU "Software\Python\PythonCore\$0\InstallPath" ""
    ${Trim} "$2" "$1"
    ${LogText} "HKCU: $2"
    StrCmp "$2" "" finishing compare
  compare:
    ${LogText} "comparing $INSTDIR to $2"
    StrCmp "$2" "$INSTDIR" finishing aborting
  aborting:
    ${LogText} "Aborting"
    Abort
  finishing:
    ${LogText} "Finihing"
FunctionEnd


Page license
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage components



UninstPage instfiles

Section Install
  SetOverwrite Try
  SetOutPath $TEMP



  File /oname=$TEMP\python.msi win/python-2.7.11.msi
  File /oname=$TEMP\wxpython.exe win/wxPython3.0-win32-3.0.2.0-py27.exe
  File /oname=$TEMP\pycrypto.exe win/pycrypto-2.6.win32-py2.7.exe
  File /oname=$TEMP\localBoxSync.exe LocalBoxSync-0.1a*.win32.exe

  CreateShortcut "$SMSTARTUP\LocalBox.lnk" "$INSTDIR\pythonw.exe" "-m sync" "$INSTDIR\localbox\localbox.ico"

  CreateDirectory "$SMPROGRAMS\LocalBox\"
  CreateDirectory "$APPDATA\localbox\"
  CreateShortcut "$SMPROGRAMS\LocalBox\LocalBox sync.lnk" "$INSTDIR\pythonw.exe" "-m sync" "$INSTDIR\localbox\localbox.ico"
  CreateShortcut "$SMPROGRAMS\LocalBox\LocalBox log.lnk" "$APPDATA\localbox\localbox-sync.log"
  CreateShortcut "$SMPROGRAMS\LocalBox\LocalBox Uninstaller.lnk" "$INSTDIR\LocalBoxUninstaller.exe"

  CreateDirectory $INSTDIR\Lib\site-packages\sync\locale\nl\LC_MESSAGES
  File "/oname=$INSTDIR\Lib\site-packages\sync\locale\nl\LC_MESSAGES\localboxsync.mo" sync/locale/nl/LC_MESSAGES/localboxsync.mo 
  CreateDirectory $INSTDIR\Lib\site-packages\sync\locale\en\LC_MESSAGES
  File "/oname=$INSTDIR\Lib\site-packages\sync\locale\en\LC_MESSAGES\localboxsync.mo" sync/locale/en/LC_MESSAGES/localboxsync.mo 
  File "/oname=$INSTDIR\run.bat" run.bat
  File "/oname=$INSTDIR\get-pip.py" get-pip.py
  File "/oname=$INSTDIR\install-pip.bat" install_pip.bat

  WriteUninstaller $INSTDIR\LocalBoxUninstaller.exe

  ExecWait 'msiexec.exe /i $TEMP\python.msi TARGETDIR="$INSTDIR" ALLUSERS=1 ADDLOCAL=DefaultFeature,Extensions,TclTk,Tools /quiet'
  ExecWait "$TEMP\wxpython.exe /silent /quiet"
  ExecWait "$TEMP\pycrypto.exe /quiet /silent"
  ExecWait "$TEMP\LocalBoxSync.exe /quiet /silent"
  #ExecWait '$INSTDIR\install-pip.bat "$INSTDIR" > c:\install_pip.log'

  ${registerExtension} "$INSTDIR\run.bat" ".lox" "LocalBox_File"
SectionEnd

SectionGroup "un.uninstall"
Section "un.Start Menu"
    delete "$SMSTARTUP\LocalBox.lnk"
    delete "$SMPROGRAMS\LocalBox\LocalBox sync.lnk"
    delete "$SMPROGRAMS\LocalBox\LocalBox log.lnk"
SectionEnd

Section "un.Program Files"
    rmDir /r /rebootok "$INSTDIR"
SectionEnd

Section "un.AppData"
    ${un.EnumUsersReg} un.DelAppData localbox
SectionEnd
SectionGroupEnd

Function un.DelAppData
    Pop $0
    ReadRegStr $0 HKU "$0\Volatile Environment" "AppData"
    rmDir /r /REBOOTOK $0\localbox

    ${unregisterExtension} ".lox" "LocalBox_File"
FunctionEnd



OutFile LocalBoxInstaller.exe
