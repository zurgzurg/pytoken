function remove_python_from_path() {
  tmp=`echo $PATH | sed 's/:/ /g'`
  PATH=
  colon=
  for d in $tmp;
  do
    if [[ $d == *python* ]]; then
      echo "Removing dir $d from PATH"
    else
      PATH=${PATH}${colon}${d}
      colon=":"
    fi
  done
}

function usage() {
    echo "Usage"
    echo "   select_python.sh  -memdebug | -stock"
    echo ""
}


function doit() {
    remove_python_from_path
    pydir=/home/ramb/src/pylex/python-2.5.1${1}/bin
    echo "Adding ${pydir} to PATH"
    PATH=${pydir}:$PATH

    if [[ ${PYTHONPATH:-notset} != notset ]]; then
	echo "unsetting PYTHONPATH"
	unset PYTHONPATH
    fi
    if [[ ${PYTHONHOME:-notset} != notset ]]; then
	echo "unsetting PYTHONHOME"
	unset PYTHONHOME
    fi
}

if [[ $# -eq 1 ]]; then
    if [[ $1 == "-stock" || $1 == "-memdebug" ]]; then
	doit $1
    else
	usage
    fi
else
    usage
fi
