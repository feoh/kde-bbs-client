# Overview

KDE BBS Client is a modern KDE client for old school telnet based BBS systems.

## Configuration

On startup, the client checks for the existence of its configuration file located at
$HOME/.config/kdebbsclient/client-config.yaml.

If that file does not exist, a nicely styled dialog appears that has prompt fields for BBS name, BBS internet address
(which accepts a FQDN or an IPv4 or IPv6 address), an optional port, username, and password (the password is hidden on
entry).

When the user clicks Submit the configuration file mentioned above is created with those values.

## BBS Chooser

Once the necessary configuration is in place, the client displays a list of BBS systems to connect to including name and
address, and allows the user to choose one and click the Connect button.

## Main Connection and Interaction Loop
Once that happens, the client makes a telnet connection to the address given, displaying the output in a nicely styled
text display window suitable for reading large volumes of text.

TODO: Figure out how to detect when a user creates a new post and offer to spawn their editor of choice - as defined by
the $EDITOR environment variable to edit it.
