#!/usr/bin/env perl

print "checking if foo matches foo|bar\n";
if ( "foo" =~ /foo|bar/ ) {
  print "\tmatched\n";
} else {
  print "\tno match\n";
}
print "\n";

print "checking if a matches a|bc\n";
if ( "a" =~ /a|bc/ ) {
  print "\tmatched\n";
} else {
  print "\tno match\n";
}
print "\n";

print "checking if abcdef matches abc|def{2}\n";
if ( "abcdef" =~ /abc|def{2}/ ) {
  print "\tmatched\n";
} else {
  print "\tno match\n";
}
print "\n";

print "checking if abc matches abc|def{2}\n";
if ( "abc" =~ /abc|def{2}/ ) {
  print "\tmatched\n";
} else {
  print "\tno match\n";
}
print "\n";

print "checking if def matches abc|def{2}\n";
if ( "def" =~ /abc|def{2}/ ) {
  print "\tmatched\n";
} else {
  print "\tno match\n";
}
print "\n";

print "checking if defdef matches abc|def{2}\n";
if ( "defdef" =~ /abc|def{2}/ ) {
  print "\tmatched\n";
} else {
  print "\tno match\n";
}
print "\n";

print "checking if deff matches abc|def{2}\n";
if ( "deff" =~ /abc|def{2}/ ) {
  print "\tmatched\n";
} else {
  print "\tno match\n";
}
print "\n";
