function remove_python_from_path() {
  tmp=`echo $PATH | sed 's/:/ /g'`
  PATH=
  for d in $tmp;
  do
    if [[ $d =~ /custom/python ]]; then
      echo "Removing dir $d from PATH"
    else
      PATH=$PATH:$d
    fi
  done
}

remove_python_from_path
PATH=/custom/python-2.5.1-memdebug/bin:$PATH

if [[ ${PYTHONPATH:-notset} =~ /custom/python ]]; then
  echo "unsetting PYTHONPATH"
  unset PYTHONPATH
fi
if [[ ${PYTHONHOME:-notset} =~ /custom/python ]]; then
  echo "unsetting PYTHONHOME"
  unset PYTHONHOME
fi
