echo ** enter update-pyenv
pushd %~dp0

@rem
@rem update pyenv
@rem

if not exist %_wspc_root%\venv (
  python -m venv %_wspc_root%\venv
  echo INFO: venv created
)

if exist %_wspc_root%\venv\Scripts\activate.bat (
  call %_wspc_root%\venv\Scripts\activate.bat

  python -m pip install -U pip
  pip install -r pip\requirements.txt
)

popd
echo ** leave update-pyenv

exit /b 0
