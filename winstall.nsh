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
InstallDir "$PROGRAMFILES\Localbox"
# Using the python location for a python interpreter installed by us
InstallDirRegKey HKLM "Software\Python\PythonCore\2.7\InstallPath" ""

Function .onInit
  UserInfo::GetAccountType
  pop $0
  ${If} $0 != "admin" ;Require admin rights on NT4+
      MessageBox mb_iconstop "Administrator rights required!"
      SetErrorLevel 740 ;ERROR_ELEVATION_REQUIRED
     Quit
  ${EndIf}
  ;StrCpy $INSTDIR "$PROGRAMFILES\Localbox"
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
    StrCmp "$2" "" aborting compare
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
  File /oname=$TEMP\localBoxSync.exe LocalboxSync-0.1a*.win32.exe

  CreateShortcut "$SMSTARTUP\localbox.lnk" "$INSTDIR\pythonw.exe" "-m sync" "$INSTDIR\localbox\localbox.ico"

  CreateDirectory "$SMPROGRAMS\localbox\"
  CreateDirectory "$APPDATA\localbox\"
  CreateShortcut "$SMPROGRAMS\localbox\localbox sync.lnk" "$INSTDIR\pythonw.exe" "-m sync" "$INSTDIR\localbox\localbox.ico"
  CreateShortcut "$SMPROGRAMS\localbox\localbox log.lnk" "$APPDATA\localbox\localbox-sync.log"

  CreateDirectory $INSTDIR\Lib\site-packages\sync\locale\nl\LC_MESSAGES
  File "/oname=$INSTDIR\Lib\site-packages\sync\locale\nl\LC_MESSAGES\localboxsync.mo" sync/locale/nl/LC_MESSAGES/localboxsync.mo 

  WriteUninstaller $INSTDIR\LocalBoxUninstaller.exe

  ExecWait 'msiexec.exe /i $TEMP\python.msi TARGETDIR="$INSTDIR" /quiet /fams /jm'
  ExecWait "$TEMP\wxpython.exe /silent"
  ExecWait "$TEMP\pycrypto.exe"
  ExecWait "$TEMP\LocalBoxSync.exe"
SectionEnd

SectionGroup "un.uninstall"
Section "un.Start Menu"
    delete "$SMSTARTUP\localbox.lnk"
    delete "$SMPROGRAMS\localbox\localbox sync.lnk"
    delete "$SMPROGRAMS\localbox\localbox log.lnk"
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
FunctionEnd



OutFile LocalBoxInstaller.exe
