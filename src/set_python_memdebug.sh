function remove_python_from_path() {
  tmp=`echo $PATH | sed 's/:/ /g'`
  PATH=
  for d in $tmp;
  do
    if [[ $d =~ /custom/python || $d =~ /home/ramb/src/pylex ]]; then
      echo "Removing dir $d from PATH"
    else
      PATH=$PATH:$d
    fi
  done
}

remove_python_from_path

if [[ ${PYTHONPATH:-notset} =~ /custom/python ]]; then
  echo "unsetting PYTHONPATH"
  unset PYTHONPATH
fi
if [[ ${PYTHONHOME:-notset} =~ /custom/python ]]; then
  echo "unsetting PYTHONHOME"
  unset PYTHONHOME
fi

if [[ `hostname` =~ maple ]]; then
  pydir=/custom/python-2.5.1-memdebug/bin
  export PYINC=/custom/python-2.5.1-memdebug/include/python2.5
else
  pydir=/home/ramb/src/pylex/python-2.5.1-memdebug/bin
  export PYINC=/home/ramb/src/pylex/python-2.5.1-memdebug/include/python2.5
fi
PATH=$pydir:$PATH
echo "Added $pydir to PATH"
