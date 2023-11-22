echo * enter pre-boot
pushd %~dp0

call win\15-update-pyenv.bat
if errorlevel 1 (
  echo ERROR: win\15-update-pyenv.bat
  exit /b 1
)

popd
echo * leave pre-boot

exit /b 0
