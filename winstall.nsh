RequestExecutionLevel admin

LicenseData "LICENSE"
Name "LocalBox"
Icon "localbox.ico"

!include LogicLib.nsh
!include MUI2.nsh
!addincludedir .
!include EnumUsersReg.nsh

var CHECKBOX

Function .onInit
UserInfo::GetAccountType
pop $0
${If} $0 != "admin" ;Require admin rights on NT4+
    MessageBox mb_iconstop "Administrator rights required!"
    SetErrorLevel 740 ;ERROR_ELEVATION_REQUIRED
    Quit
${EndIf}
StrCpy $INSTDIR "$PROGRAMFILES\Localbox"
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

  ;File /oname=$TEMP\python.msi win/python-2.7.11.msi
  ;File /oname=$TEMP\wxpython.exe win/wxPython3.0-win32-3.0.2.0-py27.exe
  ;File /oname=$TEMP\pycrypto.exe win/pycrypto-2.6.win32-py2.7.exe
  ;File /oname=$TEMP\localBoxSync.exe LocalboxSync-0.1a*.win32.exe

  CreateShortcut "$SMSTARTUP\localbox.lnk" "$INSTDIR\pythonw.exe" "-m sync" "$INSTDIR\localbox\localbox.ico"

  CreateDirectory "$SMPROGRAMS\localbox\"
  CreateDirectory "$APPDATA\localbox\"
  CreateShortcut "$SMPROGRAMS\localbox\localbox sync.lnk" "$INSTDIR\pythonw.exe" "-m sync" "$INSTDIR\localbox\localbox.ico"
  CreateShortcut "$SMPROGRAMS\localbox\localbox log.lnk" "$APPDATA\localbox\localbox-sync.log"

  CreateDirectory $INSTDIR\Lib\site-packages\sync\locale\nl\LC_MESSAGES
  File "/oname=$INSTDIR\Lib\site-packages\sync\locale\nl\LC_MESSAGES\localboxsync.mo" sync/locale/nl/LC_MESSAGES/localboxsync.mo 

  WriteUninstaller $INSTDIR\LocalBoxUninstaller.exe

  ;ExecWait 'msiexec.exe /i $TEMP\python.msi TARGETDIR="$INSTDIR" /quiet'
  ;ExecWait "$TEMP\wxpython.exe /silent"
  ;ExecWait "$TEMP\pycrypto.exe"
  ;ExecWait "$TEMP\LocalBoxSync.exe"
SectionEnd

SectionGroup "un.uninstall"
Section "un.Start Menu"
    delete "$SMSTARTUP\localbox.lnk"
    delete "$SMPROGRAMS\localbox\localbox sync.lnk"
    delete "$SMPROGRAMS\localbox\localbox log.lnk"
    ;rmDir /r /rebootok "$INSTDIR"
SectionEnd

Section "un.Program Files"
    rmDir /r /rebootok "$INSTDIR"
    ;${NSD_CreateCheckbox} 120u -18u 50% 12u "Delete AppData?"
SectionEnd

Section "un.AppData"
    #Pop $CHECKBOX
    #GetFunctionAddress $0 un.AppData
    #nsDialogs::OnClick $CHECKBOX $0
    #${If} $CHECKBOX ==  ${BST_CHECKED}
    ${un.EnumUsersReg} un.DelAppData localbox
    #${EndIf}
SectionEnd
SectionGroupEnd

Function un.DelAppData
    Pop $0
    ReadRegStr $0 HKU "$0\Volatile Environment" "AppData"
    rmDir /r /REBOOTOK $0\localbox
FunctionEnd

OutFile LocalBoxInstaller.exe
