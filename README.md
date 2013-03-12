# smtpsink - SMTP Sink Server #
(c)2013 DigiTar, All Rights Reserved

Simple SMTP server that will listen on the spec'd port and stuff messages into text files in the spec'd directory. Useful as a sink for functional tests on other SMTP servers/clients.

## Requirements ##

* Python 2.6 or newer
* Twisted 12.0 or newer.

Run `easy_install twisted` to install the latest version of Twisted.

## Usage ##

__smtpsink__ is a Twisted plugin meaning you need to add the directory this README is in to your `PATH`, then you can just run:

`twistd smtpsink -p <port_number> -d <message_directory_path>`

Add `-l <log_file_path>` to change where twistd puts its log file, or add `--nodaemon` to keep __smtpsink__  and it's logging output in the foreground.

## Message File Format ##

When __smtpsink__ receives a message, it stores it in a text file in the directory you specified. The format for the name of each message file is:

`<UNIX_timestamp>_<helo_contents>_<mail_from>_<rcpt_to>.txt`

The contents of the message file is the raw body of the message as received in the `DATA` section of the SMTP transmission. Only one message is per file.
