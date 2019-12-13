#!/usr/bin/perl
exec '/usr/bin/ssh', '-A', map {$_ eq '-oForwardAgent=no' ? ( ) : $_} @ARGV