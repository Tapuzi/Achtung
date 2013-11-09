/* 
       ArduBee 
       alon7
  
      The circuit:
      * RX is digital pin 2 (connect to TX of XBee)
      * TX is digital pin 2 (connect to RX of XBee)
  */
#include <SoftwareSerial.h>

// Declaring a software serial for the xbee module
SoftwareSerial xbee(2, 3); // Rx, Tx

const int local_led_pin = 13;
String incomingCommand;
String UID = "1111";
//String UID = "2222";

class Command
{
    public:
        Command(String command);
        String uid;
        String key;
        String value;
};

void setup() {
      // Local serial (Computer)
      Serial.begin(57600);
      Serial.println("Arduino started receiving bytes via XBee");
      
      // Setup local pin
      pinMode(local_led_pin, OUTPUT); 
      
      // Set the data rate for the SoftwareSerial port
      xbee.begin(9600);
}

void loop() {
    while (xbee.available() > 0)
    {
        char received = xbee.read();
        if (received == '\n') {
            Command current_command(incomingCommand);
            if (current_command.uid == UID) {
              Serial.println("Command for me:");
              Serial.print("uid=" + current_command.uid);
              Serial.print(" ");
              Serial.print("key=" + current_command.key);
              Serial.print(" ");
              Serial.print("value=" + current_command.value);
              Serial.println("");
              digitalWrite(local_led_pin, HIGH);
              delay(2000);
              digitalWrite(local_led_pin, LOW);
            } else {
              Serial.println("This command is not for me!");
            }
            
            incomingCommand = "";
        }
        else {
             incomingCommand += received;   
        }
    }
}

Command::Command(String command)
{
    this->uid = "-1";
    this->key = "-1";
    this->value = "-1";
    
    int beginIdx = 0;
    int idx = command.indexOf(";");
    String arg;

    while (idx != -1)
    {
      arg = command.substring(beginIdx, idx);
      
      int arg_length = arg.length();
      int split_index = arg.indexOf("=");
      
      String key = arg.substring(0, split_index);
      String value = arg.substring(split_index+1, arg_length);
      if (key == "uid") {
        this->uid = value;
      }
      else if (key == "key") {
        this->key = value;
      }
      else if (key == "value") {
        this->value = value;
      }

      beginIdx = idx + 1;
      idx = command.indexOf(";", beginIdx);
    }
    
}