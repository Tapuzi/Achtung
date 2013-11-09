Achtung
=======

ACHTUNG!

Arduino
-------
###### Arduino code
- Each unit on field has it's own Unique identifier
- The unit processes only messages that are targeted for her
- We use the SoftwareSerial to emulate Tx & Rx so we won't have to put the XBee on the regular arduino Tx & Rx pins
- We use the legit serial to get real time messages (debugging) on host

> TODO:
> - Change the code that parses the command

###### XBee & PySerial (computer side)
- This is a module of XBee that is connected directly to the host computer
- It's configured to be the sender side by X-CTU software
- Through PySerial library we are able to send XBee messages to all the field units, they are responsible for parsing and handling as stated above

> TODO:
> - Write the PySerial part that talks to the XBee module.
> - Integrate the PySerial side with the achtung game for controling the field units
> - Connect the wheels and let this baby drive!

###### OpenCV (Bot detection)
> TODO: 
> - Fill this section with information 

###### PyGame (The game)
> TODO:
> - Fill this section with information (hgbyt?)

###### SmartWatch logic ?
> TODO:
> - Fill this section with information
