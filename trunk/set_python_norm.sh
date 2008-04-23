function remove_python_from_path() {
  tmp=`echo $PATH | sed 's/:/ /g'`
  PATH=
  colon=
  for d in $tmp;
  do
    echo "checking dir $d"
    if [[ $d == *python* ]]; then
      echo "Removing dir $d from PATH"
    else
      PATH=${PATH}${colon}${d}
      colon=":"
    fi
  done
}

remove_python_from_path
PATH=/home/ramb/src/pylex/python-2.5.1-stock/bin:$PATH

if [[ ${PYTHONPATH:-notset} != notset ]]; then
  echo "unsetting PYTHONPATH"
  unset PYTHONPATH
fi
if [[ ${PYTHONHOME:-notset} != notset ]]; then
  echo "unsetting PYTHONHOME"
  unset PYTHONHOME
fi
